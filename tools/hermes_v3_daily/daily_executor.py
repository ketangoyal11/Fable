"""Hermes V3 Daily — Daily Executor.

Computes daily indicators, applies Darvas filter, and gates entries with
1h/15m trend confirmation. No ADX, no strong candle.
"""
import pandas as pd
import numpy as np

from .weekly_planner import ema, sma, compute_atr


def compute_daily_indicators(df_daily, cfg):
    """Compute all daily indicators matching the V3 Pine script logic.

    No ADX. No strong candle. Breakout = close > prior 20-bar high.
    """
    c = cfg["strategy"]
    ema_f, ema_s = c["ema_fast"], c["ema_slow"]
    sma10_n, sma20_n, sma50_n = c["sma10"], c["sma20"], c["sma50"]
    sma100_n, sma200_n = c["sma100"], c["sma200"]
    slope_len = c["slope_len"]
    atr_len = c["atr_len"]
    breakout_lb = c["breakout_lookback"]
    sl_type = c["sl_type"]
    sl_buf = c["sl_buffer_atr"]

    df = df_daily.copy()

    # --- EMAs ---
    df["daily_ema9"] = ema(df["close"], ema_f)
    df["daily_ema21"] = ema(df["close"], ema_s)

    # --- SMAs ---
    df["daily_sma10"] = sma(df["close"], sma10_n)
    df["daily_sma20"] = sma(df["close"], sma20_n)
    df["daily_sma50"] = sma(df["close"], sma50_n)
    df["daily_sma100"] = sma(df["close"], sma100_n)
    df["daily_sma200"] = sma(df["close"], sma200_n)

    # --- ATR ---
    df["daily_atr14"] = compute_atr(df, atr_len)

    # --- Short-term trend ---
    df["daily_short_stacked"] = (
        (df["daily_sma10"] > df["daily_sma20"]) &
        (df["daily_sma20"] > df["daily_sma50"])
    )
    df["daily_price_above_short"] = (
        (df["close"] > df["daily_sma10"]) &
        (df["close"] > df["daily_sma20"]) &
        (df["close"] > df["daily_sma50"])
    )
    df["daily_short_trend_ok"] = df["daily_short_stacked"] & df["daily_price_above_short"]

    # --- Long-term trend ---
    df["daily_long_stacked"] = (
        (df["daily_sma50"] > df["daily_sma100"]) &
        (df["daily_sma100"] > df["daily_sma200"])
    )
    df["daily_sma50_rising"] = df["daily_sma50"] > df["daily_sma50"].shift(slope_len)
    df["daily_sma100_rising"] = df["daily_sma100"] > df["daily_sma100"].shift(slope_len)
    df["daily_smas_rising"] = df["daily_sma50_rising"] & df["daily_sma100_rising"]
    df["daily_price_above_long"] = (
        (df["close"] > df["daily_sma50"]) &
        (df["close"] > df["daily_sma100"]) &
        (df["close"] > df["daily_sma200"])
    )
    df["daily_major_trend_ok"] = (
        (df["daily_long_stacked"] & df["daily_smas_rising"] & df["daily_price_above_long"])
        | df["daily_short_trend_ok"]
    )

    # --- EMA trend ---
    df["daily_ema_uptrend"] = df["daily_ema9"] > df["daily_ema21"]
    df["daily_price_above_ema"] = df["close"] > df["daily_ema21"]

    # --- Breakout (no strong candle — just close > prior 20-high) ---
    df["daily_high_20"] = df["high"].rolling(breakout_lb, min_periods=breakout_lb).max()
    df["daily_prev_high_20"] = df["daily_high_20"].shift(1)
    df["daily_breakout"] = df["close"] > df["daily_prev_high_20"]

    # --- Dynamic SL ---
    df["daily_low_5"] = df["low"].rolling(5, min_periods=5).min()
    if sl_type == "Consolidation Low":
        df["daily_dynamic_sl"] = df["daily_low_5"] - df["daily_atr14"] * sl_buf
    elif sl_type == "SMA 50":
        df["daily_dynamic_sl"] = df["daily_sma50"] - df["daily_atr14"] * sl_buf
    elif sl_type == "SMA 200":
        df["daily_dynamic_sl"] = df["daily_sma200"] - df["daily_atr14"] * sl_buf
    else:
        df["daily_dynamic_sl"] = df["daily_low_5"] - df["daily_atr14"] * sl_buf

    # --- Trailing SL levels ---
    df["daily_trail_sma20_sl"] = df["daily_sma20"] - df["daily_atr14"] * sl_buf
    df["daily_trail_sma50_sl"] = df["daily_sma50"] - df["daily_atr14"] * sl_buf

    # --- Trend breaks ---
    df["daily_ema_crossunder"] = (
        (df["daily_ema9"].shift(1) >= df["daily_ema21"].shift(1)) &
        (df["daily_ema9"] < df["daily_ema21"])
    )
    df["daily_sma_crossunder"] = (
        (df["daily_sma50"].shift(1) >= df["daily_sma100"].shift(1)) &
        (df["daily_sma50"] < df["daily_sma100"])
    )
    df["daily_trend_break"] = df["daily_ema_crossunder"] | df["daily_sma_crossunder"]

    return df


def compute_mtf_trend_filter(df_daily, df_1h, df_15m, cfg):
    """Compute 1h and 15m trend filter and merge into daily index.

    At each daily bar, checks:
    - 1h short_trend_ok AND 1h major_trend_ok
    - 15m short_trend_ok AND 15m major_trend_ok
    - mtf_trend_ok = both pass

    Returns daily DataFrame with mtf_trend_filter column added.
    """
    if df_1h is None or df_15m is None:
        df_daily = df_daily.copy()
        df_daily["mtf_trend_ok"] = True
        return df_daily

    # Compute indicators on intraday data
    c = cfg["strategy"]
    sma10_n, sma20_n, sma50_n = c["sma10"], c["sma20"], c["sma50"]
    sma100_n, sma200_n = c["sma100"], c["sma200"]
    slope_len = c["slope_len"]

    def compute_tf_trend(df_tf):
        d = df_tf.copy()
        d["sma10"] = sma(d["close"], sma10_n)
        d["sma20"] = sma(d["close"], sma20_n)
        d["sma50"] = sma(d["close"], sma50_n)
        d["sma100"] = sma(d["close"], sma100_n)
        d["sma200"] = sma(d["close"], sma200_n)

        d["short_stacked"] = (d["sma10"] > d["sma20"]) & (d["sma20"] > d["sma50"])
        d["price_above_short"] = (
            (d["close"] > d["sma10"]) & (d["close"] > d["sma20"]) & (d["close"] > d["sma50"])
        )
        d["short_trend_ok"] = d["short_stacked"] & d["price_above_short"]

        d["long_stacked"] = (d["sma50"] > d["sma100"]) & (d["sma100"] > d["sma200"])
        d["sma50_rising"] = d["sma50"] > d["sma50"].shift(slope_len)
        d["sma100_rising"] = d["sma100"] > d["sma100"].shift(slope_len)
        d["smas_rising"] = d["sma50_rising"] & d["sma100_rising"]
        d["price_above_long"] = (
            (d["close"] > d["sma50"]) & (d["close"] > d["sma100"]) & (d["close"] > d["sma200"])
        )
        d["major_trend_ok"] = (
            (d["long_stacked"] & d["smas_rising"] & d["price_above_long"])
            | d["short_trend_ok"]
        )

        d["trend_ok"] = d["short_trend_ok"] & d["major_trend_ok"]
        return d["trend_ok"]

    h1_trend = compute_tf_trend(df_1h)
    m15_trend = compute_tf_trend(df_15m)

    # Reindex to daily — use the LAST intraday bar of each day (point-in-time)
    h1_daily = h1_trend.resample("D").last().reindex(df_daily.index, method="ffill")
    m15_daily = m15_trend.resample("D").last().reindex(df_daily.index, method="ffill")

    # Reindexed to daily, fill NaN with True (data missing = don't block)
    h1_daily = h1_daily.fillna(True).astype(bool)
    m15_daily = m15_daily.fillna(True).astype(bool)

    df_daily = df_daily.copy()
    df_daily["mtf_trend_ok"] = (h1_daily & m15_daily).astype(bool)

    return df_daily


def build_daily_entry_signal(df_daily, weekly_state, darvas_pass, cfg):
    """Build the final daily entry signal.

    daily_entry_signal =
        weekly_active
        AND daily_major_trend_ok
        AND daily_ema_uptrend
        AND daily_price_above_ema
        AND daily_breakout
        AND daily_darvas_pass
        AND mtf_trend_ok

    No ADX. No strong candle.
    """
    df = df_daily.copy()

    # Required columns
    required = [
        "daily_major_trend_ok", "daily_ema_uptrend", "daily_price_above_ema",
        "daily_breakout",
    ]
    for col in required:
        if col not in df.columns:
            df[col] = False

    if "mtf_trend_ok" not in df.columns:
        df["mtf_trend_ok"] = True

    # Merge weekly_active from weekly_state
    weekly_active = pd.Series(False, index=df.index)
    if "weekly_active" in weekly_state.columns:
        weekly_active = weekly_state["weekly_active"].copy()
    weekly_active = weekly_active.reindex(df.index).fillna(False)

    # Darvas pass
    dp = pd.Series(True, index=df.index)
    if isinstance(darvas_pass, pd.Series):
        dp = darvas_pass.reindex(df.index).fillna(False)
    elif isinstance(darvas_pass, bool):
        dp = pd.Series(darvas_pass, index=df.index)

    df["daily_entry_signal"] = (
        weekly_active &
        df["daily_major_trend_ok"] &
        df["daily_ema_uptrend"] &
        df["daily_price_above_ema"] &
        df["daily_breakout"] &
        dp &
        df["mtf_trend_ok"]
    )

    return df

"""Hermes V3 Daily — Weekly Planner.

Runs the Pine Script "Staircase SMA TREND FILTER" logic on weekly bars,
fires L1/L2/L3 entries, and creates activation windows that gate daily entries.

Key outputs:
  w_entry_signal, w_L1_fire, w_L2_fire, w_L3_fire,
  w_activation_zone, w_activation_type, w_position_count,
  w_darvas_high, w_darvas_low, w_darvas_breakout, w_darvas_support
"""
import pandas as pd
import numpy as np


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def sma(series, period):
    return series.rolling(window=period, min_periods=period).mean()


def compute_atr(df, period=14):
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def compute_weekly_plan(df_weekly, cfg, darvas_len=20):
    """Compute the full weekly plan: indicators, entry signals, pyramiding, activation.

    Parameters:
      df_weekly: Weekly OHLCV DataFrame (DateTimeIndex, sorted)
      cfg: config dict
      darvas_len: lookback for weekly Darvas box

    Returns enriched DataFrame with w_ prefixed plan columns.
    """
    c = cfg["strategy"]
    ema_f, ema_s = c["ema_fast"], c["ema_slow"]
    sma10_n, sma20_n, sma50_n = c["sma10"], c["sma20"], c["sma50"]
    sma100_n, sma200_n = c["sma100"], c["sma200"]
    slope_len = c["slope_len"]
    atr_len = c["atr_len"]
    breakout_lb = c["breakout_lookback"]
    min_bars = c["min_bars_between_entries"]
    min_profit = c["min_profit_for_next_entry_pct"]
    lookahead = cfg["weekly_activation"]["activation_lookahead_bars"]

    df = df_weekly.copy()

    # --- EMAs ---
    df["w_ema9"] = ema(df["close"], ema_f)
    df["w_ema21"] = ema(df["close"], ema_s)

    # --- SMAs ---
    df["w_sma10"] = sma(df["close"], sma10_n)
    df["w_sma20"] = sma(df["close"], sma20_n)
    df["w_sma50"] = sma(df["close"], sma50_n)
    df["w_sma100"] = sma(df["close"], sma100_n)
    df["w_sma200"] = sma(df["close"], sma200_n)

    # --- ATR ---
    df["w_atr14"] = compute_atr(df, atr_len)

    # --- Short-term trend ---
    df["w_short_stacked"] = (
        (df["w_sma10"] > df["w_sma20"]) & (df["w_sma20"] > df["w_sma50"])
    )
    df["w_price_above_short"] = (
        (df["close"] > df["w_sma10"]) &
        (df["close"] > df["w_sma20"]) &
        (df["close"] > df["w_sma50"])
    )
    df["w_short_trend_ok"] = df["w_short_stacked"] & df["w_price_above_short"]

    # --- Long-term trend ---
    df["w_long_stacked"] = (
        (df["w_sma50"] > df["w_sma100"]) & (df["w_sma100"] > df["w_sma200"])
    )
    df["w_sma50_rising"] = df["w_sma50"] > df["w_sma50"].shift(slope_len)
    df["w_sma100_rising"] = df["w_sma100"] > df["w_sma100"].shift(slope_len)
    df["w_smas_rising"] = df["w_sma50_rising"] & df["w_sma100_rising"]
    df["w_price_above_long"] = (
        (df["close"] > df["w_sma50"]) &
        (df["close"] > df["w_sma100"]) &
        (df["close"] > df["w_sma200"])
    )
    df["w_major_trend_ok"] = (
        (df["w_long_stacked"] & df["w_smas_rising"] & df["w_price_above_long"])
        | df["w_short_trend_ok"]
    )

    # --- EMA trend ---
    df["w_ema_uptrend"] = df["w_ema9"] > df["w_ema21"]
    df["w_price_above_ema"] = df["close"] > df["w_ema21"]

    # --- Breakout (no strong candle) ---
    df["w_high_20"] = df["high"].rolling(breakout_lb, min_periods=breakout_lb).max()
    df["w_prev_high_20"] = df["w_high_20"].shift(1)
    df["w_breakout"] = df["close"] > df["w_prev_high_20"]

    # --- Weekly Darvas (using body) ---
    body_top = df[["open", "close"]].max(axis=1)
    body_bottom = df[["open", "close"]].min(axis=1)
    df["w_darvas_high"] = body_top.rolling(darvas_len, min_periods=darvas_len).max().shift(1)
    df["w_darvas_low"] = body_bottom.rolling(darvas_len, min_periods=darvas_len).min().shift(1)
    df["w_darvas_breakout"] = df["close"] > df["w_darvas_high"]
    df["w_darvas_support_ok"] = df["close"] > df["w_darvas_low"]

    # --- Weekly Entry Core (matching weekly V3, no strong candle) ---
    df["w_entry_signal"] = (
        df["w_major_trend_ok"] &
        df["w_ema_uptrend"] &
        df["w_price_above_ema"] &
        df["w_breakout"]
    )

    # --- Trend breaks for state machine ---
    df["w_ema_crossunder"] = (
        (df["w_ema9"].shift(1) >= df["w_ema21"].shift(1)) &
        (df["w_ema9"] < df["w_ema21"])
    )
    df["w_sma_crossunder"] = (
        (df["w_sma50"].shift(1) >= df["w_sma100"].shift(1)) &
        (df["w_sma50"] < df["w_sma100"])
    )
    df["w_trend_break"] = df["w_ema_crossunder"] | df["w_sma_crossunder"]

    # --- Pyramiding / Activation state machine ---
    df["w_activation_zone"] = False
    df["w_activation_type"] = ""  # "L1", "L2", "L3"
    df["w_weekly_entry_signal"] = False
    df["w_L1_fire"] = False
    df["w_L2_fire"] = False
    df["w_L3_fire"] = False
    df["w_position_count"] = 0

    pos_count = 0
    entry_prices = []
    last_entry_idx = -999

    for i in range(len(df)):
        if i < 50:
            continue

        signal = df["w_entry_signal"].iloc[i]
        close = df["close"].iloc[i]
        bars_since = i - last_entry_idx

        # Trend break resets everything
        if pos_count > 0 and df["w_trend_break"].iloc[i]:
            pos_count = 0
            entry_prices = []
            continue

        entry_ok = signal and bars_since >= min_bars
        fired = False
        activation_type = ""

        if entry_ok:
            if pos_count == 0:
                pos_count = 1
                entry_prices = [close]
                last_entry_idx = i
                fired = True
                activation_type = "L1"
                df.loc[df.index[i], "w_L1_fire"] = True

            elif pos_count == 1 and entry_prices[0] > 0:
                pnl_pct = (close - entry_prices[0]) / entry_prices[0] * 100
                if pnl_pct >= min_profit:
                    pos_count = 2
                    entry_prices.append(close)
                    last_entry_idx = i
                    fired = True
                    activation_type = "L2"
                    df.loc[df.index[i], "w_L2_fire"] = True

            elif pos_count == 2 and len(entry_prices) >= 2 and entry_prices[1] > 0:
                pnl_pct = (close - entry_prices[1]) / entry_prices[1] * 100
                if pnl_pct >= min_profit:
                    pos_count = 3
                    entry_prices.append(close)
                    last_entry_idx = i
                    fired = True
                    activation_type = "L3"
                    df.loc[df.index[i], "w_L3_fire"] = True

        if fired:
            end_idx = min(i + lookahead, len(df))
            df.loc[df.index[i:end_idx], "w_activation_zone"] = True
            df.loc[df.index[i:end_idx], "w_activation_type"] = activation_type
            df.loc[df.index[i], "w_weekly_entry_signal"] = True

        df.loc[df.index[i], "w_position_count"] = pos_count

    return df


def forward_fill_to_daily(weekly_plan_df, daily_index):
    """Forward-fill weekly activation and plan state to daily index.

    Returns DataFrame on daily_index with columns:
      weekly_active, activation_type, weekly_position_count,
      weekly_darvas_breakout, weekly_darvas_support_ok,
      weekly_major_trend_ok, weekly_short_trend_ok,
      weekly_ema_uptrend, w_L1_fire, w_L2_fire, w_L3_fire
    """
    daily_state = pd.DataFrame(index=daily_index)

    cols_to_ffill = [
        "w_activation_zone", "w_activation_type", "w_position_count",
        "w_darvas_breakout", "w_darvas_support_ok",
        "w_major_trend_ok", "w_short_trend_ok",
        "w_ema_uptrend",
    ]

    for col in cols_to_ffill:
        if col in weekly_plan_df.columns:
            daily_state[col] = weekly_plan_df[col].reindex(daily_index, method="ffill")

    # Fire columns: only true on the exact day, not forward-filled
    for fire_col in ["w_L1_fire", "w_L2_fire", "w_L3_fire", "w_weekly_entry_signal"]:
        if fire_col in weekly_plan_df.columns:
            daily_state[fire_col] = weekly_plan_df[fire_col].reindex(daily_index).fillna(False)

    # Clean column names for daily use
    daily_state["weekly_active"] = daily_state.get("w_activation_zone", pd.Series(False, index=daily_index))
    daily_state["weekly_activation_type"] = daily_state.get("w_activation_type", pd.Series("", index=daily_index))
    daily_state["weekly_position_count"] = daily_state.get("w_position_count", pd.Series(0, index=daily_index))
    daily_state["weekly_darvas_breakout"] = daily_state.get("w_darvas_breakout", pd.Series(False, index=daily_index))
    daily_state["weekly_darvas_support_ok"] = daily_state.get("w_darvas_support_ok", pd.Series(False, index=daily_index))
    daily_state["weekly_major_trend_ok"] = daily_state.get("w_major_trend_ok", pd.Series(False, index=daily_index))
    daily_state["weekly_short_trend_ok"] = daily_state.get("w_short_trend_ok", pd.Series(False, index=daily_index))
    daily_state["weekly_ema_uptrend"] = daily_state.get("w_ema_uptrend", pd.Series(False, index=daily_index))

    daily_state["weekly_active"] = daily_state["weekly_active"].fillna(False).astype(bool)
    daily_state["weekly_activation_type"] = daily_state["weekly_activation_type"].fillna("")

    return daily_state

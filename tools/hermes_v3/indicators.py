"""Hermes V3 Indicators — exact Pine Script "Staircase SMA TREND FILTER (33/33/34)" port.

All calculations match the Pine Script logic precisely:
- ATR uses EMA (RMA) smoothing, not SMA
- ADX uses Wilder's smoothing (EMA with alpha=1/period)
- breakout uses prior 20-bar high (shifted), not current bar
- majorTrendOK = (longTermStacked AND smasRising AND priceAboveLongSMAs) OR shortTermTrendOK
"""
import numpy as np
import pandas as pd


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def sma(series, period):
    return series.rolling(window=period, min_periods=period).mean()


def compute_atr(df, period=14):
    """ATR using RMA (EMA) smoothing — matches Pine ta.atr(14)."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def compute_adx(df, period=14):
    """ADX using Wilder's smoothing — matches Pine ta.dmi(14, 14)."""
    high, low, close = df["high"], df["low"], df["close"]
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr_val = compute_atr(df, period)
    # Wilder's smoothing: alpha = 1/period
    alpha = 1.0 / period
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=alpha, adjust=False).mean() / atr_val.replace(0, 1e-9)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=alpha, adjust=False).mean() / atr_val.replace(0, 1e-9)
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1e-9)
    adx = dx.ewm(alpha=alpha, adjust=False).mean()
    return adx, plus_di, minus_di


def compute_all_indicators(df, cfg, prefix=""):
    """Compute all EMA/SMA/ATR/ADX/trend signals matching the Pine script.

    Returns enriched DataFrame with all indicator and signal columns.
    """
    c = cfg["strategy"]
    ema_f, ema_s = c["ema_fast"], c["ema_slow"]
    sma10_n, sma20_n = c["sma10"], c["sma20"]
    sma50_n, sma100_n, sma200_n = c["sma50"], c["sma100"], c["sma200"]
    slope_len = c["slope_len"]
    atr_len = c["atr_len"]
    adx_len = c["adx_len"]
    adx_thresh = c["adx_threshold"]
    breakout_lb = c["breakout_lookback"]
    sl_type = c["sl_type"]
    sl_buf = c["sl_buffer_atr"]

    d = df.copy()

    # --- EMAs ---
    d[f"{prefix}ema9"] = ema(d["close"], ema_f)
    d[f"{prefix}ema21"] = ema(d["close"], ema_s)

    # --- SMAs ---
    d[f"{prefix}sma10"] = sma(d["close"], sma10_n)
    d[f"{prefix}sma20"] = sma(d["close"], sma20_n)
    d[f"{prefix}sma50"] = sma(d["close"], sma50_n)
    d[f"{prefix}sma100"] = sma(d["close"], sma100_n)
    d[f"{prefix}sma200"] = sma(d["close"], sma200_n)

    # --- ATR ---
    d[f"{prefix}atr14"] = compute_atr(d, atr_len)

    # --- ADX ---
    d[f"{prefix}adx"], d[f"{prefix}di_plus"], d[f"{prefix}di_minus"] = compute_adx(d, adx_len)

    # --- Short-term trend (SMA10 > SMA20 > SMA50 + price above all) ---
    d[f"{prefix}short_stacked"] = (
        (d[f"{prefix}sma10"] > d[f"{prefix}sma20"]) &
        (d[f"{prefix}sma20"] > d[f"{prefix}sma50"])
    )
    d[f"{prefix}price_above_short"] = (
        (d["close"] > d[f"{prefix}sma10"]) &
        (d["close"] > d[f"{prefix}sma20"]) &
        (d["close"] > d[f"{prefix}sma50"])
    )
    d[f"{prefix}short_trend_ok"] = d[f"{prefix}short_stacked"] & d[f"{prefix}price_above_short"]

    # --- Long-term trend (SMA50 > SMA100 > SMA200 + rising slopes + price above) ---
    d[f"{prefix}long_stacked"] = (
        (d[f"{prefix}sma50"] > d[f"{prefix}sma100"]) &
        (d[f"{prefix}sma100"] > d[f"{prefix}sma200"])
    )
    d[f"{prefix}sma50_rising"] = d[f"{prefix}sma50"] > d[f"{prefix}sma50"].shift(slope_len)
    d[f"{prefix}sma100_rising"] = d[f"{prefix}sma100"] > d[f"{prefix}sma100"].shift(slope_len)
    d[f"{prefix}sma200_rising"] = d[f"{prefix}sma200"] > d[f"{prefix}sma200"].shift(slope_len)
    d[f"{prefix}smas_rising"] = d[f"{prefix}sma50_rising"] & d[f"{prefix}sma100_rising"]
    d[f"{prefix}price_above_long"] = (
        (d["close"] > d[f"{prefix}sma50"]) &
        (d["close"] > d[f"{prefix}sma100"]) &
        (d["close"] > d[f"{prefix}sma200"])
    )
    # Pine: majorTrendOK = (longTermStacked and smasRising and priceAboveLongSMAs) or shortTermTrendOK
    d[f"{prefix}major_trend_ok"] = (
        (d[f"{prefix}long_stacked"] & d[f"{prefix}smas_rising"] & d[f"{prefix}price_above_long"])
        | d[f"{prefix}short_trend_ok"]
    )

    # --- EMA trend ---
    d[f"{prefix}ema_uptrend"] = d[f"{prefix}ema9"] > d[f"{prefix}ema21"]
    d[f"{prefix}price_above_ema"] = d["close"] > d[f"{prefix}ema21"]

    # --- Green bar ---
    d[f"{prefix}green_bar"] = d["close"] > d["open"]

    # --- Consolidation tracking ---
    d[f"{prefix}small_bar"] = (d["high"] - d["low"]) < d[f"{prefix}atr14"] * 1.0
    d[f"{prefix}consolidating"] = d[f"{prefix}small_bar"] & d[f"{prefix}price_above_ema"]
    # consol_count: cumulative count while consolidating, reset on gap
    consol = d[f"{prefix}consolidating"].astype(int)
    group = (consol.diff().ne(0)).cumsum()
    d[f"{prefix}consol_count"] = consol.groupby(group).cumsum() * consol
    d[f"{prefix}consol_count"] = d[f"{prefix}consol_count"].where(consol == 1, 0).astype(int)

    # --- Breakout: close > prior 20-bar high AND green bar ---
    d[f"{prefix}high_20"] = d["high"].rolling(breakout_lb, min_periods=breakout_lb).max()
    d[f"{prefix}prev_high_20"] = d[f"{prefix}high_20"].shift(1)
    d[f"{prefix}breakout"] = (d["close"] > d[f"{prefix}prev_high_20"]) & d[f"{prefix}green_bar"]

    # --- ADX gate ---
    d[f"{prefix}adx_ok"] = d[f"{prefix}adx"] >= adx_thresh

    # --- Entry signal ---
    d[f"{prefix}entry_signal"] = (
        d[f"{prefix}major_trend_ok"] &
        d[f"{prefix}ema_uptrend"] &
        d[f"{prefix}price_above_ema"] &
        d[f"{prefix}breakout"] &
        d[f"{prefix}adx_ok"]
    )

    # --- Dynamic SL ---
    d[f"{prefix}low_5"] = d["low"].rolling(5, min_periods=5).min()
    if sl_type == "Consolidation Low":
        d[f"{prefix}dynamic_sl"] = d[f"{prefix}low_5"] - d[f"{prefix}atr14"] * sl_buf
    elif sl_type == "SMA 50":
        d[f"{prefix}dynamic_sl"] = d[f"{prefix}sma50"] - d[f"{prefix}atr14"] * sl_buf
    elif sl_type == "SMA 200":
        d[f"{prefix}dynamic_sl"] = d[f"{prefix}sma200"] - d[f"{prefix}atr14"] * sl_buf
    else:
        d[f"{prefix}dynamic_sl"] = d[f"{prefix}low_5"] - d[f"{prefix}atr14"] * sl_buf

    # --- Trailing SL levels ---
    d[f"{prefix}trail_sma20_sl"] = d[f"{prefix}sma20"] - d[f"{prefix}atr14"] * sl_buf
    d[f"{prefix}trail_sma50_sl"] = d[f"{prefix}sma50"] - d[f"{prefix}atr14"] * sl_buf

    # --- Trend break exits ---
    d[f"{prefix}ema_crossunder"] = (
        (d[f"{prefix}ema9"].shift(1) >= d[f"{prefix}ema21"].shift(1)) &
        (d[f"{prefix}ema9"] < d[f"{prefix}ema21"])
    )
    d[f"{prefix}sma_crossunder"] = (
        (d[f"{prefix}sma50"].shift(1) >= d[f"{prefix}sma100"].shift(1)) &
        (d[f"{prefix}sma50"] < d[f"{prefix}sma100"])
    )
    d[f"{prefix}trend_break"] = d[f"{prefix}ema_crossunder"] | d[f"{prefix}sma_crossunder"]

    return d


def get_signal_components(df, idx, prefix=""):
    """Extract boolean signal components for a specific bar index."""
    cols = [
        f"{prefix}major_trend_ok",
        f"{prefix}short_trend_ok",
        f"{prefix}long_stacked",
        f"{prefix}smas_rising",
        f"{prefix}ema_uptrend",
        f"{prefix}price_above_ema",
        f"{prefix}breakout",
        f"{prefix}adx_ok",
    ]
    result = {}
    for col in cols:
        clean = col.replace(prefix, "")
        result[clean] = bool(df[col].iloc[idx]) if col in df.columns else False
    return result

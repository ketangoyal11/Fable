"""Hermes V3 Filters — Pine-parity filter implementations.

Each filter mirrors a toggle-able filter from the WA-LTF V1 Pine Script.
All filters operate on an enriched DataFrame (already has EMA/SMA/ATR/ADX columns).
"""
import pandas as pd
import numpy as np


# ──────────────────────────────────────────────────────────────────────────────
# VOLUME FILTER
# ──────────────────────────────────────────────────────────────────────────────

def compute_volume_filter(df, ma_len=20, min_mult=1.0, prefix=""):
    """Volume > N-bar moving average of volume.

    Matches Pine: volOK = not useVolumeFilter or (volume > volSma * volExpMult)
    Default ma_len=20, min_mult=1.0 (volume > its own 20-bar MA, no expansion required)
    """
    if "volume" not in df.columns:
        return pd.Series(True, index=df.index)

    vol_ma = df["volume"].rolling(ma_len, min_periods=ma_len).mean()
    col = f"{prefix}vol_ok"
    df[col] = df["volume"] > vol_ma * min_mult
    return df[col]


# ──────────────────────────────────────────────────────────────────────────────
# RSI OVERHEAT FILTER
# ──────────────────────────────────────────────────────────────────────────────

def compute_rsi(series, period=14):
    """Classic Wilder's RSI — matches Pine ta.rsi()."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    return 100 - (100 / (1 + rs))


def compute_rsi_filter(df, period=14, max_rsi=75, prefix=""):
    """RSI(14) <= max threshold.

    Matches Pine: rsiOK = not useRSIFilter or (rsiVal <= rsiMaxEntry)
    Default: period=14, max_rsi=75
    """
    rsi_val = compute_rsi(df["close"], period)
    col = f"{prefix}rsi_ok"
    df[col] = rsi_val <= max_rsi
    return df[col]


# ──────────────────────────────────────────────────────────────────────────────
# CANDLE STRENGTH FILTER
# ──────────────────────────────────────────────────────────────────────────────

def compute_candle_strength(df, min_body_pct=60, max_close_from_high_pct=20, prefix=""):
    """Strong bullish entry candle with solid body near the high.

    Matches Pine:
      candleRange = high - low
      candleBody = abs(close - open)
      bodyPctOK = candleRange > 0 and (candleBody / candleRange * 100) >= minBodyRangePct
      closeNearHighOK = candleRange > 0 and ((high - close) / candleRange * 100) <= maxCloseFromHighPct
      candleGateOK = not useCandleStrength or (bodyPctOK and closeNearHighOK and close > open)

    Default: min_body_pct=60, max_close_from_high_pct=20
    """
    col = f"{prefix}candle_ok"
    cr = df["high"] - df["low"]
    cb = (df["close"] - df["open"]).abs()
    body_pct = np.where(cr > 0, cb / cr * 100, 0)
    close_from_high_pct = np.where(cr > 0, (df["high"] - df["close"]) / cr * 100, 100)
    bullish = df["close"] > df["open"]
    df[col] = bullish & (body_pct >= min_body_pct) & (close_from_high_pct <= max_close_from_high_pct)
    return df[col]


# ──────────────────────────────────────────────────────────────────────────────
# ANTI-CHOP FILTER
# ──────────────────────────────────────────────────────────────────────────────

def compute_anti_chop(df, lookback=20, atr_mult=3.0, prefix=""):
    """Require sufficient price range to avoid choppy consolidation.

    Matches Pine:
      rangeN = ta.highest(high, chopLookback) - ta.lowest(low, chopLookback)
      notInChop = rangeN > atr * chopAtrMult
      chopGateOK = not useAntiChop or notInChop

    Default: lookback=20, atr_mult=3.0
    """
    col = f"{prefix}chop_ok"
    range_n = df["high"].rolling(lookback, min_periods=lookback).max() - \
              df["low"].rolling(lookback, min_periods=lookback).min()
    atr_col = f"{prefix}atr14" if prefix else "atr14"
    df[col] = range_n > df[atr_col] * atr_mult
    return df[col]


# ──────────────────────────────────────────────────────────────────────────────
# ADX THRESHOLD (raised for stricter entry)
# ──────────────────────────────────────────────────────────────────────────────

def compute_adx_threshold(df, threshold=25, prefix=""):
    """Higher ADX threshold for stricter trending requirement.

    Defaults to 25 (vs baseline 20 in the base entry signal).
    This is applied as an additional gate beyond the base adx_ok.
    """
    col = f"{prefix}adx_strict_ok"
    adx_col = f"{prefix}adx" if prefix else "adx"
    df[col] = df[adx_col] >= threshold
    return df[col]


# ──────────────────────────────────────────────────────────────────────────────
# MASTER: compute all additional filters at once
# ──────────────────────────────────────────────────────────────────────────────

def compute_all_filters(df, prefix=""):
    """Add all individual filter columns to the DataFrame.

    Parameters:
      df: enriched DataFrame (must already have atr14, close, high, low, open, volume)
      prefix: optional column prefix (e.g. "w_")

    Returns DataFrame with columns added:
      {prefix}vol_ok, {prefix}rsi_ok, {prefix}candle_ok,
      {prefix}chop_ok, {prefix}adx_strict_ok
    """
    compute_volume_filter(df, prefix=prefix)
    compute_rsi_filter(df, max_rsi=75, prefix=prefix)
    compute_candle_strength(df, prefix=prefix)
    compute_anti_chop(df, prefix=prefix)
    compute_adx_threshold(df, threshold=25, prefix=prefix)
    return df

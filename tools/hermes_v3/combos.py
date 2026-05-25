"""Hermes V3 Combo Definitions — logical filter combinations.

Each combo is a named set of additional filters applied on top of the
base entry signal (major_trend_ok + ema_uptrend + price_above_ema + breakout + adx_ok).

Filters reference columns added by filters.py:
  vol_ok       -> volume > 20-bar MA
  rsi_ok       -> RSI(14) <= 75
  candle_ok    -> strong bullish candle (body >=60% range, close <=20% from high)
  chop_ok      -> 20-bar range > ATR * 3
  adx_strict_ok -> ADX >= 25
  darvas_breakout -> close > prior N-bar body high (from darvas.py)
"""
import pandas as pd

COMBO_DEFINITIONS = {
    "BASELINE": {
        "label": "Base Signal Only",
        "filters": [],  # No additional filters — just the base entry_signal
    },
    "+VOL20": {
        "label": "Base + Volume > 20MA",
        "filters": ["vol_ok"],
    },
    "+DARVAS20": {
        "label": "Base + Darvas(20) Breakout",
        "filters": ["darvas_breakout"],
    },
    "+DARVAS20_VOL20": {
        "label": "Base + Darvas(20) + Volume",
        "filters": ["darvas_breakout", "vol_ok"],
    },
    "+CANDLE": {
        "label": "Base + Strong Candle",
        "filters": ["candle_ok"],
    },
    "+RSI75": {
        "label": "Base + RSI <= 75",
        "filters": ["rsi_ok"],
    },
    "+CHOP": {
        "label": "Base + Anti-Chop",
        "filters": ["chop_ok"],
    },
    "+ADX25": {
        "label": "Base + ADX >= 25",
        "filters": ["adx_strict_ok"],
    },
    "+DARVAS20_VOL20_CANDLE": {
        "label": "Base + Darvas(20) + Volume + Strong Candle",
        "filters": ["darvas_breakout", "vol_ok", "candle_ok"],
    },
    "+VOL20_RSI75_CHOP": {
        "label": "Base + Volume + RSI + Anti-Chop",
        "filters": ["vol_ok", "rsi_ok", "chop_ok"],
    },
    "+ALL_QUALITY": {
        "label": "Base + ALL: Darvas + Volume + Candle + RSI + Anti-Chop + ADX25",
        "filters": ["darvas_breakout", "vol_ok", "candle_ok", "rsi_ok", "chop_ok", "adx_strict_ok"],
    },
    "+DARVAS10_VOL20": {
        "label": "Base + Darvas(10) + Volume",
        "filters": ["darvas_breakout", "vol_ok"],
    },
}


def get_combo_names():
    """Return list of combo names in definition order."""
    return list(COMBO_DEFINITIONS.keys())


def get_combo_label(name):
    """Human-readable label for a combo."""
    return COMBO_DEFINITIONS[name]["label"]


def get_combo_filters(name):
    """Return list of filter column names required by this combo."""
    return COMBO_DEFINITIONS[name]["filters"]


def apply_combo(df, combo_name):
    """Apply a combo's filters to a DataFrame.

    Returns a boolean Series: True where ALL filters in the combo pass.
    BASELINE returns all True (no additional filters).

    Parameters:
      df: enriched LTF DataFrame with filter columns
      combo_name: str key from COMBO_DEFINITIONS
    """
    filters = COMBO_DEFINITIONS[combo_name]["filters"]
    if not filters:
        return pd.Series(True, index=df.index)

    result = None
    for f_col in filters:
        if f_col not in df.columns:
            raise KeyError(f"Filter column '{f_col}' not found in DataFrame. "
                           f"Available: {[c for c in df.columns if any(k in c for k in ['vol_ok','rsi_ok','candle_ok','chop_ok','adx_strict','darvas'])]}")
        if result is None:
            result = df[f_col].fillna(False)
        else:
            result = result & df[f_col].fillna(False)
    return result


def get_filter_pass_rate(df, combo_name):
    """What % of bars pass this combo's filters?

    Useful for understanding how restrictive each combo is.
    """
    if "entry_signal" not in df.columns:
        return 0.0

    base_bars = df["entry_signal"].sum()
    if base_bars == 0:
        return 0.0

    combined = df["entry_signal"] & apply_combo(df, combo_name)
    return combined.sum() / base_bars * 100

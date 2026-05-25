"""Hermes V3 Darvas Box — configurable lookback, zero-lookahead implementation.

Computes Darvas box levels per given lookback, shifted by 1 to avoid
including the current bar in the range — matching Pine's history ref behavior.
"""
import pandas as pd


def compute_darvas(df, darvas_len, prefix="darvas_"):
    """Compute Darvas box high/low for a given lookback length.

    Uses body (max of open/close) for high and min of open/close for low,
    matching existing V3 convention. All rolling windows shifted by 1 to
    avoid lookahead — current bar is NOT included in the box it tests against.

    Returns enriched DataFrame with columns:
      {prefix}high  — prior darvas_len-bar rolling max of body_top
      {prefix}low   — prior darvas_len-bar rolling min of body_bottom
      {prefix}breakout — close > prior darvas_high
      {prefix}support  — close > darvas_low
    """
    d = df.copy()
    body_top = d[["open", "close"]].max(axis=1)
    body_bottom = d[["open", "close"]].min(axis=1)

    d[f"{prefix}high"] = body_top.rolling(darvas_len, min_periods=darvas_len).max().shift(1)
    d[f"{prefix}low"] = body_bottom.rolling(darvas_len, min_periods=darvas_len).min().shift(1)

    d[f"{prefix}breakout"] = d["close"] > d[f"{prefix}high"]
    d[f"{prefix}support"] = d["close"] > d[f"{prefix}low"]

    return d


def add_darvas_variant_filter(df_weekly, df_ltf, variant, darvas_len, weekly_prefix="w_", ltf_prefix=""):
    """Apply Darvas variant filter to a lower-timeframe DataFrame.

    Parameters:
      df_weekly: Weekly DataFrame with Darvas columns (w_darvas_high, w_darvas_low, etc.)
      df_ltf: Lower timeframe DataFrame with entry signals
      variant: one of ["no_darvas", "weekly_darvas_gate", "ltf_darvas_breakout",
                        "ltf_darvas_support", "combined_darvas"]
      darvas_len: int, lookback length used
      weekly_prefix: prefix for weekly Darvas columns
      ltf_prefix: prefix for LTF Darvas columns

    Returns: boolean Series (same index as df_ltf) — True where Darvas passes.
    """
    idx = df_ltf.index

    if variant == "no_darvas":
        return pd.Series(True, index=idx)

    # Forward-fill weekly Darvas state to LTF index
    w_darvas_ok = pd.Series(False, index=df_weekly.index)
    if f"{weekly_prefix}darvas_breakout" in df_weekly.columns:
        w_darvas_ok = df_weekly[f"{weekly_prefix}darvas_breakout"].copy()

    if variant == "weekly_darvas_gate":
        return w_darvas_ok.reindex(idx, method="ffill").fillna(False)

    # Build LTF darvas columns
    ltf_breakout = pd.Series(False, index=idx)
    ltf_support = pd.Series(False, index=idx)

    if f"{ltf_prefix}darvas_breakout" in df_ltf.columns:
        ltf_breakout = df_ltf[f"{ltf_prefix}darvas_breakout"]
    if f"{ltf_prefix}darvas_support" in df_ltf.columns:
        ltf_support = df_ltf[f"{ltf_prefix}darvas_support"]

    if variant == "ltf_darvas_breakout":
        return ltf_breakout

    if variant == "ltf_darvas_support":
        return ltf_support

    if variant == "combined_darvas":
        w_gate = w_darvas_ok.reindex(idx, method="ffill").fillna(False)
        return w_gate & ltf_breakout

    return pd.Series(True, index=idx)


def get_darvas_variant_label(variant, darvas_len=None):
    """Human-readable label for a Darvas variant + length."""
    base = variant.replace("_", " ").title()
    if darvas_len and variant != "no_darvas":
        return f"{base} (len={darvas_len})"
    return base

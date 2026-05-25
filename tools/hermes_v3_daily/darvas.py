"""Hermes V3 Daily Darvas — configurable lookback, zero-lookahead.

Supports 5 variants for V3 Daily:
  - no_darvas: always pass
  - weekly_darvas_gate: pass when weekly Darvas breakout active
  - daily_darvas_breakout: pass when daily close > prior darvas_high
  - daily_darvas_support: pass when daily close > prior darvas_low
  - weekly_plus_daily_darvas: weekly gate AND daily breakout
"""
import pandas as pd


def compute_darvas(df, darvas_len, prefix="darvas_"):
    """Compute Darvas box high/low for a given lookback length.

    Uses body (max of open/close) for high and min of open/close for low.
    All rolling windows shifted by 1 to avoid lookahead.

    Returns enriched DataFrame with columns:
      {prefix}high     — prior darvas_len-bar rolling max of body_top
      {prefix}low      — prior darvas_len-bar rolling min of body_bottom
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


def apply_darvas_filter(df_daily, df_weekly, variant, darvas_len,
                         daily_prefix="darvas_", weekly_prefix="w_darvas_"):
    """Apply Darvas variant filter to daily DataFrame.

    Parameters:
      df_daily: Daily DataFrame with Darvas columns
      df_weekly: Weekly DataFrame with Darvas columns
      variant: one of the 5 variants
      darvas_len: int lookback
      daily_prefix: prefix for daily Darvas columns
      weekly_prefix: prefix for weekly Darvas columns

    Returns: boolean Series (same index as df_daily) — True where Darvas passes.
    """
    idx = df_daily.index

    if variant == "no_darvas":
        return pd.Series(True, index=idx)

    # Weekly Darvas state
    w_breakout = pd.Series(False, index=df_weekly.index)
    if f"{weekly_prefix}breakout" in df_weekly.columns:
        w_breakout = df_weekly[f"{weekly_prefix}breakout"].copy()

    # Daily Darvas state
    d_breakout = pd.Series(False, index=idx)
    d_support = pd.Series(False, index=idx)
    if f"{daily_prefix}breakout" in df_daily.columns:
        d_breakout = df_daily[f"{daily_prefix}breakout"]
    if f"{daily_prefix}support" in df_daily.columns:
        d_support = df_daily[f"{daily_prefix}support"]

    if variant == "weekly_darvas_gate":
        return w_breakout.reindex(idx, method="ffill").fillna(False)

    if variant == "daily_darvas_breakout":
        return d_breakout

    if variant == "daily_darvas_support":
        return d_support

    if variant == "weekly_plus_daily_darvas":
        w_gate = w_breakout.reindex(idx, method="ffill").fillna(False)
        return w_gate & d_breakout

    return pd.Series(True, index=idx)


def get_darvas_label(variant, darvas_len=None):
    """Human-readable label for a Darvas variant + length."""
    base = variant.replace("_", " ").title()
    if darvas_len and variant != "no_darvas":
        return f"{base} (len={darvas_len})"
    return base

"""Hermes V3 Weekly Activation — runs Pine SMA entry logic on weekly bars,
fires L1/L2/L3 activation windows that gate lower-timeframe entries.
"""
import pandas as pd
import numpy as np
from .indicators import compute_all_indicators
from .darvas import compute_darvas


def compute_weekly_activation(df_weekly, cfg, darvas_variant="no_darvas", darvas_len=None):
    """Run the full Pine SMA Trend Filter on weekly bars plus pyramiding.

    Parameters:
      df_weekly: Weekly OHLCV DataFrame
      cfg: full Hermes V3 config dict
      darvas_variant: str — if 'weekly_darvas_gate' or 'combined_darvas', requires
                      weekly darvas breakout at activation bar
      darvas_len: int for weekly Darvas lookback

    Returns enriched weekly DataFrame with:
      w_activation_zone (bool), w_L1_fire, w_L2_fire, w_L3_fire
    """
    c = cfg["strategy"]
    lookahead = cfg["weekly_activation"]["activation_lookahead_bars"]
    min_bars = c["min_bars_between_entries"]
    min_profit = c["min_profit_for_next_entry_pct"]

    df = compute_all_indicators(df_weekly, cfg, prefix="w_")

    # Compute weekly Darvas if needed for gate variants
    if darvas_variant in ("weekly_darvas_gate", "combined_darvas") and darvas_len:
        df = compute_darvas(df, darvas_len, prefix="w_darvas_")

    df["w_activation_zone"] = False
    df["w_L1_fire"] = False
    df["w_L2_fire"] = False
    df["w_L3_fire"] = False

    pos_count = 0
    entry_prices = []
    last_entry_idx = -999

    for i in range(len(df)):
        if i < 50:
            continue

        signal = df["w_entry_signal"].iloc[i]
        close = df["close"].iloc[i]
        bars_since = i - last_entry_idx

        # Check trend break first (close all, reset)
        if pos_count > 0:
            if df["w_trend_break"].iloc[i]:
                pos_count = 0
                entry_prices = []
                continue

        # Apply weekly darvas gate on entry bar
        darvas_pass = True
        if darvas_variant in ("weekly_darvas_gate", "combined_darvas"):
            darvas_pass = bool(df.get("w_darvas_breakout", pd.Series(True, index=df.index)).iloc[i])

        entry_ok = signal and bars_since >= min_bars and darvas_pass

        fired = False
        if entry_ok:
            if pos_count == 0:
                pos_count = 1
                entry_prices = [close]
                last_entry_idx = i
                fired = True
                df.loc[df.index[i], "w_L1_fire"] = True

            elif pos_count == 1 and entry_prices[0] > 0:
                pnl_pct = (close - entry_prices[0]) / entry_prices[0] * 100
                if pnl_pct >= min_profit:
                    pos_count = 2
                    entry_prices.append(close)
                    last_entry_idx = i
                    fired = True
                    df.loc[df.index[i], "w_L2_fire"] = True

            elif pos_count == 2 and len(entry_prices) >= 2 and entry_prices[1] > 0:
                pnl_pct = (close - entry_prices[1]) / entry_prices[1] * 100
                if pnl_pct >= min_profit:
                    pos_count = 3
                    entry_prices.append(close)
                    last_entry_idx = i
                    fired = True
                    df.loc[df.index[i], "w_L3_fire"] = True

        if fired:
            end_idx = min(i + lookahead, len(df))
            df.loc[df.index[i:end_idx], "w_activation_zone"] = True

    return df


def forward_fill_activation(weekly_df, ltf_df):
    """Forward-fill weekly activation zone to lower timeframe index.

    Returns boolean Series on ltf_df.index.
    """
    activation = weekly_df["w_activation_zone"]
    aligned = activation.reindex(ltf_df.index, method="ffill").fillna(False)
    return aligned.astype(bool)

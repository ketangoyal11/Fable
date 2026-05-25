"""Hermes V1 Weekly Engine — Staircase on 1wk, fires L1/L2/L3 activation windows."""
import yaml
import pandas as pd
import numpy as np
from hermes_v1_indicators import compute_all_indicators, compute_staircase_signals


class WeeklyEngine:
    def __init__(self, config_path):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)
        self.pyra_cfg = self.cfg["staircase_weekly"]["pyramiding"]
        self.entry_cfg = self.cfg.get("lower_tf_entries", {})

    def run(self, df_weekly):
        df = compute_all_indicators(df_weekly, self.cfg)
        df = compute_staircase_signals(df, self.cfg)

        df["L1_fire"] = False
        df["L2_fire"] = False
        df["L3_fire"] = False
        df["activation_zone"] = False

        pos_count = 0
        entry_prices = []
        last_entry_idx = -999
        min_bars = self.pyra_cfg.get("min_bars_between", 1)
        min_profit = self.pyra_cfg.get("min_profit_for_next", 0.0)

        for i in range(len(df)):
            signal = df["entry_signal"].iloc[i]
            close = df["close"].iloc[i]
            bars_since = i - last_entry_idx

            fired = False
            if signal and bars_since >= min_bars:
                if pos_count == 0:
                    pos_count = 1
                    entry_prices = [close]
                    last_entry_idx = i
                    fired = True
                    df.loc[df.index[i], "L1_fire"] = True

                elif pos_count == 1 and entry_prices[0] > 0:
                    pnl = (close - entry_prices[0]) / entry_prices[0] * 100
                    if pnl >= min_profit:
                        pos_count = 2
                        entry_prices.append(close)
                        last_entry_idx = i
                        fired = True
                        df.loc[df.index[i], "L2_fire"] = True

                elif pos_count == 2 and len(entry_prices) >= 2 and entry_prices[1] > 0:
                    pnl = (close - entry_prices[1]) / entry_prices[1] * 100
                    if pnl >= min_profit:
                        pos_count = 3
                        entry_prices.append(close)
                        last_entry_idx = i
                        fired = True
                        df.loc[df.index[i], "L3_fire"] = True

            trend_break = False
            if "ema_crossunder" in df.columns:
                trend_break = df["ema_crossunder"].iloc[i] or df["sma_crossunder"].iloc[i]

            if trend_break and pos_count > 0:
                pos_count = 0
                entry_prices = []

            # ACTIVATION ZONE: only the bar where L1/L2/L3 fires + next 3 weekly bars
            if fired:
                end_idx = min(i + 4, len(df))
                df.loc[df.index[i:end_idx], "activation_zone"] = True

        signals_df = df[["close", "entry_signal", "L1_fire", "L2_fire", "L3_fire",
                          "activation_zone", "ema_uptrend", "major_trend_ok", "breakout", "adx"]].copy()
        return df, signals_df

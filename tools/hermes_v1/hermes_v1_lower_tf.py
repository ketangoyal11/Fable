"""Hermes V1 Lower-TF Engine — entries on 1d/1h/15m/5m inside weekly activation windows."""
import yaml
import pandas as pd
import numpy as np
from hermes_v1_indicators import compute_all_indicators


class LowerTFEngine:
    def __init__(self, config_path):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)
        self.entry_types = self.cfg["lower_tf_entries"]["entry_types"]
        self.consol_atr_max = self.cfg["lower_tf_entries"].get("consolidation_atr_max", 1.0)
        self.vol_mult = self.cfg["lower_tf_entries"].get("volume_expansion_multiplier", 1.5)

    def _forward_fill_weekly_to_ltf(self, weekly_series, ltf_index):
        """Resample weekly boolean to LTF bars using forward-fill within each week."""
        if not isinstance(weekly_series.index, pd.DatetimeIndex):
            return pd.Series(False, index=ltf_index)
        wa_aligned = weekly_series.reindex(ltf_index, method="ffill").fillna(False)
        return wa_aligned

    def run(self, df_ltf, weekly_active_series):
        if df_ltf.empty:
            return df_ltf, pd.DataFrame()

        df = df_ltf.copy()
        df = compute_all_indicators(df, self.cfg)

        wa = self._forward_fill_weekly_to_ltf(weekly_active_series, df.index)
        df["weekly_active"] = wa.values
        df["within_weekly"] = df["weekly_active"]
        df["ema9"] = df["ema_fast"]
        df["ema21"] = df["ema_slow"]

        ctx = df[df["within_weekly"]].copy()
        if ctx.empty:
            return df, pd.DataFrame()

        entries = []

        if "breakout_20" in self.entry_types:
            ctx["high_20_lb"] = ctx["high"].rolling(20).max().shift(1)
            mask = (ctx["close"] > ctx["high_20_lb"]) & (ctx["close"] > ctx["open"]) & (ctx["ema9"] > ctx["ema21"])
            for idx in ctx[mask].index:
                entries.append({"datetime": idx, "entry_type": "breakout_20",
                               "price": ctx.loc[idx, "close"], "timeframe": df["timeframe"].iloc[0]})

        if "ema_pullback" in self.entry_types:
            mask = (
                (ctx["low"] <= ctx["ema21"] * 1.01) &
                (ctx["close"] > ctx["ema21"]) &
                (ctx["close"] > ctx["open"]) &
                (ctx["ema9"] > ctx["ema21"])
            )
            for idx in ctx[mask].index:
                entries.append({"datetime": idx, "entry_type": "ema_pullback",
                               "price": ctx.loc[idx, "close"], "timeframe": df["timeframe"].iloc[0]})

        if "consolidation_bo" in self.entry_types:
            ctx["range_5"] = (ctx["high"].rolling(5).max() - ctx["low"].rolling(5).min())
            ctx["consolidating"] = ctx["range_5"] < ctx["atr14"] * self.consol_atr_max
            mask = (
                ctx["consolidating"] &
                (ctx["close"] > ctx["high_20_lb"]) &
                (ctx["close"] > ctx["open"]) &
                (ctx["ema9"] > ctx["ema21"])
            )
            for idx in ctx[mask].index:
                entries.append({"datetime": idx, "entry_type": "consolidation_bo",
                               "price": ctx.loc[idx, "close"], "timeframe": df["timeframe"].iloc[0]})

        if "hh_hl_continuation" in self.entry_types:
            mask = (ctx["high"] > ctx["high"].shift(1)) & (ctx["low"] > ctx["low"].shift(1)) & (ctx["close"] > ctx["ema21"])
            for idx in ctx[mask].index:
                entries.append({"datetime": idx, "entry_type": "hh_hl_continuation",
                               "price": ctx.loc[idx, "close"], "timeframe": df["timeframe"].iloc[0]})

        if "volume_expansion" in self.entry_types:
            ctx["vol_exp"] = ctx["volume"] > ctx["volume_sma20"] * self.vol_mult
            mask = (
                ctx["vol_exp"] &
                (ctx["close"] > ctx["open"]) &
                (ctx["close"] > ctx["ema21"]) &
                (ctx["ema9"] > ctx["ema21"])
            )
            for idx in ctx[mask].index:
                entries.append({"datetime": idx, "entry_type": "volume_expansion",
                               "price": ctx.loc[idx, "close"], "timeframe": df["timeframe"].iloc[0]})

        if "prev_day_high_bo" in self.entry_types:
            ctx["date"] = ctx.index.normalize() if hasattr(ctx.index, "normalize") else ctx.index
            ctx["pd_high"] = ctx.groupby(ctx["date"])["high"].transform("max")
            mask = (ctx["close"] > ctx["pd_high"]) & (ctx["close"] > ctx["open"])
            for idx in ctx[mask].index:
                entries.append({"datetime": idx, "entry_type": "prev_day_high_bo",
                               "price": ctx.loc[idx, "close"], "timeframe": df["timeframe"].iloc[0]})

        df_signals = pd.DataFrame(entries).drop_duplicates(subset=["datetime", "entry_type"]) if entries else pd.DataFrame()
        returned_entries = {}
        for etype in ["breakout_20", "ema_pullback", "consolidation_bo",
                       "hh_hl_continuation", "volume_expansion", "prev_day_high_bo", "vwap_reclaim"]:
            mask = pd.Series(False, index=df.index)
            if not df_signals.empty:
                matches = df_signals[df_signals["entry_type"] == etype]
                if not matches.empty:
                    for dt in matches["datetime"]:
                        if dt in df.index:
                            mask.loc[dt] = True
            if mask.any():
                df[f"ltf_{etype}"] = mask.values
                returned_entries[etype] = mask

        df["ltf_any_entry"] = False
        for etype in returned_entries:
            df["ltf_any_entry"] = df["ltf_any_entry"] | df.get(f"ltf_{etype}", False)

        return df, df_signals

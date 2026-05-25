"""Hermes V3 Daily Engine — daily-only position state machine.

Key differences from original Hermes V3 engine:
- Only daily timeframe (no 1h/15m entries)
- No weekly deactivation exit (entries gated, exits free)
- No strong candle filter
- No ADX
- Tracks weekly activation metadata per trade
- L2/L3 require weekly_active by default (configurable)
"""
import pandas as pd
import numpy as np
from datetime import datetime


class V3DailyEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.strat = cfg["strategy"]
        self.pos_sizes = self.strat["position_size_pct_by_leg"]
        self.partial_pcts = self.strat["partial_exit_pct_by_leg"]
        self.rr_tp = self.strat["risk_reward_tp"]
        self.sl_buf = self.strat["sl_buffer_atr"]
        self.min_bars = self.strat["min_bars_between_entries"]
        self.min_profit = self.strat["min_profit_for_next_entry_pct"]
        self.initial_capital = self.strat["initial_capital"]
        self.commission = self.strat["commission_pct"]
        self.slippage = self.strat["slippage_pct"]
        self.l1_only = cfg["daily_pyramiding"].get("l1_only", False)
        self.weekly_active_required = cfg["daily_pyramiding"].get("weekly_active_required", True)

    def run(self, df_daily, symbol, darvas_variant, darvas_len,
            weekly_state, weekly_plan_df=None):
        """Run full backtest on a single symbol's daily bars.

        Parameters:
          df_daily: daily DataFrame with all indicator + entry signal columns
          symbol: str
          darvas_variant: str
          darvas_len: int or None
          weekly_state: DataFrame aligned to daily index (from forward_fill_to_daily)
          weekly_plan_df: original weekly plan DataFrame (for bar-counting)

        Returns:
          (trades, signals, skips) — lists of dicts
        """
        trades = []
        signals = []
        skips = []

        # Position state
        pos_count = 0
        last_entry_bar_idx = -999
        last_entry_bar_processed = -1

        entry1_price = None
        entry1_sl = None
        entry1_tp = None
        entry1_partial_taken = False
        entry1_bar = None
        entry1_qty = None

        entry2_price = None
        entry2_sl = None
        entry2_tp = None
        entry2_partial_taken = False
        entry2_bar = None
        entry2_qty = None

        entry3_price = None
        entry3_sl = None
        entry3_tp = None
        entry3_partial_taken = False
        entry3_bar = None
        entry3_qty = None

        equity = self.initial_capital

        # Build weekly activation tracking
        weekly_active_series = pd.Series(False, index=df_daily.index)
        weekly_activation_type_series = pd.Series("", index=df_daily.index)
        if weekly_state is not None:
            if "weekly_active" in weekly_state.columns:
                weekly_active_series = weekly_state["weekly_active"].reindex(df_daily.index).fillna(False)
            if "weekly_activation_type" in weekly_state.columns:
                weekly_activation_type_series = weekly_state["weekly_activation_type"].reindex(df_daily.index).fillna("")

        # Count bars since weekly activation
        bars_since_activation = pd.Series(0, index=df_daily.index)
        if weekly_plan_df is not None and "w_activation_zone" in weekly_plan_df.columns:
            act_zone = weekly_plan_df["w_activation_zone"]
            act_aligned = act_zone.reindex(df_daily.index, method="ffill").fillna(False)
            # Calculate days since first activation
            groups = (act_aligned.diff().fillna(0) & act_aligned).cumsum()
            bars_since_activation = act_aligned.astype(int).groupby(groups).cumsum()

        for i in range(len(df_daily)):
            if i < 50:
                continue

            bar_dt = df_daily.index[i]
            bar_dt_str = bar_dt.strftime("%Y-%m-%d") if hasattr(bar_dt, "strftime") else str(bar_dt)

            close = df_daily["close"].iloc[i]
            high = df_daily["high"].iloc[i]
            low = df_daily["low"].iloc[i]
            entry_signal = bool(df_daily["daily_entry_signal"].iloc[i]) if "daily_entry_signal" in df_daily.columns else False
            trend_break = bool(df_daily["daily_trend_break"].iloc[i]) if "daily_trend_break" in df_daily.columns else False

            weekly_active = bool(weekly_active_series.iloc[i])
            activation_type = str(weekly_activation_type_series.iloc[i])

            # Collect weekly/daily state for reporting
            def get_state(col, default=False):
                if col in df_daily.columns:
                    return bool(df_daily[col].iloc[i])
                return default

            def pnl_pct(entry_price):
                if entry_price is None or entry_price == 0:
                    return -999
                return (close - entry_price) / entry_price * 100

            # --- 1. Trend Break Exit ---
            if pos_count > 0 and trend_break:
                for (leg, eprice, esl, etp, ebar, eqty, _partial) in [
                    ("L1", entry1_price, entry1_sl, entry1_tp, entry1_bar, entry1_qty, entry1_partial_taken),
                    ("L2", entry2_price, entry2_sl, entry2_tp, entry2_bar, entry2_qty, entry2_partial_taken),
                    ("L3", entry3_price, entry3_sl, entry3_tp, entry3_bar, entry3_qty, entry3_partial_taken),
                ]:
                    if eprice is not None and eqty is not None and eqty > 0:
                        trade = self._build_trade(
                            leg, eprice, esl, etp, ebar, eqty, False,
                            close, bar_dt_str, "trend_break", symbol,
                            darvas_variant, darvas_len, df_daily, i, weekly_state, bars_since_activation
                        )
                        trades.append(trade)
                        equity = self._apply_pnl(equity, trade)

                pos_count = 0
                last_entry_bar_idx = -999
                last_entry_bar_processed = -1
                entry1_price = entry1_sl = entry1_tp = None
                entry1_partial_taken = False
                entry1_bar = None
                entry1_qty = None
                entry2_price = entry2_sl = entry2_tp = None
                entry2_partial_taken = False
                entry2_bar = None
                entry2_qty = None
                entry3_price = entry3_sl = entry3_tp = None
                entry3_partial_taken = False
                entry3_bar = None
                entry3_qty = None
                continue

            # --- 2. Trailing Stop Updates ---
            trail_sma20 = df_daily.get("daily_trail_sma20_sl", pd.Series(index=df_daily.index)).iloc[i]
            trail_sma50 = df_daily.get("daily_trail_sma50_sl", pd.Series(index=df_daily.index)).iloc[i]

            if pos_count == 1 and entry1_price is not None:
                if not pd.isna(trail_sma20):
                    entry1_sl = max(entry1_sl or 0, trail_sma20)
            elif pos_count >= 2:
                if not pd.isna(trail_sma50):
                    if entry1_price is not None:
                        entry1_sl = max(entry1_sl or 0, trail_sma50)
                    if entry2_price is not None:
                        entry2_sl = max(entry2_sl or 0, trail_sma50)
                    if entry3_price is not None:
                        entry3_sl = max(entry3_sl or 0, trail_sma50)

            # --- 3. Partial Profit Taking ---
            if pos_count >= 1 and entry1_price is not None and not entry1_partial_taken:
                if entry1_tp and close >= entry1_tp:
                    partial_qty = entry1_qty * (self.partial_pcts["L1"] / 100.0)
                    trade = self._build_partial_trade(
                        "L1", entry1_price, entry1_sl, entry1_tp,
                        entry1_bar, entry1_qty, partial_qty,
                        close, bar_dt_str, symbol, darvas_variant, darvas_len, df_daily, i,
                        weekly_state, bars_since_activation
                    )
                    trades.append(trade)
                    entry1_partial_taken = True
                    entry1_qty -= partial_qty
                    equity = self._apply_pnl(equity, trade)

            if pos_count >= 2 and entry2_price is not None and not entry2_partial_taken:
                if entry2_tp and close >= entry2_tp:
                    partial_qty = entry2_qty * (self.partial_pcts["L2"] / 100.0)
                    trade = self._build_partial_trade(
                        "L2", entry2_price, entry2_sl, entry2_tp,
                        entry2_bar, entry2_qty, partial_qty,
                        close, bar_dt_str, symbol, darvas_variant, darvas_len, df_daily, i,
                        weekly_state, bars_since_activation
                    )
                    trades.append(trade)
                    entry2_partial_taken = True
                    entry2_qty -= partial_qty
                    equity = self._apply_pnl(equity, trade)

            if pos_count >= 3 and entry3_price is not None and not entry3_partial_taken:
                if entry3_tp and close >= entry3_tp:
                    partial_qty = entry3_qty * (self.partial_pcts["L3"] / 100.0)
                    trade = self._build_partial_trade(
                        "L3", entry3_price, entry3_sl, entry3_tp,
                        entry3_bar, entry3_qty, partial_qty,
                        close, bar_dt_str, symbol, darvas_variant, darvas_len, df_daily, i,
                        weekly_state, bars_since_activation
                    )
                    trades.append(trade)
                    entry3_partial_taken = True
                    entry3_qty -= partial_qty
                    equity = self._apply_pnl(equity, trade)

            # --- 4. Stop Loss Hit ---
            composite_sl = None
            if pos_count >= 3 and entry3_sl is not None:
                composite_sl = entry3_sl
            elif pos_count >= 2 and entry2_sl is not None:
                composite_sl = entry2_sl
            elif pos_count >= 1 and entry1_sl is not None:
                composite_sl = entry1_sl

            if pos_count > 0 and composite_sl is not None and close < composite_sl:
                for (leg, eprice, esl, etp, ebar, eqty, _partial) in [
                    ("L1", entry1_price, entry1_sl, entry1_tp, entry1_bar, entry1_qty, entry1_partial_taken),
                    ("L2", entry2_price, entry2_sl, entry2_tp, entry2_bar, entry2_qty, entry2_partial_taken),
                    ("L3", entry3_price, entry3_sl, entry3_tp, entry3_bar, entry3_qty, entry3_partial_taken),
                ]:
                    if eprice is not None and eqty is not None and eqty > 0:
                        trade = self._build_trade(
                            leg, eprice, esl, etp, ebar, eqty, False,
                            close, bar_dt_str, "sl_hit", symbol,
                            darvas_variant, darvas_len, df_daily, i, weekly_state, bars_since_activation
                        )
                        trades.append(trade)
                        equity = self._apply_pnl(equity, trade)

                pos_count = 0
                last_entry_bar_idx = -999
                last_entry_bar_processed = -1
                entry1_price = entry1_sl = entry1_tp = None
                entry1_partial_taken = False
                entry1_bar = None
                entry1_qty = None
                entry2_price = entry2_sl = entry2_tp = None
                entry2_partial_taken = False
                entry2_bar = None
                entry2_qty = None
                entry3_price = entry3_sl = entry3_tp = None
                entry3_partial_taken = False
                entry3_bar = None
                entry3_qty = None
                continue

            # --- 5. Entries ---
            can_enter_new = (i - last_entry_bar_idx) >= self.min_bars
            can_take_new = i != last_entry_bar_processed

            if entry_signal and can_enter_new and can_take_new:
                dynamic_sl = df_daily.get("daily_dynamic_sl", pd.Series(index=df_daily.index)).iloc[i]
                if pd.isna(dynamic_sl):
                    skips.append({
                        "dt": bar_dt_str, "symbol": symbol,
                        "timeframe": "1d", "reason": "no_sl", "leg": "L1"
                    })
                    continue

                entry_risk = close - dynamic_sl
                pct_risk = close * 0.02
                min_risk = max(
                    (df_daily["daily_atr14"].iloc[i] * 0.5) if "daily_atr14" in df_daily.columns else 0,
                    pct_risk
                )
                if entry_risk < min_risk or entry_risk <= 0:
                    skips.append({
                        "dt": bar_dt_str, "symbol": symbol,
                        "timeframe": "1d", "reason": f"risk_too_small={entry_risk:.4f}",
                        "leg": "L1" if pos_count == 0 else "L2" if pos_count == 1 else "L3"
                    })
                    continue

                target = close + entry_risk * self.rr_tp

                sig_comps = self._get_signal_components(df_daily, i)

                if pos_count == 0:
                    qty_percent = self.pos_sizes["L1"] / 100.0
                    qty = (equity * qty_percent) / close

                    entry1_price = close
                    entry1_sl = dynamic_sl
                    entry1_tp = target
                    entry1_partial_taken = False
                    entry1_bar = i
                    entry1_qty = qty
                    pos_count = 1
                    last_entry_bar_idx = i
                    last_entry_bar_processed = i

                    signals.append({
                        "dt": bar_dt_str, "symbol": symbol, "timeframe": "1d",
                        "leg": "L1", "price": close, "sl": dynamic_sl, "tp": target,
                        "qty": qty, "equity": equity,
                        "darvas_variant": darvas_variant, "darvas_len": darvas_len,
                        "weekly_active": weekly_active,
                        "weekly_activation_type": activation_type,
                        "bars_since_activation": int(bars_since_activation.iloc[i]) if i < len(bars_since_activation) else 0,
                        **sig_comps
                    })

                elif pos_count == 1 and entry1_price is not None and not self.l1_only:
                    if pnl_pct(entry1_price) >= self.min_profit:
                        if self.weekly_active_required and not weekly_active:
                            skips.append({
                                "dt": bar_dt_str, "symbol": symbol,
                                "timeframe": "1d", "reason": "L2_blocked_weekly_inactive",
                                "leg": "L2"
                            })
                        else:
                            qty_percent = self.pos_sizes["L2"] / 100.0
                            qty = (equity * qty_percent) / close

                            entry2_price = close
                            entry2_sl = dynamic_sl
                            entry2_tp = target
                            entry2_partial_taken = False
                            entry2_bar = i
                            entry2_qty = qty
                            pos_count = 2
                            last_entry_bar_idx = i
                            last_entry_bar_processed = i
                            entry1_sl = dynamic_sl

                            signals.append({
                                "dt": bar_dt_str, "symbol": symbol, "timeframe": "1d",
                                "leg": "L2", "price": close, "sl": dynamic_sl, "tp": target,
                                "qty": qty, "equity": equity,
                                "darvas_variant": darvas_variant, "darvas_len": darvas_len,
                                "weekly_active": weekly_active,
                                "weekly_activation_type": activation_type,
                                "bars_since_activation": int(bars_since_activation.iloc[i]) if i < len(bars_since_activation) else 0,
                                **sig_comps
                            })

                elif pos_count == 2 and entry2_price is not None and not self.l1_only:
                    if pnl_pct(entry2_price) >= self.min_profit:
                        if self.weekly_active_required and not weekly_active:
                            skips.append({
                                "dt": bar_dt_str, "symbol": symbol,
                                "timeframe": "1d", "reason": "L3_blocked_weekly_inactive",
                                "leg": "L3"
                            })
                        else:
                            qty_percent = self.pos_sizes["L3"] / 100.0
                            qty = (equity * qty_percent) / close

                            entry3_price = close
                            entry3_sl = dynamic_sl
                            entry3_tp = target
                            entry3_partial_taken = False
                            entry3_bar = i
                            entry3_qty = qty
                            pos_count = 3
                            last_entry_bar_idx = i
                            last_entry_bar_processed = i
                            entry1_sl = dynamic_sl
                            entry2_sl = dynamic_sl

                            signals.append({
                                "dt": bar_dt_str, "symbol": symbol, "timeframe": "1d",
                                "leg": "L3", "price": close, "sl": dynamic_sl, "tp": target,
                                "qty": qty, "equity": equity,
                                "darvas_variant": darvas_variant, "darvas_len": darvas_len,
                                "weekly_active": weekly_active,
                                "weekly_activation_type": activation_type,
                                "bars_since_activation": int(bars_since_activation.iloc[i]) if i < len(bars_since_activation) else 0,
                                **sig_comps
                            })

        # --- End of data: close open positions ---
        if pos_count > 0:
            last_close = df_daily["close"].iloc[-1]
            last_dt_str = str(df_daily.index[-1])
            for (leg, eprice, esl, etp, ebar, eqty, _partial) in [
                ("L1", entry1_price, entry1_sl, entry1_tp, entry1_bar, entry1_qty, entry1_partial_taken),
                ("L2", entry2_price, entry2_sl, entry2_tp, entry2_bar, entry2_qty, entry2_partial_taken),
                ("L3", entry3_price, entry3_sl, entry3_tp, entry3_bar, entry3_qty, entry3_partial_taken),
            ]:
                if eprice is not None and eqty is not None and eqty > 0:
                    trade = self._build_trade(
                        leg, eprice, esl, etp, ebar, eqty, False,
                        last_close, last_dt_str, "end_of_data", symbol,
                        darvas_variant, darvas_len, df_daily, len(df_daily) - 1,
                        weekly_state, bars_since_activation
                    )
                    trades.append(trade)

        return trades, signals, skips

    def _build_trade(self, leg, entry_price, entry_sl, entry_tp, entry_bar, entry_qty,
                     partial_taken, exit_price, exit_dt, exit_reason, symbol,
                     darvas_variant, darvas_len, df, idx, weekly_state, bars_since_activation):
        entry_risk = entry_price - entry_sl if entry_sl else 0
        r_multiple = (exit_price - entry_price) / entry_risk if entry_risk > 0 else 0

        gross_pnl = (exit_price - entry_price) * entry_qty
        net_pnl = gross_pnl * (1 - self.commission / 100 - self.slippage / 100)

        entry_bar_idx = entry_bar if entry_bar is not None else idx
        entry_dt = str(df.index[entry_bar_idx]) if entry_bar_idx < len(df.index) else ""

        weekly_active_val = False
        activation_type_val = ""
        bars_since_act = 0
        if weekly_state is not None and entry_bar_idx < len(weekly_state):
            wa = weekly_state.get("weekly_active", pd.Series(False, index=weekly_state.index))
            at = weekly_state.get("weekly_activation_type", pd.Series("", index=weekly_state.index))
            weekly_active_val = bool(wa.iloc[entry_bar_idx]) if entry_bar_idx < len(wa) else False
            activation_type_val = str(at.iloc[entry_bar_idx]) if entry_bar_idx < len(at) else ""
        if bars_since_activation is not None and entry_bar_idx < len(bars_since_activation):
            bars_since_act = int(bars_since_activation.iloc[entry_bar_idx])

        weekly_darvas_state = False
        daily_darvas_state = False
        if weekly_state is not None and entry_bar_idx < len(weekly_state):
            wdb = weekly_state.get("weekly_darvas_breakout", pd.Series(False, index=weekly_state.index))
            weekly_darvas_state = bool(wdb.iloc[entry_bar_idx]) if entry_bar_idx < len(wdb) else False
        if "daily_darvas_breakout" in df.columns:
            daily_darvas_state = bool(df["daily_darvas_breakout"].iloc[entry_bar_idx]) if entry_bar_idx < len(df) else False
        if darvas_variant == "daily_darvas_support" and "daily_darvas_support" in df.columns:
            daily_darvas_state = bool(df["daily_darvas_support"].iloc[entry_bar_idx]) if entry_bar_idx < len(df) else False

        weekly_trend_state = False
        daily_trend_state = False
        if weekly_state is not None and entry_bar_idx < len(weekly_state):
            wt = weekly_state.get("weekly_major_trend_ok", pd.Series(False, index=weekly_state.index))
            weekly_trend_state = bool(wt.iloc[entry_bar_idx]) if entry_bar_idx < len(wt) else False
        if "daily_major_trend_ok" in df.columns:
            daily_trend_state = bool(df["daily_major_trend_ok"].iloc[entry_bar_idx]) if entry_bar_idx < len(df) else False

        bars_held = idx - entry_bar_idx

        return {
            "symbol": symbol,
            "timeframe": "1d",
            "darvas_variant": f"{darvas_variant}_{darvas_len}" if darvas_len else darvas_variant,
            "entry_leg": leg,
            "entry_dt": entry_dt,
            "entry_price": round(entry_price, 2),
            "entry_qty": round(entry_qty, 2) if entry_qty else 0,
            "initial_sl": round(entry_sl, 2) if entry_sl else 0,
            "final_sl": round(entry_sl, 2) if entry_sl else 0,
            "target": round(entry_tp, 2) if entry_tp else 0,
            "partial_exit_dt": "",
            "partial_exit_price": 0,
            "partial_exit_qty": 0,
            "partial_realized_r": 0,
            "final_exit_dt": exit_dt,
            "final_exit_price": round(exit_price, 2),
            "exit_reason": exit_reason,
            "gross_pnl": round(gross_pnl, 2),
            "net_pnl": round(net_pnl, 2),
            "r_multiple": round(r_multiple, 4),
            "bars_held": bars_held,
            "weekly_active_at_entry": weekly_active_val,
            "weekly_activation_type": activation_type_val,
            "bars_since_weekly_activation": bars_since_act,
            "weekly_darvas_state": str(weekly_darvas_state),
            "daily_darvas_state": str(daily_darvas_state),
            "weekly_trend_state": str(weekly_trend_state),
            "daily_trend_state": str(daily_trend_state),
        }

    def _build_partial_trade(self, leg, entry_price, entry_sl, entry_tp, entry_bar, entry_qty, partial_qty,
                              exit_price, exit_dt, symbol, darvas_variant, darvas_len, df, idx,
                              weekly_state, bars_since_activation):
        entry_risk = entry_price - entry_sl if entry_sl else 0
        r_multiple = (exit_price - entry_price) / entry_risk if entry_risk > 0 else 0
        gross_pnl = (exit_price - entry_price) * partial_qty
        net_pnl = gross_pnl * (1 - self.commission / 100 - self.slippage / 100)

        entry_bar_idx = entry_bar if entry_bar is not None else idx
        entry_dt = str(df.index[entry_bar_idx]) if entry_bar_idx < len(df.index) else ""

        weekly_active_val = False
        activation_type_val = ""
        bars_since_act = 0
        if weekly_state is not None and entry_bar_idx < len(weekly_state):
            wa = weekly_state.get("weekly_active", pd.Series(False, index=weekly_state.index))
            at = weekly_state.get("weekly_activation_type", pd.Series("", index=weekly_state.index))
            weekly_active_val = bool(wa.iloc[entry_bar_idx]) if entry_bar_idx < len(wa) else False
            activation_type_val = str(at.iloc[entry_bar_idx]) if entry_bar_idx < len(at) else ""
        if bars_since_activation is not None and entry_bar_idx < len(bars_since_activation):
            bars_since_act = int(bars_since_activation.iloc[entry_bar_idx])

        weekly_darvas_state = False
        daily_darvas_state = False
        if weekly_state is not None and entry_bar_idx < len(weekly_state):
            wdb = weekly_state.get("weekly_darvas_breakout", pd.Series(False, index=weekly_state.index))
            weekly_darvas_state = bool(wdb.iloc[entry_bar_idx]) if entry_bar_idx < len(wdb) else False
        if "daily_darvas_breakout" in df.columns:
            daily_darvas_state = bool(df["daily_darvas_breakout"].iloc[entry_bar_idx]) if entry_bar_idx < len(df) else False

        weekly_trend_state = False
        daily_trend_state = False
        if weekly_state is not None and entry_bar_idx < len(weekly_state):
            wt = weekly_state.get("weekly_major_trend_ok", pd.Series(False, index=weekly_state.index))
            weekly_trend_state = bool(wt.iloc[entry_bar_idx]) if entry_bar_idx < len(wt) else False
        if "daily_major_trend_ok" in df.columns:
            daily_trend_state = bool(df["daily_major_trend_ok"].iloc[entry_bar_idx]) if entry_bar_idx < len(df) else False

        return {
            "symbol": symbol,
            "timeframe": "1d",
            "darvas_variant": f"{darvas_variant}_{darvas_len}" if darvas_len else darvas_variant,
            "entry_leg": leg,
            "entry_dt": entry_dt,
            "entry_price": round(entry_price, 2),
            "entry_qty": round(entry_qty, 2) if entry_qty else 0,
            "initial_sl": round(entry_sl, 2) if entry_sl else 0,
            "final_sl": round(entry_sl, 2) if entry_sl else 0,
            "target": round(entry_tp, 2) if entry_tp else 0,
            "partial_exit_dt": exit_dt,
            "partial_exit_price": round(exit_price, 2),
            "partial_exit_qty": round(partial_qty, 2) if partial_qty else 0,
            "partial_realized_r": round(r_multiple, 4),
            "final_exit_dt": "",
            "final_exit_price": 0,
            "exit_reason": "partial_tp",
            "gross_pnl": round(gross_pnl, 2),
            "net_pnl": round(net_pnl, 2),
            "r_multiple": round(r_multiple, 4),
            "bars_held": idx - entry_bar_idx,
            "weekly_active_at_entry": weekly_active_val,
            "weekly_activation_type": activation_type_val,
            "bars_since_weekly_activation": bars_since_act,
            "weekly_darvas_state": str(weekly_darvas_state),
            "daily_darvas_state": str(daily_darvas_state),
            "weekly_trend_state": str(weekly_trend_state),
            "daily_trend_state": str(daily_trend_state),
        }

    def _apply_pnl(self, equity, trade):
        return equity + trade["net_pnl"]

    def _get_signal_components(self, df, idx):
        comps = {}
        for col in ["daily_major_trend_ok", "daily_short_trend_ok", "daily_long_stacked",
                     "daily_smas_rising", "daily_ema_uptrend", "daily_price_above_ema",
                     "daily_breakout"]:
            if col in df.columns:
                comps[col.replace("daily_", "")] = bool(df[col].iloc[idx])
            else:
                comps[col.replace("daily_", "")] = False
        return comps


def aggregate_trades(trades):
    """Compute summary statistics from a list of trade dicts."""
    if not trades:
        return {
            "total_trades": 0, "win_rate": 0, "avg_r": 0, "median_r": 0,
            "total_r": 0, "total_return": 0, "profit_factor": 0,
            "max_drawdown": 0, "expectancy": 0, "avg_bars_held": 0,
            "sharpe": 0, "L1_count": 0, "L2_count": 0, "L3_count": 0,
        }

    df = pd.DataFrame(trades)
    n = len(df)
    wins = df[df["r_multiple"] > 0]
    losses = df[df["r_multiple"] <= 0]

    wr = len(wins) / n * 100 if n > 0 else 0
    avg_r = df["r_multiple"].mean()
    median_r = df["r_multiple"].median()
    total_r = df["r_multiple"].sum()
    total_return = df["net_pnl"].sum() / 100000 * 100

    gp = wins["r_multiple"].sum() if len(wins) > 0 else 0
    gl = abs(losses["r_multiple"].sum()) if len(losses) > 0 else 1e-9
    pf = gp / gl

    cum_r = df["r_multiple"].cumsum()
    peak_r = cum_r.cummax()
    mdd = abs((cum_r - peak_r).min()) if n > 0 else 0

    exp_val = (wr / 100 * wins["r_multiple"].mean() if len(wins) > 0 else 0) - \
              ((1 - wr / 100) * abs(losses["r_multiple"].mean()) if len(losses) > 0 else 0)

    avg_bars = df["bars_held"].mean() if "bars_held" in df.columns else 0

    sharpe = 0
    if n > 1 and df["r_multiple"].std() > 0:
        sharpe = df["r_multiple"].mean() / df["r_multiple"].std()

    return {
        "total_trades": n,
        "win_rate": round(wr, 1),
        "avg_r": round(avg_r, 4),
        "median_r": round(median_r, 4),
        "total_r": round(total_r, 4),
        "total_return": round(total_return, 2),
        "profit_factor": round(pf, 2),
        "max_drawdown": round(mdd, 4),
        "expectancy": round(exp_val, 4),
        "avg_bars_held": round(avg_bars, 1),
        "sharpe": round(sharpe, 2),
        "L1_count": int((df["entry_leg"] == "L1").sum()),
        "L2_count": int((df["entry_leg"] == "L2").sum()),
        "L3_count": int((df["entry_leg"] == "L3").sum()),
    }

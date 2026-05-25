"""Hermes V3 Engine — full Pine-parity position state machine.

Replicates the Pine Script "Staircase SMA TREND FILTER (33/33/34)" behavior:
- L1/L2/L3 pyramiding with 33/33/34 sizing
- Partial exits at 2R targets
- Trailing stop loss: SMA20 when pos_count==1, SMA50 when pos_count>=2
- Trend break (EMA9 crossunder EMA21 or SMA50 crossunder SMA100) closes all
- SL hit closes all remaining positions
"""
import pandas as pd
import numpy as np
from datetime import datetime


class BacktestEngine:
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

    def run(self, df, symbol, timeframe, darvas_variant, darvas_len,
            weekly_active_series, weekly_df_for_state=None,
            combo_name=None, combo_pass=None):
        """Run full backtest on a single symbol/timeframe/variant combination.

        Parameters:
          df: enriched LTF DataFrame with all indicator columns
          symbol: str
          timeframe: "1d", "1h", "15m"
          darvas_variant: str
          darvas_len: int or None
          weekly_active_series: bool Series aligned to df.index
          weekly_df_for_state: enriched weekly DataFrame (for weekly_darvas_state tracking)
          combo_name: str or None — name of filter combo being tested
          combo_pass: bool Series aligned to df.index — pre-computed combo filter result

        Returns:
          list of trade dicts, list of signal dicts, list of skip dicts
        """
        trades = []
        signals = []
        skips = []

        # Position state
        pos_count = 0
        last_entry_bar_idx = -999
        last_entry_bar_processed = -1

        # L1 state
        entry1_price = None
        entry1_sl = None
        entry1_tp = None
        entry1_partial_taken = False
        entry1_bar = None
        entry1_qty = None

        # L2 state
        entry2_price = None
        entry2_sl = None
        entry2_tp = None
        entry2_partial_taken = False
        entry2_bar = None
        entry2_qty = None

        # L3 state
        entry3_price = None
        entry3_sl = None
        entry3_tp = None
        entry3_partial_taken = False
        entry3_bar = None
        entry3_qty = None

        # Equity tracking
        equity = self.initial_capital

        # Weekly state for reporting
        w_darvas_state = False
        if weekly_df_for_state is not None and "w_darvas_breakout" in weekly_df_for_state.columns:
            w_darvas_aligned = weekly_df_for_state["w_darvas_breakout"].reindex(
                df.index, method="ffill").fillna(False)
        else:
            w_darvas_aligned = pd.Series(False, index=df.index)

        ltf_darvas_state = pd.Series(False, index=df.index)
        if "darvas_breakout" in df.columns:
            ltf_darvas_state = df["darvas_breakout"]

        for i in range(len(df)):
            if i < 50:
                continue

            bar_dt = df.index[i]
            if isinstance(bar_dt, pd.Timestamp):
                bar_dt_str = bar_dt.strftime("%Y-%m-%d %H:%M")
            else:
                bar_dt_str = str(bar_dt)

            close = df["close"].iloc[i]
            high = df["high"].iloc[i]
            low = df["low"].iloc[i]
            weekly_active = weekly_active_series.iloc[i] if i < len(weekly_active_series) else False
            entry_signal = bool(df["entry_signal"].iloc[i]) if "entry_signal" in df.columns else False
            trend_break = bool(df.get("trend_break", pd.Series(False, index=df.index)).iloc[i])

            # Darvas LTF filter — applied on entry signal
            darvas_pass = True
            if darvas_variant == "ltf_darvas_breakout":
                darvas_pass = bool(ltf_darvas_state.iloc[i])
            elif darvas_variant == "ltf_darvas_support":
                darvas_pass = bool(df.get("darvas_support", pd.Series(True, index=df.index)).iloc[i])
            elif darvas_variant == "combined_darvas":
                darvas_pass = bool(ltf_darvas_state.iloc[i])

            def pnl_pct(entry_price):
                if entry_price is None or entry_price == 0:
                    return -999
                return (close - entry_price) / entry_price * 100

            def get_dynamic_sl():
                return df["dynamic_sl"].iloc[i] if "dynamic_sl" in df.columns else None

            def get_trail_sma20_sl():
                return df["trail_sma20_sl"].iloc[i] if "trail_sma20_sl" in df.columns else None

            def get_trail_sma50_sl():
                return df["trail_sma50_sl"].iloc[i] if "trail_sma50_sl" in df.columns else None

            # --- 1. Trend Break Exit ---
            if pos_count > 0 and trend_break:
                reason = "trend_break"
                for (leg, eprice, esl, etp, ebar, eqty, epartial) in [
                    ("L1", entry1_price, entry1_sl, entry1_tp, entry1_bar, entry1_qty, entry1_partial_taken),
                    ("L2", entry2_price, entry2_sl, entry2_tp, entry2_bar, entry2_qty, entry2_partial_taken),
                    ("L3", entry3_price, entry3_sl, entry3_tp, entry3_bar, entry3_qty, entry3_partial_taken),
                ]:
                    if eprice is not None:
                        trade = self._build_trade(leg, eprice, esl, etp, ebar, eqty, epartial,
                                                   close, bar_dt_str, reason, symbol, timeframe,
                                                   darvas_variant, darvas_len, df, i, combo_name)
                        trades.append(trade)
                        equity = self._apply_pnl(equity, trade)

                # Reset all position state
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

            # --- 1b. Weekly Deactivation Exit ---
            if pos_count > 0 and not weekly_active:
                # Weekly activation window closed — exit all (matches Pine deactivation)
                reason = "weekly_deactivation"
                for (leg, eprice, esl, etp, ebar, eqty, epartial) in [
                    ("L1", entry1_price, entry1_sl, entry1_tp, entry1_bar, entry1_qty, entry1_partial_taken),
                    ("L2", entry2_price, entry2_sl, entry2_tp, entry2_bar, entry2_qty, entry2_partial_taken),
                    ("L3", entry3_price, entry3_sl, entry3_tp, entry3_bar, entry3_qty, entry3_partial_taken),
                ]:
                    if eprice is not None and eqty is not None and eqty > 0:
                        trade = self._build_trade(leg, eprice, esl, etp, ebar, eqty, epartial,
                                                   close, bar_dt_str, reason, symbol, timeframe,
                                                   darvas_variant, darvas_len, df, i, combo_name)
                        trades.append(trade)
                        equity = self._apply_pnl(equity, trade)

                # Reset all position state
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
            if pos_count == 1 and entry1_price is not None:
                trail_sl = get_trail_sma20_sl()
                if trail_sl and not pd.isna(trail_sl):
                    entry1_sl = max(entry1_sl or 0, trail_sl)

            elif pos_count >= 2:
                trail_sl = get_trail_sma50_sl()
                if trail_sl and not pd.isna(trail_sl):
                    if entry1_price is not None:
                        entry1_sl = max(entry1_sl or 0, trail_sl)
                    if entry2_price is not None:
                        entry2_sl = max(entry2_sl or 0, trail_sl)
                    if entry3_price is not None:
                        entry3_sl = max(entry3_sl or 0, trail_sl)

            # --- 3. Partial Profit Taking ---
            if pos_count >= 1 and entry1_price is not None and not entry1_partial_taken:
                if entry1_tp and close >= entry1_tp:
                    partial_qty = entry1_qty * (self.partial_pcts["L1"] / 100.0)
                    trade = self._build_partial_trade("L1", entry1_price, entry1_sl, entry1_tp,
                                                       entry1_bar, entry1_qty, partial_qty,
                                                       close, bar_dt_str, symbol, timeframe,
                                                       darvas_variant, darvas_len, df, i, combo_name)
                    trades.append(trade)
                    entry1_partial_taken = True
                    entry1_qty -= partial_qty
                    equity = self._apply_pnl(equity, trade)

            if pos_count >= 2 and entry2_price is not None and not entry2_partial_taken:
                if entry2_tp and close >= entry2_tp:
                    partial_qty = entry2_qty * (self.partial_pcts["L2"] / 100.0)
                    trade = self._build_partial_trade("L2", entry2_price, entry2_sl, entry2_tp,
                                                       entry2_bar, entry2_qty, partial_qty,
                                                       close, bar_dt_str, symbol, timeframe,
                                                       darvas_variant, darvas_len, df, i, combo_name)
                    trades.append(trade)
                    entry2_partial_taken = True
                    entry2_qty -= partial_qty
                    equity = self._apply_pnl(equity, trade)

            if pos_count >= 3 and entry3_price is not None and not entry3_partial_taken:
                if entry3_tp and close >= entry3_tp:
                    partial_qty = entry3_qty * (self.partial_pcts["L3"] / 100.0)
                    trade = self._build_partial_trade("L3", entry3_price, entry3_sl, entry3_tp,
                                                       entry3_bar, entry3_qty, partial_qty,
                                                       close, bar_dt_str, symbol, timeframe,
                                                       darvas_variant, darvas_len, df, i, combo_name)
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
                for (leg, eprice, esl, etp, ebar, eqty, epartial) in [
                    ("L1", entry1_price, entry1_sl, entry1_tp, entry1_bar, entry1_qty, entry1_partial_taken),
                    ("L2", entry2_price, entry2_sl, entry2_tp, entry2_bar, entry2_qty, entry2_partial_taken),
                    ("L3", entry3_price, entry3_sl, entry3_tp, entry3_bar, entry3_qty, entry3_partial_taken),
                ]:
                    if eprice is not None and eqty is not None and eqty > 0:
                        trade = self._build_trade(leg, eprice, esl, etp, ebar, eqty, epartial,
                                                   close, bar_dt_str, "sl_hit", symbol, timeframe,
                                                   darvas_variant, darvas_len, df, i, combo_name)
                        trades.append(trade)
                        equity = self._apply_pnl(equity, trade)

                # Reset all position state
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

            combo_ok = True
            if combo_pass is not None and i < len(combo_pass):
                combo_ok = bool(combo_pass.iloc[i])

            signal_ready = entry_signal and weekly_active and darvas_pass and combo_ok

            if signal_ready and can_enter_new and can_take_new:
                dynamic_sl = get_dynamic_sl()
                if dynamic_sl is None or pd.isna(dynamic_sl):
                    skips.append({
                        "dt": bar_dt_str, "symbol": symbol, "timeframe": timeframe,
                        "reason": "no_sl", "leg": "L1"
                    })
                    continue

                entry_risk = close - dynamic_sl
                # Minimum risk distance: max(0.5 ATR, 2% of entry price)
                pct_risk = close * 0.02
                min_risk = max(
                    df["atr14"].iloc[i] * 0.5 if "atr14" in df.columns else 0,
                    pct_risk
                )
                if entry_risk < min_risk or entry_risk <= 0:
                    skips.append({
                        "dt": bar_dt_str, "symbol": symbol, "timeframe": timeframe,
                        "reason": f"risk_too_small={entry_risk:.4f}",
                        "leg": "L1" if pos_count == 0 else "L2" if pos_count == 1 else "L3"
                    })
                    continue

                target = close + entry_risk * self.rr_tp

                # Signal components for logging
                sig_comps = self._get_signal_components(df, i)

                if pos_count == 0:
                    # L1 Entry
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
                        "dt": bar_dt_str, "symbol": symbol, "timeframe": timeframe,
                        "leg": "L1", "price": close, "sl": dynamic_sl, "tp": target,
                        "qty": qty, "equity": equity,
                        "darvas_variant": darvas_variant, "darvas_len": darvas_len,
                        "combo_name": combo_name,
                        **sig_comps
                    })

                elif pos_count == 1 and entry1_price is not None:
                    if pnl_pct(entry1_price) >= self.min_profit:
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
                            "dt": bar_dt_str, "symbol": symbol, "timeframe": timeframe,
                            "leg": "L2", "price": close, "sl": dynamic_sl, "tp": target,
                            "qty": qty, "equity": equity,
                            "darvas_variant": darvas_variant, "darvas_len": darvas_len,
                            "combo_name": combo_name,
                            **sig_comps
                        })

                elif pos_count == 2 and entry2_price is not None:
                    if pnl_pct(entry2_price) >= self.min_profit:
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
                            "dt": bar_dt_str, "symbol": symbol, "timeframe": timeframe,
                            "leg": "L3", "price": close, "sl": dynamic_sl, "tp": target,
                            "qty": qty, "equity": equity,
                            "darvas_variant": darvas_variant, "darvas_len": darvas_len,
                            "combo_name": combo_name,
                            **sig_comps
                        })

        # --- End of data: close any open positions ---
        if pos_count > 0:
            last_close = df["close"].iloc[-1]
            last_dt_str = str(df.index[-1])
            for (leg, eprice, esl, etp, ebar, eqty, epartial) in [
                ("L1", entry1_price, entry1_sl, entry1_tp, entry1_bar, entry1_qty, entry1_partial_taken),
                ("L2", entry2_price, entry2_sl, entry2_tp, entry2_bar, entry2_qty, entry2_partial_taken),
                ("L3", entry3_price, entry3_sl, entry3_tp, entry3_bar, entry3_qty, entry3_partial_taken),
            ]:
                if eprice is not None and eqty is not None and eqty > 0:
                    trade = self._build_trade(leg, eprice, esl, etp, ebar, eqty, epartial,
                                               last_close, last_dt_str, "end_of_data", symbol,
                                               timeframe, darvas_variant, darvas_len, df, len(df) - 1, combo_name)
                    trades.append(trade)

        return trades, signals, skips

    def _build_trade(self, leg, entry_price, entry_sl, entry_tp, entry_bar, entry_qty, partial_taken,
                     exit_price, exit_dt, exit_reason, symbol, timeframe, darvas_variant, darvas_len, df, idx, combo_name=None):
        entry_risk = entry_price - entry_sl if entry_sl else 0
        if entry_risk <= 0:
            r_multiple = 0
        else:
            r_multiple = (exit_price - entry_price) / entry_risk

        gross_pnl = (exit_price - entry_price) * entry_qty
        net_pnl = gross_pnl * (1 - self.commission / 100 - self.slippage / 100)

        return {
            "symbol": symbol,
            "data_source": "local",
            "timeframe": timeframe,
            "darvas_variant": f"{darvas_variant}_{darvas_len}" if darvas_len else darvas_variant,
            "combo_name": combo_name,
            "entry_leg": leg,
            "entry_dt": str(df.index[entry_bar]) if entry_bar is not None else "",
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
            "bars_held": idx - entry_bar if entry_bar is not None else 0,
            "weekly_darvas_state": str(False),
            "ltf_darvas_state": str(False),
        }

    def _build_partial_trade(self, leg, entry_price, entry_sl, entry_tp, entry_bar, entry_qty, partial_qty,
                              exit_price, exit_dt, symbol, timeframe, darvas_variant, darvas_len, df, idx, combo_name=None):
        entry_risk = entry_price - entry_sl if entry_sl else 0
        if entry_risk <= 0:
            r_multiple = 0
        else:
            r_multiple = (exit_price - entry_price) / entry_risk

        gross_pnl = (exit_price - entry_price) * partial_qty
        net_pnl = gross_pnl * (1 - self.commission / 100 - self.slippage / 100)

        return {
            "symbol": symbol,
            "data_source": "local",
            "timeframe": timeframe,
            "darvas_variant": f"{darvas_variant}_{darvas_len}" if darvas_len else darvas_variant,
            "combo_name": combo_name,
            "entry_leg": leg,
            "entry_dt": str(df.index[entry_bar]) if entry_bar is not None else "",
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
            "bars_held": idx - entry_bar if entry_bar is not None else 0,
            "weekly_darvas_state": str(False),
            "ltf_darvas_state": str(False),
        }

    def _apply_pnl(self, equity, trade):
        return equity + trade["net_pnl"]

    def _get_signal_components(self, df, idx):
        comps = {}
        for col in ["major_trend_ok", "short_trend_ok", "long_stacked", "smas_rising",
                     "ema_uptrend", "price_above_ema", "breakout", "adx_ok"]:
            if col in df.columns:
                comps[col] = bool(df[col].iloc[idx])
            else:
                comps[col] = False
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
    total_return = df["net_pnl"].sum() / 100000 * 100  # as % of initial capital

    gp = wins["r_multiple"].sum() if len(wins) > 0 else 0
    gl = abs(losses["r_multiple"].sum()) if len(losses) > 0 else 1e-9
    pf = gp / gl

    cum_r = df["r_multiple"].cumsum()
    peak_r = cum_r.cummax()
    mdd = abs((cum_r - peak_r).min()) if n > 0 else 0

    expectancy = (wr / 100 * wins["r_multiple"].mean() if len(wins) > 0 else 0) - \
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
        "expectancy": round(expectancy, 4),
        "avg_bars_held": round(avg_bars, 1),
        "sharpe": round(sharpe, 2),
        "L1_count": int((df["entry_leg"] == "L1").sum()),
        "L2_count": int((df["entry_leg"] == "L2").sum()),
        "L3_count": int((df["entry_leg"] == "L3").sum()),
    }

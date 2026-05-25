"""Hermes V2.1 — V3 Staircase Principles Extension Engine.
Applies V3's winning multi-TF gating, pyramiding, Darvas, volume filter to daily
entries gated by weekly L1/L2/L3 activation. Tests 8 improvement filters independently."""
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hermes_v1_indicators import ema, sma, compute_atr, compute_adx, rolling_highest, rolling_lowest


class HermesV21Engine:
    def __init__(self, config_path):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)
        self.cfg["staircase"] = self.cfg.get("staircase", {})
        self.cfg["improvements"] = self.cfg.get("improvements", [])
        c = self.cfg["staircase"]
        self.ema_f, self.ema_s = c["ema_fast"], c["ema_slow"]
        self.adx_len, self.adx_thresh = c["adx_length"], c["adx_threshold"]
        self.breakout_lb, self.slope_lb = c["breakout_lookback"], c["slope_lookback"]
        self.atr_len = c.get("atr_length", 14)
        self.darvas_len = c.get("darvas_len", 40)
        self.pyra = c.get("pyramiding", {})
        self.exit_cfg = self.cfg.get("exit", {})
        self.vault = Path(self.cfg["vault"]["path"])
        self.out_dir = Path(self.cfg["output"]["dir"])
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / "improvement_results").mkdir(exist_ok=True)
        self.all_trades = []

    def load(self, symbol, tf):
        fp = self.vault / symbol / f"{symbol}_{tf}.parquet"
        if not fp.exists():
            return None
        df = pd.read_parquet(fp)
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime").sort_index()
        if "symbol" in df.columns:
            df = df.drop(columns=["symbol"])
        return df

    def add_v3_indicators(self, df, prefix="w_"):
        """Compute all V3 Staircase indicators as in staircase_weekly_backtest_v3.py."""
        d = df.copy()
        d[f"{prefix}ema9"] = ema(d["close"], self.ema_f)
        d[f"{prefix}ema21"] = ema(d["close"], self.ema_s)
        for w, n in [(10, "sma10"), (20, "sma20"), (50, "sma50"), (100, "sma100"), (200, "sma200")]:
            d[f"{prefix}{n}"] = sma(d["close"], w)
        # ATR
        prev_c = d["close"].shift(1)
        tr = pd.concat([d["high"] - d["low"], (d["high"] - prev_c).abs(), (d["low"] - prev_c).abs()], axis=1).max(axis=1)
        d[f"{prefix}atr"] = tr.ewm(span=self.atr_len, adjust=False).mean()
        # Volume OK
        d[f"{prefix}vol10"] = d["volume"].rolling(10, min_periods=10).mean()
        d[f"{prefix}vol20"] = d["volume"].rolling(20, min_periods=20).mean()
        d[f"{prefix}vol30"] = d["volume"].rolling(30, min_periods=30).mean()
        d[f"{prefix}volume_ok"] = d["volume"] > d[f"{prefix}vol10"]
        # Short-term stack
        d[f"{prefix}short_stacked"] = (d[f"{prefix}sma10"] > d[f"{prefix}sma20"]) & (d[f"{prefix}sma20"] > d[f"{prefix}sma50"])
        d[f"{prefix}price_above_short"] = (d["close"] > d[f"{prefix}sma10"]) & (d["close"] > d[f"{prefix}sma20"]) & (d["close"] > d[f"{prefix}sma50"])
        d[f"{prefix}short_ok"] = d[f"{prefix}short_stacked"] & d[f"{prefix}price_above_short"]
        # Long-term
        d[f"{prefix}long_stacked"] = (d[f"{prefix}sma50"] > d[f"{prefix}sma100"]) & (d[f"{prefix}sma100"] > d[f"{prefix}sma200"])
        d[f"{prefix}sma50_rising"] = d[f"{prefix}sma50"] > d[f"{prefix}sma50"].shift(self.slope_lb)
        d[f"{prefix}sma100_rising"] = d[f"{prefix}sma100"] > d[f"{prefix}sma100"].shift(self.slope_lb)
        d[f"{prefix}price_above_long"] = (d["close"] > d[f"{prefix}sma50"]) & (d["close"] > d[f"{prefix}sma100"]) & (d["close"] > d[f"{prefix}sma200"])
        d[f"{prefix}long_ok"] = d[f"{prefix}long_stacked"] & d[f"{prefix}sma50_rising"] & d[f"{prefix}sma100_rising"] & d[f"{prefix}price_above_long"]
        # EMA trend
        d[f"{prefix}ema_uptrend"] = d[f"{prefix}ema9"] > d[f"{prefix}ema21"]
        d[f"{prefix}price_above_ema"] = d["close"] > d[f"{prefix}ema21"]
        # Darvas
        body_t = d[["open", "close"]].max(axis=1)
        d[f"{prefix}darvas_top"] = body_t.rolling(self.darvas_len, min_periods=self.darvas_len).max().shift(1)
        d[f"{prefix}darvas_ok"] = d["close"] > d[f"{prefix}darvas_top"]
        # Crossunders
        d[f"{prefix}ema_crossunder"] = (d[f"{prefix}ema9"].shift(1) > d[f"{prefix}ema21"].shift(1)) & (d[f"{prefix}ema9"] < d[f"{prefix}ema21"])
        d[f"{prefix}sma_crossunder"] = (d[f"{prefix}sma50"].shift(1) > d[f"{prefix}sma100"].shift(1)) & (d[f"{prefix}sma50"] < d[f"{prefix}sma100"])
        # Consolidation SL
        d[f"{prefix}consolidation_low"] = d["low"].rolling(5, min_periods=5).min()
        d[f"{prefix}consolidation_sl"] = d[f"{prefix}consolidation_low"] - d[f"{prefix}atr"] * self.exit_cfg.get("sl_buffer_atr", 0.2)
        return d

    def compute_v3_entry_signal(self, df, prefix, tf_short_on, tf_long_on, tf_darvas_on):
        """Reproduce V3's entry_signal logic for a single timeframe."""
        d = df.copy()
        c = self.cfg["staircase"]
        # TF filter
        d["tf_short_ok"] = (not tf_short_on) | d[f"{prefix}short_ok"]
        d["tf_long_ok"] = (not tf_long_on) | d[f"{prefix}long_ok"]
        d["tf_ema_ok"] = d[f"{prefix}ema_uptrend"] & d[f"{prefix}price_above_ema"]
        d["tf_ok"] = d["tf_short_ok"] & d["tf_long_ok"] & d["tf_ema_ok"] & d[f"{prefix}volume_ok"]
        if tf_darvas_on:
            d["tf_ok"] = d["tf_ok"] & d[f"{prefix}darvas_ok"]
        # Base core
        d["base_core"] = d[f"{prefix}ema_uptrend"] & d[f"{prefix}price_above_ema"] & d[f"{prefix}volume_ok"]
        # Global Darvas
        d["global_darvas_ok"] = d[f"{prefix}darvas_ok"]
        # Entry signal
        d["entry_signal"] = d["base_core"] & d["tf_ok"] & d["global_darvas_ok"]
        return d

    def compute_weekly_activation(self, df_wk):
        """Run V3 pyramiding on weekly to find activation zones. Returns boolean Series
        where activation = the bar of L1/L2/L3 entry + N lookahead bars."""
        d = self.add_v3_indicators(df_wk, "w_")
        d = self.compute_v3_entry_signal(d, "w_",
            tf_short_on=self.cfg["staircase"].get("tf1_short", True),
            tf_long_on=self.cfg["staircase"].get("tf1_long", False),
            tf_darvas_on=self.cfg["staircase"].get("tf1_darvas", False))

        lookahead = self.pyra.get("activation_lookahead_bars", 4)
        activation = pd.Series(False, index=d.index)
        pos_count, entry_prices, last_idx = 0, [], -999

        for i in range(len(d)):
            if i < 50:
                continue
            signal = d["entry_signal"].iloc[i]
            close = d["close"].iloc[i]
            if signal and (i - last_idx) >= self.pyra.get("min_bars_between", 1):
                if pos_count == 0:
                    pos_count, entry_prices, last_idx = 1, [close], i
                    end = min(i + lookahead, len(d))
                    activation.iloc[i:end] = True
                elif pos_count == 1 and entry_prices[0] > 0 and pct(close, entry_prices[0]) >= self.pyra.get("min_profit_for_next", 0.0):
                    pos_count, last_idx = 2, i; entry_prices.append(close)
                    end = min(i + lookahead, len(d)); activation.iloc[i:end] = True
                elif pos_count == 2 and len(entry_prices) >= 2 and entry_prices[1] > 0 and pct(close, entry_prices[1]) >= 0:
                    pos_count, last_idx = 3, i; entry_prices.append(close)
                    end = min(i + lookahead, len(d)); activation.iloc[i:end] = True
            if i > 0 and (d["w_ema_crossunder"].iloc[i] or d["w_sma_crossunder"].iloc[i]):
                pos_count, entry_prices = 0, []
        return activation, d

    def apply_improvement_filter(self, df, imp_name):
        """Return a boolean mask for entries that pass the improvement filter.
        Assumes df has 'entry_signal' already computed from V3 logic."""
        c = self.cfg["staircase"]

        if imp_name == "baseline":
            return pd.Series(True, index=df.index)

        elif imp_name == "rule_50_80":
            ext = (df["close"] - df["sma200"]) / df["sma200"] * 100
            return ext.fillna(0) <= 80

        elif imp_name == "tennis_ball":
            low_touched = (df["low"].rolling(3).min() <= df["ema21"] * 1.01)
            return low_touched.fillna(False)

        elif imp_name == "strong_demand":
            vol_4w_avg = df["volume"].rolling(4).mean()
            return (df["volume"] > vol_4w_avg * 1.2).fillna(False)

        elif imp_name == "climax_avoid":
            r12w = (df["close"] / df["close"].shift(12) - 1) * 100
            return r12w.fillna(0) <= 100

        elif imp_name == "pivot_entry":
            h52 = df["high"].rolling(52).max()
            return ((df["close"] / h52.shift(1) * 100) >= 90).fillna(False)

        elif imp_name == "dual_bias":
            return pd.Series(True, index=df.index)

        elif imp_name == "sma_trail":
            return pd.Series(True, index=df.index)

        elif imp_name == "combined":
            t1 = (df["low"].rolling(3).min() <= df["ema21"] * 1.01).fillna(False)
            v4 = df["volume"].rolling(4).mean()
            t2 = (df["volume"] > v4 * 1.2).fillna(False)
            h52 = df["high"].rolling(52).max()
            t3 = ((df["close"] / h52.shift(1) * 100) >= 90).fillna(False)
            return t1 & t2 & t3

        return pd.Series(True, index=df.index)

    def backtest_improvement(self, df_daily, weekly_act, imp_name):
        """Run V3-style entries on daily, gated by weekly activation + improvement filter."""
        df = self.add_v3_indicators(df_daily, "")  # NO PREFIX for daily
        df = self.compute_v3_entry_signal(df, "",
            tf_short_on=self.cfg["staircase"].get("tf2_short", True),
            tf_long_on=self.cfg["staircase"].get("tf2_long", True),
            tf_darvas_on=self.cfg["staircase"].get("tf2_darvas", False))

        # Forward-fill weekly activation to daily
        wa = weekly_act.reindex(df.index, method="ffill").fillna(False)
        df["weekly_active"] = wa.values

        if imp_name == "dual_bias":
            df["daily_trend_ok"] = df["ema_uptrend"] & df["price_above_ema"] & df["volume_ok"]
            df["weekly_active"] = df["weekly_active"] & df["daily_trend_ok"]

        # Apply entry filter on entry_signal bars within weekly activation
        filt = self.apply_improvement_filter(df, imp_name)
        entry_mask = df["entry_signal"] & df["weekly_active"] & filt
        if not entry_mask.any():
            return []

        es = []
        for e_idx in np.where(entry_mask.values)[0]:
            if e_idx >= len(df) - 3:
                continue
            target_price = df["close"].iloc[e_idx]
            target_atr = df["atr"].iloc[e_idx]
            if pd.isna(target_atr) or target_atr <= 0:
                continue
            # SL and TP from V3 logic
            sl = target_price - target_atr * self.exit_cfg.get("sl_atr_multiplier", 1.5)
            tp = target_price + (target_price - sl) * self.exit_cfg["risk_reward_l1"]

            exit_dt, exit_price, exit_reason = None, None, "open"
            future = df.iloc[e_idx + 1:]
            for _, (fut_dt, row) in enumerate(future.iterrows()):
                ch, cl, cc = row["high"], row["low"], row["close"]
                if cl <= sl:
                    exit_dt, exit_price, exit_reason = fut_dt, min(cc, sl), "SL"
                    break
                if ch >= tp:
                    exit_dt, exit_price, exit_reason = fut_dt, tp, "TP"
                    break
                cu = row.get("ema_crossunder", False) or row.get("sma_crossunder", False)
                if cu:
                    exit_dt, exit_price, exit_reason = fut_dt, cc, "trend_break"
                    break

            if exit_dt is None:
                last = df.iloc[-1]
                exit_dt, exit_price, exit_reason = df.index[-1], last["close"], "EOD"

            if exit_price and target_price != 0:
                pnl = (exit_price - target_price) / target_price * 100
                risk = target_price - sl if target_price > sl else 0.01 * target_price
                pnl_r = pnl / (risk / target_price * 100) if risk > 0 else 0
                es.append({
                    "entry_dt": str(df.index[e_idx]), "exit_dt": str(exit_dt),
                    "entry_price": round(target_price, 2), "exit_price": round(exit_price, 2),
                    "sl": round(sl, 2), "tp": round(tp, 2),
                    "improvement": imp_name, "exit_reason": exit_reason,
                    "pnl_pct": round(pnl, 4), "pnl_r": round(pnl_r, 4),
                })
        return es

    def aggregate(self, trades):
        if not trades:
            return {"trades": 0, "win_rate": 0, "avg_r": 0, "total_return": 0, "profit_factor": 0,
                    "max_dd": 0, "total_r": 0, "avg_win_r": 0, "avg_loss_r": 0, "sharpe": 0}
        df = pd.DataFrame(trades)
        n = len(df)
        wins = df[df["pnl_pct"] > 0]
        losses = df[df["pnl_pct"] <= 0]
        wr = len(wins) / n * 100
        avg_r = df["pnl_r"].mean()
        total_ret = df["pnl_pct"].sum()
        total_r = df["pnl_r"].sum()
        gp = wins["pnl_pct"].sum() if len(wins) > 0 else 0
        gl = abs(losses["pnl_pct"].sum()) if len(losses) > 0 else 1e-9
        pf = gp / gl
        aw = wins["pnl_r"].mean() if len(wins) > 0 else 0
        al = losses["pnl_r"].mean() if len(losses) > 0 else 0
        cum = df["pnl_pct"].cumsum()
        peak = cum.cummax()
        mdd = abs((cum - peak).min()) if not df["pnl_pct"].empty else 0
        sr = (df["pnl_pct"].mean() / df["pnl_pct"].std() * np.sqrt(252 / 3)) if df["pnl_pct"].std() > 0 else 0
        return {"trades": n, "win_rate": round(wr, 1), "avg_r": round(avg_r, 3),
                "total_return": round(total_ret, 2), "total_r": round(total_r, 2),
                "profit_factor": round(pf, 2), "max_dd": round(mdd, 4),
                "avg_win_r": round(aw, 3), "avg_loss_r": round(al, 3), "sharpe": round(sr, 2)}

    def process_stock(self, symbol):
        df_wk = self.load(symbol, "1wk")
        if df_wk is None or len(df_wk) < 50:
            return
        df_d = self.load(symbol, "1d")
        if df_d is None or len(df_d) < 100:
            return

        weekly_act, _ = self.compute_weekly_activation(df_wk)
        print(f"\n--- {symbol} --- Weekly active: {weekly_act.sum()} bars")

        results = {}
        for imp in self.cfg["improvements"]:
            imp_name = imp["name"]
            trades = self.backtest_improvement(df_d, weekly_act, imp_name)
            m = self.aggregate(trades)
            m["improvement"] = imp_name
            m["symbol"] = symbol
            results[imp_name] = m
            if trades:
                pd.DataFrame(trades).to_csv(
                    self.out_dir / "improvement_results" / f"{symbol}__{imp_name}.csv", index=False)

        # Print top 3 improvements by total_return
        ranked = sorted(results.values(), key=lambda r: r["total_return"], reverse=True)[:4]
        for r in ranked:
            print(f"  {r['improvement']:20s}: {r['trades']:3d}t {r['win_rate']:.0f}%WR {r['avg_r']:.3f}R tot={r['total_return']:.1f}%")

        return results

    def build_report(self, all_results):
        if not all_results:
            print("No results")
            return
        rows = []
        for stock_results in all_results:
            for imp_name, m in stock_results.items():
                rows.append(m)
        df = pd.DataFrame(rows)

        lines = ["# Hermes V2.1 — V3 Staircase Improvement Filters",
                 f"Generated: {datetime.now(timezone.utc).isoformat()}",
                 f"Stocks: {df['symbol'].nunique()} | Filters: {df['improvement'].nunique()}",
                 ""]

        # Main ranking table
        agg = df.groupby("improvement").agg({
            "trades": "sum", "win_rate": "mean", "avg_r": "mean",
            "total_return": "sum", "total_r": "sum", "profit_factor": "mean",
            "max_dd": "max", "avg_win_r": "mean", "avg_loss_r": "mean", "sharpe": "mean",
        }).round(3).sort_values("total_r", ascending=False)

        lines.append("## Improvement Rankings (Aggregate across all stocks)")
        lines.append("")
        lines.append("| Improvement | Trades | WR% | AvgR | TotalR | PF | MaxDD | Sharpe |")
        lines.append("|-------------|--------|-----|------|--------|----|-------|--------|")
        for imp, row in agg.iterrows():
            lines.append(f"| {imp} | {int(row['trades'])} | {row['win_rate']:.0f} | {row['avg_r']:.3f} | {row['total_r']:.1f} | {row['profit_factor']:.2f} | {row['max_dd']:.1f} | {row['sharpe']:.2f} |")

        lines.append("")
        for imp_name in agg.index:
            sub = df[df["improvement"] == imp_name].sort_values("total_r", ascending=False)
            lines.append(f"### {imp_name} — Top Stocks")
            lines.append(f"| Symbol | Trades | WR% | AvgR | TotalR |")
            lines.append(f"|--------|--------|-----|------|--------|")
            for _, row in sub.head(10).iterrows():
                lines.append(f"| {row['symbol']} | {int(row['trades'])} | {row['win_rate']:.0f} | {row['avg_r']:.3f} | {row['total_r']:.1f} |")
            lines.append("")

        report_path = self.out_dir / "improvement_report.md"
        report_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nReport: {report_path}")


def pct(a, b):
    return (a - b) / b * 100 if b != 0 else 0

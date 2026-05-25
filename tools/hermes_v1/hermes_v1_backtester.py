"""Hermes V1 Backtester — walk-forward backtesting with trade logging."""
import yaml
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path


class Backtester:
    def __init__(self, config_path, output_dir):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.risk = self.cfg["risk"]
        self.sl_atr = self.risk.get("sl_atr_multiplier", 1.5)
        self.rr_ratios = self.risk.get("target_rr_ratios", [1.0, 1.5, 2.0, 2.5, 3.0])
        self.all_trades = []

    def backtest_entry(self, df, entries_df, atr_col="atr14", close_col="close",
                        high_col="high", low_col="low"):
        """Simulate trades for each entry signal. Returns trades list."""
        trades = []
        if entries_df is None or entries_df.empty:
            return trades

        for _, entry in entries_df.iterrows():
            entry_dt = entry.get("datetime")
            entry_price = entry.get("price")
            entry_type = entry.get("entry_type", "unknown")
            tf = entry.get("timeframe", "unknown")

            if entry_dt not in df.index:
                continue

            idx_loc = df.index.get_loc(entry_dt)
            atr = df[atr_col].iloc[idx_loc] if not pd.isna(df[atr_col].iloc[idx_loc]) else 0.01 * entry_price
            sl_distance = atr * self.sl_atr
            stop_loss = entry_price - sl_distance

            future = df.iloc[idx_loc + 1:]
            if future.empty:
                continue

            exit_dt, exit_price, exit_reason = None, None, "open"
            mfe, mae = 0, 0

            for j, (fut_dt, row) in enumerate(future.iterrows()):
                current_high = row[high_col]
                current_low = row[low_col]
                current_close = row[close_col]

                mfe = max(mfe, (current_high - entry_price) / entry_price * 100)
                mae = max(mae, (entry_price - current_low) / entry_price * 100)

                if current_low <= stop_loss:
                    exit_dt = fut_dt
                    exit_price = min(current_close, stop_loss)
                    exit_reason = "stop_loss"
                    break

                distance = current_close - entry_price
                if distance > sl_distance:
                    for rr in sorted(self.rr_ratios):
                        target = entry_price + sl_distance * rr
                        if current_high >= target:
                            exit_dt = fut_dt
                            exit_price = target
                            exit_reason = f"target_{rr}R"
                            break
                    if exit_dt is not None:
                        break

                if j >= 100:
                    exit_dt = fut_dt
                    exit_price = current_close
                    exit_reason = "timeout"
                    break

            if exit_dt is None and not future.empty:
                last = future.iloc[-1]
                exit_dt = future.index[-1]
                exit_price = last[close_col]
                exit_reason = "end_of_data"

            if exit_price and entry_price and entry_price != 0:
                pnl_pct = (exit_price - entry_price) / entry_price * 100
                pnl_r = pnl_pct / (sl_distance / entry_price * 100) if sl_distance > 0 else 0

                trade = {
                    "entry_dt": str(entry_dt),
                    "exit_dt": str(exit_dt),
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "stop_loss": round(stop_loss, 2),
                    "entry_type": entry_type,
                    "timeframe": tf,
                    "exit_reason": exit_reason,
                    "pnl_pct": round(pnl_pct, 4),
                    "pnl_r": round(pnl_r, 4),
                    "mfe_pct": round(mfe, 4),
                    "mae_pct": round(mae, 4),
                    "holding_bars": j if exit_dt else 0,
                }
                trades.append(trade)

        return trades

    def aggregate(self, trades):
        if not trades:
            return {"total_trades": 0, "win_rate": 0, "avg_return": 0, "total_return": 0, "profit_factor": 0,
                    "avg_r": 0, "max_drawdown": 0, "sharpe": 0}
        df = pd.DataFrame(trades)
        wins = df[df["pnl_pct"] > 0]
        losses = df[df["pnl_pct"] <= 0]
        total = len(df)
        win_rate = len(wins) / total if total > 0 else 0
        avg_return = df["pnl_pct"].mean()
        total_return = df["pnl_pct"].sum()
        gross_profit = wins["pnl_pct"].sum() if len(wins) > 0 else 0
        gross_loss = abs(losses["pnl_pct"].sum()) if len(losses) > 0 else 1e-9
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999
        avg_r = df["pnl_r"].mean() if "pnl_r" in df.columns else 0
        cum = df["pnl_pct"].cumsum()
        peak = cum.cummax()
        dd = (cum - peak)
        max_dd = abs(dd.min()) if not dd.empty else 0
        sharpe = (avg_return / df["pnl_pct"].std() * np.sqrt(252)) if df["pnl_pct"].std() > 0 else 0

        return {
            "total_trades": total,
            "win_rate": round(win_rate, 4),
            "avg_return": round(avg_return, 4),
            "total_return": round(total_return, 4),
            "profit_factor": round(profit_factor, 2),
            "avg_r": round(avg_r, 4),
            "max_drawdown": round(max_dd, 4),
            "sharpe": round(sharpe, 4),
        }

    def save_trades(self, trades, filename):
        if not trades:
            return
        path = self.output_dir / "trades" / filename
        pd.DataFrame(trades).to_csv(path, index=False)

    def save_signals(self, signals, filename):
        if signals is None or signals.empty:
            return
        path = self.output_dir / "signals" / filename
        signals.to_csv(path, index=False)

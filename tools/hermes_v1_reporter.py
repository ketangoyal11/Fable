"""Hermes V1 Reporter — generates markdown reports and CSV exports."""
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone


class Reporter:
    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.report_dir = self.output_dir / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def summary_report(self, results, filename="summary_report.md"):
        """results: dict with symbol -> {tf -> stats}"""
        path = self.report_dir / filename
        lines = []
        lines.append(f"# Hermes V1 Research Report")
        lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        lines.append("")

        lines.append("## Overall Summary")
        lines.append("")
        lines.append("| Symbol | Timeframe | Trades | Win Rate | Avg R | Total Return | Profit Factor | Max DD |")
        lines.append("|--------|-----------|--------|----------|-------|-------------|---------------|--------|")

        for symbol, tf_results in sorted(results.items()):
            for tf, stats in sorted(tf_results.items()):
                lines.append(
                    f"| {symbol} | {tf} | {stats.get('total_trades',0)} | "
                    f"{stats.get('win_rate',0):.1%} | {stats.get('avg_r',0):.2f} | "
                    f"{stats.get('total_return',0):.2f}% | {stats.get('profit_factor',0):.1f} | "
                    f"{stats.get('max_drawdown',0):.2f}% |"
                )

        lines.append("")
        with open(path, "w") as f:
            f.write("\n".join(lines))
        print(f"Report saved: {path}")

    def entry_type_breakdown(self, trades_by_type, filename="entry_type_breakdown.md"):
        path = self.report_dir / filename
        lines = ["# Entry Type Breakdown", ""]
        lines.append("| Entry Type | Trades | Win Rate | Avg R | Profit Factor |")
        lines.append("|------------|--------|----------|-------|---------------|")

        for etype, trades in sorted(trades_by_type.items()):
            if not trades:
                continue
            df = pd.DataFrame(trades)
            wins = len(df[df["pnl_pct"] > 0])
            total = len(df)
            wr = wins / total if total else 0
            avg_r = df["pnl_r"].mean() if "pnl_r" in df.columns else 0
            gp = df[df["pnl_pct"] > 0]["pnl_pct"].sum() if wins > 0 else 0
            gl = abs(df[df["pnl_pct"] <= 0]["pnl_pct"].sum()) if (total - wins) > 0 else 1e-9
            pf = gp / gl if gl > 0 else 999
            lines.append(f"| {etype} | {total} | {wr:.1%} | {avg_r:.2f} | {pf:.1f} |")

        lines.append("")
        with open(path, "w") as f:
            f.write("\n".join(lines))

    def save_all_csvs(self, all_trades, weekly_signals):
        td = self.output_dir / "trades"
        sd = self.output_dir / "signals"

        if all_trades:
            pd.DataFrame(all_trades).to_csv(td / "all_trades.csv", index=False)
        if weekly_signals:
            pd.DataFrame(weekly_signals).to_csv(sd / "weekly_signals.csv", index=False)

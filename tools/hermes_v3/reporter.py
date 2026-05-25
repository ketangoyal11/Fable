"""Hermes V3 Reporter — CSV + Markdown report generation."""
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime


class Reporter:
    def __init__(self, output_dir):
        self.out = Path(output_dir)
        self.out.mkdir(parents=True, exist_ok=True)

    def save_trades(self, all_trades, filename="all_trades.csv"):
        if not all_trades:
            return
        df = pd.DataFrame(all_trades)
        df.to_csv(self.out / filename, index=False)

    def save_signals(self, all_signals, filename="all_signals.csv"):
        if not all_signals:
            return
        df = pd.DataFrame(all_signals)
        df.to_csv(self.out / filename, index=False)

    def save_skipped(self, all_skips, filename="skipped_symbols.csv"):
        if not all_skips:
            return
        df = pd.DataFrame(all_skips)
        df.to_csv(self.out / filename, index=False)

    def per_symbol_summary(self, all_trades, filename="per_symbol_summary.csv"):
        if not all_trades:
            return
        df = pd.DataFrame(all_trades)
        rows = []
        for sym, g in df.groupby("symbol"):
            n = len(g)
            wr = (g["r_multiple"] > 0).sum() / n * 100 if n > 0 else 0
            rows.append({
                "symbol": sym,
                "trades": n,
                "win_rate": round(wr, 1),
                "avg_r": round(g["r_multiple"].mean(), 4),
                "total_r": round(g["r_multiple"].sum(), 4),
                "gross_pnl": round(g["gross_pnl"].sum(), 2),
            })
        pd.DataFrame(rows).sort_values("total_r", ascending=False).to_csv(
            self.out / filename, index=False)

    def per_timeframe_summary(self, all_trades, filename="per_timeframe_summary.csv"):
        if not all_trades:
            return
        df = pd.DataFrame(all_trades)
        rows = []
        for tf, g in df.groupby("timeframe"):
            n = len(g)
            wr = (g["r_multiple"] > 0).sum() / n * 100 if n > 0 else 0
            rows.append({
                "timeframe": tf,
                "trades": n,
                "win_rate": round(wr, 1),
                "avg_r": round(g["r_multiple"].mean(), 4),
                "total_r": round(g["r_multiple"].sum(), 4),
                "avg_bars": round(g["bars_held"].mean(), 1) if "bars_held" in g.columns else 0,
            })
        pd.DataFrame(rows).sort_values("total_r", ascending=False).to_csv(
            self.out / filename, index=False)

    def darvas_variant_summary(self, all_trades, filename="darvas_variant_summary.csv"):
        if not all_trades:
            return
        df = pd.DataFrame(all_trades)
        rows = []
        for dv, g in df.groupby("darvas_variant"):
            n = len(g)
            wr = (g["r_multiple"] > 0).sum() / n * 100 if n > 0 else 0
            rows.append({
                "darvas_variant": dv,
                "trades": n,
                "win_rate": round(wr, 1),
                "avg_r": round(g["r_multiple"].mean(), 4),
                "total_r": round(g["r_multiple"].sum(), 4),
                "profit_factor": round(
                    g[g["r_multiple"] > 0]["r_multiple"].sum() / abs(g[g["r_multiple"] <= 0]["r_multiple"].sum())
                    if abs(g[g["r_multiple"] <= 0]["r_multiple"].sum()) > 0 else 0, 2),
            })
        pd.DataFrame(rows).sort_values("total_r", ascending=False).to_csv(
            self.out / filename, index=False)

    def entry_leg_summary(self, all_trades, filename="entry_leg_summary.csv"):
        if not all_trades:
            return
        df = pd.DataFrame(all_trades)
        rows = []
        for leg, g in df.groupby("entry_leg"):
            n = len(g)
            wr = (g["r_multiple"] > 0).sum() / n * 100 if n > 0 else 0
            rows.append({
                "entry_leg": leg,
                "trades": n,
                "win_rate": round(wr, 1),
                "avg_r": round(g["r_multiple"].mean(), 4),
                "total_r": round(g["r_multiple"].sum(), 4),
            })
        pd.DataFrame(rows).to_csv(self.out / filename, index=False)

    def combo_summary(self, all_trades, filename="combo_summary.csv"):
        """Ranked summary by combo_name (across all timeframes)."""
        if not all_trades:
            return
        df = pd.DataFrame(all_trades)
        rows = []
        for cn, g in df.groupby("combo_name"):
            n = len(g)
            wr = (g["r_multiple"] > 0).sum() / n * 100 if n > 0 else 0
            gp = g[g["r_multiple"] > 0]["r_multiple"].sum() if n > 0 else 0
            gl = abs(g[g["r_multiple"] <= 0]["r_multiple"].sum()) if n > 0 else 1e-9
            rows.append({
                "combo_name": cn,
                "trades": n,
                "win_rate": round(wr, 1),
                "avg_r": round(g["r_multiple"].mean(), 4),
                "total_r": round(g["r_multiple"].sum(), 4),
                "profit_factor": round(gp / gl if gl > 0 else 0, 2),
                "avg_bars": round(g["bars_held"].mean(), 1) if "bars_held" in g.columns else 0,
                "L1": int((g["entry_leg"] == "L1").sum()),
                "L2": int((g["entry_leg"] == "L2").sum()),
                "L3": int((g["entry_leg"] == "L3").sum()),
            })
        pd.DataFrame(rows).sort_values("total_r", ascending=False).to_csv(
            self.out / filename, index=False)

    def combo_by_timeframe(self, all_trades, filename="combo_by_timeframe.csv"):
        """Ranked summary: best combo per timeframe."""
        if not all_trades:
            return
        df = pd.DataFrame(all_trades)
        rows = []
        for (tf, cn), g in df.groupby(["timeframe", "combo_name"]):
            n = len(g)
            wr = (g["r_multiple"] > 0).sum() / n * 100 if n > 0 else 0
            gp = g[g["r_multiple"] > 0]["r_multiple"].sum() if n > 0 else 0
            gl = abs(g[g["r_multiple"] <= 0]["r_multiple"].sum()) if n > 0 else 1e-9
            rows.append({
                "timeframe": tf,
                "combo_name": cn,
                "trades": n,
                "win_rate": round(wr, 1),
                "avg_r": round(g["r_multiple"].mean(), 4),
                "total_r": round(g["r_multiple"].sum(), 4),
                "profit_factor": round(gp / gl if gl > 0 else 0, 2),
            })
        pd.DataFrame(rows).sort_values(["timeframe", "total_r"], ascending=[True, False]).to_csv(
            self.out / filename, index=False)

    def per_stock_by_combo(self, all_trades, filename="per_stock_by_combo.csv"):
        """Stock-level breakdown per combo."""
        if not all_trades:
            return
        df = pd.DataFrame(all_trades)
        rows = []
        for (sym, cn), g in df.groupby(["symbol", "combo_name"]):
            n = len(g)
            wr = (g["r_multiple"] > 0).sum() / n * 100 if n > 0 else 0
            rows.append({
                "symbol": sym,
                "combo_name": cn,
                "trades": n,
                "win_rate": round(wr, 1),
                "avg_r": round(g["r_multiple"].mean(), 4),
                "total_r": round(g["r_multiple"].sum(), 4),
                "L1": int((g["entry_leg"] == "L1").sum()),
                "L2": int((g["entry_leg"] == "L2").sum()),
                "L3": int((g["entry_leg"] == "L3").sum()),
            })
        pd.DataFrame(rows).sort_values(["combo_name", "total_r"], ascending=[True, False]).to_csv(
            self.out / filename, index=False)

    def save_config_snapshot(self, cfg, filename="run_config_snapshot.yaml"):
        with open(self.out / filename, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False)

    def build_report(self, all_trades, all_signals, all_skips, cfg, compare_stats=None):
        lines = ["# Hermes V3 Backtest Report",
                 f"Generated: {datetime.now().isoformat()}",
                 f"Config: Staircase SMA Trend Filter (33/33/34)",
                 ""]

        if not all_trades:
            lines.append("**No trades generated.**")
            lines.append("")
            if all_skips:
                lines.append(f"Skipped entries: {len(all_skips)}")
            report_path = self.out / "report.md"
            report_path.write_text("\n".join(lines), encoding="utf-8")
            return report_path

        df = pd.DataFrame(all_trades)
        n = len(df)
        wr = (df["r_multiple"] > 0).sum() / n * 100 if n > 0 else 0
        avg_r = df["r_multiple"].mean()
        total_r = df["r_multiple"].sum()

        lines.append("## Overall Summary")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Trades | {n} |")
        lines.append(f"| Win Rate | {wr:.1f}% |")
        lines.append(f"| Avg R | {avg_r:.4f} |")
        lines.append(f"| Total R | {total_r:.2f} |")
        lines.append(f"| L1/L2/L3 | {(df['entry_leg']=='L1').sum()}/{(df['entry_leg']=='L2').sum()}/{(df['entry_leg']=='L3').sum()} |")
        lines.append("")

        # By timeframe
        lines.append("## By Timeframe")
        lines.append("| Timeframe | Trades | WR% | AvgR | TotalR |")
        lines.append("|-----------|--------|-----|------|--------|")
        for tf, g in df.groupby("timeframe"):
            tn = len(g)
            twr = (g["r_multiple"] > 0).sum() / tn * 100 if tn > 0 else 0
            tavg = g["r_multiple"].mean()
            ttotal = g["r_multiple"].sum()
            lines.append(f"| {tf} | {tn} | {twr:.1f} | {tavg:.4f} | {ttotal:.2f} |")
        lines.append("")

        # By Darvas variant
        lines.append("## By Darvas Variant")
        lines.append("| Variant | Trades | WR% | AvgR | TotalR |")
        lines.append("|---------|--------|-----|------|--------|")
        for dv, g in df.groupby("darvas_variant"):
            dn = len(g)
            dwr = (g["r_multiple"] > 0).sum() / dn * 100 if dn > 0 else 0
            davg = g["r_multiple"].mean()
            dtotal = g["r_multiple"].sum()
            lines.append(f"| {dv} | {dn} | {dwr:.1f} | {davg:.4f} | {dtotal:.2f} |")
        lines.append("")

        # By Combo (overall ranking across all timeframes)
        if "combo_name" in df.columns:
            df_cn = df["combo_name"].dropna()
            if len(df_cn) > 0:
                lines.append("## By Combo (Ranked, All Timeframes)")
                lines.append("| Combo | Trades | WR% | AvgR | TotalR | PF | L1/L2/L3 |")
                lines.append("|-------|--------|-----|------|--------|----|----------|")
                for cn, g in df.groupby("combo_name"):
                    cn = str(cn)
                    cn_ = cn if cn != "nan" else "BASELINE"
                    gn = len(g)
                    gwr = (g["r_multiple"] > 0).sum() / gn * 100 if gn > 0 else 0
                    gavg = g["r_multiple"].mean()
                    gtotal = g["r_multiple"].sum()
                    gp = g[g["r_multiple"] > 0]["r_multiple"].sum() if gn > 0 else 0
                    gl = abs(g[g["r_multiple"] <= 0]["r_multiple"].sum()) if gn > 0 else 1e-9
                    gpf = gp / gl if gl > 0 else 0
                    l1 = int((g["entry_leg"] == "L1").sum())
                    l2 = int((g["entry_leg"] == "L2").sum())
                    l3 = int((g["entry_leg"] == "L3").sum())
                    lines.append(f"| {cn_} | {gn} | {gwr:.1f} | {gavg:.4f} | {gtotal:.2f} | {gpf:.2f} | {l1}/{l2}/{l3} |")
                lines.append("")

            # Best combo per timeframe
            lines.append("## Best Combo Per Timeframe")
            lines.append("| Timeframe | Best Combo | Trades | WR% | AvgR | TotalR | PF |")
            lines.append("|-----------|------------|--------|-----|------|--------|----|")
            for tf, g in df.groupby("timeframe"):
                best = None
                best_r = -999
                for cn, cg in g.groupby("combo_name"):
                    tr = cg["r_multiple"].sum()
                    if tr > best_r:
                        best_r = tr
                        cn_ = str(cn) if str(cn) != "nan" else "BASELINE"
                        gn = len(cg)
                        gwr = (cg["r_multiple"] > 0).sum() / gn * 100 if gn > 0 else 0
                        gavg = cg["r_multiple"].mean()
                        gp = cg[cg["r_multiple"] > 0]["r_multiple"].sum() if gn > 0 else 0
                        gl = abs(cg[cg["r_multiple"] <= 0]["r_multiple"].sum()) if gn > 0 else 1e-9
                        gpf = gp / gl if gl > 0 else 0
                        best = (cn_, gn, gwr, gavg, tr, gpf)
                if best:
                    cn_, gn, gwr, gavg, tr, gpf = best
                    lines.append(f"| {tf} | {cn_} | {gn} | {gwr:.1f} | {gavg:.4f} | {tr:.2f} | {gpf:.2f} |")
            lines.append("")

        # By exit reason
        lines.append("## Exit Reason Breakdown")
        lines.append("| Reason | Count |")
        lines.append("|--------|-------|")
        for reason, grp in df.groupby("exit_reason"):
            lines.append(f"| {reason} | {len(grp)} |")
        lines.append("")

        # Top symbols
        lines.append("## Top Symbols by Total R")
        lines.append("| Symbol | Trades | WR% | AvgR | TotalR |")
        lines.append("|--------|--------|-----|------|--------|")
        sym_summary = []
        for sym, g in df.groupby("symbol"):
            sn = len(g)
            swr = (g["r_multiple"] > 0).sum() / sn * 100 if sn > 0 else 0
            savg = g["r_multiple"].mean()
            stotal = g["r_multiple"].sum()
            sym_summary.append((sym, sn, swr, savg, stotal))
        sym_summary.sort(key=lambda x: x[4], reverse=True)
        for sym, sn, swr, savg, stotal in sym_summary[:15]:
            lines.append(f"| {sym} | {sn} | {swr:.1f} | {savg:.4f} | {stotal:.2f} |")
        lines.append("")

        # Comparison with weekly V3 if available
        if compare_stats:
            lines.append("## Comparison with Weekly-Only V3")
            lines.append("| Metric | Weekly V3 | Hermes V3 |")
            lines.append("|--------|-----------|-----------|")
            for metric, wv in compare_stats.items():
                hv = "N/A"
                if metric == "total_trades":
                    hv = str(n)
                elif metric == "win_rate":
                    hv = f"{wr:.1f}%"
                elif metric == "total_r":
                    hv = f"{total_r:.2f}"
                elif metric == "avg_r":
                    hv = f"{avg_r:.4f}"
                lines.append(f"| {metric} | {wv} | {hv} |")
            lines.append("")

        # Skipped entries
        if all_skips:
            lines.append(f"## Skipped Entries: {len(all_skips)}")
            skip_reasons = {}
            for s in all_skips:
                reason = s.get("reason", "unknown")
                skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            lines.append("| Reason | Count |")
            lines.append("|--------|-------|")
            for reason, count in sorted(skip_reasons.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {reason} | {count} |")
            lines.append("")

        report_path = self.out / "report.md"
        report_path.write_text("\n".join(lines), encoding="utf-8")
        return report_path

    def save_all(self, all_trades, all_signals, all_skips, cfg, compare_stats=None):
        self.save_trades(all_trades)
        self.save_signals(all_signals)
        self.save_skipped(all_skips)
        self.per_symbol_summary(all_trades)
        self.per_timeframe_summary(all_trades)
        self.darvas_variant_summary(all_trades)
        self.entry_leg_summary(all_trades)
        self.combo_summary(all_trades)
        self.combo_by_timeframe(all_trades)
        self.per_stock_by_combo(all_trades)
        self.save_config_snapshot(cfg)
        return self.build_report(all_trades, all_signals, all_skips, cfg, compare_stats)

#!/usr/bin/env python3
"""Hermes V3 Daily — Weekly Plans, Daily Executes.

USAGE:
  python tools/hermes_v3_daily/run.py --pilot 50
  python tools/hermes_v3_daily/run.py --full
  python tools/hermes_v3_daily/run.py --symbol RELIANCE
  python tools/hermes_v3_daily/run.py --darvas weekly_plus_daily_darvas
  python tools/hermes_v3_daily/run.py --l1-only
  python tools/hermes_v3_daily/run.py --compare-baseline
"""
import sys
import os
import yaml
import warnings
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd

warnings.filterwarnings("ignore")

# Add tools/ to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hermes_v3.data import discover_symbols, get_symbol_list, load_data
from hermes_v3_daily.weekly_planner import compute_weekly_plan, forward_fill_to_daily
from hermes_v3_daily.daily_executor import (
    compute_daily_indicators,
    compute_mtf_trend_filter,
    build_daily_entry_signal,
)
from hermes_v3_daily.darvas import compute_darvas, apply_darvas_filter
from hermes_v3_daily.engine import V3DailyEngine, aggregate_trades
from hermes_v3_daily.reporter import V3DailyReporter


def main():
    parser = argparse.ArgumentParser(description="Hermes V3 Daily Backtesting Engine")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--pilot", type=int, default=None, help="Run on N stocks")
    parser.add_argument("--full", action="store_true", help="Run on full universe")
    parser.add_argument("--symbol", type=str, default=None, help="Run single symbol")
    parser.add_argument("--darvas", type=str, default=None,
                        choices=["no_darvas", "weekly_darvas_gate", "daily_darvas_breakout",
                                 "daily_darvas_support", "weekly_plus_daily_darvas", "all"],
                        help="Darvas variant (default from config)")
    parser.add_argument("--darvas-len", type=int, default=None, help="Darvas lookback length")
    parser.add_argument("--l1-only", action="store_true", help="L1 entries only, no pyramiding")
    parser.add_argument("--no-mtf", action="store_true", help="Disable 1h/15m trend filter")
    parser.add_argument("--compare-baseline", action="store_true", help="Include baseline comparisons in report")
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    # Load config
    config_path = args.config or str(Path(__file__).parent / "config.yaml")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    if args.output_dir:
        cfg["output"]["dir"] = args.output_dir

    if args.l1_only:
        cfg["daily_pyramiding"]["l1_only"] = True

    if args.no_mtf:
        cfg["mtf_trend_filter"]["enabled"] = False

    # Select Darvas variants
    darvas_variants = cfg["darvas"]["variants"]
    if args.darvas and args.darvas != "all":
        darvas_variants = [args.darvas]
    darvas_len = args.darvas_len or cfg["darvas"]["default_len"]
    default_variant = cfg["darvas"]["variant"]

    # Setup output
    reporter = V3DailyReporter(cfg["output"]["dir"])

    # Discover symbols
    vault_path = cfg["data"]["vault_path"]
    registry = discover_symbols(vault_path, required_timeframes=["1wk", "1d"])

    # Filter symbols
    if args.symbol:
        symbols = [args.symbol] if args.symbol in registry else []
        if not symbols:
            print(f"Symbol {args.symbol} not found in vault")
            return
    elif args.pilot:
        symbols = get_symbol_list(registry, "ready", max_stocks=args.pilot)
    elif args.full:
        symbols = get_symbol_list(registry, "ready")
    else:
        symbols = get_symbol_list(registry, "ready", max_stocks=50)

    print(f"Hermes V3 Daily — Weekly Plans, Daily Executes")
    print(f"Symbols: {len(symbols)}")
    print(f"Darvas variant(s): {darvas_variants}")
    print(f"Darvas length: {darvas_len}")
    print(f"L1-only: {cfg['daily_pyramiding']['l1_only']}")
    print(f"MTF filter: {cfg['mtf_trend_filter']['enabled']}")
    print(f"Output: {cfg['output']['dir']}")

    engine = V3DailyEngine(cfg)
    all_trades = []
    all_signals = []
    all_skips = []

    mtf_enabled = cfg["mtf_trend_filter"]["enabled"]

    for symbol in symbols:
        print(f"\n--- {symbol} ---")

        # 1. Load weekly data
        df_w = load_data(symbol, "1wk", cfg)
        if df_w is None or len(df_w) < 50:
            print(f"  Weekly: insufficient data, skipping")
            all_skips.append({"dt": "", "symbol": symbol, "timeframe": "1wk", "reason": "insufficient_weekly"})
            continue

        # 2. Load daily data
        df_d = load_data(symbol, "1d", cfg)
        if df_d is None or len(df_d) < 50:
            print(f"  Daily: insufficient data, skipping")
            all_skips.append({"dt": "", "symbol": symbol, "timeframe": "1d", "reason": "insufficient_daily"})
            continue

        # 3. Load 1h/15m if MTF enabled
        df_h1 = None
        df_m15 = None
        if mtf_enabled:
            df_h1 = load_data(symbol, "1h", cfg)
            df_m15 = load_data(symbol, "15m", cfg)

        # 4. Compute weekly plan once per symbol (independent of Darvas variant)
        weekly_plan = compute_weekly_plan(df_w, cfg, darvas_len=darvas_len)
        act_bars = weekly_plan["w_activation_zone"].sum()
        l1_fires = weekly_plan["w_L1_fire"].sum()
        l2_fires = weekly_plan["w_L2_fire"].sum()
        l3_fires = weekly_plan["w_L3_fire"].sum()
        print(f"  Weekly: {len(weekly_plan)} bars | "
              f"signals: {weekly_plan['w_entry_signal'].sum()} | "
              f"L1:{int(l1_fires)} L2:{int(l2_fires)} L3:{int(l3_fires)} | "
              f"active: {int(act_bars)} bars")

        if act_bars == 0:
            print(f"  SKIP: no weekly activation zones")
            all_skips.append({"dt": "", "symbol": symbol, "timeframe": "1wk", "reason": "no_activation_zones"})
            continue

        # 5. Forward-fill weekly plan to daily
        weekly_state = forward_fill_to_daily(weekly_plan, df_d.index)

        # 6. Compute daily indicators
        df_d_enriched = compute_daily_indicators(df_d, cfg)

        # 7. Apply MTF trend filter
        df_d_enriched = compute_mtf_trend_filter(df_d_enriched, df_h1, df_m15, cfg)

        # 8. Compute daily Darvas (once, shared across variants)
        df_d_darvas = compute_darvas(df_d_enriched, darvas_len, prefix="daily_darvas_")

        for variant in darvas_variants:
            # Apply Darvas filter
            darvas_pass = apply_darvas_filter(
                df_d_darvas, weekly_plan, variant, darvas_len,
                daily_prefix="daily_darvas_", weekly_prefix="w_darvas_"
            )

            # Build entry signal
            df_d_final = build_daily_entry_signal(df_d_darvas, weekly_state, darvas_pass, cfg)

            # Count active bars and signals
            wa = weekly_state["weekly_active"].reindex(df_d_final.index).fillna(False)
            active_daily_bars = int(wa.sum())
            entry_sig_count = int(df_d_final["daily_entry_signal"].sum())

            if entry_sig_count == 0:
                print(f"  {variant}: {active_daily_bars} active daily bars, 0 signals")
                continue

            # Run engine
            trades, sigs, skips = engine.run(
                df_d_final, symbol, variant, darvas_len,
                weekly_state, weekly_plan_df=weekly_plan
            )

            variant_label = f"{variant}_{darvas_len}"
            if trades:
                all_trades.extend(trades)
                stats = aggregate_trades(trades)
                print(f"  {variant_label}: {active_daily_bars}act {stats['total_trades']}t "
                      f"{stats['win_rate']:.1f}%WR {stats['avg_r']:.4f}R "
                      f"totR={stats['total_r']:.2f} PF={stats['profit_factor']:.2f}")
            else:
                print(f"  {variant_label}: {active_daily_bars}act 0t")
            if sigs:
                all_signals.extend(sigs)
            if skips:
                all_skips.extend(skips)

    # Load baseline stats for comparison
    baseline_daily = None
    baseline_candle = None
    if args.compare_baseline:
        baseline_daily = {"Trades": 506, "Win Rate": "17.2%", "Avg R": "1.1160",
                          "Total R": 564.70, "Profit Factor": 2.86}
        baseline_candle = {"Trades": 260, "Win Rate": "17.3%", "Avg R": "6.4134",
                           "Total R": 1667.48, "Profit Factor": 14.38}

    # Save outputs
    report_path = reporter.save_all(all_trades, all_signals, all_skips, cfg,
                                     baseline_daily, baseline_candle)

    print(f"\n{'='*60}")
    print(f"DONE — {len(all_trades)} trades across {len(symbols)} symbols")
    print(f"Report: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

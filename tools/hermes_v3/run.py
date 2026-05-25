#!/usr/bin/env python3
"""Hermes V3 — Run orchestrator. SMA Trend Filter (33/33/34) backtesting engine.

USAGE:
  python tools/hermes_v3/run.py --pilot 50
  python tools/hermes_v3/run.py --full
  python tools/hermes_v3/run.py --symbol RELIANCE --timeframes 1d,1h,15m
  python tools/hermes_v3/run.py --source local
  python tools/hermes_v3/run.py --compare-weekly-v3
"""
import sys
import os
import yaml
import warnings
import argparse
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

# Add tools/ to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hermes_v3.data import discover_symbols, get_symbol_list, load_data
from hermes_v3.indicators import compute_all_indicators
from hermes_v3.darvas import compute_darvas
from hermes_v3.activation import compute_weekly_activation, forward_fill_activation
from hermes_v3.engine import BacktestEngine, aggregate_trades
from hermes_v3.reporter import Reporter


def main():
    parser = argparse.ArgumentParser(description="Hermes V3 Backtesting Engine")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--pilot", type=int, default=None, help="Run on N stocks")
    parser.add_argument("--full", action="store_true", help="Run on full universe")
    parser.add_argument("--symbol", type=str, default=None, help="Run single symbol")
    parser.add_argument("--timeframes", type=str, default="1d,1h,15m", help="Comma-separated timeframes")
    parser.add_argument("--source", type=str, default="local", choices=["local", "yahoo", "dhan"])
    parser.add_argument("--darvas-lengths", type=str, default="5,10,15,20", help="Comma-separated darvas lengths")
    parser.add_argument("--compare-weekly-v3", action="store_true")
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    # Load config
    config_path = args.config or str(Path(__file__).parent / "config.yaml")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    if args.output_dir:
        cfg["output"]["dir"] = args.output_dir

    # Setup output
    reporter = Reporter(cfg["output"]["dir"])

    # Discover symbols
    vault_path = cfg["data"]["vault_path"]
    timeframes_to_check = args.timeframes.split(",") + ["1wk"]
    registry = discover_symbols(vault_path, required_timeframes=list(set(timeframes_to_check)))

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

    print(f"Hermes V3 — Staircase SMA Trend Filter (33/33/34)")
    print(f"Symbols: {len(symbols)}")
    print(f"Timeframes: {args.timeframes}")
    print(f"Darvas lengths: {args.darvas_lengths}")
    print(f"Output: {cfg['output']['dir']}")

    timeframes = args.timeframes.split(",")
    darvas_lengths = [int(x) for x in args.darvas_lengths.split(",")]
    darvas_variants = cfg["darvas"]["variants"]

    engine = BacktestEngine(cfg)
    all_trades = []
    all_signals = []
    all_skips = []

    for symbol in symbols:
        print(f"\n--- {symbol} ---")

        # 1. Load weekly data
        df_w = load_data(symbol, "1wk", cfg, allow_yahoo=(args.source != "local"))
        if df_w is None or len(df_w) < 50:
            print(f"  Weekly: insufficient data, skipping")
            all_skips.append({"dt": "", "symbol": symbol, "timeframe": "1wk", "reason": "insufficient_data"})
            continue

        # 2. Compute weekly indicators once
        df_w_enriched = compute_all_indicators(df_w, cfg, prefix="w_")
        print(f"  Weekly: {len(df_w_enriched)} bars | signals: {df_w_enriched['w_entry_signal'].sum()}")

        # 3. Pre-compute weekly activation for each darvas variant/length combo
        weekly_cache = {}
        for darvas_len in darvas_lengths:
            # Compute weekly Darvas
            df_w_darvas = compute_darvas(df_w_enriched, darvas_len, prefix="w_darvas_")
            for variant in darvas_variants:
                key = (variant, darvas_len)
                df_w_act = compute_weekly_activation(df_w_darvas, cfg, darvas_variant=variant, darvas_len=darvas_len)
                weekly_cache[key] = df_w_act

        # 4. For each lower timeframe
        for tf in timeframes:
            df_tf = load_data(symbol, tf, cfg, allow_yahoo=(args.source != "local"))
            if df_tf is None or len(df_tf) < 50:
                print(f"  {tf}: insufficient data, skipping")
                all_skips.append({"dt": "", "symbol": symbol, "timeframe": tf, "reason": "insufficient_data"})
                continue

            # Compute LTF indicators once
            df_tf_enriched = compute_all_indicators(df_tf, cfg, prefix="")
            print(f"  {tf}: {len(df_tf_enriched)} bars | signals: {df_tf_enriched['entry_signal'].sum()}")

            for darvas_len in darvas_lengths:
                # Compute LTF Darvas
                df_tf_darvas = compute_darvas(df_tf_enriched, darvas_len, prefix="darvas_")

                for variant in darvas_variants:
                    week_key = (variant, darvas_len)
                    if week_key not in weekly_cache:
                        continue

                    df_w_act = weekly_cache[week_key]
                    weekly_active = forward_fill_activation(df_w_act, df_tf_darvas)
                    active_bars = weekly_active.sum()

                    if active_bars == 0:
                        print(f"  {tf} {variant} d{str(darvas_len)}: 0 active bars")
                        continue

                    trades, sigs, skips = engine.run(
                        df_tf_darvas, symbol, tf, variant, darvas_len,
                        weekly_active, weekly_df_for_state=df_w_act
                    )

                    variant_label = f"{variant}_{darvas_len}"
                    if trades:
                        all_trades.extend(trades)
                        stats = aggregate_trades(trades)
                        print(f"  {tf} {variant_label}: {active_bars}act {stats['total_trades']}t "
                              f"{stats['win_rate']:.1f}%WR {stats['avg_r']:.4f}R "
                              f"totR={stats['total_r']:.2f}")
                    else:
                        print(f"  {tf} {variant_label}: {active_bars}act 0t")
                    if sigs:
                        all_signals.extend(sigs)
                    if skips:
                        all_skips.extend(skips)

    # Comparison with weekly-only V3
    compare_stats = None
    if args.compare_weekly_v3:
        compare_stats = _load_weekly_v3_stats(cfg)

    # Save outputs
    report_path = reporter.save_all(all_trades, all_signals, all_skips, cfg, compare_stats)

    print(f"\n{'='*60}")
    print(f"DONE — {len(all_trades)} trades across {len(symbols)} symbols")
    print(f"Report: {report_path}")
    print(f"{'='*60}")


def _load_weekly_v3_stats(cfg):
    """Attempt to load existing weekly V3 results for comparison."""
    v3_path = Path("analysis/staircase_dhan/staircase_strategy_weekly_backtest_v3_full_universe.json")
    if not v3_path.exists():
        return None
    import json
    with open(v3_path) as f:
        data = json.load(f)
    # Extract high-level stats from existing V3 output
    return {
        "source": "staircase_weekly_backtest_v3_full_universe.json",
        **data.get("summary", {})
    }


if __name__ == "__main__":
    main()

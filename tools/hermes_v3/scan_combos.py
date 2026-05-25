#!/usr/bin/env python3
"""Hermes V3 Combo Sweep — filter combo testing on weekly V3 winning stocks.

Tests 12 logical filter combos on 15m, 1h, 1d timeframes.
Widens weekly activation window for intraday to generate enough trades.

USAGE:
  python tools/hermes_v3/scan_combos.py --pilot 20
  python tools/hermes_v3/scan_combos.py --full
  python tools/hermes_v3/scan_combos.py --symbol DIACABS
"""
import sys
import os
import json
import yaml
import warnings
import argparse
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hermes_v3.data import discover_symbols, get_symbol_list, load_data
from hermes_v3.indicators import compute_all_indicators
from hermes_v3.darvas import compute_darvas
from hermes_v3.filters import compute_all_filters
from hermes_v3.activation import compute_weekly_activation, forward_fill_activation
from hermes_v3.combos import get_combo_names, apply_combo, get_combo_label, COMBO_DEFINITIONS
from hermes_v3.engine import BacktestEngine, aggregate_trades
from hermes_v3.reporter import Reporter

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
V3_JSON = ROOT / "analysis" / "staircase_dhan" / "staircase_strategy_weekly_backtest_v3_full_universe.json"
OUTPUT_DIR = ROOT / "research_outputs" / "hermes_v3" / "combo_sweep"

# ── Darvas lengths per combo ─────────────────────────────────────────────────
COMBO_DARVAS_LEN = {
    "+DARVAS10_VOL20": 10,
}
DEFAULT_DARVAS_LEN = 20  # All other darvas combos use 20


def get_darvas_len_for_combo(combo_name):
    return COMBO_DARVAS_LEN.get(combo_name, DEFAULT_DARVAS_LEN)


def needs_darvas(combo_name):
    filters = COMBO_DEFINITIONS[combo_name]["filters"]
    return "darvas_breakout" in filters


def load_winning_stocks(max_stocks=None, symbol_filter=None):
    """Load weekly V3 results, return list of winning stock symbols (total_r > 0)."""
    if not V3_JSON.exists():
        print(f"ERROR: V3 results not found at {V3_JSON}")
        return []

    with open(V3_JSON) as f:
        data = json.load(f)

    stocks = data["stock_summary"]
    winners = [s for s in stocks if s["total_r"] > 0]
    winners.sort(key=lambda x: x["total_r"], reverse=True)

    if symbol_filter:
        winners = [s for s in winners if s["symbol"] == symbol_filter]
        if not winners:
            print(f"Symbol {symbol_filter} not found in winning stocks")
            return []

    if max_stocks:
        winners = winners[:max_stocks]

    print(f"Loaded {len(stocks)} total stocks, {len(winners)} winners (R>0)")
    top = winners[:5]
    for s in top:
        print(f"  {s['symbol']:25s} R={s['total_r']:8.1f} T={s['total_trades']:3d} WR={s['win_rate_pct']:.0f}%")
    return [s["symbol"] for s in winners]


def main():
    parser = argparse.ArgumentParser(description="Hermes V3 Combo Sweep")
    parser.add_argument("--pilot", type=int, default=None, help="Run on N winning stocks")
    parser.add_argument("--full", action="store_true", help="Run on ALL winning stocks")
    parser.add_argument("--symbol", type=str, default=None, help="Run single symbol")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    args = parser.parse_args()

    # Load config
    config_path = args.config or str(Path(__file__).parent / "config.yaml")
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    # Widen activation window for intraday (was 4, now 20)
    cfg["weekly_activation"]["activation_lookahead_bars"] = 20

    # Setup output
    reporter = Reporter(str(OUTPUT_DIR))

    # Get winning stocks
    max_stocks = None
    if args.symbol:
        max_stocks = None
    elif args.pilot:
        max_stocks = args.pilot
    elif not args.full:
        max_stocks = 20  # Default pilot

    winning_symbols = load_winning_stocks(max_stocks=max_stocks, symbol_filter=args.symbol)
    if not winning_symbols:
        return

    # Timeframes to test
    timeframes = cfg.get("lower_timeframes", ["1d", "1h", "15m"])
    combos = get_combo_names()

    print(f"\nHermes V3 Combo Sweep")
    print(f"Stocks: {len(winning_symbols)} winners")
    print(f"Timeframes: {timeframes}")
    print(f"Combos: {len(combos)}")
    print(f"Activation lookahead: {cfg['weekly_activation']['activation_lookahead_bars']} bars")
    print(f"Output: {OUTPUT_DIR}")

    engine = BacktestEngine(cfg)
    all_trades = []
    all_signals = []
    all_skips = []

    for symbol in winning_symbols:
        print(f"\n{'='*60}")
        print(f"  {symbol}")
        print(f"{'='*60}")

        # 1. Load weekly data
        df_w = load_data(symbol, "1wk", cfg, allow_yahoo=True)
        if df_w is None or len(df_w) < 50:
            print(f"  Weekly: insufficient data, skipping")
            continue

        # 2. Compute weekly indicators once
        df_w_enriched = compute_all_indicators(df_w, cfg, prefix="w_")
        w_sigs = df_w_enriched["w_entry_signal"].sum()
        if w_sigs == 0:
            print(f"  Weekly: {len(df_w_enriched)} bars, 0 signals — skipping")
            continue
        print(f"  Weekly: {len(df_w_enriched)} bars, {w_sigs} signals")

        # 3. Pre-compute weekly activation per darvas length
        weekly_cache = {}
        darvas_lengths = set()
        for combo in combos:
            if needs_darvas(combo):
                darvas_lengths.add(get_darvas_len_for_combo(combo))

        for dlen in darvas_lengths:
            df_w_darvas = compute_darvas(df_w_enriched, dlen, prefix="w_darvas_")
            df_w_act = compute_weekly_activation(df_w_darvas, cfg, darvas_variant="no_darvas")
            weekly_cache[dlen] = df_w_act
            active_bars = df_w_act["w_activation_zone"].sum()
            print(f"  Weekly Darvas({dlen}): {active_bars} active bars")

        # 4. For each lower timeframe
        for tf in timeframes:
            df_tf = load_data(symbol, tf, cfg, allow_yahoo=(tf in ("1d",)))
            if df_tf is None or len(df_tf) < 50:
                print(f"  {tf}: insufficient data, skipping")
                continue

            # Compute base indicators + all filters once
            df_tf_enriched = compute_all_indicators(df_tf, cfg, prefix="")
            df_tf_enriched = compute_all_filters(df_tf_enriched)
            base_sigs = df_tf_enriched["entry_signal"].sum()
            print(f"  {tf}: {len(df_tf_enriched)} bars, {base_sigs} base signals")

            if base_sigs == 0:
                print(f"    No base signals, skipping all combos")
                continue

            tf_trades = 0

            for combo in combos:
                # Determine darvas length for this combo
                dlen = get_darvas_len_for_combo(combo) if needs_darvas(combo) else None

                # Compute darvas_breakout on LTF if needed
                df_combo = df_tf_enriched.copy()
                if dlen:
                    df_combo = compute_darvas(df_combo, dlen, prefix="darvas_")
                    if "darvas_breakout" in df_combo.columns:
                        df_combo["darvas_breakout"] = df_combo["darvas_breakout"]

                # Apply combo filters
                try:
                    combo_pass = apply_combo(df_combo, combo)
                except KeyError as e:
                    print(f"    {combo}: SKIP — {e}")
                    continue

                # Combined: base signal + combo filters
                combined = df_combo["entry_signal"] & combo_pass
                combined_count = combined.sum()
                if combined_count == 0:
                    continue  # No entries possible, skip engine run

                # Get weekly activation for this darvas length
                wk_key = dlen if dlen else 20  # Default to 20 for weekly activation
                if wk_key not in weekly_cache:
                    continue

                df_w_act = weekly_cache[wk_key]
                weekly_active = forward_fill_activation(df_w_act, df_combo)
                active_bars = weekly_active.sum()
                if active_bars == 0:
                    continue

                # Run engine
                trades, sigs, skips = engine.run(
                    df_combo, symbol, tf,
                    darvas_variant="no_darvas", darvas_len=dlen,
                    weekly_active_series=weekly_active,
                    weekly_df_for_state=df_w_act,
                    combo_name=combo, combo_pass=combo_pass,
                )

                if trades:
                    all_trades.extend(trades)
                    stats = aggregate_trades(trades)
                    tf_trades += len(trades)
                    print(f"    {combo:30s}: {stats['total_trades']:3d}t "
                          f"WR={stats['win_rate']:.0f}% avgR={stats['avg_r']:.3f} "
                          f"totR={stats['total_r']:.2f}")
                else:
                    print(f"    {combo:30s}: 0 trades ({combined_count} signals, {active_bars} active)")

                if sigs:
                    all_signals.extend(sigs)
                if skips:
                    all_skips.extend(skips)

            print(f"  {tf}: {tf_trades} total trades across all combos")

    # Save and report
    report_path = reporter.save_all(all_trades, all_signals, all_skips, cfg)

    print(f"\n{'='*60}")
    print(f"DONE — {len(all_trades)} trades across {len(winning_symbols)} stocks")
    print(f"Report: {report_path}")
    print(f"CSVs: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

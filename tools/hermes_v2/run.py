"""Hermes V2.1 — V3 Staircase Principles Extension Orchestrator."""
import sys
from pathlib import Path
from engine import HermesV21Engine

HERMES_DIR = Path(r"C:\Users\yugan\hermes-trading")
sys.path.insert(0, str(HERMES_DIR / "hermes_v2"))
sys.path.insert(0, str(HERMES_DIR / "hermes_v1"))

VAULT = Path(r"C:\Users\yugan\OneDrive\Desktop\CLAUDE\data\nifty_universe")

if __name__ == "__main__":
    print("HERMES V2.1 — V3 Staircase Principles + 8 Improvement Filters")
    print("=" * 60)

    config_path = Path(__file__).parent / "config.yaml"
    engine = HermesV21Engine(str(config_path))

    stocks = sorted([d.name for d in VAULT.iterdir() if d.is_dir() and not d.name.startswith("_")])
    total = len(stocks)
    max_s = engine.cfg["pilot"]["max_stocks"]
    limit = min(total, max_s)
    print(f"Stocks: {total} total, {limit} processing")

    all_results = []
    for i, symbol in enumerate(stocks[:limit]):
        try:
            res = engine.process_stock(symbol)
            if res:
                all_results.append(res)
            if (i + 1) % 10 == 0:
                print(f"\n--- Progress: {i+1}/{limit} ---")
        except Exception as e:
            print(f"  [ERROR] {symbol}: {e}")

    engine.build_report(all_results)
    print("\nDONE")

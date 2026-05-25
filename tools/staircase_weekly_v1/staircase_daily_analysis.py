#!/usr/bin/env python3
"""Quant-style analysis of staircase daily scan results."""
import pandas as pd
import sys
from pathlib import Path

csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("analysis/staircase_daily_dual/staircase_daily_dual_20260524_0302.csv")
df = pd.read_csv(csv_path)

today = "2026-05-23"

# Per-symbol aggregation
per_sym = df.groupby("symbol").agg(
    entries=("level", "count"),
    L1=("level", lambda x: (x == "L1").sum()),
    L2=("level", lambda x: (x == "L2").sum()),
    L3=("level", lambda x: (x == "L3").sum()),
    first=("entry_date", "min"),
    last=("entry_date", "max"),
    avg_cls=("close", "mean"),
).reset_index()

per_sym["pyramid"] = per_sym.apply(lambda r: "L3" if r["L3"] > 0 else "L2" if r["L2"] > 0 else "L1-only", axis=1)
per_sym["recent"] = per_sym["last"] >= "2026-05-15"
per_sym["live"]   = per_sym["last"] >= "2026-05-18"

n_stocks = per_sym["symbol"].nunique()
n_total  = len(df)
n_l3     = len(per_sym[per_sym["L3"] > 0])
n_l2     = len(per_sym[per_sym["L2"] > 0])
n_l1     = len(per_sym)

print(f"=== STAIRCASE DAILY SCAN — {today} ===")
print(f"Universe: 1203 NSE stocks | Lookback: 8 weeks | Source: Yahoo Finance")
print(f"")
print(f"TOTAL STOCKS w/ entries:  {n_stocks}")
print(f"TOTAL ENTRIES fired:      {n_total}")
print(f"")
print(f"L3 reached (full pyramid): {n_l3:3d}  ({n_l3/n_stocks*100:.1f}%)")
print(f"L2 only (partial):         {n_l2-n_l3:3d}  ({(n_l2-n_l3)/n_stocks*100:.1f}%)")
print(f"L1 only (unbuilt):         {n_l1-n_l2:3d}  ({(n_l1-n_l2)/n_stocks*100:.1f}%)")
print(f"")
print(f"Active/recent (last >= May 15): {per_sym['recent'].sum()}")
print(f"Still live   (last >= May 18):   {per_sym['live'].sum()}")

# Entry stats by level
print(f"\n--- ENTRY STATS BY LEVEL ---")
for lvl in ["L1", "L2", "L3"]:
    sub = df[df["level"] == lvl]
    risk = sub["close"] - sub["sl"]
    print(f"  {lvl}: {len(sub):3d} entries | close={sub['close'].mean():.0f} | SL={sub['sl'].mean():.0f} | risk={risk.mean():.0f} ({(risk/sub['close']*100).mean():.1f}%)")

# Top stocks
print(f"\n--- TOP 20 BY ENTRY COUNT ---")
top = per_sym.sort_values("entries", ascending=False).head(20)
for _, r in top.iterrows():
    print(f"  {r['symbol']:15s} {int(r['entries']):2d} entries  L1={int(r['L1'])} L2={int(r['L2'])} L3={int(r['L3'])}  {r['first']} -> {r['last']}")

# Live L3 stocks
print(f"\n--- LIVE L3 STOCKS (entry in last 5 days) ---")
live_l3 = per_sym[(per_sym["live"]) & (per_sym["L3"] > 0)].sort_values("last", ascending=False)
for _, r in live_l3.iterrows():
    print(f"  {r['symbol']:15s} L3 on {r['last']}  avg close={r['avg_cls']:.0f}  {int(r['entries'])} entries")

# All L3 stocks
print(f"\n--- ALL L3 STOCKS ({n_l3}) ---")
l3_all = per_sym[per_sym["L3"] > 0].sort_values("last", ascending=False)
for _, r in l3_all.iterrows():
    tag = "LIVE" if r["live"] else "    "
    print(f"  {tag}  {r['symbol']:15s} L3 {r['last']}  {int(r['entries'])} entries  cls={r['avg_cls']:.0f}")

# Recent L2 only (no L3)
print(f"\n--- RECENT L2 ONLY (no L3 yet, last >= May 15) ---")
l2_recent = per_sym[(per_sym["recent"]) & (per_sym["L2"] > 0) & (per_sym["L3"] == 0)].sort_values("last", ascending=False)
for _, r in l2_recent.iterrows():
    tag = "LIVE" if r["live"] else "    "
    print(f"  {tag}  {r['symbol']:15s} L2 {r['last']}  cls={r['avg_cls']:.0f}")

# Recent L1 only
print(f"\n--- RECENT L1 ONLY (last >= May 15) ---")
l1_recent = per_sym[(per_sym["recent"]) & (per_sym["L2"] == 0)].sort_values("last", ascending=False)
for _, r in l1_recent.iterrows():
    print(f"       {r['symbol']:15s} L1 {r['last']}  cls={r['avg_cls']:.0f}  SL nearby={r['avg_cls']*0.92:.0f}")

# Entry chain example
print(f"\n--- ENTRY CHAIN EXAMPLES ---")
for sym in ["POLYCAB", "CUMMINSIND", "GRWRHITECH", "LAURUSLABS", "ADANIPORTS"]:
    chain = df[df["symbol"] == sym].sort_values("entry_date")
    if len(chain) > 0:
        items = " -> ".join([f"{r['level']}@{r['close']:.0f}({r['entry_date']})" for _, r in chain.iterrows()])
        print(f"  {sym}: {items}")

#!/usr/bin/env python3
"""Rating script for Staircase 33/33/34 backtest."""
import pandas as pd
import numpy as np

path = "analysis/staircase_dhan/staircase_strategy_weekly_backtest_33_33_34.xlsx"
trades = pd.read_excel(path, sheet_name="Trade_Summary")
trades = trades.dropna(subset=["final_return_pct", "r_multiple"])

total = len(trades)
wins = trades[trades["final_return_pct"] > 0]
losses = trades[trades["final_return_pct"] < 0]
wr = len(wins) / total * 100

med_win_r = wins["r_multiple"].median()
med_loss_r = abs(losses["r_multiple"].median())

pf = wins["r_multiple"].sum() / abs(losses["r_multiple"].sum())

capped = trades["r_multiple"].clip(-10, 10)
avg_r = capped.mean()
r_std = capped.std()

# Account sim: 2% risk, R capped [-1.5, 5]
acct = 100000.0
peak = acct
max_dd = 0.0
dd_dur = 0
max_dd_dur = 0
for _, t in trades.iterrows():
    r = max(min(t["r_multiple"], 5.0), -1.5)
    pct = r * 0.02 * 100
    acct *= (1 + pct / 100)
    if acct > peak:
        peak = acct
        dd_dur = 0
    else:
        dd_dur += 1
        max_dd_dur = max(max_dd_dur, dd_dur)
    dd = (peak - acct) / peak * 100
    max_dd = max(max_dd, dd)

total_ret = (acct - 100000) / 100000 * 100
car = ((acct / 100000) ** (1 / total) - 1) * 100
calmar = total_ret / max_dd if max_dd > 0 else float("inf")

down = capped[capped < 0]
sortino = avg_r / down.std() if len(down) > 0 else float("inf")
sharpe = avg_r / r_std if r_std > 0 else 0

entry_d = pd.to_datetime(trades["entry_date"])
exit_d = pd.to_datetime(trades["exit_date"])
hp = (exit_d - entry_d).dt.days
exits = trades["exit_reason"].value_counts()

levels = {}
for lvl in ["L1", "L2", "L3"]:
    l = trades[trades["level"] == lvl]
    if len(l) > 0:
        levels[lvl] = {
            "count": len(l),
            "wr": (l["r_multiple"] > 0).sum() / len(l) * 100,
            "avg_r": l["r_multiple"].mean(),
            "total_r": l["r_multiple"].sum(),
        }

partials = trades["partial_date"].notna().sum()

# Score
pf_score = min(25, pf * 12.5)
wr_score = min(20, wr * 0.333)
ar_score = min(20, max(0, avg_r) * 10)
sh_score = min(15, sortino * 7.5) if sortino != float("inf") else 15
dd_score = max(0, min(10, (40 - max_dd) * 0.25))
cal_score = min(10, calmar * 5) if calmar != float("inf") else 10
cons_score = min(10, wr / 10)
scale_score = min(5, capped.sum() / 30)
total_score = round(pf_score + wr_score + ar_score + sh_score + dd_score + cal_score + cons_score + scale_score, 1)

labels = [
    (80, "A+ (Excellent)"), (70, "A (Very Good)"), (60, "B+ (Good)"),
    (50, "B (Decent)"), (40, "C (Average)"), (30, "D (Below Average)")
]
rating = next((l for s, l in labels if total_score >= s), "F (Poor)")

print("=" * 70)
print("  STAIRCASE STRATEGY 33/33/34 -- PERFORMANCE RATING")
print("=" * 70)
print(f"\nOverall Score: {total_score}/100  [{rating}]")

print("\n--- TRADE STATISTICS ---")
print(f"Total Trades:        {total}")
print(f"Winners:             {len(wins)} ({wr:.1f}%)")
print(f"Losers:              {len(losses)}")
print(f"Median Win R:        +{med_win_r:.1f}R")
print(f"Median Loss R:       -{med_loss_r:.1f}R")

print("\n--- RISK & REWARD ---")
print(f"Profit Factor:       {pf:.2f}")
print(f"Avg R (capped +-10): {avg_r:.2f}R")
print(f"R Std Dev (capped):  {r_std:.2f}")
print(f"Sortino:             {sortino:.2f}")
print(f"Sharpe (R-based):    {sharpe:.2f}")
print(f"Total R (capped):    +{capped.sum():.1f}R")

print("\n--- ACCOUNT SIMULATION (2% risk/trade) ---")
print(f"Total Return:        +{total_ret:.1f}%")
print(f"Compounded/Trade:    {car:.2f}%")
print(f"Max Drawdown:        {max_dd:.1f}%")
print(f"Max DD Duration:     {max_dd_dur} trades")
print(f"Calmar:              {calmar:.2f}")

print("\n--- TIMING ---")
print(f"Avg Holding:         {hp.mean():.0f} days ({hp.mean()/7:.1f} weeks)")
print(f"Median Holding:      {hp.median():.0f} days ({hp.median()/7:.1f} weeks)")
print(f"Max Holding:         {hp.max():.0f} days ({hp.max()/7:.1f} weeks)")
print(f"Partial Exits:       {partials}")

print("\n--- EXIT REASONS ---")
for reason, count in exits.items():
    print(f"  {reason}: {count}")

print("\n--- PER-LEVEL ANALYSIS (raw R) ---")
for lvl, s in levels.items():
    print(f"  {lvl}: {s['count']} trades | {s['wr']:.1f}% WR | {s['avg_r']:.1f}R avg | {s['total_r']:.1f}R total")

print("\n--- SCORE BREAKDOWN ---")
print(f"  Profit Factor:   {pf_score:.0f}/25  (PF={pf:.2f})")
print(f"  Win Rate:        {wr_score:.0f}/20  ({wr:.1f}%)")
print(f"  Expectancy:      {ar_score:.0f}/20  ({avg_r:.2f}R)")
print(f"  Sortino:         {sh_score:.0f}/15  ({sortino:.2f})")
print(f"  Max DD Control:  {dd_score:.0f}/10  ({max_dd:.1f}%)")
print(f"  Calmar:          {cal_score:.0f}/10  ({calmar:.2f})")
print(f"  Consistency:     {cons_score:.0f}/10  ({wr:.1f}% WR)")
print(f"  Scale:           {scale_score:.0f}/5  ({capped.sum():.1f}R total)")

print("\n" + "=" * 70)
print(f"  FINAL RATING: {total_score}/100 -- {rating}")
print("=" * 70)

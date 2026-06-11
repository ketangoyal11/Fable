"""Analyze APOLLO for Minervini entry points post-COVID"""
import csv
from datetime import datetime

# Load raw data from yfinance source
raw = []
with open("data/yfinance_universe/history/APOLLO.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        try:
            d = datetime.strptime(r["Date"][:10], "%Y-%m-%d")
        except:
            continue
        if d.year >= 2020:
            raw.append({
                "date": r["Date"][:10],
                "open": float(r["Open"]) if r["Open"] else 0,
                "high": float(r["High"]) if r["High"] else 0,
                "low": float(r["Low"]) if r["Low"] else 0,
                "close": float(r["Close"]) if r["Close"] else 0,
                "volume": int(float(r["Volume"])) if r["Volume"] and float(r["Volume"]) > 0 else 0,
            })

# Compute SMAs
closes = [r["close"] for r in raw]
vols = [r["volume"] for r in raw]

def sma(data, period):
    return [sum(data[i-period:i])/period if i >= period else None for i in range(len(data))]

sma50 = sma(closes, 50)
sma150 = sma(closes, 150)
sma200 = sma(closes, 200)
vsma50 = sma(vols, 50)

# Add to data
for i, r in enumerate(raw):
    r["sma50"] = sma50[i]
    r["sma150"] = sma150[i]
    r["sma200"] = sma200[i]
    r["vsma50"] = vsma50[i]

# ============================================================
print("=" * 80)
print("APOLLO (NSE) — MINERVINI-STYLE POST-COVID ANALYSIS")
print("=" * 80)
print(f"\nDate Range: {raw[0]['date']} to {raw[-1]['date']}")
print(f"COVID Low: ~Q1 2020")

# Find COVID low
min_covid = min(raw, key=lambda x: x["low"])
print(f"COVID Low Point: {min_covid['date']} @ {min_covid['low']:.2f}")

# Latest data
last = raw[-1]
print(f"Latest: {last['date']} @ C={last['close']:.2f} (H={last['high']:.2f})")
print(f"Total Gain from COVID low: {((last['close']/min_covid['low'])-1)*100:.1f}%")

# ============================================================
# 1. FIND THE FIRST UPTREND (SMA200 crossover + trend template)
print("\n" + "=" * 80)
print("PHASE 0: COVID CRASH & FIRST BASE (Mar-Jun 2020)")
print("=" * 80)
for r in raw:
    if r["date"] >= "2020-03-01" and r["date"] <= "2020-06-30":
        print(f"  {r['date']}: O={r['open']:.2f} H={r['high']:.2f} L={r['low']:.2f} C={r['close']:.2f} V={r['volume']:,}")

# ============================================================
# 2. FIND MAJOR PEAKS (pivots) for entry point identification
print("\n" + "=" * 80)
print("MAJOR WEEKLY PIVOTS / ENTRY POINTS IDENTIFIED")
print("=" * 80)

# Find 50-bar peaks as pivots
pivots = []
for i in range(50, len(raw)-50):
    h = raw[i]["high"]
    prev_max = max(raw[j]["high"] for j in range(i-25, i))
    next_max = max(raw[j]["high"] for j in range(i+1, i+26))
    if h >= prev_max and h >= next_max:
        pivots.append((i, raw[i]))
        print(f"  PIVOT: {raw[i]['date']}: H={h:.2f} C={raw[i]['close']:.2f} V={raw[i]['volume']:,}")

# ============================================================
# 3. PRICE ABOVE SMA200 CROSSOVERS (stage 2 entry signals)
print("\n" + "=" * 80)
print("PRICE ABOVE SMA200 CROSSOVERS (Stage 2 Entry Signal)")
print("=" * 80)
for i in range(201, len(raw)):
    if raw[i]["sma200"] and raw[i-1]["sma200"]:
        c = raw[i]["close"]
        s200 = raw[i]["sma200"]
        pc = raw[i-1]["close"]
        ps200 = raw[i-1]["sma200"]
        if pc <= ps200 and c > s200:
            print(f"  {raw[i]['date']}: C={c:.2f} > SMA200={s200:.2f}  (vol {raw[i]['volume']:,})")

# ============================================================
# 4. VCP / TIGHT CONSOLIDATION PATTERNS
print("\n" + "=" * 80)
print("VCP PATTERNS & TIGHT CONSOLIDATIONS (looking for cramming)")
print("=" * 80)

for i in range(50, len(raw)):
    r = raw[i]
    c = r["close"]
    h = r["high"]
    l = r["low"]
    d_range = (h - l) / l * 100  # daily range %
    
    if r["sma200"] and c > r["sma200"]:
        # Tight day below 2.5% range with volume dry-up
        if d_range < 2.5 and r["volume"] > 0 and r["vsma50"]:
            vr = r["volume"] / r["vsma50"]
            if vr < 0.7:
                sma50_pct = (c / r["sma50"] - 1) * 100 if r["sma50"] else 0
                if abs(sma50_pct) < 5:  # Near SMA50 = consolidation
                    print(f"  {r['date']}: C={c:.2f} Rng={d_range:.1f}% VR={vr:.2f} AboveSMA50={sma50_pct:+.1f}%")

# ============================================================
# 5. BIG VOLUME UP DAYS (accumulation signals)
print("\n" + "=" * 80)
print("BIG VOLUME ACCUMULATION DAYS (VR > 2.0, close up > 2%)")
print("=" * 80)
for i in range(50, len(raw)):
    r = raw[i]
    if r["vsma50"] and r["volume"] > 0:
        vr = r["volume"] / r["vsma50"]
        prev_c = raw[i-1]["close"]
        pct = (r["close"] / prev_c - 1) * 100
        if vr > 1.5 and pct > 2.0 and r["sma200"] and r["close"] > r["sma200"]:
            print(f"  {r['date']}: C={r['close']:.2f} Chg={pct:+.1f}% VR={vr:.2f}x V={r['volume']:,}")

# ============================================================
print("\n" + "=" * 80)
print("DATA SUMMARY: KEY LEVELS FOR ANALYSIS")
print("=" * 80)

# Yearly closes
for yr in ["2020", "2021", "2022", "2023", "2024", "2025", "2026"]:
    yr_closes = [r for r in raw if r["date"].startswith(yr)]
    if yr_closes:
        first = yr_closes[0]
        last_yr = yr_closes[-1]
        yr_high = max(r["high"] for r in yr_closes)
        yr_low = min(r["low"] for r in yr_closes)
        yr_change = ((last_yr["close"] / first["close"]) - 1) * 100
        print(f"  {yr}: Open={first['close']:.2f} Close={last_yr['close']:.2f} H={yr_high:.2f} L={yr_low:.2f} Chg={yr_change:+.1f}%")

print("\nDone.")

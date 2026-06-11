"""Verify 2025-2026 buy points with proper VCP setups"""
import csv

rows = []
with open("data/yfinance_universe/history/APOLLO.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append(r)

closes = [float(r["Close"]) if r["Close"] else 0 for r in rows]
vols = [int(float(r["Volume"])) if r["Volume"] else 0 for r in rows]

def sma(data, period):
    return [sum(data[i-period:i])/period if i >= period else None for i in range(len(data))]

sma50 = sma(closes, 50)
vsma50 = sma(vols, 50)

for i, r in enumerate(rows):
    if r["Date"][:4] not in ["2024", "2025", "2026"]:
        continue
    if r["Date"] < "2024-10-01":
        continue
    if i < 50:
        continue
    
    c = float(r["Close"]) if r["Close"] else 0
    h = float(r["High"]) if r["High"] else 0
    l = float(r["Low"]) if r["Low"] else 0
    o = float(r["Open"]) if r["Open"] else 0
    v = int(float(r["Volume"])) if r["Volume"] else 0
    
    # Volume ratio
    vr = v / vsma50[i] if vsma50[i] and vsma50[i] > 0 else 0
    prev_c = float(rows[i-1]["Close"]) if rows[i-1]["Close"] else 0
    pct = ((c / prev_c) - 1) * 100 if prev_c > 0 else 0
    
    # Check for VCP breakouts: 
    # 1. Big volume day (>1.5x avg)
    # 2. Price up > 2%
    # 3. Price above SMA50 (in Stage 2)
    # 4. Check if there was a tight base before (look back 20-40 days)
    if vr > 1.5 and pct > 2.0 and c > 0 and sma50[i] and c > sma50[i]:
        # Look back 30 days to see if range was contracting
        lookback = 30
        if i >= lookback:
            prices_30 = [float(rows[j]["Close"]) for j in range(i-lookback, i) if rows[j]["Close"]]
            high_30 = max(float(rows[j]["High"]) for j in range(i-lookback, i) if rows[j]["High"])
            low_30 = min(float(rows[j]["Low"]) for j in range(i-lookback, i) if rows[j]["Low"])
            range_30 = ((high_30 - low_30) / low_30) * 100 if low_30 > 0 else 0
            
            # Last 10 days range
            prices_10 = [float(rows[j]["Close"]) for j in range(i-10, i) if rows[j]["Close"]]
            high_10 = max(float(rows[j]["High"]) for j in range(i-10, i) if rows[j]["High"])
            low_10 = min(float(rows[j]["Low"]) for j in range(i-10, i) if rows[j]["Low"])
            range_10 = ((high_10 - low_10) / low_10) * 100 if low_10 > 0 else 0
            
            # Check if last 5 days had declining volume
            vol_last5 = [int(float(rows[j]["Volume"])) for j in range(i-5, i) if rows[j]["Volume"]]
            avg_vol_last5 = sum(vol_last5) / len(vol_last5) if vol_last5 else 0
            
            # Print potential VCP breakouts
            if range_30 < 30 and range_10 < 15:
                print(f"VCP CANDIDATE: {r['Date'][:10]} C={c:.2f} Chg={pct:+.1f}% VR={vr:.1f}x R30={range_30:.1f}% R10={range_10:.1f}% V={v}")

print()
print("=== CHECK JUN 14, 2023 ===")
for r in rows:
    d = r["Date"][:10]
    if d in ["2023-06-13", "2023-06-14", "2023-06-15", "2023-06-16", "2023-06-19"]:
        c = float(r["Close"]) if r["Close"] else 0
        h = float(r["High"]) if r["High"] else 0
        l = float(r["Low"]) if r["Low"] else 0
        o = float(r["Open"]) if r["Open"] else 0
        v = int(float(r["Volume"])) if r["Volume"] else 0
        print(f"{d}: O={o:.2f} H={h:.2f} L={l:.2f} C={c:.2f} V={v}")

print()
print("=== OCT 31, 2023 CHECK ===")
for r in rows:
    d = r["Date"][:10]
    if d in ["2023-10-30", "2023-10-31", "2023-11-01"]:
        c = float(r["Close"]) if r["Close"] else 0
        h = float(r["High"]) if r["High"] else 0
        l = float(r["Low"]) if r["Low"] else 0
        o = float(r["Open"]) if r["Open"] else 0
        v = int(float(r["Volume"])) if r["Volume"] else 0
        print(f"{d}: O={o:.2f} H={h:.2f} L={l:.2f} C={c:.2f} V={v}")

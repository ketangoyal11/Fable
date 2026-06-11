"""Analyze APOLLO pivots and Minervini setup patterns from SMA data"""
import csv

rows = []
with open('analysis/minervini_obsidian/Indian Stocks/APOLLO/APOLLO_ohlcv_sma.csv') as f:
    for r in csv.DictReader(f):
        rows.append(r)

print("=== RANGE ===")
print(f"Start: {rows[0]['Date']} @ C={rows[0]['Close']}")
print(f"End:   {rows[-1]['Date']} @ C={rows[-1]['Close']}")

# COVID low
print("\n=== COVID CRASH LOW ===")
lows = [(i, float(r['Low'])) for i,r in enumerate(rows)]
min_low = min(lows, key=lambda x: x[1])
print(f"Lowest: {rows[min_low[0]]['Date']} @ {min_low[1]:.2f}")

# Major peaks (50-day forward/backward look)
print("\n=== MAJOR PIVOTS (50-bar window) ===")
for i in range(50, len(rows)-50):
    h = float(rows[i]['High'])
    prev_h = max([float(rows[j]['High']) for j in range(i-25, i)])
    next_h = max([float(rows[j]['High']) for j in range(i+1, i+26)])
    if h >= prev_h and h >= next_h:
        c = float(rows[i]['Close'])
        v = rows[i]['Volume']
        print(f"  {rows[i]['Date']}: PEAK H={h:.2f} C={c:.2f} V={v}")

# SMA200 crossovers
print("\n=== PRICE > SMA200 CROSSOVERS ===")
for i in range(201, len(rows)):
    if rows[i]['SMA200'] and rows[i-1]['SMA200']:
        c = float(rows[i]['Close'])
        s200 = float(rows[i]['SMA200'])
        p_c = float(rows[i-1]['Close'])
        p_s200 = float(rows[i-1]['SMA200'])
        if p_c <= p_s200 and c > s200:
            print(f"  {rows[i]['Date']}: C={c:.2f} crossed above SMA200={s200:.2f} V={rows[i]['Volume']}")

# Price above SMA50, SMA150, SMA200 (Trend Template)
print("\n=== TREND TEMPLATE CHECKS (selected dates) ===")
checkpoints = [
    "2020-06-01", "2020-07-01", "2020-08-01", "2020-09-01",
    "2020-10-01", "2020-11-02", "2020-12-01",
    "2021-01-01", "2021-02-01", "2021-03-01",
    "2021-04-01", "2021-05-03", "2021-06-01", "2021-07-01",
]
for r in rows:
    if r['Date'] in checkpoints and r['SMA50'] and r['SMA150'] and r['SMA200']:
        c = float(r['Close'])
        s50 = float(r['SMA50'])
        s150 = float(r['SMA150'])
        s200 = float(r['SMA200'])
        a50 = c > s50
        a150 = c > s150
        a200 = c > s200
        print(f"  {r['Date']}: C={c:.2f} | SMA50={s50:.2f}({a50}) SMA150={s150:.2f}({a150}) SMA200={s200:.2f}({a200})")

# Find tight weekly closes (VCP patterns)
print("\n=== TIGHT WEEKS / VCP CANDIDATES (looking for contraction) ===")
for i in range(20, len(rows)):
    r = rows[i]
    c = float(r['Close'])
    h = float(r['High'])
    l = float(r['Low'])
    rangep = (h - l) / l * 100  # daily range as %
    
    # Look for price above SMA200 + tight daily range (<3%)
    if r['SMA200'] and c > float(r['SMA200']) and rangep < 3.0:
        # Check volume dry-up
        if r['VolSMA50']:
            vr = float(r['Volume']) / float(r['VolSMA50'])
            if vr < 0.7:
                print(f"  {r['Date']}: C={c:.2f} Range={rangep:.1f}% VR={vr:.2f} V={r['Volume']}")

print("\nDone.")

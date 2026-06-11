"""

Generate Synthetic OHLCV Test Data for Failure Pattern Analysis
Simulates the three Minervini book failure patterns:
1. WAGE (Mar-Apr 2014) - 3 lower lows, increasing volume, below 20-day
2. OUTR (2014) - Low vol out, high vol in reversal
3. LL (Nov-Dec 2013) - Late-stage base, low vol breakout, breaks 20-day & 50-day

Output: Creates CSV files in the data/ directory for scanner testing.
"""

import csv
import os
import math

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def sma(series, n):
    """Simple moving average"""
    if len(series) < n:
        return None
    return sum(series[-n:]) / n

def write_csv(ticker, dates, closes, highs, lows, opens, volumes):
    """Write OHLCV CSV in the format expected by _minervini_sepa.py"""
    fp = os.path.join(OUT_DIR, f"{ticker}_ohlcv.csv")
    
    # Calculate SMAs for columns 7-14
    sma20s = []
    sma50s = []
    sma150s = []
    sma200s = []
    vol_sma50s = []
    high252s = []
    low252s = []
    atr20pcts = []
    
    for i in range(len(closes)):
        # SMA20
        s20 = sma(closes[:i+1], 20) if i >= 19 else ""
        sma20s.append(s20 if s20 is not None else "")
        # SMA50
        s50 = sma(closes[:i+1], 50) if i >= 49 else ""
        sma50s.append(s50 if s50 is not None else "")
        # SMA150
        s150 = sma(closes[:i+1], 150) if i >= 149 else ""
        sma150s.append(s150 if s150 is not None else "")
        # SMA200
        s200 = sma(closes[:i+1], 200) if i >= 199 else ""
        sma200s.append(s200 if s200 is not None else "")
        # Volume SMA50
        vs50 = sma(volumes[:i+1], 50) if i >= 49 else ""
        vol_sma50s.append(vs50 if vs50 is not None else "")
        # High252
        h252 = max(highs[max(0,i-251):i+1]) if i >= 0 else ""
        high252s.append(h252)
        # Low252
        l252 = min(lows[max(0,i-251):i+1]) if i >= 0 else ""
        low252s.append(l252)
        # ATR20Pct
        if i >= 19:
            atrs = []
            for j in range(i-19, i+1):
                tr = max(highs[j] - lows[j], abs(highs[j] - (closes[j-1] if j > 0 else closes[j])), abs(lows[j] - (closes[j-1] if j > 0 else closes[j])))
                atrs.append(tr)
            atr20 = sum(atrs) / len(atrs)
            atr20pcts.append(atr20 / closes[i] * 100 if closes[i] else "")
        else:
            atr20pcts.append("")

    header = ["Date", "Adj Close", "Close", "High", "Low", "Open", "Volume",
              "SMA20", "SMA50", "SMA150", "SMA200", "High252", "Low252",
              "VolSMA50", "ATR20Pct", "RS", "RS_SMA20"]

    with open(fp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for i in range(len(dates)):
            w.writerow([
                dates[i],
                closes[i], closes[i], highs[i], lows[i], opens[i], volumes[i],
                sma20s[i], sma50s[i], sma150s[i], sma200s[i], high252s[i], low252s[i],
                vol_sma50s[i], atr20pcts[i], "", ""
            ])
    print(f"Created: {fp} ({len(dates)} bars)")

# ============================================================
# PATTERN 1: WAGE (Mar-Apr 2014)
# "Low-volume breakout → fails → 3 lower lows on increasing volume → below 20-day"
# ============================================================
def generate_wage():
    """Simulate WAGE failure pattern"""
    ticker = "WAGE"
    dates = []
    c, h, l, o, v = [], [], [], [], []
    
    # Phase 1: Uptrend (120 bars) - Stage 2, price rising from ~30 to ~45
    base_price = 30.0
    for i in range(120):
        d = f"2013-{9 + (i // 30):02d}-{(i % 30) + 1:02d}"
        dates.append(d)
        trend = base_price + (i / 120) * 15  # 30 → 45
        noise = (i % 5) * 0.3 - 0.6
        cp = trend + noise
        hp = cp + 0.5 + abs(noise) * 0.8
        lp = cp - 0.5 - abs(noise) * 0.6
        op = cp - 0.2 + (i % 3) * 0.2
        vl = 200000 + (i % 10) * 50000
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Phase 2: Base forming (30 bars) - tight range 43-46
    for i in range(30):
        d = f"2014-{1 + (i // 31):02d}-{(i % 31) + 1:02d}"
        dates.append(d)
        cp = 44 + math.sin(i * 0.3) * 1.5
        hp = cp + 0.4 + abs(math.sin(i * 0.5)) * 0.6
        lp = cp - 0.4 - abs(math.sin(i * 0.4)) * 0.5
        op = cp - 0.1 + (i % 5) * 0.05
        vl = 150000 + (i % 20) * 10000  # Volume declines (dry-up)
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Phase 3: LOW VOLUME BREAKOUT attempt (bar 150-151)
    # Breakout day - price up 3.2% but volume only 1.15x SMA50 (low conviction)
    base_v50 = sma(v, 50) or 200000
    d = "2014-03-03"; dates.append(d)
    cp = 46.2; hp = 46.8; lp = 44.8; op = 44.9; vl = int(base_v50 * 1.15)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 2 - small follow-through attempt, stalls (high wick)
    d = "2014-03-04"; dates.append(d)
    cp = 46.5; hp = 47.2; lp = 45.8; op = 46.3; vl = int(base_v50 * 1.0)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 3 - FAILS, closes lower on INCREASED volume
    d = "2014-03-05"; dates.append(d)
    cp = 45.6; hp = 46.6; lp = 45.3; op = 46.5; vl = int(base_v50 * 1.4)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 4 - LOWER LOW #1, volume up again
    d = "2014-03-06"; dates.append(d)
    cp = 44.8; hp = 45.8; lp = 44.5; op = 45.6; vl = int(base_v50 * 1.6)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 5 - LOWER LOW #2, volume even higher
    d = "2014-03-07"; dates.append(d)
    cp = 44.0; hp = 45.2; lp = 43.7; op = 44.8; vl = int(base_v50 * 1.9)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 6 - LOWER LOW #3, volume SURGES - SELL SIGNAL
    d = "2014-03-10"; dates.append(d)
    cp = 42.8; hp = 44.5; lp = 42.5; op = 44.0; vl = int(base_v50 * 2.5)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 7 - close below 20-day MA on high volume (now confirmed)
    d = "2014-03-11"; dates.append(d)
    cp = 42.0; hp = 43.2; lp = 41.8; op = 42.8; vl = int(base_v50 * 2.2)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 8-12: Continued weakness on elevated volume (distribution)
    for i in range(5):
        d = f"2014-03-{12+i:02d}"; dates.append(d)
        cp = 42.0 - i * 0.3
        hp = cp + 0.8; lp = cp - 0.8; op = cp + 0.1
        vl = int(base_v50 * (1.5 + i * 0.1))
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Phase 4: Stabilization (lows made)
    for i in range(5):
        d = f"2014-03-{17+i:02d}"; dates.append(d)
        cp = 40.5 + math.sin(i) * 0.5
        hp = cp + 0.6; lp = cp - 0.6; op = cp - 0.1
        vl = int(base_v50 * (0.8 + i * 0.05))
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    write_csv(ticker, dates, c, h, l, o, v)

# ============================================================
# PATTERN 2: OUTR (2014)
# "Attempted breakout → reverses on increase in volume. Low vol out, high vol in."
# ============================================================
def generate_outr():
    """Simulate OUTR failure pattern"""
    ticker = "OUTR"
    dates = []
    c, h, l, o, v = [], [], [], [], []
    
    # Phase 1: Uptrend (100 bars) from ~20 to ~32
    base_price = 20.0
    for i in range(100):
        d = f"2013-{9 + (i // 30):02d}-{(i % 30) + 1:02d}"
        dates.append(d)
        trend = base_price + (i / 100) * 12
        noise = (i % 7) * 0.2 - 0.6
        cp = trend + noise
        hp = cp + 0.4 + abs(noise)
        lp = cp - 0.4 - abs(noise) * 0.7
        op = cp - 0.1 + (i % 5) * 0.1
        vl = 500000 + (i % 15) * 30000
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Phase 2: Tight base (20 bars) - range 30-32
    base_v50 = sma(v, 50) or 500000
    for i in range(20):
        d = f"2014-{1 + (i // 31):02d}-{(i % 31) + 1:02d}"
        dates.append(d)
        cp = 31 + math.sin(i * 0.5) * 0.8
        hp = cp + 0.3
        lp = cp - 0.3
        op = cp - 0.05 + (i % 3) * 0.05
        vl = int(base_v50 * (0.4 + (i % 15) * 0.02))  # Volume drying up
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Phase 3: LOW VOLUME BREAKOUT attempt
    # Day 1 - Breaks out on LOW volume
    d = "2014-03-03"; dates.append(d)
    cp = 32.5; hp = 33.0; lp = 31.5; op = 31.5; vl = int(base_v50 * 0.9)  # LOW VOL out!
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 2 - LOW VOLUME follow-through (weak)
    d = "2014-03-04"; dates.append(d)
    cp = 32.8; hp = 33.3; lp = 32.3; op = 32.5; vl = int(base_v50 * 0.85)  # Still low = no conviction
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 3 - HIGH VOLUME REVERSAL! "Low vol out, high vol in" - THE TRAP
    d = "2014-03-05"; dates.append(d)
    cp = 30.5; hp = 33.2; lp = 30.2; op = 32.8; vl = int(base_v50 * 2.8)  # MASSIVE VOL on reversal!
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 4 - Continued selling, high volume (distribution confirmation)
    d = "2014-03-06"; dates.append(d)
    cp = 29.5; hp = 30.8; lp = 29.2; op = 30.5; vl = int(base_v50 * 2.2)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 5 - More downside
    d = "2014-03-07"; dates.append(d)
    cp = 29.0; hp = 29.8; lp = 28.8; op = 29.5; vl = int(base_v50 * 1.8)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 6-10 - recovery attempt fails, volume normalizes lower
    for i in range(5):
        d = f"2014-03-{10+i:02d}"; dates.append(d)
        cp = 29.0 + math.sin(i * 0.7) * 0.5
        hp = cp + 0.5; lp = cp - 0.5; op = cp - 0.1
        vl = int(base_v50 * (0.7 + i * 0.05))
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    write_csv(ticker, dates, c, h, l, o, v)

# ============================================================
# PATTERN 3: LL (Nov-Dec 2013)
# Late-stage base, low-volume breakout → fails → breaks 20-day & 50-day on big volume
# ============================================================
def generate_ll():
    """Simulate LL failure pattern"""
    ticker = "LL"
    dates = []
    c, h, l, o, v = [], [], [], [], []
    
    # Phase 1: Major uptrend (200 bars) - Stage 2 advance from ~20 to ~75
    # This is already a huge multi-year move (late-stage)
    base_price = 20.0
    for i in range(200):
        d = f"2012-{1 + (i // 28):02d}-{(i % 28) + 1:02d}"
        dates.append(d)
        trend = base_price + (i / 200) * 55  # 20 → 75
        noise = (i % 8) * 0.3 - 1.0
        cp = trend + noise
        hp = cp + 0.6 + abs(noise) * 0.5
        lp = cp - 0.6 - abs(noise) * 0.4
        op = cp - 0.2 + (i % 5) * 0.15
        vl = 800000 + (i % 20) * 40000
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    base_v50 = sma(v, 50) or 800000
    
    # Phase 2: Late-stage base formation (40 bars) at 70-78
    # This is the 4th+ base after a massive advance
    for i in range(40):
        d = f"2013-{9 + (i // 30):02d}-{(i % 30) + 1:02d}"
        dates.append(d)
        cp = 74 + math.sin(i * 0.25) * 2.5  # wider range, late-stage instability
        hp = cp + 0.8 + abs(math.sin(i * 0.3)) * 1.0
        lp = cp - 0.8 - abs(math.sin(i * 0.3)) * 0.8
        op = cp - 0.2 + (i % 7) * 0.1
        vl = int(base_v50 * (0.5 + (i % 20) * 0.03))
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Phase 3: LOW VOLUME BREAKOUT (late-stage = already high risk)
    d = "2013-11-04"; dates.append(d)
    cp = 79.0; hp = 79.8; lp = 77.5; op = 77.5; vl = int(base_v50 * 1.1)  # LOW VOL!
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 2: Stalls, fails to follow through
    d = "2013-11-05"; dates.append(d)
    cp = 78.5; hp = 80.0; lp = 78.0; op = 79.0; vl = int(base_v50 * 1.0)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 3: Reverses on BIG volume
    d = "2013-11-06"; dates.append(d)
    cp = 76.0; hp = 79.0; lp = 75.5; op = 78.5; vl = int(base_v50 * 2.2)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 4: Selling continues
    d = "2013-11-07"; dates.append(d)
    cp = 74.5; hp = 76.5; lp = 74.0; op = 76.0; vl = int(base_v50 * 2.0)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 5: Falls below 20-day MA on HIGH volume - SELL SIGNAL #1
    d = "2013-11-08"; dates.append(d)
    cp = 72.0; hp = 74.5; lp = 71.5; op = 74.5; vl = int(base_v50 * 2.5)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 6-8: Bounce attempt FAILS (dead cat bounce)
    for i in range(3):
        d = f"2013-11-{11+i:02d}"; dates.append(d)
        cp = 72.5 + i * 1.0
        hp = cp + 1.0; lp = cp - 1.2; op = cp - 0.3
        vl = int(base_v50 * (0.8 + i * 0.2))
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 9-11: Second leg down
    for i in range(3):
        d = f"2013-11-{14+i:02d}"; dates.append(d)
        cp = 74.0 - i * 2.0
        hp = cp + 1.0; lp = cp - 1.0; op = cp + 0.5
        vl = int(base_v50 * (1.5 + i * 0.3))
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Day 12: BREAKS 50-day MA on MASSIVE VOLUME - SELL SIGNAL #2 - MUST EXIT
    d = "2013-11-19"; dates.append(d)
    cp = 67.0; hp = 71.0; lp = 66.5; op = 70.0; vl = int(base_v50 * 3.0)
    c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Phase 4: Continued decline
    for i in range(10):
        d = f"2013-11-{20+i:02d}"; dates.append(d)
        cp = 66.0 - i * 0.8
        hp = cp + 1.0; lp = cp - 1.0; op = cp + 0.3
        vl = int(base_v50 * (1.2 - i * 0.05))
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    # Some stabilization
    for i in range(5):
        d = f"2013-12-{2+i:02d}"; dates.append(d)
        cp = 58.0 + math.sin(i) * 1.0
        hp = cp + 0.8; lp = cp - 0.8; op = cp - 0.2
        vl = int(base_v50 * (0.6 + i * 0.05))
        c.append(cp); h.append(hp); l.append(lp); o.append(op); v.append(vl)
    
    write_csv(ticker, dates, c, h, l, o, v)

if __name__ == "__main__":
    print("Generating synthetic failure pattern test data...\n")
    generate_wage()
    generate_outr()
    generate_ll()
    print("\nDone! 3 synthetic test CSVs created.")
    print("Run: python _minervini_sepa.py WAGE")
    print("Run: python _minervini_sepa.py OUTR")
    print("Run: python _minervini_sepa.py LL")

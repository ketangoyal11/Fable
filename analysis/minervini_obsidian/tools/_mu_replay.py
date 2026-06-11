"""

MU & ISIS Bar-by-Bar Replay — Learning the Squat-Recovery Pattern
=================================================================
Focuses on the exact days around the squat and reversal recovery.
"""

import csv, os, sys
from datetime import datetime

D = os.path.join(os.path.dirname(__file__), "..", "data", "book_stock_images")

def S(data, n, i):
    if i < n - 1: return None
    return sum(data[i-n+1:i+1]) / n

def compute_sma(data, n):
    return [S(data, n, i) if i >= n-1 else None for i in range(len(data))]

def analyze_ticker(filepath, label, squat_window_start, squat_window_end):
    print(f"\n{'='*140}")
    print(f"  BAR-BY-BAR REPLAY: {label}")
    print(f"  File: {os.path.basename(filepath)}")
    print(f"  Scanning window: bars {squat_window_start} to {squat_window_end}")
    print(f"{'='*140}")
    
    with open(filepath) as f:
        r = csv.reader(f)
        h = next(r)
        rows = list(r)
    
    # Normalize column names — handle both formats
    headers = [x.strip().lower() for x in h]
    
    # Map columns flexibly
    def col_idx(name_variants):
        for v in name_variants:
            for i, hh in enumerate(headers):
                if hh == v.lower():
                    return i
        return -1
    
    date_col = col_idx(["date", "dates"])
    close_col = col_idx(["close", "adj close"])
    high_col = col_idx(["high"])
    low_col = col_idx(["low"])
    open_col = col_idx(["open"])
    vol_col = col_idx(["volume"])
    
    # If no explicit date col, use index 0
    if date_col < 0:
        # Check if first column looks like a date
        try:
            datetime.strptime(rows[0][0][:10], "%Y-%m-%d")
            date_col = 0
        except:
            date_col = 0
    
    dates = [r[date_col][:10] for r in rows]
    c = [float(r[close_col]) for r in rows]
    hh = [float(r[high_col]) for r in rows]
    ll = [float(r[low_col]) for r in rows]
    o = [float(r[open_col]) for r in rows]
    v = [int(float(r[vol_col])) if r[vol_col] else 0 for r in rows]
    
    # If close_col is same as date_col or weird, try common patterns
    if len(c) < 10:
        # Try different mapping
        close_col = 2 if len(rows[0]) > 2 else 1
        c = [float(r[close_col]) for r in rows]
    
    n = len(rows)
    print(f"  Total bars: {n}, Date range: {dates[0]} to {dates[-1]}")
    
    sma20 = compute_sma(c, 20)
    sma50 = compute_sma(c, 50)
    v50_arr = compute_sma(v, 50)
    
    # Print header
    print(f"\n{'Date':<12} {'Open':>7} {'High':>7} {'Low':>7} {'Close':>7} {'Chg%':>7} {'Vol':>10} {'VR':>6} {'SMA20':>8} {'SMA50':>8} {'Range%':>7} {'Midpt':>7} {'Cl-Mid%':>8} {'SQUAT?':>8} {'SIGNAL':<35}")
    print("-" * 165)
    
    # Track squat detection
    squat_days = []  # list of (index, squat_info)
    recovery_window = 5  # Check 5 days after squat for recovery
    
    for i in range(max(0, squat_window_start - 10), min(n, squat_window_end + 10)):
        if i < 1: continue
        
        v50 = v50_arr[i]
        vr = v[i] / v50 if v50 and v50 > 0 else 0
        pchg = (c[i] / c[i-1] - 1) * 100
        
        rng = hh[i] - ll[i]
        rng_pct = rng / ll[i] * 100 if ll[i] > 0 else 0
        midpoint = (hh[i] + ll[i]) / 2
        closeto_mid_pct = (c[i] - midpoint) / midpoint * 100 if midpoint > 0 else 0
        
        # === SQUAT DETECTION (CORRECTED) ===
        # Squat = red candle where close is below midpoint, upper wick > body,
        # body < 40% of range, after a breakout attempt
        is_squat = False
        squat_note = ""
        
        if i >= 1:
            body = abs(c[i] - o[i])
            rng_p = hh[i] - ll[i]
            body_pct = body / rng_p * 100 if rng_p > 0 else 0
            uw = hh[i] - max(o[i], c[i])
            
            is_squat = (pchg < 0 and                  # red candle
                        closeto_mid_pct < -0.8 and    # close below midpoint
                        uw > body * 0.5 and           # upper wick > body
                        body_pct < 40)                # body < 40% of range
            
            if is_squat:
                squat_note = "SQUAT"
        
        # === SIGNAL DETECTION ===
        signals = []
        
        # Failed Breakout Detection
        if i >= 5:
            for lb in range(1, 6):
                prev = i - lb
                if prev <= 0: continue
                prev_v50 = v50_arr[prev] if prev < len(v50_arr) else None
                prev_vr = v[prev] / prev_v50 if prev_v50 and prev_v50 > 0 else 0
                prev_chg = (c[prev] / c[prev-1] - 1) * 100 if prev > 0 else 0
                if prev_chg >= 1.5 and prev_vr < 1.3 and pchg <= -1.5 and vr >= 1.5:
                    if ll[i] < ll[prev] and c[i] < c[prev]:
                        signals.append(f"FAILED-B/O(d{lb})")
                        break
        
        # Distribution
        if i >= 3:
            if all(ll[i-k] < ll[i-k-1] for k in range(3)) and \
               all(c[i-k] < c[i-k-1] for k in range(3)) and \
               all(v[i-k] > v[i-k-1] for k in range(2)):
                signals.append("DISTRIBUTION-3LL")
        
        # Low vol out / high vol in
        if i >= 2 and pchg <= -2.0 and vr >= 2.0:
            for lb in range(3, 11):
                if i - lb < 0: break
                pb = i - lb
                pb_v50 = v50_arr[pb] if pb < len(v50_arr) else None
                pb_vr = v[pb] / pb_v50 if pb_v50 and pb_v50 > 0 else 0
                pb_chg = (c[pb] / c[pb-1] - 1) * 100 if pb > 0 else 0
                if pb_chg >= 1.0 and pb_vr < 1.3:
                    signals.append("LOW-VOL-OUT/HI-VOL-IN")
                    break
        
        # MA violations
        if sma20[i] is not None and c[i] < sma20[i] and vr >= 1.5:
            signals.append(f"<20-MA(v{vr:.1f})")
        if sma50[i] is not None and c[i] < sma50[i] and vr >= 1.5:
            signals.append(f"<50-MA(v{vr:.1f})")
        
        # Squat recovery check: green candle, above midpoint, after a prior squat
        if c[i] > o[i] and closeto_mid_pct > 0:
            for si, (sidx, sinfo) in enumerate(squat_days):
                days_since = i - sidx
                if 0 < days_since <= recovery_window:
                    if c[i] >= c[sidx]:  # Recovered to squat-day close or better
                        signals.append(f"RECOVER-SQUAT(d{days_since})")
                        break
        
        # Bracket stop protection
        if is_squat or any("RECOVER" in s for s in signals):
            bracket1 = c[i] * 0.96
            bracket2 = c[i] * 0.92
            signals.append(f"BRK(${bracket1:.2f}/${bracket2:.2f})")
        
        # Entry day check
        if pchg >= 1.5 and vr >= 1.3:
            signals.append(f"BREAKOUT(v{vr:.1f})")
        
        squat_flag = squat_note if is_squat else ""
        sig_str = "; ".join(signals) if signals else ""
        
        # Print only window + interesting bars outside window
        show = False
        if squat_window_start <= i <= squat_window_end:
            show = True
        elif is_squat or signals or abs(pchg) >= 3 or vr >= 2.0:
            show = True
        
        if show:
            print(f"{dates[i]:<12} {o[i]:>7.2f} {hh[i]:>7.2f} {ll[i]:>7.2f} {c[i]:>7.2f} {pchg:>7.2f} {v[i]:>10,d} {vr:>6.2f} {sma20[i] if sma20[i] else 0:>8.2f} {sma50[i] if sma50[i] else 0:>8.2f} {rng_pct:>7.2f} {midpoint:>7.2f} {closeto_mid_pct:>8.2f} {squat_flag:>8}  {sig_str:<35}")
    
    print("-" * 165)
    print()

def main():
    # MU data
    mu_path = os.path.join(D, "think-and-trade-like-a-champion-figure-1-13-mu-page-39_ohlcv.csv")
    
    # First let's find where Feb 2013 is in the data
    with open(mu_path) as f:
        r = csv.reader(f)
        h = next(r)
        rows = list(r)
    
    # Find Feb 2013 bars
    for i, row in enumerate(rows):
        if row[0].startswith("2013-02-14"):
            print(f"MU Entry date 2013-02-14 is at row index {i}")
        if row[0].startswith("2013-02-15"):
            print(f"MU Squat date 2013-02-15 is at row index {i}")
        if row[0].startswith("2013-02-19"):
            print(f"MU Recovery date 2013-02-19 is at row index {i}")
        if row[0].startswith("2013-03-01"):
            print(f"MU Post-recovery 2013-03-01 at row index {i}")
    
    # Find ISIS (the data was not found earlier)
    isis_path = os.path.join(D, "think-and-trade-like-a-champion-figure-3-3-isis-page-60_ohlcv.csv")
    has_isis = os.path.exists(isis_path)
    if has_isis:
        print(f"\nISIS data exists at: {isis_path}")
    else:
        print(f"\nISIS data NOT found at: {isis_path}")
    
    # Run full replay for MU around the squat window (Feb 2013)
    # The key period is Nov 2013 squat: entries around index 460-480
    # Let's scan the full range
    analyze_ticker(mu_path, "MU (Figure 1-13, Page 39) — Cup Completion Cheat Squat", 440, 500)

if __name__ == "__main__":
    main()

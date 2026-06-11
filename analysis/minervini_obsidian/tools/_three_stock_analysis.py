"""
Three-Stock Time-Boxed Analysis: MU 2013, IONS 2014, GPRE 2014
==============================================================
Purpose: Analyze each stock ONLY within its specified timeframe
to identify the exact buy points and pattern structure.
"""

import csv, os, sys
from datetime import datetime

def S(data, n, i):
    if i < n - 1: return None
    return sum(data[i-n+1:i+1]) / n

def compute_sma(data, n):
    return [S(data, n, i) if i >= n-1 else None for i in range(len(data))]

def scan_stock_data(filepath, year, label):
    """Load data, filter to year, run full analysis."""
    print(f"\n{'#'*150}")
    print(f"#  STOCK: {label}")
    print(f"#  TIMEFRAME: {year} ONLY")
    print(f"#  FILE: {os.path.basename(filepath)}")
    print(f"{'#'*150}")
    
    with open(filepath) as f:
        r = csv.reader(f)
        h = next(r)
        rows = list(r)
    
    dates = []
    c, hh, ll, o, vv = [], [], [], [], []
    
    for row in rows:
        d = row[0][:10]
        if not d.startswith(str(year)):
            continue
        
        # Skip bad data
        try:
            float(row[2])
        except:
            continue
            
        dates.append(d)
        c.append(float(row[2]))
        hh.append(float(row[3]) if len(row) > 3 else float(row[2]))
        ll.append(float(row[4]) if len(row) > 4 else float(row[2]))
        o.append(float(row[5]) if len(row) > 5 else float(row[2]))
        vol = int(float(row[6])) if len(row) > 6 and row[6] else 0
        vv.append(vol)
    
    n = len(dates)
    print(f"\n  Total bars in {year}: {n}")
    print(f"  Date range: {dates[0]} to {dates[-1]}")
    print(f"  Price range: ${min(ll):.2f} to ${max(hh):.2f}")
    print(f"  Open: ${o[0]:.2f}, Close: ${c[-1]:.2f}")
    print(f"  Return: {((c[-1]/o[0])-1)*100:.1f}%")
    
    # Compute indicators
    sma10 = compute_sma(c, 10)
    sma20 = compute_sma(c, 20)
    sma50 = compute_sma(c, 50)
    sma150 = compute_sma(c, 150)
    sma200 = compute_sma(c, 200)
    v20 = compute_sma(vv, 20)
    v50 = compute_sma(vv, 50)
    
    print(f"\n  {'='*155}")
    print(f"  {'Date':<12} {'Open':>7} {'High':>7} {'Low':>7} {'Close':>7} {'Chg%':>7} {'Vol':>10} {'VR':>6} {'SMA20':>8} {'SMA50':>8} {'SMA150':>8} {'Cl-Mid%':>7} {'Pattern':<35}")
    print(f"  {'-'*155}")
    
    # Find buy points and squat patterns
    entries = []
    for i in range(n):
        if i < 1: continue
        
        v20_i = v20[i] if v20[i] else 1
        v50_i = v50[i] if v50[i] else 1
        vr = vv[i] / v50_i if v50_i > 0 else 0
        vr20 = vv[i] / v20_i if v20_i > 0 else 0
        pchg = (c[i] / c[i-1] - 1) * 100
        
        rng = hh[i] - ll[i]
        midpoint = (hh[i] + ll[i]) / 2
        cl_mid_pct = (c[i] - midpoint) / midpoint * 100 if midpoint > 0 else 0
        
        # === MINERVINI SEPA BUY POINT DETECTION ===
        patterns = []
        
        # 1. VCP Breakout: VR>=1.3, Chg>=2%, tightening in prior 20 days
        if vr >= 1.3 and pchg >= 2.0:
            if i >= 20:
                prior_range = [(hh[j] - ll[j]) / c[j] * 100 for j in range(i-20, i) if c[j] > 0]
                if prior_range:
                    first_half = sum(prior_range[:10]) / 10 if len(prior_range) >= 10 else max(prior_range)
                    second_half = sum(prior_range[-10:]) / 10 if len(prior_range) >= 10 else max(prior_range)
                    if second_half < first_half * 0.85:
                        patterns.append("VCP-B/O")
            
            # Cheat entry: VR < 2.0 (low volume breakout)
            if vr < 1.5:
                patterns.append("CHEAT")
        
        # 2. Squat detection (corrected from Figure 1-13): red candle, close below mid, upper wick > body, small body
        body = abs(c[i] - o[i])
        r = hh[i] - ll[i]
        body_pct = body / r * 100 if r > 0 else 0
        uw = hh[i] - max(o[i], c[i])
        is_squat = (pchg < 0 and                  # red candle
                    cl_mid_pct < -0.8 and          # close below midpoint
                    uw > body * 0.5 and            # upper wick > body
                    body_pct < 40)                 # body < 40% of range
        if is_squat:
            patterns.append("SQUAT")
        
        # 3. Squat recovery: after squat, recovery within 1-5 days
        # Recovery means: green candle, close above squat day close, close above midpoint
        if i >= 1 and c[i] > o[i] and cl_mid_pct > 0:  # green, above midpoint
            for lookback in range(1, 6):
                if i - lookback < 0: break
                body_p = abs(c[i-lookback] - o[i-lookback])
                r_p = hh[i-lookback] - ll[i-lookback]
                bp_p = body_p / r_p * 100 if r_p > 0 else 0
                uw_p = hh[i-lookback] - max(o[i-lookback], c[i-lookback])
                mid_p = (hh[i-lookback] + ll[i-lookback]) / 2
                cl_mid_p = (c[i-lookback] - mid_p) / mid_p * 100 if mid_p > 0 else 0
                
                sq_p = (c[i-lookback] < o[i-lookback] and
                        cl_mid_p < -0.8 and
                        uw_p > body_p * 0.5 and
                        bp_p < 40)
                if sq_p and c[i] > c[i-lookback]:
                    patterns.append(f"RECOVER(d{lookback})")
                    break
        
        # 4. Bracket stop protection (Minervini: sell half at -4%, half at -8%)
        # Applied to all entries: avg risk = 6%, but 50% survives shakeouts
        if patterns and any(p in patterns for p in ["SQUAT", "RECOVER", "CHEAT", "VCP"]):
            entry = c[i]
            bracket1 = entry * 0.96  # -4%
            bracket2 = entry * 0.92  # -8%
            avg_stop = entry * 0.94  # hard 6%
            patterns.append(f"BRK(${bracket1:.2f}/${bracket2:.2f})")
        
        # 5. Natural reaction breakout (GPRE pattern)
        if vr >= 1.0 and pchg >= 2.0:
            if i >= 5:
                # Check if price took out a prior reaction high from last 20 days
                max_10 = max(hh[max(0,i-10):i])
                if c[i] > max_10 * 1.0 and c[i] > c[max(0,i-5)]:
                    aw = sum(hh[max(0,i-10):i]) / min(10, i)
                    if c[i] > aw:
                        patterns.append("BO-REACT-HI")
        
        # Show interesting bars
        show = False
        if patterns or abs(pchg) >= 3 or vr >= 2.0:
            show = True
        # Also show the first 20 bars and around key dates
        if i < 20:
            show = True
        
        if show:
            pat_str = "; ".join(patterns) if patterns else ""
            print(f"  {dates[i]:<12} {o[i]:>7.2f} {hh[i]:>7.2f} {ll[i]:>7.2f} {c[i]:>7.2f} {pchg:>7.2f} {vv[i]:>10,d} {vr:>6.2f} {sma20[i] if sma20[i] else 0:>8.2f} {sma50[i] if sma50[i] else 0:>8.2f} {sma150[i] if sma150[i] else 0:>8.2f} {cl_mid_pct:>7.2f}  {pat_str:<35}")
    
    print(f"  {'='*155}")
    print()

def main():
    # Base path for book_stock_images
    D = os.path.join(os.path.dirname(__file__), "..", "data", "book_stock_images")
    
    # ===== MU 2013 =====
    mu_path = os.path.join(D, "think-and-trade-like-a-champion-figure-1-13-mu-page-39_ohlcv.csv")
    if os.path.exists(mu_path):
        scan_stock_data(mu_path, 2013, "MU (Figure 1-13, Page 39) — Cup Completion Cheat Squat")
    else:
        print(f"\n*** MU data NOT found at: {mu_path}")
    
    # ===== GPRE 2014 =====
    gpre_path = os.path.join(D, "think-and-trade-like-a-champion-figure-3-4-gpre-page-61_ohlcv.csv")
    if os.path.exists(gpre_path):
        scan_stock_data(gpre_path, 2014, "GPRE (Figure 3-4, Page 61) — Natural Reaction, Raise Stop")
    else:
        print(f"\n*** GPRE data NOT found at: {gpre_path}")
    
    # ===== IONS 2014 — check possible paths =====
    print(f"\n{'#'*150}")
    print(f"#  STOCK: IONS (ISIS) — Figure 3-3, Page 60")
    print(f"#  TIMEFRAME: 2014 ONLY")
    print(f"{'#'*150}")
    
    # Check multiple possible paths
    possible_paths = [
        os.path.join(D, "think-and-trade-like-a-champion-figure-3-3-isis-page-60_ohlcv.csv"),
        os.path.join(D, "think-and-trade-like-a-champion-figure-3-3-ISIS-page-60_ohlcv.csv"),
        os.path.join(D, "..", "data", "ISIS_ohlcv.csv"),
        os.path.join(D, "..", "data", "IONS_ohlcv.csv"),
    ]
    
    found_ions = False
    for p in possible_paths:
        p_normalized = os.path.normpath(os.path.join(os.path.dirname(__file__), p))
        if os.path.exists(p):
            print(f"\n  Found IONS data at: {p}")
            scan_stock_data(p, 2014, "IONS (ISIS) — Figure 3-3, Bracketed Stops")
            found_ions = True
            break
    
    if not found_ions:
        print(f"\n  *** IONS/ISIS data NOT available (Yahoo returned no OHLCV) ***")
        print(f"  Checking main data directory...")
        
        # Check the main data dir
        main_data = os.path.join(os.path.dirname(__file__), "..", "data")
        all_files = [f for f in os.listdir(main_data) if f.endswith('.csv') and ('IONS' in f or 'ISIS' in f or 'ions' in f or 'isis' in f)]
        if all_files:
            print(f"  Found: {all_files}")
            for f in all_files:
                scan_stock_data(os.path.join(main_data, f), 2014, f"IONS ({f})")
        else:
            print(f"  No IONS/ISIS data found anywhere in the repository.")
            print(f"  Creating SYNTHETIC data based on Figure 3-3 caption...")
            
            # Create synthetic IONS data based on book description
            print(f"""
  SYNTHETIC FIGURE 3-3 RECONSTRUCTION (ISIS -> IONS):
  
  Book caption: "Isis Pharmaceuticals (ISIS) 2014. +54% in two months. 
  The stock pulled back 6.10 percent, stopping you out completely if you 
  used a 6 percent stop. By bracketing stops, selling half at 4 percent 
  and half at 8 percent, you maintained 6 percent risk, but stayed in 
  half the position."
  
  Buy point data NOT available from Yahoo. 
  To get IONS data: 
    Ticker: IONS (was ISIS) on Yahoo Finance
    Try: python _fetch_yahoo.py IONS 2014-01-01 2014-12-31""")

if __name__ == "__main__":
    main()

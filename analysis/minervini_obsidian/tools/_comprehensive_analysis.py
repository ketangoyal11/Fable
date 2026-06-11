"""
Comprehensive Three-Stock Analysis
===================================
1. MU: Nov 2013 squat + breakout level + last 1 year buy points
2. IONS: 2014 bracketed-stops lesson
3. GPRE: 2013
"""

import csv, os

def load_book_csv(path):
    with open(path) as f:
        r = csv.reader(f)
        h = next(r)
        rows = list(r)
    return rows

def parse_yahoo_csv(filepath):
    with open(filepath) as f:
        lines = f.readlines()
    data_points = []
    for line in lines[3:]:
        parts = line.strip().split(',')
        if len(parts) < 6: continue
        try:
            d = parts[0][:10]
            c = float(parts[1])
            hh = float(parts[2])
            ll = float(parts[3])
            o = float(parts[4])
            v = int(float(parts[5]))
            data_points.append((d, o, hh, ll, c, v))
        except:
            continue
    return data_points

# ============================================================
# 1. MU - Nov 2013 Squat
# ============================================================
def analyze_mu_nov2013():
    print("="*130)
    print("  MU -- NOV 2013 SQUAT: IDENTIFY BREAKOUT LEVEL")
    print("="*130)
    
    D = os.path.join(os.path.dirname(__file__), "..", "data", "book_stock_images")
    fp = os.path.join(D, "think-and-trade-like-a-champion-figure-1-13-mu-page-39_ohlcv.csv")
    rows = load_book_csv(fp)
    
    dates, c, hh, ll, o, vv = [], [], [], [], [], []
    for row in rows:
        d = row[0][:10]
        if d < '2013-10-01' or d > '2013-12-31': continue
        dates.append(d)
        c.append(float(row[2]))
        hh.append(float(row[3]))
        ll.append(float(row[4]))
        o.append(float(row[5]))
        vv.append(int(float(row[6])))
    
    n = len(dates)
    v50_arr = [sum(vv[max(0,i-49):i+1])/min(50,i+1) for i in range(n)]
    
    print(f"\n{'Date':<12} {'O':>7} {'H':>7} {'L':>7} {'C':>7} {'Chg%':>7} {'Vol':>11} {'VR':>6} {'SMA20':>7} {'Midpt':>7} {'Cl-Mid%':>7} {'Pattern':<40}")
    print("-"*125)
    
    for i in range(max(0, n-60), n):
        if i < 1: continue
        pchg = (c[i]/c[i-1]-1)*100
        vr = vv[i]/v50_arr[i] if v50_arr[i] > 0 else 0
        mid = (hh[i]+ll[i])/2
        cl_mid = (c[i]-mid)/mid*100
        sma20 = sum(c[max(0,i-19):i+1])/min(20,i+1)
        
        pat = []
        body = abs(c[i] - o[i])
        rng = hh[i] - ll[i]
        body_pct = body / rng * 100 if rng > 0 else 0
        uw = hh[i] - max(o[i], c[i])
        is_sq = (pchg < 0 and cl_mid < -0.8 and uw > body * 0.5 and body_pct < 40)
        if is_sq:
            pat.append("SQUAT")
        if cl_mid > 1.0 and pchg >= 1.5:
            pat.append("RECOVER")
        rng_pct = (hh[i]-ll[i])/c[i]*100 if c[i] > 0 else 0
        if rng_pct < 2.0 and abs(pchg) < 1.5:
            pat.append(f"tight({rng_pct:.1f}%)")
        
        pat_str = "; ".join(pat) if pat else ""
        
        note = ""
        if dates[i] == "2013-11-14": note = "  <-- BASE HIGH ($19.20)"
        elif dates[i] == "2013-11-15": note = "  <-- FIRST BREAKOUT"
        elif dates[i] == "2013-11-18": note = "  <-- SQUAT DAY ($19.88)"
        elif dates[i] == "2013-11-19": note = "  <-- SQUAT CONTINUES"
        elif dates[i] == "2013-11-21": note = "  <-- RECOVERY (2 days)"
        elif dates[i] == "2013-11-27": note = "  <-- NEW HIGH"
        
        print(f"{dates[i]:<12} {o[i]:>7.2f} {hh[i]:>7.2f} {ll[i]:>7.2f} {c[i]:>7.2f} {pchg:>7.2f} {vv[i]:>11,d} {vr:>6.2f} {sma20:>7.2f} {mid:>7.2f} {cl_mid:>7.2f}  {pat_str:<40}{note}")
    
    print()
    print("  BREAKOUT LEVEL IDENTIFICATION:")
    print("  ---------------------------------------------------------")
    print("  Base: Oct 15 - Nov 14 (23 days), range $16.35-$19.20")
    print("  Base high (resistance): $19.20 (Nov 14)")
    print("  Squat day high: $19.88 (Nov 18) = THE BREAKOUT LEVEL")
    print("  Recovery: Nov 21, C=$19.99 above $19.88")
    print("  Confirmation: Nov 27, C=$21.17 (+6.5%)")
    print("  ---------------------------------------------------------")
    print("  PIVOT/BREAKOUT LEVEL: $19.88")
    print("  ENTRY: $19.88-$20.11 (breakout + recovery)")
    print("  STOP: ~$18.50 (below Nov 20 low)")
    print("  RISK: ~7%")
    print()

# ============================================================
# 2. MU - Last 1 Year
# ============================================================
def analyze_mu_recent():
    print("="*130)
    print("  MU -- LAST 1 YEAR (Jun 2025 - Jun 2026)")
    print("="*130)
    
    D2 = os.path.join(os.path.dirname(__file__), "..", "data")
    fp = os.path.join(D2, "MU_recent_ohlcv.csv")
    data_points = parse_yahoo_csv(fp)
    if not data_points:
        print("  Could not parse MU_recent data.")
        return
    
    print(f"  Bars: {len(data_points)}")
    print(f"  Range: {data_points[0][0]} to {data_points[-1][0]}")
    print(f"  Price range: ${min(p[2] for p in data_points):.2f} to ${max(p[3] for p in data_points):.2f}")
    print(f"  Open: ${data_points[0][4]:.2f}  Last: ${data_points[-1][4]:.2f}")
    
    c_vals = [p[4] for p in data_points]
    h_vals = [p[3] for p in data_points]
    v_vals = [p[5] for p in data_points]
    n = len(data_points)
    v50 = [sum(v_vals[max(0,i-49):i+1])/min(50,i+1) for i in range(n)]
    
    print(f"\n{'Date':<12} {'O':>9} {'H':>9} {'L':>9} {'C':>9} {'Chg%':>7} {'VR':>6} {'SMA20':>9} {'SMA50':>9} {'Pattern':<40}")
    print("-"*140)
    
    for i in range(n):
        if i < 1: continue
        d, o, h_i, l_i, c, v = data_points[i]
        pchg = (c/data_points[i-1][4]-1)*100
        vr = v/v50[i] if v50[i] > 0 else 0
        sma20 = sum(c_vals[max(0,i-19):i+1])/min(20,i+1)
        sma50 = sum(c_vals[max(0,i-49):i+1])/min(50,i+1) if i >= 49 else None
        
        pat = []
        if vr >= 1.3 and pchg >= 2.0:
            pat.append(f"BO(v{vr:.1f})")
        mid = (h_i+l_i)/2
        cl_mid = (c-mid)/mid*100
        body = abs(c - o)
        rng_mu = h_i - l_i
        body_pct = body / rng_mu * 100 if rng_mu > 0 else 0
        uw = h_i - max(o, c)
        is_sq = (pchg < 0 and cl_mid < -0.8 and uw > body * 0.5 and body_pct < 40)
        if is_sq:
            pat.append(f"SQ({cl_mid:.1f}%)")
        if cl_mid > 1.0 and pchg >= 1.5:
            pat.append("REC")
        if vr >= 2.5 and pchg >= 3:
            pat.append("CLIMAX")
        
        pat_str = "; ".join(pat) if pat else ""
        
        if i < 3 or pat or abs(pchg) >= 3 or vr >= 2.0:
            print(f"{d:<12} {o:>9.2f} {h_i:>9.2f} {l_i:>9.2f} {c:>9.2f} {pchg:>7.2f} {vr:>6.2f} {sma20:>9.2f} {sma50 if sma50 else 0:>9.2f}  {pat_str:<40}")
    
    print()

# ============================================================
# 3. IONS 2014
# ============================================================
def analyze_ions_2014():
    print("="*130)
    print("  IONS (ISIS) -- 2014: BRACKETED STOPS (Figure 3-3)")
    print("="*130)
    
    D2 = os.path.join(os.path.dirname(__file__), "..", "data")
    fp = os.path.join(D2, "IONS_2014_ohlcv.csv")
    data_points = parse_yahoo_csv(fp)
    if not data_points:
        print("  Could not parse IONS data.")
        return
    
    print(f"  Bars: {len(data_points)}")
    print(f"  Range: {data_points[0][0]} to {data_points[-1][0]}")
    print(f"  Price range: ${min(p[2] for p in data_points):.2f} to ${max(p[3] for p in data_points):.2f}")
    print(f"  Start: ${data_points[0][4]:.2f}  End: ${data_points[-1][4]:.2f}  Return: {(data_points[-1][4]/data_points[0][4]-1)*100:.1f}%")
    
    c_vals = [p[4] for p in data_points]
    v_vals = [p[5] for p in data_points]
    n = len(data_points)
    v50 = [sum(v_vals[max(0,i-49):i+1])/min(50,i+1) for i in range(n)]
    
    print(f"\n{'Date':<12} {'O':>9} {'H':>9} {'L':>9} {'C':>9} {'Chg%':>7} {'VR':>6} {'SMA20':>9} {'SMA50':>9} {'Note':<45}")
    print("-"*135)
    
    for i in range(n):
        if i < 1: continue
        d, o, h_i, l_i, c, v = data_points[i]
        pchg = (c/data_points[i-1][4]-1)*100
        vr = v/v50[i] if v50[i] > 0 else 0
        sma20 = sum(c_vals[max(0,i-19):i+1])/min(20,i+1)
        sma50 = sum(c_vals[max(0,i-49):i+1])/min(50,i+1) if i >= 49 else None
        
        note = ""
        if vr >= 1.3 and pchg >= 2.0:
            note = f"BO(v{vr:.1f})"
        if pchg <= -2.0 and vr >= 1.3:
            note = f"SELLOFF({pchg:.1f}%)"
        
        show = (i < 5 or note or abs(pchg) >= 3 or vr >= 2.0)
        if show:
            print(f"{d:<12} {o:>9.2f} {h_i:>9.2f} {l_i:>9.2f} {c:>9.2f} {pchg:>7.2f} {vr:>6.2f} {sma20:>9.2f} {sma50 if sma50 else 0:>9.2f}  {note:<45}")
    
    print()

# ============================================================
# 4. GPRE 2013
# ============================================================
def analyze_gpre_2013():
    print("="*130)
    print("  GPRE -- 2013: FULL YEAR ANALYSIS")
    print("="*130)
    
    D2 = os.path.join(os.path.dirname(__file__), "..", "data")
    fp = os.path.join(D2, "GPRE_2013_ohlcv.csv")
    data_points = parse_yahoo_csv(fp)
    if not data_points:
        print("  Could not parse GPRE 2013 data.")
        return
    
    print(f"  Bars: {len(data_points)}")
    print(f"  Range: {data_points[0][0]} to {data_points[-1][0]}")
    print(f"  Price range: ${min(p[2] for p in data_points):.2f} to ${max(p[3] for p in data_points):.2f}")
    print(f"  Start: ${data_points[0][4]:.2f}  End: ${data_points[-1][4]:.2f}  Return: {(data_points[-1][4]/data_points[0][4]-1)*100:.1f}%")
    
    c_vals = [p[4] for p in data_points]
    h_vals = [p[3] for p in data_points]
    v_vals = [p[5] for p in data_points]
    n = len(data_points)
    v50 = [sum(v_vals[max(0,i-49):i+1])/min(50,i+1) for i in range(n)]
    
    print(f"\n{'Date':<12} {'O':>8} {'H':>8} {'L':>8} {'C':>8} {'Chg%':>7} {'VR':>6} {'SMA20':>8} {'SMA50':>8} {'Pattern':<30}")
    print("-"*120)
    
    for i in range(n):
        if i < 1: continue
        d, o, h_i, l_i, c, v = data_points[i]
        pchg = (c/data_points[i-1][4]-1)*100
        vr = v/v50[i] if v50[i] > 0 else 0
        sma20 = sum(c_vals[max(0,i-19):i+1])/min(20,i+1)
        sma50 = sum(c_vals[max(0,i-49):i+1])/min(50,i+1) if i >= 49 else None
        
        pat = []
        if vr >= 1.3 and pchg >= 2.0:
            pat.append(f"BO(v{vr:.1f})")
        mid = (h_i+l_i)/2
        cl_mid = (c-mid)/mid*100
        body = abs(c - o)
        rng_gp = h_i - l_i
        body_pct = body / rng_gp * 100 if rng_gp > 0 else 0
        uw = h_i - max(o, c)
        is_sq = (pchg < 0 and cl_mid < -0.8 and uw > body * 0.5 and body_pct < 40)
        if is_sq:
            pat.append("SQ")
        if vr >= 2.5:
            pat.append(f"HV({vr:.1f})")
        
        pat_str = "; ".join(pat) if pat else ""
        
        show = (i < 5 or pat or abs(pchg) >= 4 or (vr >= 2.0 and abs(pchg) >= 2))
        if show:
            print(f"{d:<12} {o:>8.2f} {h_i:>8.2f} {l_i:>8.2f} {c:>8.2f} {pchg:>7.2f} {vr:>6.2f} {sma20:>8.2f} {sma50 if sma50 else 0:>8.2f}  {pat_str:<30}")
    
    print()

if __name__ == "__main__":
    analyze_mu_nov2013()
    analyze_mu_recent()
    analyze_ions_2014()
    analyze_gpre_2013()
    print("Done.")

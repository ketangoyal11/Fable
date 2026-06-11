"""
BUY POINTS DETECTOR
===================
Scans any stock CSV and outputs:
  WHEN  -> date of entry
  WHERE -> entry price (level)
  HOW   -> setup type, stop placement, bracket levels, status

Usage:
  python _buy_points.py <csv_path>
  python _buy_points.py (runs on all known datasets)

Corrected Squat Definition (from Figure 1-13 analysis):
  Red candle (c < o)
  Close below midpoint of daily range (cl_mid < -0.8%)
  Upper wick > body * 0.5 (rejection at highs)
  Body < 40% of total range (small candle body)
  Then recovery back up within 1-5 days
"""

import csv, os, sys

# ===============================================================
# CORE CALCULATIONS
# ===============================================================
def load_csv(filepath):
    """Load any OHLCV CSV (Yahoo format or simple)."""
    lines = open(filepath).readlines()
    dp = []
    for line in lines[3:] if len(lines) > 3 else lines:
        p = line.strip().split(",")
        if len(p) < 6: continue
        try:
            d = p[0][:10]; c = float(p[1]); hh = float(p[2]); ll = float(p[3])
            o = float(p[4]); v = int(float(p[5]))
            dp.append((d, o, hh, ll, c, v))
        except: continue
    return dp

def v50_list(dp):
    """50-day volume average."""
    vv = [p[5] for p in dp]
    return [sum(vv[max(0,i-49):i+1])/min(50,i+1) for i in range(len(dp))]

def detect_squat(c, o, hh, ll, cl_mid):
    """Corrected squat: red candle, close below mid, upper wick > body, small body."""
    body = abs(c - o)
    rng = hh - ll
    if rng <= 0: return False
    bp = body / rng * 100
    uw = hh - max(o, c)
    return (c < o and                # red candle
            cl_mid < -0.8 and        # close below midpoint
            uw > body * 0.5 and      # upper wick > body
            bp < 40)                 # body < 40% of range

# ===============================================================
# BUY POINT TYPES
# ===============================================================
def find_all_buy_points(dp):
    """Scan entire dataset for all buy signals."""
    n = len(dp)
    v50 = v50_list(dp)
    buy_signals = []

    for i in range(1, n):
        d, o, hh, ll, c, v = dp[i]
        d_prev, o_prev, hh_prev, ll_prev, c_prev, v_prev = dp[i-1]
        vr = v / v50[i] if v50[i] > 0 else 0
        pchg = (c / c_prev - 1) * 100

        mid = (hh + ll) / 2
        cl_mid = (c - mid) / mid * 100 if mid > 0 else 0

        body = abs(c - o)
        rng = hh - ll
        bp = body / rng * 100 if rng > 0 else 0
        uw = hh - max(o, c)

        is_sq = detect_squat(c, o, hh, ll, cl_mid)

        if is_sq:
            # ----- SQUAT DETECTED -----
            # Look for recovery in next 1-5 days
            for j in range(1, 6):
                if i + j >= n: break
                dj, oj, hhj, llj, cj, vj = dp[i+j]
                midj = (hhj + llj) / 2
                cl_midj = (cj - midj) / midj * 100 if midj > 0 else 0
                pchgj = (cj / dp[i+j-1][4] - 1) * 100
                vrj = vj / v50[i+j] if v50[i+j] > 0 else 0

                # Recovery: green, above squat day close, close near/above midpoint
                if cj > c and cj > oj and cl_midj > 0:
                    entry = cj
                    # Stop options
                    stop6 = entry * 0.94
                    stop4 = entry * 0.96  # bracket 1
                    stop8 = entry * 0.92  # bracket 2

                    buy_signals.append({
                        "type": "SQUAT-RECOVERY",
                        "squat_date": d,
                        "squat_high": hh,
                        "squat_close": c,
                        "entry_date": dj,
                        "entry_price": entry,
                        "entry_vr": vrj,
                        "setup_detail": "Squat at $%.2f high, recovered %d days later" % (hh, j),
                        "bracket1": stop4,   # half at -4%
                        "bracket2": stop8,   # half at -8%
                        "stop_hard": stop6,  # full 6% stop
                        "status": "ACTIVE",
                        "days_to_recovery": j
                    })
                    break

        # ----- CUP BREAKOUT (VR >= 1.3, gain >= 2%, above prior resistance) -----
        if vr >= 1.3 and pchg >= 2.0 and i >= 20:
            # Check if above prior 20-day high (cup rim)
            prior_high_20 = max(dp[k][2] for k in range(max(0,i-20), i))
            if c > prior_high_20 * 1.0:  # above prior resistance
                buy_signals.append({
                    "type": "CUP-BREAKOUT",
                    "entry_date": d,
                    "entry_price": c,
                    "entry_vr": vr,
                    "setup_detail": "Breakout above $%.2f resistance, VR=%.2f" % (prior_high_20, vr),
                    "bracket1": c * 0.96,
                    "bracket2": c * 0.92,
                    "stop_hard": c * 0.94,
                    "status": "ACTIVE",
                    "days_to_recovery": 0
                })

        # ----- 3-C CHEAT (low volume breakout, VR < 1.2 but solid gain) -----
        if vr < 1.2 and vr > 0.3 and pchg >= 2.0:
            prior_high_10 = max(dp[k][2] for k in range(max(0,i-10), i))
            if c > prior_high_10 * 1.0:
                buy_signals.append({
                    "type": "3-C CHEAT",
                    "entry_date": d,
                    "entry_price": c,
                    "entry_vr": vr,
                    "setup_detail": "Low VR=%.2f cheat breakout, +%.1f%%" % (vr, pchg),
                    "bracket1": c * 0.96,
                    "bracket2": c * 0.92,
                    "stop_hard": c * 0.94,
                    "status": "ACTIVE",
                    "days_to_recovery": 0
                })

        # ----- DARVAS BOX BREAKOUT (tight range then VR >= 1.2 with gain) -----
        if vr >= 1.2 and pchg >= 2.0 and i >= 15:
            prior_10 = [dp[k] for k in range(max(0,i-15), i)]
            avg_range = sum((p[2]-p[3])/p[4] for p in prior_10 if p[4] > 0) / len(prior_10) * 100 if prior_10 else 100
            if avg_range < 3.5:  # tight trading range
                buy_signals.append({
                    "type": "DARVAS-BOX",
                    "entry_date": d,
                    "entry_price": c,
                    "entry_vr": vr,
                    "setup_detail": "Tight box (avg range %.1f%%), breakout +%.1f%%" % (avg_range, pchg),
                    "bracket1": c * 0.96,
                    "bracket2": c * 0.92,
                    "stop_hard": c * 0.94,
                    "status": "ACTIVE",
                    "days_to_recovery": 0
                })

    return buy_signals

# ===============================================================
# OUTPUT
# ===============================================================
def print_buy_points(buy_signals, label="STOCK"):
    """Pretty-print buy points in order."""
    # Sort by date
    buy_signals.sort(key=lambda x: x["entry_date"])

    if not buy_signals:
        print("  No buy points detected.")
        return

    print("\n%s" % ("=" * 100))
    print("  BUY POINTS: %s" % label)
    print("  (WHEN -> WHERE -> HOW)")
    print("%s" % ("=" * 100))

    for i, bp in enumerate(buy_signals):
        print("\n  #%d: %s" % (i+1, bp["type"]))
        print("  %s" % ("-" * 60))
        print("    WHEN:  %s" % bp["entry_date"])
        print("    WHERE: $%.2f (entry price)" % bp["entry_price"])
        print("    HOW:   %s" % bp["setup_detail"])
        print("           VR=%.2f" % bp["entry_vr"])

        # Check if bracket holds within data
        print("           Brackets: -4%%=$%.2f | -8%%=$%.2f | Hard 6%%=$%.2f" % (
            bp["bracket1"], bp["bracket2"], bp["stop_hard"]))
        print("           Strategy: Sell half at $%.2f (-4%%), half at $%.2f (-8%%)" % (
            bp["bracket1"], bp["bracket2"]))
        print("           Avg risk = 6%%, but 50%% survives the -6%% shakeout")

    print()

def print_bracket_summary(buy_signals):
    """Show which brackets would have survived."""
    print("  %s" % ("=" * 60))
    print("  BRACKET SURVIVAL ANALYSIS")
    print("  %s" % ("-" * 60))

    for i, bp in enumerate(buy_signals):
        entry = bp["entry_price"]
        b1 = bp["bracket1"]  # -4%
        b2 = bp["bracket2"]  # -8%
        label = "%s %s" % (bp["entry_date"], bp["type"])
        print("  %d. %s" % (i+1, label))
        print("     Entry: $%.2f | Bracket1(-4%%): $%.2f | Bracket2(-8%%): $%.2f" % (entry, b1, b2))
        print("     Risk per half: -4%% on 50%%, -8%% on 50%% = avg -6%%")
        print("     Max loss with brackets: -6%%, Max gain with full stop: exited at -6%%")
        print("     Benefit: 50%% stays in to ride the uptrend")

# ===============================================================
# MAIN
# ===============================================================
if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

    # If csv path provided, scan that file
    if len(sys.argv) > 1:
        fp = sys.argv[1]
        if os.path.exists(fp):
            dp = load_csv(fp)
            sigs = find_all_buy_points(dp)
            print_buy_points(sigs, os.path.basename(fp))
            print_bracket_summary(sigs)
        else:
            print("File not found: %s" % fp)
        sys.exit(0)

    # Otherwise run on all known datasets
    datasets = [
        # (path, label)
        ("book_stock_images/think-and-trade-like-a-champion-figure-1-13-mu-page-39_ohlcv.csv", "MU 2013 (Figure 1-13)"),
        ("IONS_2012_2014_ohlcv.csv", "IONS 2012-2014 (Figure 3-3)"),
        ("GPRE_2012_2014_ohlcv.csv", "GPRE 2012-2014 (Figure 3-4)"),
        ("MU_recent_ohlcv.csv", "MU Last 1 Year"),
    ]

    for rel_path, label in datasets:
        fp = os.path.join(data_dir, rel_path)
        if os.path.exists(fp):
            dp = load_csv(fp)
            sigs = find_all_buy_points(dp)
            print_buy_points(sigs, label)
            if sigs:
                print_bracket_summary(sigs)
        else:
            print("  NOT FOUND: %s" % fp)

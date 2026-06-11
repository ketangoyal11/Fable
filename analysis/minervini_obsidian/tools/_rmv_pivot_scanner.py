"""
RMV + PIVOT SCANNER -- Minervini Entry Detection with RMV Tightness Levels
=========================================================================
Combines the RMV (Range Magnitude Value) indicator with pivot detection
to identify high-quality Minervini entry points.

RMV measures candle "tightness" -- lower values = tighter consolidation.
When RMV drops below threshold and forms a streak, it identifies areas
of contraction that frequently precede breakouts/VCPs/cheat entries.

Usage:
    python _rmv_pivot_scanner.py <csv_path> [--year YYYY] [--ticker TICKER]
    
    <csv_path>  : Path to OHLCV CSV (standard Yahoo format with extra columns)
    --year YYYY : Optional year filter
    --ticker T  : Ticker symbol (for output labeling)

Examples:
    python _rmv_pivot_scanner.py ../../data/yfinance_universe/history/APOLLO.csv --ticker APOLLO
    python _rmv_pivot_scanner.py ../../data/yfinance_universe/history/IRFC.csv --ticker IRFC
"""

import csv, sys, os, math
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

# RMV Parameters (from TradingView indicator)
RMV_TIGHT_THRESHOLD = 15.0       # RMV <= 15 = "tight" bar
RMV_STREAK_MIN = 2               # Minimum consecutive tight bars for a streak
VCP_CONTRACT_THRESHOLD = 0.85    # Second half / first half range ratio
PIVOT_LOOKBACK = 25              # Bars to look each side for pivot detection
BREAKOUT_VR_MIN = 1.3            # Minimum volume ratio for breakout
BREAKOUT_CHG_MIN = 2.0           # Minimum % change for breakout

# =============================================================================
# DATA LOADING
# =============================================================================

def load_csv(filepath):
    """Load OHLCV CSV with auto-detection of extra columns."""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            try:
                d = r.get("Date", "").strip()[:10]
                datetime.strptime(d, '%Y-%m-%d')
            except:
                continue
            
            try:
                open_ = float(r.get("Open", r.get("open", 0)))
                high = float(r.get("High", r.get("high", 0)))
                low = float(r.get("Low", r.get("low", 0)))
                close = float(r.get("Close", r.get("close", 0)))
                volume = int(float(r.get("Volume", r.get("volume", 0))))
            except (ValueError, TypeError):
                continue
            
            if high == 0 or low == 0 or close == 0:
                continue  # Skip empty rows
                
            rows.append({
                "date": d,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume
            })
    return rows


def filter_year(data, year):
    """Filter to a single year."""
    if year is None:
        return data
    return [d for d in data if d["date"][:4] == str(year)]


# =============================================================================
# INDICATOR COMPUTATION
# =============================================================================

def compute_atr(data, period=14):
    """Average True Range."""
    atrs = []
    for i in range(len(data)):
        if i == 0:
            atrs.append(None)
            continue
        tr = max(
            data[i]["high"] - data[i]["low"],
            abs(data[i]["high"] - data[i-1]["close"]),
            abs(data[i]["low"] - data[i-1]["close"])
        )
        if i < period:
            atrs.append(tr if i == 1 else (atrs[-1] * (period-1) + tr) / period if atrs[-1] else tr)
        else:
            atrs.append((atrs[-1] * (period-1) + tr) / period)
    return atrs


def compute_sma(values, period):
    """Simple Moving Average."""
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i-period+1:i+1]) / period)
    return result


def compute_ema(values, period):
    """Exponential Moving Average."""
    result = []
    multiplier = 2 / (period + 1)
    for i in range(len(values)):
        if i == 0:
            result.append(values[0])
        elif i < period:
            # Simple SMA until enough data
            result.append(sum(values[:i+1]) / (i+1))
        else:
            result.append((values[i] - result[-1]) * multiplier + result[-1])
    return result


def compute_rmv(data, atr5, atr3):
    """
    Compute RMV (Range Magnitude Value) for each bar.
    
    Logic from TradingView indicator:
    - absTight: range <= ATR(5) * 0.75
    - strongOC: open & close both in upper 50% of range
    - numerator = body if absTight OR strongOC, else range
    - denominator = max(ATR(3), highest(range, 3))
    - rmv = min((numerator / denominator) * 50, 100)
    """
    rmv_vals = []
    
    for i in range(len(data)):
        if i < 3 or atr5[i] is None or atr3[i] is None:
            rmv_vals.append(None)
            continue
        
        r = data[i]
        rng = r["high"] - r["low"]
        if rng == 0:
            rmv_vals.append(100.0)
            continue
        
        body = abs(r["close"] - r["open"])
        open_pos_pct = (r["open"] - r["low"]) / rng * 100
        close_pos_pct = (r["close"] - r["low"]) / rng * 100
        
        # absTight: range <= ATR(5) * 0.75
        abs_tight = rng <= atr5[i] * 0.75
        
        # strongOC: both open and close in upper 50%
        strong_oc = open_pos_pct > 50 and close_pos_pct > 50
        
        # Numerator: body if tight or strong OC, else full range
        numerator = body if (abs_tight or strong_oc) else rng
        
        # Denominator: max(ATR(3), highest(range, 3))
        h3 = max(abs(data[j]["high"] - data[j]["low"]) for j in range(max(0, i-2), i+1))
        denominator = max(atr3[i], h3)
        
        if denominator == 0:
            rmv_vals.append(100.0)
            continue
        
        rmv = min((numerator / denominator) * 50, 100)
        rmv_vals.append(rmv)
    
    return rmv_vals


# =============================================================================
# PATTERN DETECTION
# =============================================================================

def detect_pivots(data, lookback=PIVOT_LOOKBACK):
    """
    Detect swing highs (pivots) using lookback window.
    Returns list of (index, high_price) tuples for pivots.
    """
    pivots = []
    for i in range(lookback, len(data) - lookback):
        h = data[i]["high"]
        # Check if this bar's high is higher than lookback bars on each side
        prev_max = max(data[j]["high"] for j in range(i - lookback, i))
        next_max = max(data[j]["high"] for j in range(i + 1, i + lookback + 1))
        if h >= prev_max and h >= next_max:
            pivots.append((i, h))
    return pivots


def find_squat(data, i):
    """Check if bar i is a Minervini squat."""
    if i < 1:
        return False
    r = data[i]
    p = data[i-1]
    pchg = (r["close"] / p["close"] - 1) * 100
    rng = r["high"] - r["low"]
    if rng == 0:
        return False
    body = abs(r["close"] - r["open"])
    body_pct = body / rng * 100
    upper_wick = r["high"] - max(r["open"], r["close"])
    midpoint = (r["high"] + r["low"]) / 2
    cl_mid_pct = (r["close"] - midpoint) / midpoint * 100
    
    return (pchg < 0 and cl_mid_pct < -0.8 and 
            upper_wick > body * 0.5 and body_pct < 40)


def check_vcp(data, i, lookback=20):
    """Check if bar i completes a VCP (range contraction)."""
    if i < lookback:
        return False, 0
    
    ranges = []
    for j in range(i - lookback, i):
        if data[j]["close"] > 0:
            rng_pct = (data[j]["high"] - data[j]["low"]) / data[j]["close"] * 100
            ranges.append(rng_pct)
    
    if len(ranges) < lookback:
        return False, 0
    
    first_half = sum(ranges[:10]) / 10
    second_half = sum(ranges[-10:]) / 10
    
    if first_half == 0:
        return False, 0
    
    ratio = second_half / first_half
    return ratio < VCP_CONTRACT_THRESHOLD, ratio


# =============================================================================
# MAIN ANALYSIS
# =============================================================================

def analyze(data, ticker="STOCK"):
    """Full RMV + Pivot analysis pipeline."""
    n = len(data)
    if n < 50:
        print(f"[err] Need at least 50 bars, got {n}")
        return
    
    print(f"\n{'='*100}")
    print(f"  {ticker} -- RMV + PIVOT ENTRY ANALYSIS")
    print(f"{'='*100}")
    print(f"  Period: {data[0]['date']} -> {data[-1]['date']} ({n} bars)")
    
    # ---- Compute Indicators ----
    closes = [d["close"] for d in data]
    highs = [d["high"] for d in data]
    lows = [d["low"] for d in data]
    volumes = [d["volume"] for d in data]
    
    atr3 = compute_atr(data, 3)
    atr5 = compute_atr(data, 5)
    atr14 = compute_atr(data, 14)
    sma10 = compute_sma(closes, 10)
    sma20 = compute_sma(closes, 20)
    sma50 = compute_sma(closes, 50)
    sma150 = compute_sma(closes, 150)
    sma200 = compute_sma(closes, 200)
    v20 = compute_sma(volumes, 20)
    v50 = compute_sma(volumes, 50)
    ema21 = compute_ema(closes, 21)
    
    rmv = compute_rmv(data, atr5, atr3)
    
    # ---- Detect Pivots ----
    pivots = detect_pivots(data)
    pivot_prices = {idx: price for idx, price in pivots}
    
    # ---- Build Bar Analysis ----
    results = []
    tight_streaks = []  # Track tight streak regions
    current_streak = []
    
    for i in range(n):
        r = data[i]
        bar = {
            "date": r["date"],
            "open": r["open"],
            "high": r["high"],
            "low": r["low"],
            "close": r["close"],
            "volume": r["volume"],
            "sma20": sma20[i],
            "sma50": sma50[i],
            "sma150": sma150[i],
            "sma200": sma200[i],
            "atr14": atr14[i],
            "rmv": rmv[i],
            "is_pivot": i in pivot_prices,
            "pivot_high": pivot_prices.get(i, None),
            "pchg": ((r["close"] / data[i-1]["close"]) - 1) * 100 if i > 0 else 0,
            "patterns": [],
            "is_tight": False,
            "streak_id": None,
            "near_pivot": None,
            "pivot_vcp": False,
            "prev_pivot_idx": None,
            "entry_signal": False,
        }
        
        # VR
        if v50[i] is not None and v50[i] > 0:
            bar["vr"] = r["volume"] / v50[i]
        elif v20[i] is not None and v20[i] > 0:
            bar["vr"] = r["volume"] / v20[i]
        else:
            bar["vr"] = 0
        
        # Range % 
        bar["rng_pct"] = (r["high"] - r["low"]) / r["close"] * 100 if r["close"] > 0 else 0
        
        # SMA distances
        bar["sma50_dist"] = (r["close"] / sma50[i] - 1) * 100 if sma50[i] else 0
        bar["sma200_dist"] = (r["close"] / sma200[i] - 1) * 100 if sma200[i] else 0
        
        # Above SMAs
        bar["above_sma20"] = sma20[i] is not None and r["close"] > sma20[i]
        bar["above_sma50"] = sma50[i] is not None and r["close"] > sma50[i]
        bar["above_sma150"] = sma150[i] is not None and r["close"] > sma150[i]
        bar["above_sma200"] = sma200[i] is not None and r["close"] > sma200[i]
        
        # ---- RMV Tightness ----
        if rmv[i] is not None and rmv[i] <= RMV_TIGHT_THRESHOLD and i >= 3:
            bar["is_tight"] = True
            current_streak.append(i)
        else:
            # End of streak
            if len(current_streak) >= RMV_STREAK_MIN:
                tight_streaks.append(list(current_streak))
            current_streak = []
        
        # ---- Squat Detection ----
        if find_squat(data, i):
            bar["patterns"].append("SQUAT")
        
        # ---- VCP Check ----
        is_vcp, vcp_ratio = check_vcp(data, i)
        if is_vcp:
            bar["patterns"].append(f"VCP({vcp_ratio:.2f})")
            bar["pivot_vcp"] = True
        
        # ---- Breakout Detection ----
        pchg = bar["pchg"]
        if bar["vr"] >= BREAKOUT_VR_MIN and pchg >= BREAKOUT_CHG_MIN and i >= 1:
            bar["patterns"].append(f"BO(v{bar['vr']:.1f})")
            bar["entry_signal"] = True
        
        # ---- Cheat Entry ----
        if bar["vr"] >= BREAKOUT_VR_MIN and pchg >= BREAKOUT_CHG_MIN and bar["vr"] < 1.5:
            bar["patterns"].append("CHEAT")
            bar["entry_signal"] = True
        
        # ---- PENNY-ANTE (tight prior -> gap breakout) ----
        if bar["vr"] >= 1.5 and pchg >= 3.0 and bar["rng_pct"] > 3.0:
            # Check if prior 5 bars were tight
            if i >= 5:
                tight_prior = all(
                    rmv[j] is not None and rmv[j] <= 20 
                    for j in range(i-5, i)
                )
                if tight_prior:
                    bar["patterns"].append("PENNY-ANTE")
                    bar["entry_signal"] = True
        
        # ---- Breakout Above Reaction High ----
        if pchg >= 2.0 and bar["vr"] >= 1.0 and i >= 10:
            max_prior = max(highs[i-10:i])
            if r["close"] > max_prior * 1.02:
                bar["patterns"].append("BO-REACT-HI")
        
        # ---- Gap-Up ----
        if i > 0:
            o_pct = (r["open"] / data[i-1]["close"] - 1) * 100
            if o_pct > 0.5 and r["close"] > r["open"] and r["open"] > data[i-1]["high"]:
                bar["patterns"].append("GAP-UP")
                bar["entry_signal"] = True
        
        # ---- Pivot-Relative Position ----
        # Find nearest prior pivot and how far above/below
        prior_pivots = [(idx, p) for idx, p in pivots if idx < i]
        if prior_pivots:
            nearest_pivot_idx, nearest_pivot_price = prior_pivots[-1]
            bar["prev_pivot_idx"] = nearest_pivot_idx
            bar["near_pivot"] = nearest_pivot_price
            bar["pivot_dist"] = (r["close"] / nearest_pivot_price - 1) * 100
            
            # Mark when price breaks above nearest pivot
            if r["close"] > nearest_pivot_price:
                bar["patterns"].append(f"ABOVE-PIVOT({nearest_pivot_price:.2f})")
                if pchg > 0 and bar["vr"] >= 1.0:
                    bar["patterns"].append("PIVOT-B/O")
                    bar["entry_signal"] = True
        
        # ---- Stage Determination ----
        all_above = (bar["above_sma20"] and bar["above_sma50"] and 
                     bar["above_sma150"] and bar["above_sma200"])
        all_below = (sma20[i] is not None and sma50[i] is not None and
                     sma150[i] is not None and sma200[i] is not None and
                     r["close"] < sma20[i] and r["close"] < sma50[i] and
                     r["close"] < sma150[i] and r["close"] < sma200[i])
        
        if all_above:
            bar["stage"] = "S2"
            bar["patterns"].append("STAGE2")
        elif all_below:
            bar["stage"] = "S4"
        elif bar["above_sma200"] and not all_above:
            bar["stage"] = "S1"
        else:
            bar["stage"] = "?"
        
        # ---- RMV Rank ----
        if rmv[i] is not None:
            if rmv[i] <= 10:
                bar["rmv_rank"] = "?"  # Ultra-tight
            elif rmv[i] <= 15:
                bar["rmv_rank"] = "?"  # Very tight
            elif rmv[i] <= 25:
                bar["rmv_rank"] = "?"  # Moderate
            elif rmv[i] <= 40:
                bar["rmv_rank"] = "?"  # Loose
            else:
                bar["rmv_rank"] = " "   # Wide
        else:
            bar["rmv_rank"] = " "
        
        # ---- Volume Drying (VDU component) ----
        if v20[i] is not None and v20[i] > 0:
            vr20 = r["volume"] / v20[i]
            if vr20 < 0.5 and bar["is_tight"]:
                bar["patterns"].append("VDU")
        
        # ---- Accumulation ----
        if pchg > 2.0 and bar["vr"] >= 1.3:
            bar["patterns"].append("ACCUM")
        
        # ---- Distribution ----
        if pchg < 0 and bar["vr"] >= 1.3:
            bar["patterns"].append("DIST")
        
        results.append(bar)
    
    # Handle final streak
    if len(current_streak) >= RMV_STREAK_MIN:
        tight_streaks.append(list(current_streak))
    
    # ---- Assign Streak IDs ----
    for sid, streak in enumerate(tight_streaks):
        for idx in streak:
            if idx < len(results):
                results[idx]["streak_id"] = sid
    
    return results, tight_streaks, pivots


# =============================================================================
# REPORTING
# =============================================================================

def print_report(results, tight_streaks, pivots, data, ticker):
    """Generate comprehensive report."""
    n = len(results)
    
    # ---- Summary stats ----
    tight_bars = sum(1 for r in results if r["is_tight"])
    entry_signals = [r for r in results if r["entry_signal"]]
    vcp_events = [r for r in results if "VCP" in str(r["patterns"])]
    
    print(f"\n  {'-'*60}")
    print(f"  RMV TIGHTNESS SUMMARY")
    print(f"  {'-'*60}")
    print(f"  Tight bars (RMV <= {RMV_TIGHT_THRESHOLD}):  {tight_bars} / {n} bars ({tight_bars/max(n,1)*100:.1f}%)")
    print(f"  Tight streaks (>={RMV_STREAK_MIN} bars):     {len(tight_streaks)}")
    print(f"  Entry signals:                {len(entry_signals)}")
    print(f"  VCP completions:              {len(vcp_events)}")
    print(f"  Major pivots:                 {len(pivots)}")
    
    # ---- Tight streak regions ----
    if tight_streaks:
        print(f"\n  {'-'*60}")
        print(f"  TIGHT STREAK REGIONS (RMV <= {RMV_TIGHT_THRESHOLD}, min {RMV_STREAK_MIN} bars)")
        print(f"  {'-'*60}")
        print(f"  {'#':<4} {'Start':<12} {'End':<12} {'Bars':<5} {'Avg RMV':<8} {'Range%':<8} {'Streak High':<12} {'Breakout?':<12}")
        print(f"  {'-'*60}")
        
        for sid, streak in enumerate(tight_streaks):
            start_idx = streak[0]
            end_idx = streak[-1]
            start_bar = results[start_idx]
            end_bar = results[end_idx]
            
            avg_rmv = sum(results[i]["rmv"] for i in streak if results[i]["rmv"] is not None) / len(streak)
            streak_high = max(data[i]["high"] for i in streak)
            
            # Check if a breakout followed within 10 bars
            breakout_found = False
            breakout_date = ""
            for lookahead in range(1, 11):
                bi = end_idx + lookahead
                if bi < n:
                    if results[bi]["entry_signal"]:
                        breakout_found = True
                        breakout_date = results[bi]["date"]
                        break
            
            bo_str = f"? {breakout_date}" if breakout_found else "--"
            
            # Average range during streak
            avg_rng = sum((data[i]["high"] - data[i]["low"]) / data[i]["close"] * 100 
                         for i in streak if data[i]["close"] > 0) / len(streak)
            
            print(f"  {sid:<4} {start_bar['date']:<12} {end_bar['date']:<12} "
                  f"{len(streak):<5} {avg_rmv:<8.1f} {avg_rng:<8.2f}% "
                  f"{streak_high:<12.2f} {bo_str:<12}")
    
    # ---- Entry Signals ----
    if entry_signals:
        print(f"\n  {'-'*60}")
        print(f"  ENTRY SIGNALS (Ranked by RMV Context)")
        print(f"  {'-'*60}")
        print(f"  {'Date':<12} {'Price':>8} {'Chg%':>7} {'VR':>6} {'Rng%':>6} "
              f"{'RMV':>5} {'Stage':<6} {'Type':<20} {'Prior Pivot':<15}")
        print(f"  {'-'*60}")
        
        # Filter to more significant entries
        significant = [r for r in entry_signals if r["vr"] >= 1.0]
        significant.sort(key=lambda x: x["date"])
        
        for r in significant:
            types = [p for p in r["patterns"] if any(x in p for x in 
                    ["BO(", "CHEAT", "PIVOT-B/O", "PENNY", "GAP-UP", "BO-REACT"])]
            type_str = types[0] if types else ";".join(r["patterns"][:2])
            
            pivot_info = f"?{r['near_pivot']:.2f}" if r["near_pivot"] else "--"
            
            print(f"  {r['date']:<12} {r['close']:>8.2f} {r['pchg']:>7.2f} "
                  f"{r['vr']:>6.2f} {r['rng_pct']:>6.2f} "
                  f"{r['rmv']:>5.1f} {r['stage']:<6} {type_str:<20} {pivot_info:<15}")
    
    # ---- VCP Sequences ----
    if vcp_events:
        print(f"\n  {'-'*60}")
        print(f"  VCP COMPLETIONS (Range Contraction)")
        print(f"  {'-'*60}")
        print(f"  {'Date':<12} {'Price':>8} {'RMV':>5} {'Stage':<6} {'Patterns':<40}")
        print(f"  {'-'*60}")
        for r in vcp_events[:20]:
            pat_str = "; ".join(r["patterns"][:4])
            print(f"  {r['date']:<12} {r['close']:>8.2f} {r['rmv']:>5.1f} "
                  f"{r['stage']:<6} {pat_str:<40}")
    
    # ---- RMV Distribution ----
    print(f"\n  {'-'*60}")
    print(f"  RMV DISTRIBUTION")
    print(f"  {'-'*60}")
    rmv_tiers = {"? (<=10)": 0, "? (<=15)": 0, "? (<=25)": 0, "? (<=40)": 0, ">40": 0}
    for r in results:
        if r["rmv"] is not None:
            if r["rmv"] <= 10: rmv_tiers["? (<=10)"] += 1
            elif r["rmv"] <= 15: rmv_tiers["? (<=15)"] += 1
            elif r["rmv"] <= 25: rmv_tiers["? (<=25)"] += 1
            elif r["rmv"] <= 40: rmv_tiers["? (<=40)"] += 1
            else: rmv_tiers[">40"] += 1
    for tier, count in rmv_tiers.items():
        bar_len = int(count / max(n, 1) * 50)
        print(f"    {tier:<12} {'#' * bar_len} {count} ({count/max(n,1)*100:.1f}%)")
    
    # ---- Daily RMV Calendar ----
    print(f"\n  {'-'*60}")
    print(f"  DETAILED BAR-BY-BAR (Tight streaks + Entry signals)")
    print(f"  {'-'*60}")
    print(f"  {'Date':<12} {'O':>7} {'H':>7} {'L':>7} {'C':>7} {'Chg':>7} "
          f"{'VR':>5} {'RMV':>5} {'Rk':<3} {'Stg':<4} {'Streak':<7} {'Pivot':<12} {'Patterns':<30}")
    print(f"  {'-'*100}")
    
    for i, r in enumerate(results):
        # Show: tight bars, entry signals, pivots, VCP
        show = (r["is_tight"] or r["entry_signal"] or r["is_pivot"] or 
                "VCP" in str(r["patterns"]) or "SQUAT" in str(r["patterns"]))
        if not show:
            continue
        
        streak_str = f"#{r['streak_id']}" if r["streak_id"] is not None else "--"
        
        # Pivot marker
        pivot_str = f"^ {r['pivot_high']:.2f}" if r["is_pivot"] else ""
        if not pivot_str and r["near_pivot"]:
            pivot_str = f"?{r['pivot_dist']:+.1f}%"
        
        pat = "; ".join(r["patterns"][:3]) if r["patterns"] else ""
        
        vol_str = f"{r['volume']/1e6:.1f}M" if r["volume"] > 1e6 else f"{r['volume']/1e3:.0f}K"
        
        print(f"  {r['date']:<12} {r['open']:>7.2f} {r['high']:>7.2f} {r['low']:>7.2f} {r['close']:>7.2f} "
              f"{r['pchg']:>7.2f} {r['vr']:>5.2f} {r['rmv']:>5.1f} {r['rmv_rank']:<3} "
              f"{r['stage']:<4} {streak_str:<7} {pivot_str:<12} {pat:<30}")
    
    # ---- ENTRY RECOMMENDATIONS ----
    print(f"\n\n  {'='*100}")
    print(f"  * RMV-GUIDED ENTRY RECOMMENDATIONS")
    print(f"  {'='*100}")
    
    # Find tight streaks that were followed by breakouts within 10 bars
    successes = []
    for sid, streak in enumerate(tight_streaks):
        end_idx = streak[-1]
        for lookahead in range(1, 15):
            bi = end_idx + lookahead
            if bi < n:
                if results[bi]["entry_signal"]:
                    successes.append({
                        "streak_id": sid,
                        "streak_end": results[end_idx]["date"],
                        "streak_high": max(data[j]["high"] for j in streak),
                        "streak_low": min(data[j]["low"] for j in streak),
                        "streak_avg_rmv": sum(results[j]["rmv"] for j in streak if results[j]["rmv"] is not None) / len(streak),
                        "entry_date": results[bi]["date"],
                        "entry_price": results[bi]["close"],
                        "entry_chg": results[bi]["pchg"],
                        "entry_vr": results[bi]["vr"],
                        "entry_type": [p for p in results[bi]["patterns"] if any(x in p for x in ["BO(", "CHEAT", "PIVOT-B/O", "PENNY", "GAP-UP", "BO-REACT"])],
                        "days_from_streak": lookahead
                    })
                    break
    
    if successes:
        print(f"\n  TIGHT STREAK -> BREAKOUT (RMV Anticipates Entry):")
        for s in successes:
            etype = s["entry_type"][0] if s["entry_type"] else "?"
            print(f"    * Streak #{s['streak_id']} ended {s['streak_end']} "
                  f"(avg RMV {s['streak_avg_rmv']:.1f}, range ?{s['streak_low']:.2f}-?{s['streak_high']:.2f})")
            print(f"      -> {s['days_from_streak']}d later: {etype} @ {s['entry_date']} "
                  f"?{s['entry_price']:.2f} ({s['entry_chg']:+.1f}%, VR {s['entry_vr']:.1f}x)")
    
    # Find tight streaks without breakouts (potential failure)
    failed_streaks = []
    for sid, streak in enumerate(tight_streaks):
        end_idx = streak[-1]
        has_breakout = False
        for lookahead in range(1, 15):
            bi = end_idx + lookahead
            if bi < n and results[bi]["entry_signal"]:
                has_breakout = True
                break
        if not has_breakout:
            failed_streaks.append(sid)
    
    if failed_streaks:
        print(f"\n  TIGHT STREAKS WITHOUT FOLLOW-THROUGH (no breakout within 15d):")
        for sid in failed_streaks[:5]:  # Show first 5
            streak = tight_streaks[sid]
            start_bar = results[streak[0]]
            end_bar = results[streak[-1]]
            print(f"    * Streak #{sid}: {start_bar['date']} -> {end_bar['date']} "
                  f"({len(streak)} bars, avg RMV {sum(results[j]['rmv'] for j in streak if results[j]['rmv'] is not None)/len(streak):.1f})")
    
    # ---- MINERVA-STYLE ENTRY SUMMARY ----
    print(f"\n\n  {'='*100}")
    print(f"  * ENTRY STRATEGY (Minervini: Buy tightness, not breakouts)")
    print(f"  {'='*100}")
    print(f"""
  WORKFLOW:
    1. SCAN: Look for RMV streaks (?/?) where price is consolidating near
       a prior pivot or above key SMAs
    2. WAIT: Don't buy the tight area -- wait for confirmation
       (volume + price clearing streak high)
    3. ENTRY: When price closes above streak high with VR >= 1.3:
       -> Pivot Breakout (above prior pivot)
       -> Cheat Entry (low volume breakout within base)
       -> VCP Resolution (range contraction complete)
    4. RISK: Place bracket stop at -4% (half) / -8% (half)
    5. RMV LEVELS: Draw horizontal lines at streak highs for visual reference
  """)
    
    print(f"\n  {'='*100}\n")


# =============================================================================
# VALIDATE AGAINST KNOWN APOLLO ENTRIES
# =============================================================================

def validate_known_entries(results, known_entries):
    """
    Check if the RMV+Pivot scanner catches known entry points.
    known_entries: list of (date, price, name) tuples
    """
    print(f"\n\n  {'='*100}")
    print(f"  * VALIDATION: KNOWN ENTRY POINTS")
    print(f"  {'='*100}")
    print(f"  {'Date':<12} {'Known Entry':<20} {'RMV':<6} {'Tight?':<8} {'Streak':<8} {'Near Pivot?':<15} {'Entry Signal':<15}")
    print(f"  {'-'*100}")
    
    for date, price, name in known_entries:
        # Find the bar closest to this date
        found = None
        for r in results:
            if r["date"] == date:
                found = r
                break
        if not found:
            # Try 1 day prior
            for r in results:
                if r["date"] >= date:
                    found = r
                    break
        
        if found:
            tight_str = "?" if found["is_tight"] else "[NO]"
            streak_str = f"#{found['streak_id']}" if found["streak_id"] is not None else "--"
            pivot_str = f"?{found['pivot_dist']:+.1f}%" if found["near_pivot"] else "--"
            sig_str = "?" if found["entry_signal"] else "[NO]"
            print(f"  {date:<12} {name:<20} {found['rmv']:<6.1f} {tight_str:<8} "
                  f"{streak_str:<8} {pivot_str:<15} {sig_str:<15}")
        else:
            print(f"  {date:<12} {name:<20} {'N/A':<6} {'N/A':<8} {'N/A':<8} {'N/A':<15} {'N/A':<15}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="RMV + Pivot Entry Scanner")
    parser.add_argument("csv", help="Path to OHLCV CSV file")
    parser.add_argument("--year", type=int, default=None, help="Year filter")
    parser.add_argument("--ticker", default="STOCK", help="Ticker symbol")
    parser.add_argument("--validate", nargs="*", help="Validate specific dates (date:price:name)")
    args = parser.parse_args()
    
    # Load data
    if not os.path.exists(args.csv):
        print(f"[err] File not found: {args.csv}")
        return
    
    data = load_csv(args.csv)
    print(f"  Loaded: {len(data)} bars from {args.csv}")
    
    if args.year:
        data = filter_year(data, args.year)
        print(f"  Filtered to {args.year}: {len(data)} bars")
    
    if len(data) < 50:
        print(f"[err] Need >=50 bars after filtering, got {len(data)}")
        return
    
    # Run analysis
    results, tight_streaks, pivots = analyze(data, ticker=args.ticker)
    
    # Print report
    print_report(results, tight_streaks, pivots, data, args.ticker)
    
    # Validate known entries if provided
    if args.validate:
        known = []
        for item in args.validate:
            parts = item.split(":")
            if len(parts) >= 3:
                known.append((parts[0], float(parts[1]), parts[2]))
        if known:
            validate_known_entries(results, known)
    
    # Export CSV of RMV analysis
    export_path = f"{args.ticker}_rmv_analysis.csv"
    with open(export_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Date","Open","High","Low","Close","Volume","RMV","RMV_Rank",
                        "Is_Tight","Streak_ID","Rng%","VR","Stage","Pivot_High",
                        "Pivot_Dist%","Pchg%","Patterns"])
        for r in results:
            writer.writerow([
                r["date"], r["open"], r["high"], r["low"], r["close"], r["volume"],
                f"{r['rmv']:.1f}" if r["rmv"] else "", r["rmv_rank"],
                1 if r["is_tight"] else 0,
                r["streak_id"] if r["streak_id"] is not None else "",
                f"{r['rng_pct']:.2f}", f"{r['vr']:.2f}", r["stage"],
                f"{r['pivot_high']:.2f}" if r["pivot_high"] else "",
                f"{r['pivot_dist']:+.1f}" if r.get('pivot_dist') is not None else "",
                f"{r['pchg']:.2f}",
                "; ".join(r["patterns"])
            ])
    print(f"\n  Exported: {export_path}")
    
    # Also export tight streak regions
    streak_path = f"{args.ticker}_tight_streaks.csv"
    with open(streak_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Streak_ID","Start_Date","End_Date","Bar_Count",
                        "Avg_RMV","Low_Price","High_Price","Mid_Price",
                        "Followed_By_Breakout","BO_Date","BO_Price"])
        for sid, streak in enumerate(tight_streaks):
            start_idx = streak[0]
            end_idx = streak[-1]
            avg_rmv = sum(results[i]["rmv"] for i in streak if results[i]["rmv"] is not None) / len(streak)
            low_p = min(data[i]["low"] for i in streak)
            high_p = max(data[i]["high"] for i in streak)
            mid_p = (low_p + high_p) / 2
            
            # Check for breakout
            bo_date = ""
            bo_price = ""
            has_bo = False
            for lookahead in range(1, 15):
                bi = end_idx + lookahead
                if bi < len(results) and results[bi]["entry_signal"]:
                    has_bo = True
                    bo_date = results[bi]["date"]
                    bo_price = f"{results[bi]['close']:.2f}"
                    break
            
            writer.writerow([
                sid, results[start_idx]["date"], results[end_idx]["date"],
                len(streak), f"{avg_rmv:.1f}", f"{low_p:.2f}", f"{high_p:.2f}", f"{mid_p:.2f}",
                1 if has_bo else 0, bo_date, bo_price
            ])
    
    print(f"  Exported: {streak_path}")


if __name__ == "__main__":
    main()

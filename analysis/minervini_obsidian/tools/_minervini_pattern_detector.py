"""
MINERVINI PATTERN DETECTOR — Universal Stock Analysis Engine
=============================================================
Detects ALL concepts from 'Think and Trade Like a Champion'
and 'Trade Like a Stock Market Wizard' on ANY stock's OHLCV data.

Usage:
    python _minervini_pattern_detector.py <path_to_csv> [year]

    <path_to_csv> : Path to OHLCV CSV file (supports standard and book formats)
    [year]        : Optional year filter (e.g., 2013). Default: show all years

Examples:
    python _minervini_pattern_detector.py ../data/GPRE_2013_ohlcv.csv 2013
    python _minervini_pattern_detector.py ../data/MU_recent_ohlcv.csv

Supported CSV Formats:
    Standard: Date,Open,High,Low,Close,Volume
    Book:     Date,Close,High,Low,Open,Volume (auto-detected by header)
    Yahoo:    Date,Open,High,Low,Close,Adj Close,Volume (auto-detected)

Patterns Detected (20+):
    See PATTERN_DEFINITIONS in the output header.
"""

import csv, os, sys
from datetime import datetime

# =============================================================================
# PATTERN DEFINITIONS (Minervini, 'Think and Trade Like a Champion')
# =============================================================================
PATTERN_HELP = """
PATTERN DETECTION SUMMARY
=========================
 1. SQUAT        → Red candle, close below midpoint, upper wick > body, body < 40% of range
 2. RECOVER      → Green candle recovery above squat day close (1-5 days after squat)
 3. BREAKOUT     → Price clears pivot/prior high with volume > 1.3x 50-day avg
 4. VCP-B/O      → VCP breakout: progressive 20-day range tightening + volume > 1.3x
 5. CHEAT        → Low-volume breakout within a base (VR < 1.5)
 6. FAILED-B/O   → Breakout that reverses and closes below pivot within 5 days
 7. CLIMAX       → Price + volume climax: VR ≥ 2.0 with close > 3% above open
 8. DISTRIBUTION → Down day with VR ≥ 1.3 (institutional selling)
 9. ACCUMULATION → Up day with VR ≥ 1.3 (institutional buying)
10. TIGHT        → Day range < 2% of close (low volatility contraction)
11. 3LL          → Failed follow-through: closes at lower lows for 3+ days
12. BRK-STOP     → Price broke below 20-day SMA (danger signal)
13. GAP-UP       → Open > prior high with volume (momentum entry)
14. CHEAT-ENTRY  → Tight staircase pattern within a base (w/ bracket stops)
15. BO-REACT-HI  → Price takes out a prior reaction high within the base
16. STAGE2       → Price above all SMAs (20/50/150/200) = uptrend confirmed
17. STAGE1-BASE  → Base-building: price coiling near 50/150 SMA, volume drying
18. STAGE4       → Price below 150 & 200 SMA = downtrend, avoid
19. TENNIS-BALL  → Squat → quick recovery within 2 days (strongest signal)
20. CUP-HANDLE   → Handle-forming: tight days (range < 1.5%) near base high
21. LOW-CHEAT    → Entry within a base during tight consolidation, below base high
22. BRACKET-STOP → Bracket stop levels automatically calculated at 4%/7%

DETECTION CRITERIA
==================
SQUAT (Figure 1-13, Page 39):
    pchg < 0                    # RED candle
    cl_mid_pct < -0.8           # Close in lower half of range
    upper_wick > body * 0.5      # Upper shadow > candle body
    body_pct < 40                # Body < 40% of total range

RECOVER (Tennis Ball Action):
    c[i] > o[i]                 # Green candle
    cl_mid_pct > 0               # Close above midpoint
    exists squat within 5 prior bars
    c[i] > squat_bar_close       # Price recovered above squat level

BREAKOUT (Pivot Breakout):
    Volume Ratio >= 1.3
    Change >= 2.0%
    Close at or near high of day

VCP (Volatility Contraction Pattern):
    Range progression over 20 days: wide → narrow
    Second half (days 11-20) avg range < 85% of first half (days 1-10)
    Volume drying as range contracts

FAILED BREAKOUT:
    Prior day was a breakout
    Next 1-5 days close below breakout pivot or make lower lows
    Volume on failure days >= 1.0x average

CLIMAX (Climax Top):
    Volume Ratio >= 2.0
    Price change >= 3.0%
    Stock extremely extended above moving averages

DISTRIBUTION (Institutional Selling):
    Close < prior close (down day)
    Volume >= 1.3x 50-day average

ACCUMULATION (Institutional Buying):
    Close > prior close (up day)
    Volume >= 1.3x 50-day average

LOW CHEAT ENTRY:
    Series of 5+ days with range < 2.5%
    Volume drying (VR < 0.7)
    Within 10% of base high
    Entry triggers when price breaks above tight area with volume

CUP WITH HANDLE:
    Base of at least 6 weeks
    Declines 12-35% from peak
    Handle forms with tight, drying range in upper 1/3 of base
    Buy point = handle high + 0.10
"""

# =============================================================================
# DATA LOADING
# =============================================================================

def load_csv(filepath):
    """Load any OHLCV CSV file, auto-detecting column format."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Skip empty lines
    lines = [l.strip() for l in lines if l.strip()]
    if not lines:
        return []
    
    # Read header to detect format
    header = lines[0].lower().split(',')
    
    # Check if this is a "book format" (Price,Close,High,Low,Open,Volume)
    is_book_format = False
    is_yahoo_format = False
    is_standard = False
    
    col_map = {}
    col_names = ['open', 'high', 'low', 'close', 'volume']
    
    # Try to match column names
    for i, h in enumerate(header):
        h = h.strip().lower()
        if h == 'price':
            # Book format: Price,Close,High,Low,Open,Volume
            is_book_format = True
            break
    
    if not is_book_format:
        # Check for Yahoo format (has Adj Close)
        if 'adj close' in header:
            is_yahoo_format = True
        else:
            is_standard = True
    
    # Parse data rows
    data = []
    start_row = 1
    for j in range(start_row, len(lines)):
        parts = lines[j].split(',')
        
        # Skip header-like rows (Ticker,Date, etc.)
        if len(parts) < 5:
            continue
        
        date_str = parts[0].strip()[:10]
        # Skip non-date rows
        try:
            datetime.strptime(date_str[:10], '%Y-%m-%d')
        except:
            # Try other date formats
            try:
                datetime.strptime(date_str[:10], '%m/%d/%Y')
            except:
                continue
        
        try:
            if is_book_format:
                # Book: Price,Close,High,Low,Open,Volume
                close = float(parts[1])
                high = float(parts[2])
                low = float(parts[3])
                open_ = float(parts[4])
                volume = int(float(parts[5])) if len(parts) > 5 else 0
            elif is_yahoo_format:
                # Yahoo: Date,Open,High,Low,Close,Adj Close,Volume
                open_ = float(parts[1])
                high = float(parts[2])
                low = float(parts[3])
                close = float(parts[4])
                volume = int(float(parts[6])) if len(parts) > 6 else 0
            else:
                # Standard: Date,Open,High,Low,Close,Volume
                open_ = float(parts[1])
                high = float(parts[2])
                low = float(parts[3])
                close = float(parts[4])
                volume = int(float(parts[5])) if len(parts) > 5 else 0
        except (ValueError, IndexError):
            continue
        
        data.append((date_str, open_, high, low, close, volume))
    
    return data


def filter_year(data, year):
    """Filter data to a specific year."""
    if year is None:
        return data
    return [d for d in data if d[0].startswith(str(year))]


def compute_sma(values, period):
    """Simple moving average."""
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i-period+1:i+1]) / period)
    return result


# =============================================================================
# PATTERN DETECTION FUNCTIONS
# =============================================================================

def detect_patterns(data, verbose=True):
    """
    Main pattern detection engine.
    Returns list of dicts with all detected patterns per bar.
    """
    n = len(data)
    if n < 50:
        print(f"  [warn] Only {n} bars — some patterns need 50+ bars (SMA50, VCP)")
        if n < 20:
            print(f"  [err] Need at least 20 bars for analysis")
            return []
    
    # Extract arrays
    dates = [d[0] for d in data]
    opens = [d[1] for d in data]
    highs = [d[2] for d in data]
    lows = [d[3] for d in data]
    closes = [d[4] for d in data]
    volumes = [d[5] for d in data]
    
    # Compute indicators
    sma10  = compute_sma(closes, 10)
    sma20  = compute_sma(closes, 20)
    sma50  = compute_sma(closes, 50)
    sma150 = compute_sma(closes, 150)
    sma200 = compute_sma(closes, 200)
    v20 = compute_sma(volumes, 20)
    v50 = compute_sma(volumes, 50)
    
    results = []
    
    # Track breakout events for failed breakout detection
    breakout_bars = {}
    
    for i in range(n):
        if i < 1:
            continue
        
        bar = {'date': dates[i], 'open': opens[i], 'high': highs[i],
               'low': lows[i], 'close': closes[i], 'volume': volumes[i]}
        
        # === BASIC CALCULATIONS ===
        pchg = (closes[i] / closes[i-1] - 1) * 100
        o_pct = (opens[i] / closes[i-1] - 1) * 100  # open gap%
        
        # VR only meaningful once we have 50 bars (for v50) or 20 bars (for v20)
        v50_available = v50[i] is not None and i >= 49
        v20_available = v20[i] is not None and i >= 19
        
        if v50_available and v50[i] > 0:
            vr = volumes[i] / v50[i]
        elif v20_available and v20[i] > 0:
            vr = volumes[i] / v20[i]
        else:
            vr = 0.0  # Not enough data yet
        
        if v20_available and v20[i] > 0:
            vr20 = volumes[i] / v20[i]
        else:
            vr20 = 0.0
        
        rng = highs[i] - lows[i]
        rng_pct = rng / closes[i] * 100 if closes[i] > 0 else 0
        midpoint = (highs[i] + lows[i]) / 2
        cl_mid_pct = (closes[i] - midpoint) / midpoint * 100 if midpoint > 0 else 0
        
        body = abs(closes[i] - opens[i])
        body_pct = body / rng * 100 if rng > 0 else 0
        upper_wick = highs[i] - max(opens[i], closes[i])
        lower_wick = min(opens[i], closes[i]) - lows[i]
        
        # Price relative to SMAs
        above_sma20 = sma20[i] is not None and closes[i] > sma20[i]
        above_sma50 = sma50[i] is not None and closes[i] > sma50[i]
        above_sma150 = sma150[i] is not None and closes[i] > sma150[i]
        above_sma200 = sma200[i] is not None and closes[i] > sma200[i]
        all_sma_above = (above_sma20 and above_sma50 and 
                         above_sma150 and above_sma200)
        all_sma_below = (sma20[i] is not None and sma50[i] is not None and
                         sma150[i] is not None and sma200[i] is not None and
                         closes[i] < sma20[i] and closes[i] < sma50[i] and
                         closes[i] < sma150[i] and closes[i] < sma200[i])
        
        # SMA distances
        sma20_dist = (closes[i] / sma20[i] - 1) * 100 if sma20[i] else 0
        sma50_dist = (closes[i] / sma50[i] - 1) * 100 if sma50[i] else 0
        
        patterns = []
        
        # ----- 1. SQUAT (Figure 1-13, Page 39) -----
        is_squat = (pchg < 0 and                  # RED candle
                    cl_mid_pct < -0.8 and          # Close below midpoint
                    upper_wick > body * 0.5 and    # Upper wick > body
                    body_pct < 40)                 # Body < 40% of range
        if is_squat:
            patterns.append("SQUAT")
        
        # ----- 2. RECOVER (Tennis Ball Action) -----
        if closes[i] > opens[i] and cl_mid_pct > 0:  # Green, above midpoint
            for lookback in range(1, 11):
                if i - lookback < 0:
                    break
                # Check if prior bar was a squat
                pbody = abs(closes[i-lookback] - opens[i-lookback])
                prng = highs[i-lookback] - lows[i-lookback]
                pbp = pbody / prng * 100 if prng > 0 else 0
                puw = highs[i-lookback] - max(opens[i-lookback], closes[i-lookback])
                pmid = (highs[i-lookback] + lows[i-lookback]) / 2
                pcm = (closes[i-lookback] - pmid) / pmid * 100 if pmid > 0 else 0
                
                p_squat = (closes[i-lookback] < opens[i-lookback] and
                           pcm < -0.8 and puw > pbody * 0.5 and pbp < 40)
                if p_squat and closes[i] > closes[i-lookback]:
                    tennis_ball = lookback <= 2
                    tag = "TENNIS-BALL" if tennis_ball else "RECOVER"
                    patterns.append(f"{tag}(d{lookback})")
                    break
        
        # ----- 3. TIGHT CONSOLIDATION -----
        if rng_pct < 2.0 and abs(pchg) < 1.5:
            # Check for consecutive tight days
            tight_count = 1
            for j in range(i-5, i):
                if j >= 0:
                    jrng = (highs[j] - lows[j]) / closes[j] * 100 if closes[j] > 0 else 0
                    jchg = (closes[j+1] / closes[j] - 1) * 100 if j+1 < n else 100
                    if jrng < 2.0 and abs(jchg) < 1.5:
                        tight_count += 1
                    else:
                        break
            if tight_count >= 3:
                patterns.append(f"TIGHT({tight_count}d)")
        
        # ----- 4. BREAKOUT (Pivot Breakout) -----
        is_breakout = False
        if vr >= 1.3 and pchg >= 2.0:
            is_breakout = True
            patterns.append(f"BREAKOUT(v{vr:.1f})")
            breakout_bars[i] = {'vr': vr, 'close': closes[i], 'pivot': closes[i-1]}
        
        # ----- 5. VCP BREAKOUT -----
        if is_breakout and i >= 20:
            prior_ranges = []
            for j in range(i-20, i):
                if closes[j] > 0:
                    prior_ranges.append((highs[j] - lows[j]) / closes[j] * 100)
            if prior_ranges:
                first_half = sum(prior_ranges[:10]) / 10 if len(prior_ranges) >= 10 else max(prior_ranges)
                second_half = sum(prior_ranges[-10:]) / 10 if len(prior_ranges) >= 10 else max(prior_ranges)
                if second_half < first_half * 0.85:
                    patterns.append("VCP-B/O")
                elif second_half < first_half * 0.70:
                    patterns.append("VCP-B/O(★tight)")
        
        # ----- 6. CHEAT (Low-volume breakout within base) -----
        if is_breakout and vr < 1.5:
            patterns.append("CHEAT-ENTRY")
        
        # ----- 7. FAILED BREAKOUT -----
        # Check if this bar violates a recent breakout
        for b_bar, b_info in list(breakout_bars.items()):
            if i - b_bar <= 5 and i != b_bar:
                if closes[i] < b_info['close'] * 0.98:  # Closed below breakout close
                    patterns.append(f"FAILED-B/O(d{i-b_bar})")
                    del breakout_bars[b_bar]
                    break
                elif i - b_bar >= 4 and closes[i] < closes[b_bar]:
                    patterns.append(f"FAILED-B/O(d{i-b_bar})")
                    del breakout_bars[b_bar]
                    break
        
        # ----- 8. CLIMAX (Climax Top) -----
        if vr >= 2.0 and pchg >= 3.0:
            patterns.append(f"CLIMAX(v{vr:.1f})")
        
        # ----- 9. DISTRIBUTION (Institutional Selling) -----
        if pchg < 0 and vr >= 1.3:
            # Consecutive distribution check
            dist_count = 1 if pchg < 0 and vr >= 1.3 else 0
            for j in range(i-4, i):
                if j >= 0:
                    jchg = (closes[j+1] / closes[j] - 1) * 100 if j+1 < n else 0
                    jvr = volumes[j] / v50[j] if v50[j] else 0
                    if jchg < 0 and jvr >= 1.0:
                        dist_count += 1
            if dist_count >= 3:
                patterns.append(f"DISTRIBUTION-{dist_count}LL")
            else:
                patterns.append("DISTRIBUTION")
        
        # ----- 10. ACCUMULATION (Institutional Buying) -----
        if pchg > 0 and vr >= 1.3:
            patterns.append(f"ACCUMULATION(v{vr:.1f})")
        
        # ----- 11. STAGE ANALYSIS -----
        if all_sma_above and sma150[i] is not None and sma200[i] is not None:
            # Check higher highs / higher lows
            if i >= 20:
                hh = max(highs[max(0,i-20):i])
                ll = min(lows[max(0,i-20):i])
                if closes[i] > sma50[i] and highs[i] > hh * 0.95:
                    if "STAGE2" not in patterns:
                        patterns.append("STAGE2")
        
        if all_sma_below and sma200[i] is not None and closes[i] < sma200[i] * 0.95:
            patterns.append("STAGE4-⚠")
        
        # ----- 12. TIGHT NEAR HIGH (Cup Handle / Low Cheat setup) -----
        if rng_pct < 1.5 and vr < 0.8 and sma50[i] is not None:
            # Near the high of a potential base (within 5%)
            if i >= 20:
                max_20 = max(highs[max(0,i-20):i+1])
                if closes[i] > max_20 * 0.95:
                    patterns.append("CUP-HANDLE")
                # Or potentially a low cheat setup if below ATH but tight
                base_high = max(highs[max(0,i-50):i+1])
                if closes[i] < base_high * 0.98 and rng_pct < 1.0:
                    patterns.append("LOW-CHEAT")
        
        # ----- 13. BRACKET STOPS (4%/7%) -----
        # These are always calculated for entry consideration
        bracket1 = closes[i] * 0.96  # Sell half at -4%
        bracket2 = closes[i] * 0.92  # Sell half at -8%
        patterns.append(f"BRK(${bracket1:.2f}/${bracket2:.2f})")
        
        # ----- 14. BREAKOUT ABOVE REACTION HIGH -----
        if pchg >= 2.0 and vr >= 1.0:
            if i >= 10:
                max_reaction = max(highs[max(0,i-10):i])
                if closes[i] > max_reaction * 1.02:
                    patterns.append("BO-REACT-HI")
        
        # ----- 15. GAP UP -----
        if o_pct > 0.5 and closes[i] > opens[i]:
            if i >= 1:
                prior_high = highs[i-1]
                if opens[i] > prior_high:
                    patterns.append("GAP-UP")
        
        # ----- 16. VIOLATION (Below 20-MA on volume) -----
        if not above_sma20 and sma20[i] is not None and vr >= 1.0:
            # Check if it broke below on volume
            if closes[i] < sma20[i] * 0.98:
                patterns.append("BRK-STOP")
        
        # ----- 17. PENNY ANTE (Tight days → gap breakout) -----
        if is_breakout and vr >= 1.5 and rng_pct > 3.0:
            # Check if prior 5 days were tight
            tight_prior = all(
                (highs[min(i-1, max(0,j))] - lows[min(i-1, max(0,j))]) / 
                closes[min(i-1, max(0,j))] * 100 < 2.5 
                for j in range(i-5, i) if j >= 0
            ) if i >= 5 else False
            if tight_prior:
                patterns.append("PENNY-ANTE")
        
        # ----- 18. PRICE EXTENSION (Extended from MA - climax risk) -----
        if sma50[i] is not None and sma50_dist > 30:
            patterns.append(f"EXTENDED({sma50_dist:.0f}%>50MA)")
        
        # Store results
        bar['v50_available'] = v50_available
        bar['pchg'] = pchg
        bar['vr'] = vr
        bar['sma20'] = sma20[i]
        bar['sma50'] = sma50[i]
        bar['sma150'] = sma150[i]
        bar['sma200'] = sma200[i]
        bar['rng_pct'] = rng_pct
        bar['cl_mid_pct'] = cl_mid_pct
        bar['body_pct'] = body_pct
        bar['uw'] = upper_wick
        bar['lw'] = lower_wick
        bar['above_sma20'] = above_sma20
        bar['above_sma50'] = above_sma50
        bar['above_sma150'] = above_sma150
        bar['above_sma200'] = above_sma200
        bar['patterns'] = patterns
        bar['bracket_stop_1'] = bracket1
        bar['bracket_stop_2'] = bracket2
        
        results.append(bar)
    
    return results


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================

def print_results(data, results, year_label, show_all=False):
    """Print formatted analysis table."""
    n = len(results)
    
    # Count total patterns detected
    all_patterns = []
    for r in results:
        for p in r['patterns']:
            cat = p.split('(')[0]
            all_patterns.append(cat)
    
    from collections import Counter
    pattern_counts = Counter(all_patterns)
    
    # ===== HEADER =====
    print(f"\n{'='*160}")
    print(f"  MINERVINI PATTERN DETECTOR — RESULTS")
    print(f"  Period: {year_label}")
    print(f"  Bars analyzed: {n}")
    print(f"  Patterns detected: {sum(pattern_counts.values())}")
    print(f"{'='*160}")
    
    # ===== PATTERN COUNT SUMMARY =====
    if pattern_counts:
        print(f"\n  PATTERN SUMMARY:")
        print(f"  {'-'*60}")
        priority_patterns = ['SQUAT', 'TENNIS-BALL', 'RECOVER', 'BREAKOUT', 'VCP-B/O', 
                           'FAILED-B/O', 'CLIMAX', 'DISTRIBUTION', 'ACCUMULATION',
                           'CHEAT-ENTRY', 'STAGE2', 'STAGE4-⚠', 'CUP-HANDLE', 
                           'LOW-CHEAT', 'TIGHT', 'PENNY-ANTE', 'GAP-UP',
                           'BRK-STOP', 'BO-REACT-HI', 'EXTENDED']
        for p in priority_patterns:
            if p in pattern_counts:
                print(f"    {p:<18} → {pattern_counts[p]:>3} occurrences")
        other = {k: v for k, v in pattern_counts.items() if k not in priority_patterns}
        for p, c in sorted(other.items(), key=lambda x: -x[1]):
            print(f"    {p:<18} → {c:>3} occurrences")
    
    # ===== DETAILED TABLE =====
    print(f"\n  {'Date':<12} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'Chg%':>7} {'Vol':>9} "
          f"{'VR':>6} {'SMA20':>8} {'SMA50':>8} {'SMA150':>8} {'Rng%':>5} {'Cl-Mid%':>6}  Pattern Details")
    print(f"  {'-'*160}")
    
    for i, r in enumerate(results):
        show = show_all
        if r['patterns']:
            # Always show bars with these critical patterns
            critical = ['SQUAT', 'BREAKOUT', 'VCP-B/O', 'FAILED-B/O', 'CLIMAX',
                       'DISTRIBUTION-3LL', 'TENNIS-BALL', 'RECOVER', 'STAGE2',
                       'GAP-UP', 'PENNY-ANTE', 'BRK-STOP', 'CHEAT-ENTRY', 'BO-REACT-HI']
            if any(c in str(r['patterns']) for c in critical):
                show = True
            # Also show TIGHT with count >= 5
            if any('TIGHT(' in p and int(p.split('(')[1].split('d')[0]) >= 5 for p in r['patterns']):
                show = True
        
        if not show and i % 20 != 0:
            continue
        
        if r['sma20'] is None:
            sma20_s = " —  "
            sma50_s = " —  "
            sma150_s = " —    "
        else:
            sma20_s = f"{r['sma20']:>8.2f}"
            sma50_s = f"{r['sma50']:>8.2f}" if r['sma50'] else "   —  "
            sma150_s = f"{r['sma150']:>8.2f}" if r['sma150'] else "    —    "
        
        # Strip BRK from main pattern display to show it separately
        main_patterns = [p for p in r['patterns'] if not p.startswith('BRK(')]
        bracket_stop = [p for p in r['patterns'] if p.startswith('BRK(')]
        
        pat_str = "; ".join(main_patterns) if main_patterns else ""
        brk_str = f" {bracket_stop[0]}" if bracket_stop else ""
        
        vol_str = f"{r['volume']:>9,d}" if r['volume'] < 999999999 else f"{r['volume']/1e6:>9.1f}M"
        
        print(f"  {r['date']:<12} {r['open']:>8.2f} {r['high']:>8.2f} {r['low']:>8.2f} {r['close']:>8.2f} "
              f"{r['pchg']:>7.2f} {vol_str} {r['vr']:>6.2f} {sma20_s} {sma50_s} {sma150_s} "
              f"{r['rng_pct']:>5.2f} {r['cl_mid_pct']:>6.2f}  {pat_str:<45}{brk_str}")
    
    print(f"  {'-'*160}")
    print()


def print_buy_point_summary(results):
    """Summarize the best buy point candidates."""
    print(f"\n  === POTENTIAL BUY POINTS (Ranked) ===")
    print(f"  {'Date':<12} {'Type':<20} {'Price':>8} {'VR':>6} {'Stop4%':>8} {'Stop8%':>8} {'Risk':>6}")
    print(f"  {'-'*75}")
    
    candidates = []
    for r in results:
        has_buy_pattern = any(p in str(r['patterns']) for p in 
            ['BREAKOUT', 'VCP-B/O', 'CHEAT-ENTRY', 'BO-REACT-HI', 'PENNY-ANTE', 'GAP-UP'])
        if has_buy_pattern:
            buy_type = [p for p in r['patterns'] if any(x in p for x in 
                        ['BREAKOUT', 'VCP-B/O', 'CHEAT-ENTRY', 'BO-REACT-HI', 'PENNY-ANTE', 'GAP-UP'])]
            candidates.append({
                'date': r['date'],
                'type': buy_type[0] if buy_type else '?',
                'price': r['close'],
                'vr': r['vr'],
                'stop4': r['close'] * 0.96,
                'stop8': r['close'] * 0.92,
                'risk': (r['close'] * 0.96) / r['close'] - 1  # primary stop risk
            })
    
    for c in candidates[:10]:
        print(f"  {c['date']:<12} {c['type']:<20} {c['price']:>8.2f} {c['vr']:>6.2f} "
              f"{c['stop4']:>8.2f} {c['stop8']:>8.2f} {c['risk']*100:>5.1f}%")
    print()


def print_vcp_summary(results):
    """Show VCP contraction sequences."""
    print(f"\n  === VCP (Volatility Contraction Pattern) Sequences ===")
    
    # Look for VCP-like tightening in 20-day windows
    for i in range(20, len(results)):
        rngs = [results[j]['rng_pct'] for j in range(i-20, i)]
        if max(rngs) > 5 and min(rngs[-5:]) < 2.5:
            # Potential VCP completion
            max_r = max(rngs)
            min_r = min(rngs[-5:])
            contract_pct = (1 - min_r / max_r) * 100 if max_r > 0 else 0
            if contract_pct > 50:  # At least 50% contraction
                # Check if followed by a breakout
                forward = 10
                for j in range(i, min(len(results), i+forward)):
                    if 'BREAKOUT' in str(results[j]['patterns']):
                        print(f"  VCP @ {results[i]['date']}: {max_r:.1f}%→{min_r:.1f}% "
                              f"({contract_pct:.0f}% contraction) → "
                              f"BO @ {results[j]['date']} ${results[j]['close']:.2f}")
                        break
    print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print(__doc__)
        print(PATTERN_HELP)
        print("\nAvailable CSV files:")
        # List CSVs in the data directory
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        book_dir = os.path.join(data_dir, "book_stock_images")
        if os.path.exists(data_dir):
            for f in sorted(os.listdir(data_dir)):
                if f.endswith('.csv'):
                    print(f"  data/{f}")
        if os.path.exists(book_dir):
            for f in sorted(os.listdir(book_dir)):
                if f.endswith('.csv'):
                    print(f"  data/book_stock_images/{f}")
        return
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        # Try relative to tools directory
        tools_dir = os.path.dirname(__file__)
        alt_path = os.path.join(tools_dir, filepath)
        if os.path.exists(alt_path):
            filepath = alt_path
        else:
            print(f"[err] File not found: {filepath}")
            return
    
    year = None
    if len(sys.argv) >= 3:
        try:
            year = int(sys.argv[2])
        except ValueError:
            print(f"[warn] Invalid year: {sys.argv[2]}, analyzing all data")
    
    # Load and analyze
    print(f"\n  -> Loading: {os.path.basename(filepath)}")
    data = load_csv(filepath)
    print(f"  -> Bars loaded: {len(data)}")
    
    if year:
        data = filter_year(data, year)
        print(f"  -> Filtered to: {year} ({len(data)} bars)")
    
    if not data:
        print("  -> No data to analyze")
        return
    
    year_label = f"{data[0][0][:4]} to {data[-1][0][:4]}" if not year else str(year)
    price_range = f"${min(d[3] for d in data):.2f} to ${max(d[2] for d in data):.2f}"
    returns = (data[-1][4] / data[0][1] - 1) * 100
    print(f"  -> Price range: {price_range}")
    print(f"  -> Return: {returns:+.1f}%")
    
    # Detect patterns
    results = detect_patterns(data)
    
    if not results:
        return
    
    # Print results
    print_results(data, results, year_label)
    print_buy_point_summary(results)
    print_vcp_summary(results)
    
    # Final summary
    total_events = sum(len(r['patterns']) for r in results)
    print(f"\n  {'='*160}")
    print(f"  ANALYSIS COMPLETE: {len(results)} bars analyzed, {total_events} pattern events detected")
    print(f"  {'='*160}")
    print(f"""
  NEXT STEPS:
    - Review SQUAT / TENNIS-BALL / RECOVER sequences for entry signals
    - Check VCP-B/O patterns for tightening + volume confirmation
    - Use BRACKET STOPS (4%/7%) to manage risk on entries
    - Verify STAGE2 context (all SMAs above) before taking entries
    - Avoid STAGE4 (all SMAs below) — wait for STAGE1 base building
  """)


if __name__ == "__main__":
    main()

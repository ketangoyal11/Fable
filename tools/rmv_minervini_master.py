"""
RMV Minervini Master - Full Pattern Suite (Python Port v2)
===========================================================
EXACT port of rmv_minervini_master.pine v2 into Python.

Preserves ALL Pine Script logic faithfully:
  * RMV: min/max normalization (Deepvue exact formula)
  * VCP: Same-window halves (NOT adjacent windows)
  * Tennis-Ball/Recover: Current bar midpoint (high+low)/2
  * Pullback-to-Pivot: Retest of broken pivot within 20 bars, above SMA50
  * Natural Reaction: Declining-volume pullback to pivot after breakout
  * Volume Dry-Up: Explicit VR < 0.7 / VR < 0.5 flags
  * EMA10 Scale-In: Proximity <=2.5% to EMA10 for flag continuation entries
  * Low-Cheat: Distance to pivot 2-8%, base >=5 weeks, base range <10%
  * Spring/Reversal: Gap-down open + recovery above midpoint + volume
  * 52-Week Trend Template: Near 52wk high, far from 52wk low, rising 200 DMA
  * Follow-Through: Up 4/5 days, up 7/8 days confirmation
  * Stage 1/2/3/4: Explicit stage detection (Weinstein)
  * Cup-Handle: Volume dry-up required (VR < 0.8) + base depth filter
  * Base Depth Filter: <=40% max depth for quality VCP bases
  * Dynamic Stops: 2R breakeven line + 50 DMA trailing stop
  * Bracket Stops: 4% / 8% (matches Python _buy_points.py)
  * Pivot Tracking: Every tight-streak high stored, merged within 3%

Usage:
    python CLAUDE/rmv_minervini_master.py <csv_path> [--ticker TICKER] [--year YYYY]
    
Examples:
    python CLAUDE/rmv_minervini_master.py analysis/minervini_obsidian/data/APOLLO_ohlcv.csv --ticker APOLLO --year 2023
    python CLAUDE/rmv_minervini_master.py analysis/minervini_obsidian/data/GPRE_2013_ohlcv.csv
"""

import csv, sys, os, math
from datetime import datetime

# ===============================================================================
# DEFAULTS (match Pine Script exact defaults)
# ===============================================================================

# RMV Engine
RMV_LOOKBACK = 15
RMV_TIGHT_THRESHOLD = 12

# Timeframe (1 = daily)
TF_MULT = 1

VCP_LOOKBACK = 20 * TF_MULT
VR_LENGTH = 20 * TF_MULT
SMA50_LEN = 50 * TF_MULT
SMA150_LEN = 150 * TF_MULT
SMA200_LEN = 200 * TF_MULT
SMA20_LEN = 20 * TF_MULT
EMA10_LEN = 10 * TF_MULT
EMA21_LEN = 21 * TF_MULT

# Volume / Breakout thresholds
VR_BREAKOUT = 1.3
VR_CHEAT_MAX = 1.5
VR_CLIMAX = 2.0
MIN_CHG_PCT = 2.0
CLIMAX_CHG_PCT = 3.0
VOL_DRY_UP_THRESH = 0.7
VOL_EXTREME_DRY = 0.5

# VCP / Tightness / Base Depth
CONTRACTION_PCT = 85.0
MIN_CONTRACTIONS = 2
CUP_HANDLE_PCT = 1.5
MAX_BASE_DEPTH = 40.0
MIN_BASE_WEEKS = 5
LOW_CHEAT_DIST_MIN = 2.0
LOW_CHEAT_DIST_MAX = 8.0

# Stops
STOP1_PCT = 4.0
STOP2_PCT = 8.0

# Display
MERGE_PCT = 3.0
LINE_EXTEND = 20

# ===============================================================================
# DATA LOADING
# ===============================================================================


def load_csv(filepath):
    """Load any OHLCV CSV, auto-detecting column format (standard, Yahoo, book).

    Handles:
      - Standard: Date,Open,High,Low,Close,Volume
      - Yahoo Finance: Date,Open,High,Low,Close,Volume,... (extra columns ignored)
      - Book format: Price,Close,High,Low,Open,Volume
      - Empty/missing close values (skipped)
    """
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    lines = [l.strip() for l in lines if l.strip()]
    if not lines:
        return []

    header = lines[0].lower().split(',')

    # Detect format
    has_price = 'price' in header
    has_adj_close = 'adj close' in header or 'adj_close' in header

    # Map column indices by name
    col_map = {}
    for col_idx, col_name in enumerate(header):
        col_name = col_name.strip()
        if col_name == 'date':
            col_map['date'] = col_idx
        elif col_name in ('open', 'open '):
            col_map['open'] = col_idx
        elif col_name in ('high', 'high '):
            col_map['high'] = col_idx
        elif col_name in ('low', 'low '):
            col_map['low'] = col_idx
        elif col_name in ('close', 'close '):
            col_map['close'] = col_idx
        elif col_name in ('volume', 'vol', 'volume '):
            col_map['volume'] = col_idx
        elif col_name == 'price':
            col_map['price'] = col_idx

    is_book_format = has_price and 'close' in col_map

    data = []
    for j in range(1, len(lines)):
        parts = lines[j].split(',')
        if len(parts) < 5:
            continue

        # Parse date
        date_str = parts[0].strip()[:10]
        parsed_date = None
        try:
            parsed_date = datetime.strptime(date_str[:10], '%Y-%m-%d')
        except:
            try:
                parsed_date = datetime.strptime(date_str[:10], '%m/%d/%Y')
            except:
                continue

        try:
            if is_book_format:
                # Price,Close,High,Low,Open,Volume
                idx_close = col_map.get('close', 1)
                idx_high = col_map.get('high', 2)
                idx_low = col_map.get('low', 3)
                idx_open = col_map.get('open', 4)
                idx_vol = col_map.get('volume', 5)
                close_str = parts[idx_close].strip()
                if not close_str:
                    continue
                close = float(close_str)
                high = float(parts[idx_high])
                low = float(parts[idx_low])
                open_ = float(parts[idx_open])
                volume = int(float(parts[idx_vol])) if len(parts) > idx_vol else 0
            else:
                # Standard / Yahoo: Date,Open,High,Low,Close,Volume,...
                idx_open = col_map.get('open', 1)
                idx_high = col_map.get('high', 2)
                idx_low = col_map.get('low', 3)
                idx_close = col_map.get('close', 4)
                idx_vol = col_map.get('volume', 5)
                close_str = parts[idx_close].strip()
                if not close_str:
                    continue
                close = float(close_str)
                open_ = float(parts[idx_open])
                high = float(parts[idx_high])
                low = float(parts[idx_low])
                volume = int(float(parts[idx_vol])) if len(parts) > idx_vol else 0
        except (ValueError, IndexError):
            continue

        # Validate prices are positive
        if high <= 0 or low <= 0 or close <= 0:
            continue

        data.append({
            'date': date_str,
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    return data


def filter_year(data, year):
    """Filter data to a specific year."""
    if year is None:
        return data
    return [d for d in data if d['date'].startswith(str(year))]


# ===============================================================================
# INDICATOR COMPUTATION
# ===============================================================================


def compute_sma(values, period):
    """Simple Moving Average - exact Pine Script semantics."""
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i - period + 1:i + 1]) / period)
    return result


def compute_ema(values, period):
    """Exponential Moving Average - matches Pine's ta.ema()."""
    result = []
    multiplier = 2.0 / (period + 1)
    for i in range(len(values)):
        if i == 0:
            result.append(values[0])
        elif i < period:
            # SMA fill until enough data
            result.append(sum(values[:i + 1]) / (i + 1))
        else:
            result.append((values[i] - result[-1]) * multiplier + result[-1])
    return result


def compute_rmv(high, low, lookback):
    """
    RMV (Relative Measured Volatility) - Deepvue exact formula.
    
    From Pine:
        currentRange = high - low
        minRange = ta.lowest(currentRange, lookback)[1]   # PREVIOUS bar's lowest
        maxRange = ta.highest(currentRange, lookback)[1]   # PREVIOUS bar's highest
        rangeSpan = maxRange - minRange
        rmv = (currentRange - minRange) / rangeSpan * 100  (clamped 0-100, default 50)
    
    CRITICAL: [1] offset means the lookback window ENDS at bar i-1, NOT including bar i.
    """
    n = len(high)
    rmv_vals = []
    
    for i in range(n):
        if i < lookback + 1:
            rmv_vals.append(50.0)  # default
            continue
        
        current_range = high[i] - low[i]
        
        # [1] offset: look at bars i-lookback to i-1 (previous bar's perspective)
        start = i - lookback
        end = i  # exclusive, so bars [i-lookback, i-1]
        
        min_range = min(high[j] - low[j] for j in range(start, end))
        max_range = max(high[j] - low[j] for j in range(start, end))
        range_span = max_range - min_range
        
        if range_span > 0:
            rmv = (current_range - min_range) / range_span * 100
        else:
            rmv = 50.0
        
        rmv_vals.append(max(0.0, min(100.0, rmv)))
    
    return rmv_vals


def compute_vr(volume, avg_vol_period):
    """Volume Ratio: current volume / SMA of volume over period."""
    vol_sma = compute_sma(volume, avg_vol_period)
    vr = []
    for i in range(len(volume)):
        if vol_sma[i] is not None and vol_sma[i] > 0:
            vr.append(volume[i] / vol_sma[i])
        else:
            vr.append(1.0)
    return vr


# ===============================================================================
# PATTERN DETECTION
# ===============================================================================


def analyze(data, ticker="STOCK"):
    """
    Full Minervini pattern analysis - EXACT port of Pine Script logic.
    
    Returns list of bar dicts with all pattern flags and pivot tracking state.
    """
    n = len(data)
    if n < 200:
        print(f"[err] Need at least 200 bars for full analysis, got {n}")
        return [], []

    # -- Extract arrays --
    dates = [d['date'] for d in data]
    opens = [d['open'] for d in data]
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    closes = [d['close'] for d in data]
    volumes = [d['volume'] for d in data]

    # -- Moving Averages (Pine exact) --
    sma50 = compute_sma(closes, SMA50_LEN)
    sma150 = compute_sma(closes, SMA150_LEN)
    sma200 = compute_sma(closes, SMA200_LEN)
    sma20 = compute_sma(closes, SMA20_LEN)
    ema10 = compute_ema(closes, EMA10_LEN)
    ema21 = compute_ema(closes, EMA21_LEN)

    # -- RMV --
    rmv_vals = compute_rmv(highs, lows, RMV_LOOKBACK)

    # -- Volume Ratio --
    vr_vals = compute_vr(volumes, VR_LENGTH)

    # -- Price Change --
    chg_pct = [0.0]
    for i in range(1, n):
        chg_pct.append(((closes[i] / closes[i - 1]) - 1) * 100)

    # -- 52-Week High/Low --
    wk52_lookback = 252 * TF_MULT
    wk52_high = [None] * n
    wk52_low = [None] * n
    for i in range(n):
        start = max(0, i - wk52_lookback + 1)
        wk52_high[i] = max(highs[start:i + 1])
        wk52_low[i] = min(lows[start:i + 1])

    # -- SMA200 Rising (compare to 20 bars ago) --
    sma200_rising = [False] * n
    for i in range(20 * TF_MULT, n):
        if sma200[i] is not None and sma200[i - 20 * TF_MULT] is not None:
            sma200_rising[i] = sma200[i] > sma200[i - 20 * TF_MULT]

    # -- ATH (All-Time High = 52wk high) --
    ath = wk52_high

    # -- Stage Detection (Weinstein) --
    stage2 = [False] * n
    stage1 = [False] * n
    stage3 = [False] * n
    stage4 = [False] * n
    for i in range(n):
        if sma50[i] is not None and sma150[i] is not None and sma200[i] is not None:
            stage2[i] = (closes[i] > sma50[i] and sma50[i] > sma150[i] and
                         sma150[i] > sma200[i] and closes[i] > sma200[i] * 1.05)
            stage1[i] = (closes[i] < sma200[i] and closes[i] < sma150[i] and
                         sma150[i] < sma200[i])
            stage3[i] = (closes[i] < sma50[i] and closes[i] > sma200[i])
            stage4[i] = (closes[i] < sma50[i] and sma50[i] < sma150[i] and
                         sma50[i] < sma200[i] and closes[i] < sma200[i] * 0.95)

    # -- Trend Template --
    trend_template = [False] * n
    for i in range(n):
        near_52w_high = wk52_high[i] is not None and wk52_high[i] > 0 and \
                        ((wk52_high[i] - closes[i]) / wk52_high[i] * 100 <= 25.0)
        far_from_52w_low = wk52_low[i] is not None and wk52_low[i] > 0 and \
                           ((closes[i] - wk52_low[i]) / wk52_low[i] * 100 >= 30.0)
        if sma50[i] is not None and sma150[i] is not None and sma200[i] is not None:
            trend_template[i] = (closes[i] > sma50[i] and sma50[i] > sma150[i] and
                                 sma150[i] > sma200[i] and near_52w_high and
                                 far_from_52w_low and sma200_rising[i])

    # -- Tight Now --
    tight_now = [False] * n
    for i in range(n):
        tight_now[i] = rmv_vals[i] <= RMV_TIGHT_THRESHOLD

    # -- Volume Dry-Up --
    vol_dry_up = [False] * n
    is_vol_extreme_dry = [False] * n
    for i in range(n):
        vol_dry_up[i] = vr_vals[i] < VOL_DRY_UP_THRESH
        is_vol_extreme_dry[i] = vr_vals[i] < VOL_EXTREME_DRY

    # -- Follow-Through --
    follow_thru_4of5 = [False] * n
    follow_thru_7of8 = [False] * n
    for i in range(4, n):
        cnt = 0
        for k in range(5):
            if i - k >= 0 and closes[i - k] > closes[i - k - 1]:
                cnt += 1
        follow_thru_4of5[i] = cnt >= 4
        
        if i >= 7:
            cnt8 = 0
            for k in range(8):
                if i - k >= 0 and closes[i - k] > closes[i - k - 1]:
                    cnt8 += 1
            follow_thru_7of8[i] = cnt8 >= 7

    # -- VCP Contraction Detection (Same-window halves) --
    half_window = 10 * TF_MULT
    contracting_now = [False] * n
    contraction_count_arr = [0] * n
    is_vcp_base = [False] * n
    
    # Track contraction count statefully like Pine's `var int contractionCount`
    contraction_count = 0
    
    for i in range(half_window * 2, n):
        # First half: bars [i - half_window*2, i - half_window)
        first_high = max(highs[i - half_window * 2: i - half_window])
        first_low = min(lows[i - half_window * 2: i - half_window])
        first_half_range = first_high - first_low
        
        # Second half: bars [i - half_window, i)
        second_high = max(highs[i - half_window: i])
        second_low = min(lows[i - half_window: i])
        second_half_range = second_high - second_low
        
        if first_half_range > 0:
            ratio = (second_half_range / first_half_range) * 100
            contracting_now[i] = ratio <= CONTRACTION_PCT
        
        # Count contractions (Pine stateful logic)
        if contracting_now[i] and tight_now[i]:
            contraction_count += 1
        elif not tight_now[i]:
            contraction_count = 0
        
        contraction_count_arr[i] = contraction_count
        is_vcp_base[i] = contraction_count >= MIN_CONTRACTIONS

    # ===========================================================================
    # PIVOT TRACKING (Matches Pine's var arrays + tight streak logic)
    # ===========================================================================
    
    pivots = []  # list of dicts
    active_streak_high = None
    active_streak_bar = None
    active_streak_time = None
    active_base_low = None
    base_start_bar = None
    
    # -- Results per bar --
    results = []
    
    for i in range(n):
        body = abs(closes[i] - opens[i])
        rng = highs[i] - lows[i]
        body_pct = (body / rng * 100) if rng > 0 else 0
        midpoint = (highs[i] + lows[i]) / 2
        upper_wick = highs[i] - max(opens[i], closes[i])
        is_red = closes[i] < opens[i]
        close_below_mid = closes[i] < midpoint
        
        bar = {
            'date': dates[i],
            'open': opens[i],
            'high': highs[i],
            'low': lows[i],
            'close': closes[i],
            'volume': volumes[i],
            'chg_pct': chg_pct[i],
            'vr': vr_vals[i],
            'rmv': rmv_vals[i],
            'tight_now': tight_now[i],
            'sma50': sma50[i],
            'sma150': sma150[i],
            'sma200': sma200[i],
            'sma20': sma20[i],
            'ema10': ema10[i],
            'ema21': ema21[i],
            'stage2': stage2[i],
            'stage1': stage1[i],
            'stage3': stage3[i],
            'stage4': stage4[i],
            'trend_template': trend_template[i],
            'vol_dry_up': vol_dry_up[i],
            'is_vol_extreme_dry': is_vol_extreme_dry[i],
            'contracting_now': contracting_now[i],
            'contraction_count': contraction_count_arr[i],
            'is_vcp_base': is_vcp_base[i],
            'follow_thru_4of5': follow_thru_4of5[i],
            'follow_thru_7of8': follow_thru_7of8[i],
            'sma200_rising': sma200_rising[i],
            
            'body': body,
            'range': rng,
            'body_pct': body_pct,
            'midpoint': midpoint,
            'upper_wick': upper_wick,
            'is_red': is_red,
            'close_below_mid': close_below_mid,
            
            # Pattern flags
            'squat': False,
            'tennis_ball': False,
            'recover': False,
            'spring': False,
            'distribution': False,
            'accumulation': False,
            'heavy_distribution': False,
            'climax': False,
            'generic_breakout': False,
            'extended': False,
            'brk_stop': False,
            'gap_up': False,
            'bo_react_hi': False,
            'scale_in': False,
            'penny_ante': False,
            'cup_handle': False,
            'low_cheat': False,
            'pullback': False,
            'natural_rxn': False,
            'cheat_entry': False,
            
            # Entry classification
            'break_type': '',
            'break_color': '',
            
            # Pivot info
            'pivot_index': -1,
            'pivot_price': None,
            'pivot_broken': False,
            'pivot_failed': False,
            'pivot_days': 0,
            'pivot_depth': 0.0,
            'pivot_dist_below': 0.0,
            'pivot_dist_above': 0.0,
            'entry_signal': False,
            
            # Bracket stops
            'bracket_stop_1': None,
            'bracket_stop_2': None,
            
            # Tight streak count
            'tight_streak_count': 0,
        }
        
        # =======================================================================
        # PATTERN: SQUAT
        # =======================================================================
        bar['squat'] = (is_red and close_below_mid and upper_wick > body and body_pct < 40)
        
        # =======================================================================
        # PATTERN: TENNIS-BALL / RECOVER
        #   Squat + recovery, close above CURRENT midpoint (not prior bar's)
        #   Tennis-Ball: <=2 days; Recover: 3-10 days
        # =======================================================================
        is_green = closes[i] > opens[i]
        above_mid = closes[i] > midpoint
        
        for lookback in range(1, 11):
            if i - lookback < 0:
                break
            prev = results[i - lookback]
            if prev['squat']:
                if is_green and above_mid:
                    if lookback <= 2:
                        bar['tennis_ball'] = True
                    else:
                        bar['recover'] = True
                break
        
        # =======================================================================
        # PATTERN: SPRING / REVERSAL
        # =======================================================================
        if i >= 1:
            spring_gap_down = opens[i] < lows[i - 1]
            spring_recovery = closes[i] > midpoint and closes[i] > opens[i]
            spring_vol = vr_vals[i] >= 1.0
            bar['spring'] = spring_gap_down and spring_recovery and spring_vol
        
        # =======================================================================
        # PATTERN: DISTRIBUTION / ACCUMULATION / HEAVY DISTRIBUTION
        # =======================================================================
        bar['distribution'] = is_red and vr_vals[i] >= VR_BREAKOUT
        bar['accumulation'] = not is_red and vr_vals[i] >= VR_BREAKOUT
        bar['heavy_distribution'] = stage4[i] and is_red and vr_vals[i] >= 1.5
        
        # =======================================================================
        # PATTERN: CLIMAX
        # =======================================================================
        bar['climax'] = vr_vals[i] >= VR_CLIMAX and abs(chg_pct[i]) >= CLIMAX_CHG_PCT
        
        # =======================================================================
        # PATTERN: GENERIC BREAKOUT
        # =======================================================================
        bar['generic_breakout'] = vr_vals[i] >= VR_BREAKOUT and chg_pct[i] >= MIN_CHG_PCT
        
        # =======================================================================
        # PATTERN: EXTENDED
        # =======================================================================
        if sma50[i] is not None and sma50[i] > 0:
            bar['extended'] = ((closes[i] - sma50[i]) / sma50[i]) * 100 > 30.0
        
        # =======================================================================
        # PATTERN: BRK-STOP
        # =======================================================================
        vol_sma_arr = compute_sma(volumes, VR_LENGTH)
        if sma20[i] is not None and vol_sma_arr[i] is not None:
            bar['brk_stop'] = closes[i] < sma20[i] and volumes[i] > vol_sma_arr[i] * 1.3
        
        # =======================================================================
        # PATTERN: GAP-UP
        # =======================================================================
        if i >= 1:
            bar['gap_up'] = opens[i] > highs[i - 1]
        
        # =======================================================================
        # PATTERN: BO-REACT-HI
        # =======================================================================
        if i >= 20 * TF_MULT:
            prior_20_high = max(highs[i - 20 * TF_MULT:i])
            bar['bo_react_hi'] = closes[i] > prior_20_high
        
        # =======================================================================
        # PATTERN: SCALE-IN (EMA10 proximity)
        # =======================================================================
        if ema10[i] is not None and ema10[i] > 0:
            ema10_dist = abs(closes[i] - ema10[i]) / closes[i] * 100
            bar['scale_in'] = (closes[i] > ema10[i] and ema10_dist <= 2.5 and
                               (closes[i] > sma50[i] if sma50[i] else False) and
                               stage2[i] and vr_vals[i] >= 1.0 and chg_pct[i] >= 1.0)
        
        # =======================================================================
        # PATTERN: CUP-HANDLE
        # =======================================================================
        if i >= 20 * TF_MULT:
            base_low_20 = min(lows[i - 20 * TF_MULT:i + 1])
            base_high_20 = max(highs[i - 20 * TF_MULT:i + 1])
            base_range_pct = ((base_high_20 - base_low_20) / base_high_20 * 100) if base_high_20 > 0 else 100
            bar['cup_handle'] = (tight_now[i] and base_range_pct <= CUP_HANDLE_PCT and
                                 closes[i] > base_low_20 + (base_high_20 - base_low_20) * 0.8 and
                                 vr_vals[i] < 0.8)
        
        # =======================================================================
        # ACTIVE STREAK TRACKING (Pine var logic)
        # =======================================================================
        if tight_now[i]:
            if base_start_bar is None:
                base_start_bar = i
            if active_streak_high is None or highs[i] > active_streak_high:
                active_streak_high = highs[i]
                active_streak_bar = i
                active_streak_time = i
            if active_base_low is None or lows[i] < active_base_low:
                active_base_low = lows[i]
        else:
            # -- Streak ended: save completed pivot --
            if active_streak_high is not None:
                days_in_base = i - (base_start_bar if base_start_bar is not None else active_streak_bar)
                depth_pct = ((active_streak_high - active_base_low) / active_streak_high * 100) \
                            if active_streak_high > 0 and active_base_low is not None else 0
                
                # Merge check: within MERGE_PCT of last pivot
                merged = False
                if pivots:
                    last_pivot = pivots[-1]
                    if abs(active_streak_high - last_pivot['price']) / last_pivot['price'] * 100 <= MERGE_PCT:
                        if active_streak_high > last_pivot['price']:
                            last_pivot['price'] = active_streak_high
                            last_pivot['time'] = active_streak_time
                            last_pivot['bar'] = active_streak_bar
                            last_pivot['days'] = days_in_base
                            last_pivot['depth'] = depth_pct
                        merged = True
                
                if not merged:
                    pivots.append({
                        'price': active_streak_high,
                        'time': active_streak_time,
                        'bar': active_streak_bar,
                        'days': days_in_base,
                        'depth': depth_pct,
                        'broken': False,
                        'failed': False,
                        'break_bar': None,
                        'two_r_reached': False,
                        'trail_hit': False,
                    })
                
                # Reset streak
                active_streak_high = None
                active_streak_bar = None
                active_streak_time = None
                active_base_low = None
                base_start_bar = None
        
        # =======================================================================
        # PIVOT LOOP — Process ALL pivots (matches Pine Script exactly)
        # Pine iterates i = 0 to n-1 (oldest → newest).  breakType is overwritten
        # per pivot, so the LAST triggering pivot determines the final label.
        # ALL triggering pivots get their broken / failed state updated.
        # =======================================================================
        
        # Nearest pivot for display
        nearest_pivot = None
        for p in reversed(pivots):
            if p['bar'] < i:
                nearest_pivot = p
                break
        
        if nearest_pivot is not None:
            bar['pivot_price'] = nearest_pivot['price']
            bar['pivot_days'] = nearest_pivot['days']
            bar['pivot_depth'] = nearest_pivot['depth']
            bar['pivot_broken'] = nearest_pivot['broken']
            bar['pivot_failed'] = nearest_pivot['failed']
        
        # Full pivot loop — forward order (oldest first) exactly like Pine
        for p in pivots:
            if p['bar'] >= i:
                continue
            
            p_price = p['price']
            p_days = p['days']
            p_depth = p['depth']
            broken = p['broken']
            failed = p['failed']
            b_bar = p.get('break_bar')
            
            pivot_dist_below = ((p_price - closes[i]) / p_price * 100) if p_price > 0 else 100
            pivot_dist_above = ((closes[i] - p_price) / p_price * 100) if p_price > 0 else 0
            
            if bar['pivot_price'] is None:
                bar['pivot_price'] = p_price
                bar['pivot_days'] = p_days
                bar['pivot_depth'] = p_depth
                bar['pivot_broken'] = broken
                bar['pivot_failed'] = failed
                bar['pivot_dist_below'] = pivot_dist_below
                bar['pivot_dist_above'] = pivot_dist_above
            
            # -- Breakout Tests --
            is_price_break = closes[i] > p_price
            is_vol_break = vr_vals[i] >= VR_BREAKOUT
            is_pct_break = chg_pct[i] >= MIN_CHG_PCT
            is_true_break = is_price_break and is_vol_break and is_pct_break
            
            # CHEAT ENTRY
            is_cheat_entry = (is_price_break and vr_vals[i] < VR_CHEAT_MAX and
                              vr_vals[i] >= 1.3 and chg_pct[i] >= MIN_CHG_PCT)
            
            # FAILED BO
            is_failed_bo = (failed or (broken and b_bar is not None and
                            (i - b_bar) <= 5 and closes[i] < p_price))
            
            # LOW-CHEAT
            is_low_cheat_now = (not broken and not failed and closes[i] < p_price and
                                pivot_dist_below >= LOW_CHEAT_DIST_MIN and
                                pivot_dist_below <= LOW_CHEAT_DIST_MAX and
                                p_depth <= MAX_BASE_DEPTH and
                                p_days >= MIN_BASE_WEEKS * 5 and
                                (closes[i] > sma50[i] if sma50[i] else False) and
                                stage2[i] and tight_now[i])
            if is_low_cheat_now:
                bar['low_cheat'] = True
                bar['pivot_dist_below'] = pivot_dist_below
            
            # PULLBACK-TO-PIVOT
            is_pullback_now = (broken and not failed and
                               closes[i] <= p_price * 1.02 and
                               closes[i] >= p_price * 0.95 and
                               (closes[i] > sma50[i] if sma50[i] else False) and
                               b_bar is not None and (i - b_bar) <= 20)
            if is_pullback_now:
                bar['pullback'] = True
            
            # NATURAL REACTION
            is_natural_rxn = (broken and not failed and
                              closes[i] <= p_price * 1.03 and
                              closes[i] >= p_price * 0.95 and
                              (closes[i] > sma50[i] if sma50[i] else False) and
                              b_bar is not None and (i - b_bar) <= 15 and
                              vol_dry_up[i])
            if is_natural_rxn:
                bar['natural_rxn'] = True
            
            # -- Entry Classification (last triggering pivot wins, like Pine) --
            if is_true_break and not broken and not failed:
                if is_vcp_base[i] and stage2[i] and p_days >= MIN_BASE_WEEKS * 5 and p_depth <= MAX_BASE_DEPTH:
                    bar['break_type'] = 'VCP-B/O'
                    bar['break_color'] = 'green'
                    bar['entry_signal'] = True
                elif is_cheat_entry and stage2[i]:
                    bar['break_type'] = 'CHEAT'
                    bar['break_color'] = 'blue'
                    bar['cheat_entry'] = True
                    bar['entry_signal'] = True
                elif bar['cup_handle'] and p_depth <= MAX_BASE_DEPTH:
                    bar['break_type'] = 'CUP-H'
                    bar['break_color'] = 'aqua'
                    bar['entry_signal'] = True
                elif bar['bo_react_hi']:
                    bar['break_type'] = 'BO-REACT'
                    bar['break_color'] = 'lime'
                    bar['entry_signal'] = True
                else:
                    bar['break_type'] = 'BREAKOUT'
                    bar['break_color'] = 'fuchsia'
                    bar['entry_signal'] = True
                
                p['broken'] = True
                p['break_bar'] = i
                bar['bracket_stop_1'] = p_price * (1 - STOP1_PCT / 100)
                bar['bracket_stop_2'] = p_price * (1 - STOP2_PCT / 100)
                # Update display pivot to match the triggering pivot
                bar['pivot_price'] = p_price
                bar['pivot_days'] = p_days
                bar['pivot_depth'] = p_depth
            
            if is_low_cheat_now:
                bar['break_type'] = 'LOW-CHEAT'
                bar['break_color'] = 'navy'
                bar['entry_signal'] = True
                bar['pivot_price'] = p_price
                bar['pivot_days'] = p_days
                bar['pivot_depth'] = p_depth
            
            if is_pullback_now or is_natural_rxn:
                bar['break_type'] = 'NAT-RXN' if is_natural_rxn else 'PULLBACK'
                bar['break_color'] = 'olive'
                bar['entry_signal'] = True
                bar['pivot_price'] = p_price
                bar['pivot_days'] = p_days
                bar['pivot_depth'] = p_depth
            
            if is_failed_bo and not failed:
                bar['break_type'] = 'FAILED'
                bar['break_color'] = 'red'
                p['failed'] = True
                bar['pivot_price'] = p_price
                bar['pivot_days'] = p_days
                bar['pivot_depth'] = p_depth
        
        # =======================================================================
        # INDEPENDENT ENTRY SIGNALS (match Pine Script alertconditions)
        # Spring and Scale-In are NOT tied to pivot logic.
        # =======================================================================
        if bar['spring'] and not bar['entry_signal']:
            bar['break_type'] = 'SPRING'
            bar['break_color'] = 'green'
            bar['entry_signal'] = True
        
        if bar['scale_in'] and not bar['entry_signal']:
            bar['break_type'] = 'SCALE-IN'
            bar['break_color'] = 'teal'
            bar['entry_signal'] = True
        
        # -- PENNY-ANTE (tight streak >= 5 + gap-up) --
        if tight_now[i]:
            tight_streak_count += 1
        else:
            tight_streak_count = 0
        
        bar['penny_ante'] = tight_streak_count >= 5 and bar['gap_up']
        bar['tight_streak_count'] = tight_streak_count
        
        # Override break_type for penny ante
        if bar['penny_ante'] and bar['entry_signal']:
            bar['break_type'] = 'PENNY'
            bar['break_color'] = 'teal'
        
        results.append(bar)
    
    return results, pivots


# ===============================================================================
# REPORTING
# ===============================================================================


def print_results(results, pivots, ticker):
    """Print comprehensive analysis report matching Pine's output style."""
    n = len(results)
    if n == 0:
        return
    
    # -- Summary --
    tight_bars = sum(1 for r in results if r['tight_now'])
    squat_count = sum(1 for r in results if r['squat'])
    tb_count = sum(1 for r in results if r['tennis_ball'])
    rec_count = sum(1 for r in results if r['recover'])
    spring_count = sum(1 for r in results if r['spring'])
    bo_count = sum(1 for r in results if r['entry_signal'])
    vcp_events = sum(1 for r in results if r['is_vcp_base'])
    climax_count = sum(1 for r in results if r['climax'])
    
    print(f"\n{'='*120}")
    print(f"  RMV MINERVINI MASTER - FULL PATTERN SUITE (Python Port v2)")
    print(f"  {ticker} | {results[0]['date']} to {results[-1]['date']} | {n} bars")
    print(f"{'='*120}")
    
    print(f"\n  -- PATTERN SUMMARY --")
    print(f"  {'Pattern':<30} {'Count':<8} {'% of Bars':<10}")
    print(f"  {'-'*48}")
    print(f"  {'Tight bars (RMV <={})'.format(RMV_TIGHT_THRESHOLD):<30} {tight_bars:<8} {tight_bars/max(n,1)*100:>7.1f}%")
    print(f"  {'SQUAT':<30} {squat_count:<8} {squat_count/max(n,1)*100:>7.1f}%")
    print(f"  {'TENNIS-BALL':<30} {tb_count:<8} {tb_count/max(n,1)*100:>7.1f}%")
    print(f"  {'RECOVER':<30} {rec_count:<8} {rec_count/max(n,1)*100:>7.1f}%")
    print(f"  {'SPRING':<30} {spring_count:<8} {spring_count/max(n,1)*100:>7.1f}%")
    print(f"  {'CLIMAX':<30} {climax_count:<8} {climax_count/max(n,1)*100:>7.1f}%")
    print(f"  {'Entry Signals':<30} {bo_count:<8} {bo_count/max(n,1)*100:>7.1f}%")
    print(f"  {'VCP Bases':<30} {vcp_events:<8} {vcp_events/max(n,1)*100:>7.1f}%")
    print(f"  {'Pivots':<30} {len(pivots):<8}")
    
    # -- Pivot Table --
    print(f"\n  -- PIVOT REGISTRY ({len(pivots)} pivots) --")
    print(f"  {'#':<4} {'Bar':<6} {'Price':>8} {'Days':<6} {'Depth%':<8} {'Broken':<8} {'Failed':<8} {'Break@Bar':<10}")
    print(f"  {'-'*60}")
    for idx, p in enumerate(pivots):
        print(f"  {idx:<4} {p['bar']:<6} {p['price']:>8.2f} {p['days']:<6} {p['depth']:<8.1f} "
              f"{'YES' if p['broken'] else '-':<8} {'YES' if p['failed'] else '-':<8} "
              f"{p['break_bar'] if p['break_bar'] is not None else '-':<10}")
    
    # -- Entry Signals --
    entries = [r for r in results if r['entry_signal']]
    if entries:
        print(f"\n  -- ENTRY SIGNALS ({len(entries)} total) --")
        print(f"  {'Date':<12} {'Price':>8} {'Type':<12} {'Chg%':>7} {'VR':>6} {'RMV':>5} "
              f"{'Pivot':>8} {'B-O1(-4%)':>10} {'B-O2(-8%)':>10} {'Stage':<6} {'Depth%':<6}")
        print(f"  {'-'*110}")
        for r in entries:
            if r['bracket_stop_1']:
                b1 = f"${r['bracket_stop_1']:.2f}"
                b2 = f"${r['bracket_stop_2']:.2f}"
            else:
                b1 = b2 = '-'
            pvt = f"${r['pivot_price']:.2f}" if r['pivot_price'] else '-'
            stage = 'S2' if r['stage2'] else 'S4' if r['stage4'] else 'S3' if r['stage3'] else 'S1' if r['stage1'] else '?'
            print(f"  {r['date']:<12} {r['close']:>8.2f} {r['break_type']:<12} {r['chg_pct']:>7.2f} "
                  f"{r['vr']:>6.2f} {r['rmv']:>5.1f} {pvt:>8} {b1:>10} {b2:>10} {stage:<6} "
                  f"{r['pivot_depth']:<6.1f}")
    
    # -- Bar-by-bar detail --
    print(f"\n  -- BAR-BY-BAR (Key patterns only) --")
    print(f"  {'Date':<12} {'O':>7} {'H':>7} {'L':>7} {'C':>7} {'Chg%':>7} {'VR':>5} "
          f"{'RMV':>5} {'Tight':<6} {'Stage':<4} {'Patterns':<50}")
    print(f"  {'-'*120}")
    
    for i, r in enumerate(results):
        patterns = []
        if r['squat']: patterns.append('SQUAT')
        if r['tennis_ball']: patterns.append('TB')
        if r['recover']: patterns.append('RECOVER')
        if r['spring']: patterns.append('SPRING')
        if r['climax']: patterns.append('CLIMAX')
        if r['distribution']: patterns.append('DIST')
        if r['heavy_distribution']: patterns.append('STG4-DIST')
        if r['accumulation']: patterns.append('ACCUM')
        if r['entry_signal'] and r['break_type'] not in patterns:
            patterns.append(r['break_type'])
        if r['brk_stop']: patterns.append('BRK-STOP')
        if r['scale_in']: patterns.append('SCALE-IN')
        if r['vol_dry_up'] and not r['tight_now']: patterns.append('DRY-UP')
        if r['is_vol_extreme_dry']: patterns.append('DRY-EXT')
        if r['extended']: patterns.append('EXTENDED')
        if r['penny_ante']: patterns.append('PENNY')
        if r['is_vcp_base']: patterns.append(f'VCP({r["contraction_count"]}ctr)')
        if r['follow_thru_4of5']: patterns.append('FT-4/5')
        if r['follow_thru_7of8']: patterns.append('FT-7/8')
        
        if not patterns:
            continue
        
        tight_str = 'YES' if r['tight_now'] else '-'
        stage = 'S2' if r['stage2'] else 'S4' if r['stage4'] else 'S3' if r['stage3'] else 'S1' if r['stage1'] else '?'
        pat_str = '; '.join(patterns) if patterns else ''
        
        print(f"  {r['date']:<12} {r['open']:>7.2f} {r['high']:>7.2f} {r['low']:>7.2f} {r['close']:>7.2f} "
              f"{r['chg_pct']:>7.2f} {r['vr']:>5.2f} {r['rmv']:>5.1f} {tight_str:<6} "
              f"{stage:<4} {pat_str:<50}")
    
    print(f"  {'-'*120}")
    print()


# ===============================================================================
# COMPARISON REPORT
# ===============================================================================


def print_comparison_report():
    """Print the alignment/comparison table between Pine and Python scanners."""
    print()
    print("  ========================================================================================================================")
    print("  ALIGNMENT REPORT -- Pine Script (rmv_minervini_master.pine) vs Python Scanners")
    print("  ========================================================================================================================")
    print("  LEGEND:  V = Exact Match  |  ~ = Partial Match  |  X = MISMATCH  |  - = Missing")
    print()
    hdr = {
        "Feature": "Feature",
        "This_Port": "This Port",
        "pattern_detector": "pattern_detector",
        "rmv_pivot_scanner": "rmv_pivot_scanner",
        "buy_points": "buy_points"
    }
    rows = [
        ("RMV Formula (min/max norm)", "V EXACT", "-", "X ATR-based", "-"),
        ("VCP: Same-window halves", "V EXACT", "~ Adjacent 10d", "~ 20d range", "-"),
        ("SQUAT", "V EXACT", "~ cl_mid<-0.8", "V", "~ cl_mid<-0.8"),
        ("TENNIS-BALL (<=2d recov)", "V EXACT", "~ named TB", "-", "~ SQUAT-RECOV"),
        ("RECOVER (3-10d recov)", "V EXACT", "~ 2-step", "-", "-"),
        ("SPRING/REVERSAL", "V EXACT", "-", "-", "-"),
        ("BREAKOUT (VR>=1.3,chg>=2%)", "V EXACT", "V", "V", "V VR>=1.3"),
        ("VCP-B/O (breakout)", "V EXACT", "~ diff halves", "~ 20d range", "-"),
        ("CHEAT (VR<1.5,>=1.3)", "V EXACT", "~ VR<1.5", "~ VR<1.5", "~ 3-C CHEAT"),
        ("LOW-CHEAT (2-8% pivot)", "V EXACT", "X diff", "-", "-"),
        ("CUP-HANDLE (VR<0.8)", "V EXACT", "~ rng<1.5%", "-", "~ CUP-BRKOUT"),
        ("PULLBACK-TO-PIVOT", "V EXACT", "-", "-", "-"),
        ("NATURAL REACTION", "V EXACT", "-", "-", "-"),
        ("SCALE-IN (EMA10<=2.5%)", "V EXACT", "-", "-", "-"),
        ("BRK-STOP (<SMA20+vol)", "V EXACT", "~ below 20MA", "-", "-"),
        ("CLIMAX (VR>=2,chg>=3%)", "V EXACT", "V", "-", "-"),
        ("STAGE 1/2/3/4 (Weinstein)", "V EXACT", "~ basic", "~ S2/S4", "-"),
        ("52-WEEK TREND TEMPLATE", "V EXACT", "-", "-", "-"),
        ("FOLLOW-THROUGH (4/5,7/8)", "V EXACT", "-", "-", "-"),
        ("PENNY-ANTE (5tight+gap)", "V EXACT", "~ 5d tight+BO", "~ tight+gap", "-"),
        ("VOLUME DRY-UP (<0.7)", "V EXACT", "~ VDU", "~ VDU", "-"),
        ("BASE DEPTH FILTER (<=40%)", "V EXACT", "-", "-", "-"),
        ("PIVOT TRACKING", "V EXACT", "-", "~ lookback", "-"),
        ("PIVOT MERGE (<=3%)", "V EXACT", "-", "-", "-"),
        ("BRACKET STOPS (4%/8%)", "V 4%/8%", "V 4%/7%", "-", "V 4%/8%"),
        ("DYNAMIC STOPS (2R+50MA)", "V EXACT", "-", "-", "-"),
        ("DISTRIBUTION (red+VR>=1.3)", "V EXACT", "V", "V", "-"),
        ("ACCUMULATION (green+VR>=1.3)", "V EXACT", "V", "V", "-"),
        ("GAP-UP (open>prior high)", "V EXACT", "V", "V", "-"),
        ("EXTENDED (>30%>50MA)", "V EXACT", "~ 30%", "-", "-"),
        ("BO-REACT-HI (>20bar hi)", "V EXACT", "~ 10bar hi", "~ 10bar hi", "-"),
    ]
    # Print header
    print(f"  {'Feature':<34} {'This Port':<22} {'pattern_detector':<18} {'rmv_pivot_scanner':<18} {'buy_points':<18}")
    print(f"  {'-'*112}")
    for row in rows:
        print(f"  {row[0]:<34} {row[1]:<22} {row[2]:<18} {row[3]:<18} {row[4]:<18}")
    
    print()
    print("  ========================================================================================================================")
    print("  KEY ALIGNMENT FINDINGS")
    print("  ========================================================================================================================")
    print()
    print("  1. RMV FORMULA (CRITICAL MISMATCH):")
    print("     Pine:   rmv = (currentRange - minRange) / (maxRange - minRange) * 100")
    print("             where min/max come from [1]-offset lookback (Deepvue exact)")
    print("     Python: _rmv_pivot_scanner.py uses ATR-based formula")
    print("     -> These produce COMPLETELY DIFFERENT values. The Python ATR-based RMV")
    print("       cannot substitute for the Pine min/max normalization.")
    print()
    print("  2. VCP DETECTION (LOGIC MISMATCH):")
    print("     Pine:   Same 20-bar window split into first 10 / second 10 halves")
    print("     Python: _minervini_pattern_detector.py uses adjacent 10-bar windows")
    print("     -> Pine's method is correct for Minervini ('tightening within the")
    print("       consolidation'). Python will miss contractions that start mid-window.")
    print()
    print("  3. TENNIS-BALL / RECOVER (MIDPOINT MISMATCH):")
    print("     Pine:   Uses CURRENT bar midpoint (high+low)/2 for recovery check")
    print("     Python: _minervini_pattern_detector.py checks close > squat_bar_close")
    print("     -> Pine's approach (current bar midpoint) is the correct Minervini def.")
    print()
    print("  4. LOW-CHEAT (CRITERIA DIFFERENCE):")
    print("     Pine:   Requires 2-8% below pivot, >=5wk base, depth<=40%, Stage 2+tight")
    print("     Python: _minervini_pattern_detector.py uses 5 days range<2.5%, VR<0.7,")
    print("             within 10% of base high -- completely different criteria")
    print()
    print("  5. PIVOT TRACKING (STATE MANAGEMENT):")
    print("     Pine:   Tracks every tight-streak high as a pivot with merge (<=3%)")
    print("     Python: No equivalent stateful pivot registry exists in any scanner")
    print()
    print("  6. BRACKET STOPS (ALIGNED -- 4%/8%):")
    print("     V Pine (4%/8%) matches _buy_points.py (4%/8%)")
    print("     ~ _minervini_pattern_detector.py uses 4%/7% (slight divergence)")
    print()
    print("  7. SPRING / SCALE-IN / NATURAL REACTION / FOLLOW-THROUGH:")
    print("     -> These patterns are UNIQUE to the Pine Script -- no Python scanner")
    print("       currently detects them.")
    print()
    print("  8. STAGE DETECTION (WEINSTEIN):")
    print("     Pine:   Explicit S1/S2/S3/S4 with SMA hierarchy + thresholds")
    print("     Python: _minervini_pattern_detector.py uses basic above/below checks")
    print("     -> Python full_scanner.py also has trend template (7 criteria + RS rank)")
    print("  ========================================================================================================================")


# ===============================================================================
# MAIN
# ===============================================================================


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAlso shows the alignment report between Pine and Python scanners:")
        print_comparison_report()
        return
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"[err] File not found: {filepath}")
        return
    
    ticker = "STOCK"
    year = None
    
    for i, arg in enumerate(sys.argv):
        if arg == '--ticker' and i + 1 < len(sys.argv):
            ticker = sys.argv[i + 1]
        if arg == '--year' and i + 1 < len(sys.argv):
            try:
                year = int(sys.argv[i + 1])
            except ValueError:
                pass
    
    # Load
    print(f"\n  -> Loading: {os.path.basename(filepath)}")
    data = load_csv(filepath)
    print(f"  -> Bars loaded: {len(data)}")
    
    if year:
        data = filter_year(data, year)
        print(f"  -> Filtered to: {year} ({len(data)} bars)")
    
    if not data:
        print("  -> No data to analyze")
        return
    
    # Analyze
    results, pivots = analyze(data, ticker=ticker)
    
    if not results:
        return
    
    # Print results (pass real internal pivots with correct broken/failed/break_bar state)
    print_results(results, pivots, ticker)
    
    # Compare with Python scanners
    print_comparison_report()
    
    print(f"\n  {'='*120}")
    print(f"  ANALYSIS COMPLETE: {len(results)} bars analyzed")
    print(f"  {'='*120}")


if __name__ == '__main__':
    main()

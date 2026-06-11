"""
RMV Consolidation Zone Detector  (v3.2 - Dual Pivot + Resistance Line)
=====================================================================
Detects consolidation zones with TWO breakout levels per zone,
PLUS a rolling resistance-line breakout for ranges that never form
a long-enough tight zone (e.g. ADANIPOWER Apr 2026).

  1. TIGHT PIVOT  - max high of tight bars only (RMV volatility contraction ceiling)
  2. BASE PIVOT   - max high of ALL bars from the prior breakout to the zone end
  3. RESISTANCE   - highest high of last N bars, broken on close (independent of RMV)

v2 CHANGES
----------
* Zones now qualify for buy points when EITHER:
  - tight-bar duration >= MIN_ZONE_DURATION  (original), OR
  - total base buildup (lookback_start -> zone_end) >= MIN_ZONE_DURATION
* Added 'Buildup' column to zone table -- this is the resistance line length.
* Added RESISTANCE breakout signal for horizontal-range breakouts that the
  tight-zone filter would otherwise miss.
"""

import sys
import os

sys.path.append(os.path.abspath("d:/CLAUDE"))
from rmv_minervini_master import load_csv, compute_rmv


# ==============================================================================
# CONFIGURATION
# ==============================================================================

RMV_LOOKBACK = 10
TIGHT_THRESHOLD = 20
MAX_GAP_BARS = 5
MIN_ZONE_DURATION = 5   # Only zones with >= 5 tight bars produce buy points

# ---- Resistance-line breakout (new in v2) ----
RESISTANCE_LOOKBACK = 15          # bars to scan for horizontal resistance
MIN_RESISTANCE_TOUCHES = 2        # how many bars must touch within 2% of the high


# ==============================================================================
# CORE ALGORITHM
# ==============================================================================

def detect_zones_and_breakouts(data, rmv_lookback=RMV_LOOKBACK,
                                tight_threshold=TIGHT_THRESHOLD,
                                max_gap=MAX_GAP_BARS, cutoff_date=None,
                                min_duration=MIN_ZONE_DURATION):
    """
    Single-pass detection with dual pivot levels + resistance breakout.

    Returns:
        zones      - list of zone dicts (with tight_pivot + base_pivot)
        buy_points - list of buy-point dicts (type = 'TIGHT' / 'BASE' / 'RESISTANCE')
        rmv_vals   - raw RMV array for tracing
    """
    dates  = [d['date'] for d in data]
    highs  = [d['high'] for d in data]
    lows   = [d['low']  for d in data]
    closes = [d['close'] for d in data]
    opens  = [d['open'] for d in data]
    vols   = [d['volume'] for d in data]

    rmv_vals = compute_rmv(highs, lows, lookback=rmv_lookback)
    n = len(data)
    tight = [rmv_vals[i] <= tight_threshold for i in range(n)]
    
    # Pre-calculate volume ratios (VR) and >5% down days
    vrs = []
    down_days = []
    for i in range(n):
        s = max(0, i - 50 + 1)
        va = sum(vols[s:i+1]) / (i - s + 1) if (i - s + 1) > 0 else 0
        vrs.append(vols[i]/va if va > 0 else 0)
        chg = (closes[i] / closes[i-1] - 1) if i > 0 else 0
        down_days.append(chg <= -0.05)

    def is_valid_breakout(idx, pivot):
        if pivot == 0: return False
        # Avoid extremely weak margins (< 0.5%) and post-crash breakouts
        if (closes[idx] - pivot) / pivot < 0.005: return False
        for j in range(max(0, idx-2), idx):
            if down_days[j]: return False
        return True

    def calc_score(idx, pivot, dur, recent_handle=False):
        score = 1
        if (closes[idx] - pivot) / pivot >= 0.02: score += 1
        if vrs[idx] >= 1.3: score += 1
        if dur >= 15: score += 1
        if not any(down_days[j] for j in range(max(0, idx-4), idx)): score += 1
        if recent_handle: score += 1
        return min(5, score)

    zones = []
    buy_points = []

    az = None            # active zone being built
    pending = []         # zones not fully resolved
    lookback_start = 0   # window start for base_pivot calculation
    last_gap_pwr_bar = -999  # cooldown: only one GAP_PWR per MIN_ZONE_DURATION bars

    # ---- Resistance tracker state (v2) ----
    res_last_reset = 0   # bar index where resistance window last reset
    res_high = 0.0       # highest high in current resistance window

    for i in range(n):
        if cutoff_date and dates[i] > cutoff_date:
            break

        # Update rolling resistance high
        if i == 0 or lookback_start != res_last_reset:
            res_last_reset = lookback_start
            res_high = highs[i]
        else:
            res_high = max(res_high, highs[i])

        if tight[i]:
            # ---- TIGHT BAR ----
            if az is None:
                # Start a brand-new zone
                az = {
                    'start_idx':      i,
                    'last_tight_idx': i,
                    'tight_high':     highs[i],
                    'lookback_start': lookback_start,
                    'streak_count':   1,
                    'tight_count':    1,
                    'in_streak':      True,
                    'current_streak_len': 1,
                    'current_streak_high': highs[i],
                    'sub_clusters':   [],
                }
            else:
                gap = i - az['last_tight_idx'] - 1
                if gap <= max_gap:
                    # Merge into active zone
                    if not az['in_streak']:
                        az['streak_count'] += 1
                        az['in_streak'] = True
                        az['current_streak_len'] = 1
                        az['current_streak_high'] = highs[i]
                    else:
                        az['current_streak_len'] += 1
                        az['current_streak_high'] = max(az['current_streak_high'], highs[i])
                        
                    az['tight_high']     = max(az['tight_high'], highs[i])
                    az['last_tight_idx'] = i
                    az['tight_count']   += 1
                else:
                    # Gap too large -- expire active zone, start fresh
                    z = _finalize_zone(az, dates, highs, lows)
                    zones.append(z)
                    pending.append(z)
                    az = {
                        'start_idx':      i,
                        'last_tight_idx': i,
                        'tight_high':     highs[i],
                        'lookback_start': lookback_start,
                        'streak_count':   1,
                        'tight_count':    1,
                        'in_streak':      True,
                        'current_streak_len': 1,
                        'current_streak_high': highs[i],
                        'sub_clusters':   [],
                    }
        else:
            # ---- NON-TIGHT BAR ----
            if az is not None:
                if az['in_streak']:
                    # Just ended a streak
                    if az['current_streak_len'] >= 2:
                        az['sub_clusters'].append({
                            'end_idx': az['last_tight_idx'],
                            'high': az['current_streak_high'],
                            'len': az['current_streak_len'],
                            'broken': False
                        })
                    az['in_streak'] = False
                    
                gap = i - az['last_tight_idx']

                # Check PRELIM_BREAK inside active zone
                if az['sub_clusters']:
                    last_sc = az['sub_clusters'][-1]
                    if closes[i] > last_sc['high'] and closes[i] <= az['tight_high'] and not last_sc['broken']:
                        last_sc['broken'] = True
                        if is_valid_breakout(i, last_sc['high']) and not az.get('disqualified', False):
                            temp_z = _finalize_zone(az, dates, highs, lows)
                            buy_points.append(_make_bp(temp_z, i, dates, closes, 'PRELIM', vrs, calc_score, custom_pivot=last_sc['high']))

                if closes[i] > az['tight_high']:
                    # === TIGHT BREAKOUT from active zone ===
                    z = _finalize_zone(az, dates, highs, lows)
                    z['tight_broken']      = True
                    z['tight_break_date']  = dates[i]
                    z['tight_break_price'] = closes[i]
                    zones.append(z)
                    recent_handle = bool(z['sub_clusters'] and (i - z['sub_clusters'][-1]['end_idx'] <= 5))
                    
                    if _zone_qualifies(z, min_duration) and is_valid_breakout(i, z['tight_pivot']) and not z['disqualified']:
                        buy_points.append(_make_bp(z, i, dates, closes, 'TIGHT', vrs, lambda i, p, d: calc_score(i, p, d, recent_handle)))

                    # Option C: clear ALL stale pending zones on TIGHT breakout
                    pending = []

                    # Check simultaneous base breakout
                    if closes[i] > z['base_pivot']:
                        z['base_broken']      = True
                        z['base_break_date']  = dates[i]
                        z['base_break_price'] = closes[i]
                        if z['base_pivot'] > z['tight_pivot'] and _zone_qualifies(z, min_duration) and is_valid_breakout(i, z['base_pivot']) and not z['disqualified']:
                            buy_points.append(_make_bp(z, i, dates, closes, 'BASE', vrs, lambda i, p, d: calc_score(i, p, d, recent_handle)))
                    elif z['base_pivot'] > z['tight_pivot']:
                        # Only keep this zone's base pivot alive
                        pending.append(z)

                    lookback_start = i + 1
                    az = None

                elif gap > max_gap:
                    # Zone expired without breakout
                    z = _finalize_zone(az, dates, highs, lows)
                    zones.append(z)
                    pending.append(z)
                    az = None

            # Check ALL pending zones for breakouts
            tight_fired_this_bar = False
            for pz in pending[:]:
                recent_handle = bool(pz['sub_clusters'] and (i - pz['sub_clusters'][-1]['end_idx'] <= 5))
                
                # Check PRELIM_BREAK inside pending zone
                if pz['sub_clusters'] and not pz['tight_broken']:
                    last_sc = pz['sub_clusters'][-1]
                    if closes[i] > last_sc['high'] and closes[i] <= pz['tight_pivot'] and not last_sc['broken']:
                        last_sc['broken'] = True
                        if is_valid_breakout(i, last_sc['high']):
                            buy_points.append(_make_bp(pz, i, dates, closes, 'PRELIM', vrs, calc_score, custom_pivot=last_sc['high']))

                if not pz['tight_broken'] and closes[i] > pz['tight_pivot']:
                    pz['tight_broken']      = True
                    pz['tight_break_date']  = dates[i]
                    pz['tight_break_price'] = closes[i]
                    if _zone_qualifies(pz, min_duration) and is_valid_breakout(i, pz['tight_pivot']) and not pz['disqualified']:
                        buy_points.append(_make_bp(pz, i, dates, closes, 'TIGHT', vrs, lambda i, p, d: calc_score(i, p, d, recent_handle)))
                    lookback_start = max(lookback_start, i + 1)
                    # Option C: flag that a TIGHT fired; we'll purge other pending after the loop
                    tight_fired_this_bar = True

                if not pz['base_broken'] and closes[i] > pz['base_pivot']:
                    pz['base_broken']      = True
                    pz['base_break_date']  = dates[i]
                    pz['base_break_price'] = closes[i]
                    if _zone_qualifies(pz, min_duration) and is_valid_breakout(i, pz['base_pivot']) and not pz['disqualified']:
                        buy_points.append(_make_bp(pz, i, dates, closes, 'BASE', vrs, lambda i, p, d: calc_score(i, p, d, recent_handle)))

                if pz['tight_broken'] and pz['base_broken']:
                    pending.remove(pz)

            # Option C: after any TIGHT breakout, keep only zones whose base is still unresolved
            if tight_fired_this_bar:
                pending = [pz for pz in pending if pz['tight_broken'] and not pz['base_broken']]

        # ---- RESISTANCE BREAKOUT (v2) ----
        # Independent of RMV zones: if price closes above the rolling resistance high
        # and there have been enough bars / touches, flag it.
        if i > res_last_reset and (i - res_last_reset) >= min_duration:
            # Prior high in this window (excluding current bar's high)
            prior_window = highs[res_last_reset:i]
            prior_resistance = max(prior_window) if prior_window else 0
            if prior_resistance > 0 and closes[i] > prior_resistance:
                touches = sum(1 for h in prior_window if h >= prior_resistance * 0.98)
                if touches >= MIN_RESISTANCE_TOUCHES:
                    # Avoid duplicate if TIGHT/BASE already fired on this bar
                    already = any(
                        bp['date'] == dates[i] and bp['type'] in ('TIGHT', 'BASE')
                        for bp in buy_points
                    )
                    if not already and is_valid_breakout(i, prior_resistance):
                        buy_points.append({
                            'type':         'RESISTANCE',
                            'date':         dates[i],
                            'close':        closes[i],
                            'pivot_price':  prior_resistance,
                            'base_low':     min(lows[res_last_reset:i+1]),
                            'depth_pct':    _depth(prior_resistance, min(lows[res_last_reset:i+1])),
                            'duration':     i - res_last_reset,
                            'zone_start':   dates[res_last_reset],
                            'zone_end':     dates[i-1] if i > res_last_reset else dates[i],
                            'streak_count': touches,
                            'score':        min(5, calc_score(i, prior_resistance, i - res_last_reset)),
                            'vr':           vrs[i],
                        })
                        # Reset resistance window after breakout
                        res_last_reset = i + 1
                        res_high = 0.0

        # ---- GAP POWER SIGNAL ----
        if vrs[i] >= 2.0 and (closes[i] / closes[i-1] - 1) >= 0.08:
            recent_tight_count = sum(1 for t in tight[max(0, i - MIN_ZONE_DURATION - 5):i] if t)
            gap_pwr_cooldown_ok = (i - last_gap_pwr_bar) > MIN_ZONE_DURATION
            if recent_tight_count >= MIN_ZONE_DURATION and gap_pwr_cooldown_ok:
                last_gap_pwr_bar = i
                buy_points.append({
                    'type':         'GAP_PWR',
                    'date':         dates[i],
                    'close':        closes[i],
                    'pivot_price':  0.0,
                    'base_low':     lows[i],
                    'depth_pct':    0.0,
                    'duration':     recent_tight_count,
                    'zone_start':   dates[i],
                    'zone_end':     dates[i],
                    'streak_count': 1,
                    'score':        5,
                    'vr':           vrs[i],
                })

    # Finalize any remaining active zone
    if az is not None:
        z = _finalize_zone(az, dates, highs, lows)
        zones.append(z)

    return zones, buy_points, rmv_vals


# --------------------------------------------------------------------------- #
#  Internal helpers
# --------------------------------------------------------------------------- #

PRE_ZONE_MAX_RUN = 20.0
PRE_ZONE_LOOKBACK = 10


def _finalize_zone(az, dates, highs, lows):
    """Build a finalised zone dict from active-zone state."""
    s  = az['start_idx']
    e  = az['last_tight_idx']
    lb = az['lookback_start']

    tight_pivot = az['tight_high']
    base_pivot  = max(highs[lb : e + 1])
    base_low    = min(lows[s : e + 1])

    pre_start = max(0, s - PRE_ZONE_LOOKBACK)
    pre_close = lows[pre_start]
    pre_run_pct = (highs[s] - pre_close) / pre_close * 100 if pre_close > 0 else 0

    return {
        'start_idx':        s,
        'end_idx':          e,
        'start_date':       dates[s],
        'end_date':         dates[e],
        'tight_pivot':      tight_pivot,
        'base_pivot':       base_pivot,
        'base_low':         base_low,
        'tight_depth_pct':  _depth(tight_pivot, base_low),
        'base_depth_pct':   _depth(base_pivot, base_low),
        'duration':         e - s + 1,
        'lookback_start':   lb,
        'base_buildup':     e - lb + 1,
        'streak_count':     az['streak_count'],
        'tight_bar_count':  az['tight_count'],
        'tight_broken':     False,
        'tight_break_date': None,
        'tight_break_price':None,
        'base_broken':      False,
        'base_break_date':  None,
        'base_break_price': None,
        'sub_clusters':     az.get('sub_clusters', []),
        'vcp_contractions': len(az.get('sub_clusters', [])),
        'pre_run_pct':      pre_run_pct,
        'disqualified':     pre_run_pct > PRE_ZONE_MAX_RUN,
    }


def _depth(pivot, low):
    return (pivot - low) / pivot * 100 if pivot > 0 else 0


def _zone_qualifies(zone, min_dur):
    """A zone qualifies for buy points if it has enough tight bars
    OR enough total base buildup (lookback window)."""
    buildup = zone['end_idx'] - zone['lookback_start'] + 1
    return zone['duration'] >= min_dur or buildup >= min_dur


def _make_bp(zone, break_idx, dates, closes, bp_type, vrs_array, calc_score_fn, custom_pivot=None):
    pivot = custom_pivot if custom_pivot is not None else (zone['tight_pivot'] if bp_type == 'TIGHT' else zone['base_pivot'])
    depth = zone['tight_depth_pct'] if bp_type == 'TIGHT' else zone['base_depth_pct']
    return {
        'type':         bp_type,
        'date':         dates[break_idx],
        'close':        closes[break_idx],
        'pivot_price':  pivot,
        'base_low':     zone['base_low'],
        'depth_pct':    depth,
        'duration':     zone['duration'],
        'zone_start':   zone['start_date'],
        'zone_end':     zone['end_date'],
        'streak_count': zone['streak_count'],
        'score':        calc_score_fn(break_idx, pivot, zone['duration']),
        'vr':           vrs_array[break_idx],
    }


# =========================================================================== #
#  CLI / Reporting
# =========================================================================== #

def run_scan(ticker, filepath, cutoff_date, trace_start=None, trace_end=None):
    """Run the full dual-pivot scan and print results."""
    data = load_csv(filepath)
    print(f"Loaded {len(data)} bars for {ticker}")

    zones, buy_points, rmv_vals = detect_zones_and_breakouts(
        data, cutoff_date=cutoff_date)

    dates_list  = [d['date'] for d in data]
    highs_list  = [d['high'] for d in data]
    lows_list   = [d['low']  for d in data]
    closes_list = [d['close'] for d in data]

    zr = [z for z in zones if z['start_date'] <= cutoff_date]
    bps = [b for b in buy_points if b['date'] <= cutoff_date]

    # ---- Header ----
    print(f"\n{'='*120}")
    print(f"  {ticker} - RMV DUAL PIVOT SCAN (v3.2: Tight + Base + Resistance)")
    print(f"  Lookback={RMV_LOOKBACK}  Threshold<={TIGHT_THRESHOLD}  MaxGap={MAX_GAP_BARS}  MinDur={MIN_ZONE_DURATION}  Period: to {cutoff_date}")
    print(f"{'='*120}")

    # ---- Zones ----
    print(f"\n  --- CONSOLIDATION ZONES ({len(zr)}) ---")
    print(f"  {'#':<3} {'Start':<12} {'End':<12} {'Dur':<8} "
          f"{'TightPvt':<10} {'BasePvt':<10} {'Low':<10} {'Buildup':<8} {'VCP':<4} {'Status'}")
    print(f"  {'-'*120}")
    for idx, z in enumerate(zr):
        parts = []
        if z['tight_broken']:
            parts.append(f"T-brk {z['tight_break_date']} @${z['tight_break_price']:.2f}")
        if z['base_broken']:
            parts.append(f"B-brk {z['base_break_date']} @${z['base_break_price']:.2f}")
        if not z['tight_broken'] and not z['base_broken']:
            parts.append("ACTIVE")
        status = " | ".join(parts)
        vcp = f"{z['vcp_contractions']}-T" if z['vcp_contractions'] > 1 else "-"

        print(f"  {idx:<3} {z['start_date']:<12} {z['end_date']:<12} "
              f"{z['duration']:<3} bars "
              f"${z['tight_pivot']:<9.2f} ${z['base_pivot']:<9.2f} "
              f"${z['base_low']:<9.2f} {z['base_buildup']:<7} {vcp:<4} {status}")

    # ---- Buy Points ----
    print(f"\n  --- BUY POINTS ({len(bps)}) ---")
    print(f"  {'Type':<10} {'Date':<12} {'Close':<8} {'Pivot':<8} {'VR':<6} {'Score':<5} {'Zone Dur'}  {'Zone'}")
    print(f"  {'-'*98}")
    for bp in bps:
        score_stars = '*' * bp['score']
        print(f"  {bp['type']:<10} {bp['date']:<12} ${bp['close']:<7.2f} ${bp['pivot_price']:<7.2f} "
              f"{bp['vr']:<5.1f}x {score_stars:<5} {bp['duration']:<3} bars  "
              f"{bp['zone_start']} -> {bp['zone_end']}")

    # ---- Trace ----
    if trace_start and trace_end:
        print(f"\n  --- BAR-BY-BAR TRACE ({trace_start} to {trace_end}) ---")
        print(f"  {'Date':<12} {'High':>8} {'Low':>8} {'Close':>8} "
              f"{'RMV':>6} {'Tight':<6} {'Zone'}")
        print(f"  {'-'*80}")
        for i in range(len(data)):
            if dates_list[i] < trace_start or dates_list[i] > trace_end:
                continue
            tight_str = "YES" if rmv_vals[i] <= TIGHT_THRESHOLD else "no"
            zone_str = ""
            for idx, z in enumerate(zr):
                if z['start_idx'] <= i <= z['end_idx']:
                    zone_str = (f"<- Z{idx} T:${z['tight_pivot']:.2f} "
                                f"B:${z['base_pivot']:.2f}")
                    break
            print(f"  {dates_list[i]:<12} {highs_list[i]:>8.2f} {lows_list[i]:>8.2f} "
                  f"{closes_list[i]:>8.2f} {rmv_vals[i]:>6.1f} {tight_str:<6} {zone_str}")

    print(f"\n{'='*120}")
    print(f"  SCAN COMPLETE")
    print(f"{'='*120}")


# =========================================================================== #
#  Main
# =========================================================================== #

def main():
    import sys
    if len(sys.argv) >= 3:
        ticker = sys.argv[1]
        filepath = sys.argv[2]
        cutoff = sys.argv[3] if len(sys.argv) >= 4 else "2026-06-09"
    else:
        ticker = "MU"
        filepath = "d:/CLAUDE/data/MU/MU_ohlcv.csv"
        cutoff = "2026-06-09"

    run_scan(
        ticker=ticker,
        filepath=filepath,
        cutoff_date=cutoff,
    )


if __name__ == "__main__":
    main()

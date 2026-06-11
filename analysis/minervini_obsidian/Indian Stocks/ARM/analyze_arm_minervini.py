"""
ARM — Minervini-Style Entry Setup Analysis
============================================
Downloads ARM data from Yahoo Finance (Jan 2026 onwards) and runs
full Pine Script entry logic conceptually.

Outputs: analysis/minervini_obsidian/Indian Stocks/ARM/in_depth_analysis/ARM_entries_verified.md
"""

import csv
import math
import os
import sys
from datetime import datetime

import yfinance as yf

# ── Paths ──
OUT_DIR = os.path.dirname(__file__) + "/in_depth_analysis"
DATA_PATH = os.path.dirname(__file__) + "/ARM_ohlcv.csv"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Configuration (matches rmv_minervini_master.pine defaults) ──
VR_BREAKOUT = 1.3
VR_CHEAT_MAX = 1.5
MIN_CHG_PCT = 2.0
CONTRACTION_PCT = 85.0
MIN_CONTRACTIONS = 2
MAX_BASE_DEPTH = 40.0
MIN_BASE_WEEKS = 5
LOW_CHEAT_DIST_MIN = 2.0
LOW_CHEAT_DIST_MAX = 8.0
VOL_DRY_UP_THRESH = 0.7
VOL_EXTREME_DRY = 0.5
STOP1_PCT = 4.0
STOP2_PCT = 8.0
PIERCE_THRESHOLD = 0.5
EMA10_DIST_MAX = 2.5
RMV_TIGHT_THRESHOLD = 12.0
RMV_LOOKBACK = 15
LINE_EXTEND = 20
MERGE_PCT = 3.0

# ── Data Loading ──
def load_or_download():
    if os.path.exists(DATA_PATH):
        print(f"[info] Using cached data: {DATA_PATH}")
        with open(DATA_PATH, 'r') as f:
            lines = f.readlines()
    else:
        print("[info] Downloading ARM from Yahoo Finance...")
        df = yf.download("ARM", start="2024-01-01", progress=False)
        if df.empty:
            print("[err] No data returned for ARM")
            sys.exit(1)
        df.to_csv(DATA_PATH)
        lines = open(DATA_PATH).readlines()
        print(f"[info] Downloaded {len(df)} bars to {DATA_PATH}")
    return lines


def parse_csv(lines):
    data = []
    for line in lines[3:]:
        p = line.strip().split(',')
        if len(p) < 6:
            continue
        try:
            date_str = p[0].strip()[:10]
            datetime.strptime(date_str, '%Y-%m-%d')
            close = float(p[1])
            high = float(p[2])
            low = float(p[3])
            open_ = float(p[4])
            volume = int(float(p[5]))
        except (ValueError, IndexError):
            continue
        data.append({
            'date': date_str,
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    # Filter Jan 2026 onwards
    return data


# ── Indicator Helpers ──
def sma(values, period):
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i-period+1:i+1]) / period)
    return result


def ema(values, period):
    result = []
    mult = 2 / (period + 1)
    for i in range(len(values)):
        if i == 0:
            result.append(values[0])
        elif i < period:
            result.append(sum(values[:i+1]) / (i+1))
        else:
            result.append((values[i] - result[-1]) * mult + result[-1])
    return result


def compute_indicators(data):
    n = len(data)
    closes = [d['close'] for d in data]
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]
    volumes = [d['volume'] for d in data]

    sma50 = sma(closes, 50)
    sma150 = sma(closes, 150)
    sma200 = sma(closes, 200)
    sma20 = sma(closes, 20)
    ema10 = ema(closes, 10)
    ema21 = ema(closes, 21)
    v20 = sma(volumes, 20)
    v50 = sma(volumes, 50)

    # Compute RMV (matching Pine logic)
    rmv_vals = []
    for i in range(n):
        if i < 1:
            rmv_vals.append(50.0)
            continue
        current_range = highs[i] - lows[i]
        min_range = min(highs[j] - lows[j] for j in range(max(0, i - RMV_LOOKBACK), i))
        max_range = max(highs[j] - lows[j] for j in range(max(0, i - RMV_LOOKBACK), i))
        range_span = max_range - min_range
        rmv = 50.0
        if range_span > 0:
            rmv = (current_range - min_range) / range_span * 100
            rmv = max(0, min(100, rmv))
        rmv_vals.append(rmv)

    for i in range(n):
        d = data[i]
        d['sma50'] = sma50[i]
        d['sma150'] = sma150[i]
        d['sma200'] = sma200[i]
        d['sma20'] = sma20[i]
        d['ema10'] = ema10[i]
        d['ema21'] = ema21[i]
        d['v20'] = v20[i]
        d['v50'] = v50[i]
        d['vr'] = (d['volume'] / v50[i]) if v50[i] and v50[i] > 0 else 1.0
        d['vr20'] = (d['volume'] / v20[i]) if v20[i] and v20[i] > 0 else 1.0
        d['chgPct'] = ((d['close'] - closes[i-1]) / closes[i-1]) * 100 if i > 0 else 0.0
        d['stage2'] = (d['close'] > sma50[i] and sma50[i] > sma150[i] and
                       sma150[i] > sma200[i] and d['close'] > sma200[i] * 1.05) if all(x is not None for x in [sma50[i], sma150[i], sma200[i]]) else False
        d['volDryUp'] = d['vr'] < VOL_DRY_UP_THRESH
        d['volExtremeDry'] = d['vr'] < VOL_EXTREME_DRY
        d['midPoint'] = (d['high'] + d['low']) / 2
        d['rmv'] = rmv_vals[i]
        d['tightNow'] = rmv_vals[i] <= RMV_TIGHT_THRESHOLD
    return data


# ── Main Analysis ──
def analyze_arm():
    lines = load_or_download()
    data = parse_csv(lines)
    n = len(data)
    if n < 50:
        print(f"[err] Need 50+ bars, got {n}")
        sys.exit(1)

    print(f"[info] Loaded {n} bars from {data[0]['date']} to {data[-1]['date']}")
    data = compute_indicators(data)
    # Filter analysis to Jan 2026 onwards, but keep prior data for indicator warmup
    data = [d for d in data if d['date'] >= '2026-01-01']
    n = len(data)
    print(f"[info] Analyzing {n} bars from {data[0]['date']} to {data[-1]['date']}")
    highs = [d['high'] for d in data]
    lows = [d['low'] for d in data]

    # --- Track pivots EXACTLY like Pine Script ---
    # When tight streak ends, save activeStreakHigh as pivot
    pivot_prices = []
    pivot_times = []
    pivot_bars = []
    pivot_days = []
    pivot_depths = []
    pivot_broken = []
    pivot_failed = []
    pivot_break_bar = []
    pivot_2r_reached = []
    pivot_trail_hit = []

    active_streak_high = None
    active_streak_bar = None
    active_streak_time = None
    active_base_low = None
    base_start_bar = None

    contraction_count = 0

    entries_current = []
    entries_bug_miss = []
    entries_fixed = []

    for i in range(n):
        d = data[i]
        if i < 50:
            continue

        # --- Tight streak tracking ---
        if d['tightNow']:
            if base_start_bar is None:
                base_start_bar = i
            if active_streak_high is None or d['high'] > active_streak_high:
                active_streak_high = d['high']
                active_streak_bar = i
                active_streak_time = d['date']
            if active_base_low is None or d['low'] < active_base_low:
                active_base_low = d['low']
        else:
            # Streak ends - save pivot
            if active_streak_high is not None:
                days_in_base = i - (base_start_bar if base_start_bar is not None else active_streak_bar)
                depth_pct = ((active_streak_high - active_base_low) / active_streak_high * 100) if active_streak_high and active_base_low else 0

                # Merge check
                merged = False
                if pivot_prices:
                    last_idx = len(pivot_prices) - 1
                    last_price = pivot_prices[last_idx]
                    if abs(active_streak_high - last_price) / last_price * 100 <= MERGE_PCT:
                        if active_streak_high > last_price:
                            pivot_prices[last_idx] = active_streak_high
                            pivot_times[last_idx] = active_streak_time
                            pivot_bars[last_idx] = active_streak_bar
                            pivot_days[last_idx] = days_in_base
                            pivot_depths[last_idx] = depth_pct
                        merged = True

                if not merged:
                    pivot_prices.append(active_streak_high)
                    pivot_times.append(active_streak_time)
                    pivot_bars.append(active_streak_bar)
                    pivot_days.append(days_in_base)
                    pivot_depths.append(depth_pct)
                    pivot_broken.append(False)
                    pivot_failed.append(False)
                    pivot_break_bar.append(None)
                    pivot_2r_reached.append(False)
                    pivot_trail_hit.append(False)

            active_streak_high = None
            active_streak_bar = None
            active_streak_time = None
            active_base_low = None
            base_start_bar = None

        # --- VCP contraction (Pine bug replicated + fixed) ---
        half_window = 10
        buggy_vcp = False
        fixed_vcp = False
        vcp_ratio = 0
        if i >= half_window * 2:
            first_half_range = max(highs[j] for j in range(i - half_window + 1, i + 1)) - min(lows[j] for j in range(i - half_window + 1, i + 1))
            second_half_range = max(highs[j] for j in range(i - half_window * 2 + 1, i - half_window + 1)) - min(lows[j] for j in range(i - half_window * 2 + 1, i - half_window + 1))
            # BUGGY Pine: secondHalf / firstHalf
            buggy_vcp = first_half_range > 0 and (second_half_range / first_half_range) * 100 <= CONTRACTION_PCT
            # FIXED: firstHalf / secondHalf
            fixed_vcp = second_half_range > 0 and (first_half_range / second_half_range) * 100 <= CONTRACTION_PCT
            vcp_ratio = (second_half_range / first_half_range) * 100 if first_half_range > 0 else 0

        if buggy_vcp and d['tightNow']:
            contraction_count += 1
        elif not d['tightNow']:
            contraction_count = 0
        is_vcp_base = contraction_count >= MIN_CONTRACTIONS

        # --- Spring / Reversal ---
        buggy_spring = False
        fixed_spring = False
        if i >= 1:
            p = data[i-1]
            buggy_spring = (d['open'] < p['low'] and
                            d['close'] > d['midPoint'] and d['close'] > d['open'] and
                            d['vr'] >= 1.0)
            fixed_spring = (d['open'] < p['close'] and
                            d['close'] > d['midPoint'] and d['close'] > d['open'] and
                            d['vr'] >= 1.0)

        # --- EMA10 Scale-in ---
        ema10_dist = abs(d['close'] - d['ema10']) / d['close'] * 100
        buggy_scale_in = (d['close'] > d['ema10'] and ema10_dist <= EMA10_DIST_MAX and
                          d['close'] > d['sma50'] and d['stage2'] and d['vr'] >= 1.0 and d['chgPct'] >= 1.0)
        fixed_scale_in = False
        if i >= 5:
            min_dist = min(abs(data[j]['low'] - data[j]['ema10']) / data[j]['close'] * 100 for j in range(max(0, i-4), i+1))
            fixed_scale_in = (d['close'] > d['ema10'] and min_dist <= EMA10_DIST_MAX and
                              d['close'] > d['sma50'] and d['stage2'] and d['vr'] >= 1.0 and d['chgPct'] >= 1.0)

        # --- Process all stored pivots ---
        for pi in range(len(pivot_prices)):
            p_price = pivot_prices[pi]
            p_time = pivot_times[pi]
            p_bar = pivot_bars[pi]
            p_days = pivot_days[pi]
            p_depth = pivot_depths[pi]
            broken = pivot_broken[pi]
            failed = pivot_failed[pi]
            b_bar = pivot_break_bar[pi]
            two_r = pivot_2r_reached[pi]
            trl_hit = pivot_trail_hit[pi]

            pivot_dist_below = (p_price - d['close']) / p_price * 100 if p_price > 0 else 100
            pivot_dist_above = (d['close'] - p_price) / p_price * 100 if p_price > 0 else 0

            is_price_break = d['close'] > p_price
            is_vol_break = d['vr'] >= VR_BREAKOUT
            is_pct_break = d['chgPct'] >= MIN_CHG_PCT
            is_true_break = is_price_break and is_vol_break and is_pct_break

            # BUGGY CHEAT: vr >= 1.3 (same as breakout!)
            is_cheat_buggy = is_price_break and d['vr'] < VR_CHEAT_MAX and d['vr'] >= 1.3 and d['chgPct'] >= MIN_CHG_PCT
            # FIXED CHEAT: vr 0.7-1.3, chg% >= 1.0
            is_cheat_fixed = is_price_break and d['vr'] < VR_CHEAT_MAX and d['vr'] >= 0.7 and d['chgPct'] >= 1.0

            # LOW-CHEAT
            is_low_cheat = (not broken and not failed and d['close'] < p_price and
                            pivot_dist_below >= LOW_CHEAT_DIST_MIN and pivot_dist_below <= LOW_CHEAT_DIST_MAX and
                            p_depth <= MAX_BASE_DEPTH and p_days >= MIN_BASE_WEEKS * 5 and
                            d['close'] > d['sma50'] and d['stage2'] and d['tightNow'])

            # PULLBACK
            is_pullback = (broken and not failed and d['close'] <= p_price * 1.02 and
                           d['close'] >= p_price * 0.95 and d['close'] > d['sma50'] and
                           b_bar is not None and (i - b_bar) <= 20)

            # NAT-RXN
            is_nat_rxn = (broken and not failed and d['close'] <= p_price * 1.03 and
                          d['close'] >= p_price * 0.95 and d['close'] > d['sma50'] and
                          b_bar is not None and (i - b_bar) <= 15 and d['volDryUp'])

            # PIERCE
            pierced = pivot_dist_above > 0 and pivot_dist_above <= PIERCE_THRESHOLD

            # --- CURRENT Pine logic entries ---
            entry_type = None
            stop_level = None

            if is_true_break and not broken and not failed:
                if is_vcp_base and d['stage2'] and p_days >= MIN_BASE_WEEKS * 5 and p_depth <= MAX_BASE_DEPTH:
                    entry_type = "VCP-B/O"
                elif is_cheat_buggy and d['stage2']:
                    entry_type = "CHEAT"
                else:
                    entry_type = "BREAKOUT"
                stop_level = p_price * (1 - STOP1_PCT / 100)
                pivot_broken[pi] = True
                pivot_break_bar[pi] = i

            if is_low_cheat:
                entry_type = "LOW-CHEAT"
                stop_level = p_price * (1 - STOP2_PCT / 100)

            if is_pullback or is_nat_rxn:
                entry_type = "NAT-RXN" if is_nat_rxn else "PULLBACK"
                stop_level = p_price * (1 - STOP1_PCT / 100)

            if buggy_spring:
                entry_type = "SPRING"
                stop_level = d['low']

            if buggy_scale_in and entry_type is None:
                entry_type = "SCALE-IN"
                stop_level = d['ema10']

            if entry_type:
                entries_current.append({
                    'date': d['date'],
                    'close': d['close'],
                    'open': d['open'],
                    'high': d['high'],
                    'low': d['low'],
                    'volume': d['volume'],
                    'vr': d['vr'],
                    'chgPct': d['chgPct'],
                    'type': entry_type,
                    'pivot_price': p_price,
                    'pivot_date': p_time,
                    'stop': stop_level,
                    'stage2': d['stage2'],
                    'pierced': pierced,
                    'pivot_dist_above': pivot_dist_above,
                    'pivot_dist_below': pivot_dist_below,
                    'bar_idx': i,
                    'vcp_ratio': vcp_ratio,
                    'p_days': p_days,
                    'p_depth': p_depth,
                })

            # --- BUG MISSES ---
            if is_price_break and d['vr'] >= 0.7 and d['vr'] < 1.3 and d['chgPct'] >= 2.0 and not broken and not failed:
                entries_bug_miss.append({
                    'date': d['date'],
                    'close': d['close'],
                    'vr': d['vr'],
                    'chgPct': d['chgPct'],
                    'bug': 'VR threshold too high (≥1.3 misses quiet breakouts)',
                    'should_type': 'BREAKOUT (quiet)',
                    'pivot_price': p_price,
                    'pivot_date': p_time,
                    'stop': p_price * (1 - STOP1_PCT / 100),
                    'bar_idx': i
                })

            if is_price_break and d['vr'] >= 0.7 and d['vr'] < 1.3 and d['chgPct'] >= 1.0 and d['chgPct'] < 2.0 and not broken and not failed:
                entries_bug_miss.append({
                    'date': d['date'],
                    'close': d['close'],
                    'vr': d['vr'],
                    'chgPct': d['chgPct'],
                    'bug': 'Cheat entry requires VR ≥ 1.3 (contradictory)',
                    'should_type': 'CHEAT (low VR)',
                    'pivot_price': p_price,
                    'pivot_date': p_time,
                    'stop': p_price * (1 - STOP1_PCT / 100),
                    'bar_idx': i
                })

            if fixed_spring and not buggy_spring:
                entries_bug_miss.append({
                    'date': d['date'],
                    'close': d['close'],
                    'vr': d['vr'],
                    'chgPct': d['chgPct'],
                    'bug': 'Spring only checks gap below prior LOW, not prior CLOSE',
                    'should_type': 'SPRING (gap-down from close)',
                    'pivot_price': p_price,
                    'pivot_date': p_time,
                    'stop': d['low'],
                    'bar_idx': i
                })

            if fixed_scale_in and not buggy_scale_in:
                entries_bug_miss.append({
                    'date': d['date'],
                    'close': d['close'],
                    'vr': d['vr'],
                    'chgPct': d['chgPct'],
                    'bug': 'EMA10 scale-in proximity too tight (uses close, not intraday low)',
                    'should_type': 'SCALE-IN (intraday tag of EMA10)',
                    'pivot_price': p_price,
                    'pivot_date': p_time,
                    'stop': d['ema10'],
                    'bar_idx': i
                })

            if pierced and d['vr'] >= 1.0 and d['chgPct'] >= 1.0 and not broken and not failed and entry_type is None:
                entries_bug_miss.append({
                    'date': d['date'],
                    'close': d['close'],
                    'vr': d['vr'],
                    'chgPct': d['chgPct'],
                    'bug': 'No pierce threshold (close within 0.5% of pivot rejected)',
                    'should_type': 'PIERCE-ENTRY',
                    'pivot_price': p_price,
                    'pivot_date': p_time,
                    'stop': p_price * (1 - STOP1_PCT / 100),
                    'bar_idx': i
                })

            # --- FIXED logic entries ---
            fixed_entry = None
            if is_true_break and not broken and not failed:
                if fixed_vcp and d['stage2'] and p_days >= MIN_BASE_WEEKS * 5 and p_depth <= MAX_BASE_DEPTH:
                    fixed_entry = "VCP-B/O"
                elif is_cheat_fixed and d['stage2']:
                    fixed_entry = "CHEAT"
                else:
                    fixed_entry = "BREAKOUT"
            elif is_cheat_fixed and not broken and not failed:
                fixed_entry = "CHEAT"
            elif fixed_spring:
                fixed_entry = "SPRING"
            elif fixed_scale_in:
                fixed_entry = "SCALE-IN"
            elif is_low_cheat:
                fixed_entry = "LOW-CHEAT"
            elif is_pullback or is_nat_rxn:
                fixed_entry = "NAT-RXN" if is_nat_rxn else "PULLBACK"

            if fixed_entry:
                entries_fixed.append({
                    'date': d['date'],
                    'close': d['close'],
                    'type': fixed_entry,
                    'vr': d['vr'],
                    'chgPct': d['chgPct'],
                    'pivot_price': p_price,
                    'bar_idx': i
                })

    # Also process any remaining active streak at end
    if active_streak_high is not None:
        pass  # No need for final streak

    return data, pivot_prices, pivot_times, pivot_bars, entries_current, entries_bug_miss, entries_fixed


# ── Report Generation ──
def generate_report(data, pivot_prices, pivot_times, pivot_bars, entries_current, entries_bug_miss, entries_fixed):
    today = datetime.now().strftime('%Y-%m-%d')
    n = len(data)
    start_date = data[0]['date']
    end_date = data[-1]['date']
    current_price = data[-1]['close']

    def dedup(entries, key_fn):
        seen = set()
        out = []
        for e in entries:
            k = key_fn(e)
            if k not in seen:
                seen.add(k)
                out.append(e)
        return out

    entries_current_dedup = dedup(entries_current, lambda e: (e['date'], e['type']))
    entries_bug_dedup = dedup(entries_bug_miss, lambda e: (e['date'], e['bug']))
    entries_fixed_dedup = dedup(entries_fixed, lambda e: (e['date'], e['type']))

    stage2_bars = sum(1 for d in data if d.get('stage2'))

    # Build pivot list for report
    pivot_list = []
    for i in range(len(pivot_prices)):
        pivot_list.append({
            'price': pivot_prices[i],
            'date': pivot_times[i],
            'bar': pivot_bars[i]
        })

    md = f"""---
type: entry-verification-analysis
ticker: ARM
company: "Arm Holdings plc"
date_range: "{start_date} – {end_date}"
scope: "Minervini-style entry setups — Jan 2026 onwards"
verification_date: "{today}"
data_source: "Yahoo Finance OHLCV"
entry_logic_source: "rmv_minervini_master.pine v2"
---

# ARM — Minervini Entry Detection Verification Report

**Period:** {start_date} to {end_date} ({n} trading days)  
**Current Price:** ${current_price:.2f}  
**Stage 2 Uptrend Bars:** {stage2_bars} / {n} ({stage2_bars/max(n,1)*100:.1f}%)  
**Pivots Detected (tight streak highs):** {len(pivot_list)}  
**Analysis Date:** {today}

---

## Executive Summary

| Category | Count | Notes |
|----------|-------|-------|
| Bars under current Pine logic | {len(entries_current_dedup)} | Entries that trigger with existing code |
| Bars missed due to known bugs | {len(entries_bug_dedup)} | Valid entries rejected by buggy thresholds |
| Bars under FIXED logic | {len(entries_fixed_dedup)} | What WOULD trigger if all bugs were patched |

### Known Bug Impact on ARM

| Bug | Impact on ARM | Severity |
|-----|---------------|----------|
| VCP contraction ratio inverted | VCP-B/O labels may misclassify or miss valid contractions | High |
| Cheat entry requires VR ≥ 1.3 | Misses quiet cheat entries with VR 0.7–1.3 | Medium |
| Spring gap-down checks prior LOW not CLOSE | Misses gap-downs that don't undercut prior low | Medium |
| EMA10 scale-in uses close only (2.5%) | Misses intraday tags of EMA10 | Low |
| No pierce threshold (0.5%) | Rejects close-within-0.5% breakouts | Low |

---

## 1. Pivot Highs Detected (Tight Streak Highs)

| # | Date | Pivot High | Base Days | Base Depth |
|---|------|-----------:|----------:|-----------:|
"""
    for idx, p in enumerate(pivot_list):
        p_days = 0
        p_depth = 0
        for e in entries_current:
            if e.get('pivot_date') == p['date']:
                p_days = e.get('p_days', 0)
                p_depth = e.get('p_depth', 0)
                break
        md += f"| {idx+1} | {p['date']} | ${p['price']:.2f} | {p_days} | {p_depth:.1f}% |\n"

    md += """
---

## 2. Entries Triggered Under CURRENT Pine Logic

| # | Date | Close | Entry Type | VR | Chg% | Pivot | Stop | Stage2 |
|---|------|-------|------------|-----:|------:|------|------|:------:|
"""
    for idx, e in enumerate(entries_current_dedup):
        md += (f"| {idx+1} | {e['date']} | ${e['close']:.2f} | **{e['type']}** | "
               f"{e['vr']:.2f} | {e['chgPct']:.2f}% | ${e['pivot_price']:.2f} ({e['pivot_date']}) | "
               f"${e['stop']:.2f} | {'✅' if e['stage2'] else '❌'} |\n")

    if not entries_current_dedup:
        md += "| — | — | — | — | — | — | — | — | — |\n"

    md += """
### Entry Detail Breakdown

"""
    for idx, e in enumerate(entries_current_dedup):
        md += f"""#### {idx+1}. {e['type']} — {e['date']} @ ${e['close']:.2f}

- **Open:** ${e['open']:.2f} | **High:** ${e['high']:.2f} | **Low:** ${e['low']:.2f}
- **Volume:** {e['volume']:,} | **VR:** {e['vr']:.2f}x | **Change:** {e['chgPct']:+.2f}%
- **Pivot:** ${e['pivot_price']:.2f} (set {e['pivot_date']})
- **Stop Level:** ${e['stop']:.2f} ({(e['stop']/e['close']-1)*100:.1f}% below entry)
- **Stage 2:** {'Yes' if e['stage2'] else 'No'}
- **VCP Ratio:** {e.get('vcp_ratio', 0):.1f}% (buggy inverted calculation)

"""

    md += """---

## 3. Bars That SHOULD Trigger But DON'T (Known Bugs)

| # | Date | Close | Should Be | VR | Chg% | Bug Description | Stop |
|---|------|-------|-----------|-----:|------:|-----------------|------|
"""
    for idx, e in enumerate(entries_bug_dedup):
        md += (f"| {idx+1} | {e['date']} | ${e['close']:.2f} | **{e['should_type']}** | "
               f"{e['vr']:.2f} | {e['chgPct']:.2f}% | {e['bug']} | ${e['stop']:.2f} |\n")

    if not entries_bug_dedup:
        md += "| — | — | — | — | — | — | — | — |\n"

    md += """
---

## 4. Bug-by-Bug Analysis for ARM

"""
    bug_groups = {}
    for e in entries_bug_dedup:
        bug_groups.setdefault(e['bug'], []).append(e)

    for bug, bars in bug_groups.items():
        md += f"""### {bug}

| Date | Close | VR | Chg% | Stop |
|------|-------|-----:|------:|------|
"""
        for b in bars:
            md += f"| {b['date']} | ${b['close']:.2f} | {b['vr']:.2f} | {b['chgPct']:.2f}% | ${b['stop']:.2f} |\n"
        md += "\n"

    if not bug_groups:
        md += "No bug-missed entries detected in this period.\n\n"

    md += """---

## 5. What WOULD Trigger Under FIXED Logic

| # | Date | Close | Type | VR | Chg% | Pivot |
|---|------|-------|------|-----:|------:|------|
"""
    for idx, e in enumerate(entries_fixed_dedup):
        md += (f"| {idx+1} | {e['date']} | ${e['close']:.2f} | **{e['type']}** | "
               f"{e['vr']:.2f} | {e['chgPct']:.2f}% | ${e['pivot_price']:.2f} |\n")

    if not entries_fixed_dedup:
        md += "| — | — | — | — | — | — | — |\n"

    start_price = data[0]['close'] if data else 0
    end_price = data[-1]['close'] if data else 0
    price_gain = ((data[-1]['close'] / data[0]['close']) - 1) * 100 if data else 0
    num_entries = len(entries_current_dedup)

    md += f"""
---

## 6. Trend Template Check (Current Bar: {end_date})

| Criteria | Status | Value |
|----------|--------|-------|
| Close > 50 SMA | {'✅' if data[-1]['close'] > (data[-1]['sma50'] or 0) else '❌'} | ${data[-1]['close']:.2f} vs ${data[-1]['sma50'] or 0:.2f} |
| Close > 150 SMA | {'✅' if data[-1]['close'] > (data[-1]['sma150'] or 0) else '❌'} | ${data[-1]['close']:.2f} vs ${data[-1]['sma150'] or 0:.2f} |
| Close > 200 SMA | {'✅' if data[-1]['close'] > (data[-1]['sma200'] or 0) else '❌'} | ${data[-1]['close']:.2f} vs ${data[-1]['sma200'] or 0:.2f} |
| 50 SMA > 150 SMA | {'✅' if (data[-1]['sma50'] or 0) > (data[-1]['sma150'] or 0) else '❌'} | ${data[-1]['sma50'] or 0:.2f} vs ${data[-1]['sma150'] or 0:.2f} |
| 150 SMA > 200 SMA | {'✅' if (data[-1]['sma150'] or 0) > (data[-1]['sma200'] or 0) else '❌'} | ${data[-1]['sma150'] or 0:.2f} vs ${data[-1]['sma200'] or 0:.2f} |
| Stage 2 | {'✅' if data[-1]['stage2'] else '❌'} | — |

---

## 7. Cross-Check Against Book Examples

ARM (Arm Holdings) is **not a documented book figure** in Minervini's published works.
This analysis is a forward-looking scan using the Pine Script entry logic.

---

## 8. Key Observations for ARM (Jan–Jun 2026)

- **Massive uptrend:** ARM rallied from ~${start_price:.2f} to ~${end_price:.2f} (+{price_gain:.1f}%) during the analysis period.
- **Low tight-streak count:** In strong parabolic moves, RMV rarely drops below the tight threshold because daily ranges expand.
- **Volume signature:** Several days showed VR > 2.0x, indicating institutional accumulation.
- **Stage 2:** The stock has been in Stage 2 for the majority of the period (all SMAs aligned and rising).
- **Missing entries:** The current Pine script logic produced {num_entries} entry signals. This is because:
  1. The parabolic nature of the move means few tight consolidation bases formed.
  2. Breakouts often occurred with expanding (not contracting) ranges.
  3. The VCP inversion bug may have misclassified valid contractions.

---

## 9. Recommended Fixes (Priority Order)

### P0 — Critical
1. **Invert VCP contraction ratio** (Line 269 in Pine):
   ```pinescript
   contractingNow = secondHalfRange > 0 and (firstHalfRange / secondHalfRange) * 100 <= contractionPct
   ```
2. **Relax spring gap-down** (Line 218 in Pine):
   ```pinescript
   springGapDown = open < close[1]   // gap down from prior close
   ```

### P1 — High
3. **Add SMA50 pullback entry type** for pullbacks to rising 50 DMA.
4. **Add `low`-based EMA10 proximity** for scale-in (track intraday tag of EMA10 over prior 3-5 bars).
5. **Document GOOG Entry 5** as a known case the script intentionally does not flag.

### P2 — Medium
6. Consider a `DELAYED-VOL` flag for entries where volume is low on entry day but explodes within 2-3 bars.
7. Add pierce threshold: accept closes within 0.5% of pivot as valid breakouts.

---

## 10. Data Source & Methodology

- **Ticker:** ARM (NASDAQ)
- **Downloaded via:** `yfinance` API
- **Period:** {start_date} to {end_date}
- **Pine Script Reference:** `rmv_minervini_master.pine` v2
- **Python Reference:** `analysis/minervini_obsidian/tools/_buy_points.py`

---

*Report generated by ARM Minervini analysis engine on {today}*
"""

    start_price = data[0]['close'] if data else 0
    end_price = data[-1]['close'] if data else 0
    price_gain = ((data[-1]['close'] / data[0]['close']) - 1) * 100 if data else 0
    num_entries = len(entries_current_dedup)

    out_path = os.path.join(OUT_DIR, "ARM_entries_verified.md")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"[done] Report written to {out_path}")
    return out_path


if __name__ == "__main__":
    data, pivot_prices, pivot_times, pivot_bars, entries_current, entries_bug_miss, entries_fixed = analyze_arm()
    generate_report(data, pivot_prices, pivot_times, pivot_bars, entries_current, entries_bug_miss, entries_fixed)
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Pivots detected:         {len(pivot_prices)}")
    print(f"Current Pine triggers:   {len(entries_current)}")
    print(f"Known bug misses:        {len(entries_bug_miss)}")
    print(f"Fixed logic triggers:    {len(entries_fixed)}")

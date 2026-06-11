"""
MINERVINI SEPA ANALYZER v2.0 - Enhanced with Failure/Sell Pattern Detection
===========================================================================
Usage: python _minervini_sepa_v2.py TICKER [--verbose]
       python _minervini_sepa_v2.py TICKER --sell-only
       python _minervini_sepa_v2.py TICKER --buy-only
Example: python _minervini_sepa_v2.py WAGE
         python _minervini_sepa_v2.py NETWEB

Detects both:
  -> BUY patterns: VCP tightening, volume dry-up, shakeouts, coils, resistance tests
  -> SELL/FAILURE patterns: Failed breakouts, distribution, low-vol-out/high-vol-in,
     MA violations, late-stage base failures
"""

import csv
import sys
import os

T = sys.argv[1].upper() if len(sys.argv) > 1 else exit(print("Usage: python _minervini_sepa_v2.py TICKER [--verbose]"))
VERBOSE = "--verbose" in sys.argv
SELL_ONLY = "--sell-only" in sys.argv
BUY_ONLY = "--buy-only" in sys.argv

D = os.path.join(os.path.dirname(__file__), "..", "data")


def S(data, n, i):
    """Simple moving average at index i over n periods"""
    if i < n - 1:
        return None
    return sum(data[i - n + 1:i + 1]) / n


def compute_sma(data, n):
    """Compute SMA array for all points"""
    return [S(data, n, i) if i >= n - 1 else None for i in range(len(data))]


def detect_buy_patterns(dates, c, hh, ll, o, v, sma20, sma50):
    """Detect Minervini BUY patterns (VCP, coils, shakeouts, etc.)"""
    cans = []
    v50_arr = compute_sma(v, 50)

    for i in range(100, len(c)):
        v50 = v50_arr[i]
        vr = v[i] / v50 if v50 and v50 > 0 else 0
        pchg = (c[i] / c[i - 1] - 1) * 100

        if vr >= 1.3 and pchg >= 2:
            s = max(0, i - 20)
            pr = (max(hh[s:i]) - min(ll[s:i])) / min(ll[s:i]) * 100
            uwl = [(hh[j] - max(o[j], c[j])) / (hh[j] - ll[j]) * 100
                   for j in range(max(0, i - 10), i) if hh[j] - ll[j] > 0]
            uw = sum(uwl) / max(1, len(uwl))

            # Resistance test count (52-week high touches)
            h80 = max(hh[max(0, i - 80):i])
            rt = sum([1 for j in range(max(0, i - 80), i - 3) if hh[j] >= h80 * 0.97])

            # Shakeout and coil detection
            shake = False
            coil = False
            for j in range(max(0, i - 12), i - 1):
                rng = (hh[j] - ll[j]) / c[j] * 100
                v50j = v50_arr[j]
                vrj = v[j] / v50j if v50j and v50j > 0 else 0
                if rng > 5 and vrj > 2:
                    shake = True
                if rng < 3 and vrj < 0.6:
                    coil = True

            labels = []
            if pr <= 12 and uw < 35:
                labels.append(f"TIGHT({round(pr,1)}%)")
            if rt >= 2:
                labels.append(f"{rt}X-RESIST")
            if shake:
                labels.append("SHAKE")
            if coil:
                labels.append("COIL")
            if not labels:
                labels.append("NO-PATTERN")

            cans.append({
                "date": dates[i], "price": c[i], "vr": round(vr, 1),
                "chg": round(pchg, 1), "pr": round(pr, 1), "uw": round(uw, 1),
                "idx": i, "labels": labels, "type": "BUY"
            })

    return cans


def detect_sell_patterns(dates, c, hh, ll, o, v, sma20, sma50):
    """
    Detect Minervini SELL/FAILURE patterns:

    1. FAILED BREAKOUT - Low VR into breakout, high VR on reversal within 5 days
    2. DISTRIBUTION - 3+ lower lows on increasing volume
    3. LOW VOL OUT / HIGH VOL IN - Breakout VR<1.3, reversal VR>2.0
    4. 20-day MA VIOLATION - Close below 20-day SMA on elevated volume
    5. 50-day MA VIOLATION - Close below 50-day SMA on elevated volume
    6. LATE-STAGE BASE FAILURE - Base #3+ breakout that fails
    """
    signals = []
    v50_arr = compute_sma(v, 50)

    for i in range(120, len(c)):
        v50 = v50_arr[i]
        vr = v[i] / v50 if v50 and v50 > 0 else 0
        pchg = (c[i] / c[i - 1] - 1) * 100

        # === PATTERN 1: FAILED BREAKOUT ===
        # A day that looked like a breakout (price up, but VR was low)
        # followed by reversal(s) with high volume within the next 5 days
        if i >= 5:
            for lookback in range(1, 6):
                prev = i - lookback
                prev_v50 = v50_arr[prev]
                prev_vr = v[prev] / prev_v50 if prev_v50 and prev_v50 > 0 else 0
                prev_chg = (c[prev] / c[prev - 1] - 1) * 100

                # Was there a low-volume breakout attempt?
                if prev_chg >= 1.5 and prev_vr < 1.3:
                    # Now we're in the reversal phase: price down, VR elevated
                    if pchg <= -1.5 and vr >= 1.5:
                        # Check if low of today is below the breakout day's low
                        if ll[i] < ll[prev] and c[i] < c[prev]:
                            days_since = lookback
                            severity = "MODERATE"
                            if vr >= 1.8 and pchg <= -2.0:
                                severity = "SEVERE"
                            if vr >= 2.5 or (vr >= 1.8 and pchg <= -3.5):
                                severity = "CRITICAL"

                            labels = [f"FAILED-BREAKOUT({severity})"]
                            labels.append(f"B/O-VR:{round(prev_vr,1)} Rev-VR:{round(vr,1)}")
                            labels.append(f"B/O-Day:{dates[prev]}")

                            signals.append({
                                "date": dates[i], "price": round(c[i], 2),
                                "vr": round(vr, 1), "chg": round(pchg, 1),
                                "idx": i, "labels": labels, "type": "SELL-FAILED-BREAKOUT"
                            })
                            break  # Only flag the first match

        # === PATTERN 2: DISTRIBUTION (3+ Lower Lows, Increasing Volume) ===
        if i >= 3:
            # Check if current bar has: lower low, lower close, higher volume than previous
            ll_lower = all(ll[i - k] < ll[i - k - 1] for k in range(3))
            c_lower = all(c[i - k] < c[i - k - 1] for k in range(3))
            v_increasing = all(v[i - k] > v[i - k - 1] for k in range(2))

            if ll_lower and c_lower and v_increasing:
                vol_trend = [round(v[i - k] / v50_arr[i - k], 1) if v50_arr[i - k] and v50_arr[i - k] > 0 else 0
                             for k in range(3)]
                labels = ["DISTRIBUTION(3-LL)"]
                if vr >= 2.0:
                    labels.append(f"VOL-SURGE(x{round(vr,1)})")
                labels.append(f"Lows:{round(ll[i-2],1)}>{round(ll[i-1],1)}>{round(ll[i],1)}")

                signals.append({
                    "date": dates[i], "price": round(c[i], 2),
                    "vr": round(vr, 1), "chg": round(pchg, 1),
                    "idx": i, "labels": labels, "type": "SELL-DISTRIBUTION"
                })

        # === PATTERN 3: LOW VOL OUT / HIGH VOL IN ===
        if i >= 2 and pchg <= -2.0 and vr >= 2.0:
            # Check if the prior 3-10 days had low volume advance
            for lookback in range(3, 11):
                if i - lookback < 0:
                    break
                pb = i - lookback
                pb_v50 = v50_arr[pb]
                pb_vr = v[pb] / pb_v50 if pb_v50 and pb_v50 > 0 else 0
                pb_chg = (c[pb] / c[pb - 1] - 1) * 100

                if pb_chg >= 1.0 and pb_vr < 1.3:
                    # Count how many green days with low volume in the window
                    low_vol_days = 0
                    up_days = 0
                    for j in range(pb, i):
                        j_v50 = v50_arr[j]
                        j_vr = v[j] / j_v50 if j_v50 and j_v50 > 0 else 0
                        j_chg = (c[j] / c[j - 1] - 1) * 100
                        if j_chg > 0 and j_vr < 1.3:
                            low_vol_days += 1
                        if j_chg > 0:
                            up_days += 1

                    if low_vol_days >= 1 and up_days >= 1:
                        labels = ["LOW-VOL-OUT-HIGH-VOL-IN"]
                        labels.append(f"Up:{low_vol_days}xLowVol>DownVR:{round(vr,1)}")
                        signals.append({
                            "date": dates[i], "price": round(c[i], 2),
                            "vr": round(vr, 1), "chg": round(pchg, 1),
                            "idx": i, "labels": labels, "type": "SELL-VOLUME-TRAP"
                        })
                        break

        # === PATTERN 4: 20-day MA VIOLATION on High Volume ===
        if sma20[i] is not None and c[i] < sma20[i] and vr >= 1.5:
            # Check if previous day was above 20-day (to catch the VIOLATION, not just being below)
            was_above = sma20[i - 1] is not None and c[i - 1] >= sma20[i - 1]
            if was_above or (i >= 2 and c[i - 1] < sma20[i - 1] and vr >= 2.0):
                labels = [f"20-MA-VIOLATION(VR:{round(vr,1)})"]
                if pchg <= -2:
                    labels.append("BREAKDOWN")

                signals.append({
                    "date": dates[i], "price": round(c[i], 2),
                    "vr": round(vr, 1), "chg": round(pchg, 1),
                    "idx": i, "labels": labels, "type": "SELL-MA20-VIOLATION"
                })

        # === PATTERN 5: 50-day MA VIOLATION on High Volume (MORE SEVERE) ===
        if sma50[i] is not None and c[i] < sma50[i] and vr >= 1.5:
            was_above_50 = sma50[i - 1] is not None and c[i - 1] >= sma50[i - 1]
            if was_above_50 or (i >= 2 and c[i - 1] < sma50[i - 1] and vr >= 2.0):
                labels = [f"50-MA-VIOLATION(VR:{round(vr,1)})"]
                if pchg <= -3:
                    labels.append("MAJOR-BREAKDOWN")
                if c[i] < (sma20[i] if sma20[i] else 0):
                    labels.append("20+50-CROSS-BELOW")

                signals.append({
                    "date": dates[i], "price": round(c[i], 2),
                    "vr": round(vr, 1), "chg": round(pchg, 1),
                    "idx": i, "labels": labels, "type": "SELL-MA50-VIOLATION"
                })

        # === PATTERN 6: LATE-STAGE BASE FAILURE ===
        # Detect if this is late-stage (3rd+ base) by counting prior VCP-like contractions
        if i >= 200 and pchg <= -2.0 and vr >= 1.8:
            # Count VCP bases in the last 200 bars
            base_count = 0
            base_starts = []
            for j in range(100, i - 50):
                lookback_range = min(hh[j - 20:j + 1])  # low of recent 20
                lookback_range_pct = (max(hh[j - 20:j + 1]) - min(ll[j - 20:j + 1])) / min(ll[j - 20:j + 1]) * 100
                # A base candidate: 20-bar range < 15% and price near highs
                if lookback_range_pct < 15 and c[j] > max(c[j - 20:j]) * 0.95:
                    # Check if this is distinct from previous base (separated by at least 30 bars)
                    if not base_starts or j - base_starts[-1] > 30:
                        base_count += 1
                        base_starts.append(j)

            if base_count >= 3:
                labels = [f"LATE-STAGE-BASE(base#{base_count})"]
                labels.append(f"FAILED(low-vol-out)")

                signals.append({
                    "date": dates[i], "price": round(c[i], 2),
                    "vr": round(vr, 1), "chg": round(pchg, 1),
                    "idx": i, "labels": labels, "type": "SELL-LATE-STAGE"
                })

    return signals


def bar_by_bar_replay(dates, c, hh, ll, o, v, sma20, sma50):
    """Scan the critical window for this ticker and replay key bars"""
    print("\n=== BAR-BY-BAR REPLAY (Critical Zone) ===")
    print(f"{'Date':<14} {'Open':>8} {'High':>8} {'Low':>8} {'Close':>8} {'Chg%':>7} {'Vol':>10} {'VR':>6} {'SMA20':>8} {'SMA50':>8} {'Signal':<35}")
    print("-" * 130)

    signals = []

    for i in range(max(100, len(c) - 80), len(c)):
        v50 = S(v, 50, i)
        vr = v[i] / v50 if v50 and v50 > 0 else 0
        pchg = (c[i] / c[i - 1] - 1) * 100

        # Detect ALL patterns per bar
        bar_signals = []

        # Failed breakout
        if i >= 5:
            for lookback in range(1, 6):
                prev = i - lookback
                prev_v50 = S(v, 50, prev)
                prev_vr = v[prev] / prev_v50 if prev_v50 and prev_v50 > 0 else 0
                prev_chg = (c[prev] / c[prev - 1] - 1) * 100
                if prev_chg >= 1.5 and prev_vr < 1.3 and pchg <= -1.5 and vr >= 1.5 and ll[i] < ll[prev]:
                    bar_signals.append(f"FAILED-B/O(d{lookback} VR:{round(vr,1)})")
                    break

        # Distribution
        if i >= 3:
            if all(ll[i - k] < ll[i - k - 1] for k in range(3)) and \
               all(c[i - k] < c[i - k - 1] for k in range(3)) and \
               all(v[i - k] > v[i - k - 1] for k in range(2)):
                bar_signals.append(f"DISTRIBUTION-3LL(VR:{round(vr,1)})")

        # Low vol out, high vol in
        if i >= 2 and pchg <= -2.0 and vr >= 2.0:
            for lookback in range(3, 11):
                if i - lookback < 0:
                    break
                pb = i - lookback
                pb_v50 = S(v, 50, pb)
                pb_vr = v[pb] / pb_v50 if pb_v50 and pb_v50 > 0 else 0
                pb_chg = (c[pb] / c[pb - 1] - 1) * 100
                if pb_chg >= 1.0 and pb_vr < 1.3:
                    bar_signals.append("LOW-VOL-OUT/HIGH-VOL-IN")
                    break

        # MA violations
        if sma20[i] is not None and c[i] < sma20[i] and vr >= 1.5:
            bar_signals.append("BELOW-20-MA")
        if sma50[i] is not None and c[i] < sma50[i] and vr >= 1.5:
            bar_signals.append("BELOW-50-MA!!!")

        signal_str = "; ".join(bar_signals) if bar_signals else ""

        # Print the bar (show all bars with signals or key bars)
        if bar_signals or abs(pchg) >= 2 or vr >= 1.5:
            print(f"{dates[i]:<14} {o[i]:>8.2f} {hh[i]:>8.2f} {ll[i]:>8.2f} {c[i]:>8.2f} {pchg:>7.2f} {v[i]:>10,d} {vr:>6.2f} {sma20[i] if sma20[i] else 0:>8.2f} {sma50[i] if sma50[i] else 0:>8.2f}  {signal_str:<35}")

    print("-" * 130)


def analyze_ticker(t):
    """Main analysis function"""
    fp = os.path.join(D, f"{t}_ohlcv.csv")
    if not os.path.exists(fp):
        print(f"Not found: {fp}")
        return

    with open(fp) as f:
        r = csv.reader(f)
        h = next(r)
        rows = list(r)

    # Parse columns: Date(0), AdjClose(1), Close(2), High(3), Low(4), Open(5), Volume(6)
    dates = [x[0] for x in rows]
    c = [float(x[2]) for x in rows]
    hh = [float(x[3]) for x in rows]
    ll = [float(x[4]) for x in rows]
    o = [float(x[5]) for x in rows]
    v = [int(x[6]) if x[6] else 0 for x in rows]

    # Compute moving averages
    sma20 = compute_sma(c, 20)
    sma50 = compute_sma(c, 50)

    print(f"\n{'=' * 80}")
    print(f"  MINERVINI SEPA ANALYZER v2.0 - {t}")
    print(f"  {len(rows)} sessions, {dates[0]} to {dates[-1]}")
    print(f"{'=' * 80}")

    # ---- BUY PATTERNS ----
    if not SELL_ONLY:
        buy_signals = detect_buy_patterns(dates, c, hh, ll, o, v, sma20, sma50)
        print(f"\n>>> BUY PATTERNS (VR>=1.3, Chg>=2%): {len(buy_signals)} candidates")
        if buy_signals:
            for bs in buy_signals:
                print(f"  {bs['date']} C:{int(bs['price'])} VR:{bs['vr']} Chg:{bs['chg']}% >> {' '.join(bs['labels'])}")
        print(f"  Total Buy Candidates: {len(buy_signals)}")

    # ---- SELL/FAILURE PATTERNS ----
    if not BUY_ONLY:
        sell_signals = detect_sell_patterns(dates, c, hh, ll, o, v, sma20, sma50)
        print(f"\n>>> SELL/FAILURE PATTERNS: {len(sell_signals)} signals")

        # Group by type
        by_type = {}
        for sig in sell_signals:
            st = sig['type']
            if st not in by_type:
                by_type[st] = []
            by_type[st].append(sig)

        for stype, signals in sorted(by_type.items()):
            print(f"\n  [{stype}] ({len(signals)} occurrences):")
            for sig in signals[:10]:  # Show max 10 per type
                print(f"    {sig['date']} C:{sig['price']} VR:{sig['vr']} Chg:{sig['chg']}% >> {' '.join(sig['labels'])}")
            if len(signals) > 10:
                print(f"    ... and {len(signals) - 10} more")

        # Summary
        if sell_signals:
            print(f"\n  SELL SIGNAL SUMMARY:")
            critical = [s for s in sell_signals if 'CRITICAL' in ' '.join(s['labels']) or 'MAJOR' in ' '.join(s['labels']) or '50-MA' in s['type']]
            severe = [s for s in sell_signals if 'SEVERE' in ' '.join(s['labels']) or '20-MA' in s['type']]
            print(f"    CRITICAL (50-MA violation / major breakdown): {len(critical)}")
            print(f"    SEVERE (20-MA violation / severe reversal):   {len(severe)}")
            print(f"    MODERATE (distribution / volume traps):       {len(sell_signals) - len(critical) - len(severe)}")
        else:
            print(f"\n  ✅ No sell/failure patterns detected")

        print(f"  Total Sell Signals: {len(sell_signals)}")

    # ---- BAR-BY-BAR REPLAY ----
    if VERBOSE:
        bar_by_bar_replay(dates, c, hh, ll, o, v, sma20, sma50)


if __name__ == "__main__":
    analyze_ticker(T)

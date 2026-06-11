# GOOG (Google) — In-Depth 5-Entry Analysis

## Source Files Used

| # | File | Path |
|---|---|---|
| 1 | Bar-by-Bar Candle Analysis (original doc) | `CLAUDE\MINERVINI_CANDLE_NATURE_BAR_BY_BAR_REPLAY.md` |
| 2 | Book: Figure 10-52 — GOOG (p260) | `analysis\minervini_obsidian\Book Stock Images\Trade Like a Stock Market Wizard - Figure 10-52 - GOOG - page 260.md` |
| 3 | Book: Figure 7-14 — GOOG (p136) | `analysis\minervini_obsidian\Book Stock Images\Think and Trade Like a Champion - Figure 7-14 - GOOG - page 136.md` |
| 4 | OHLCV Data (2004-2006) — Fig 10-52 | `analysis\minervini_obsidian\data\book_stock_images\trade-like-a-stock-market-wizard-figure-10-52-goog-page-260_ohlcv.csv` |
| 5 | OHLCV Data (2004-2015) — Fig 7-14 | `analysis\minervini_obsidian\data\book_stock_images\think-and-trade-like-a-champion-figure-7-14-goog-page-136_ohlcv.csv` |
| 6 | OHLCV Data (GOOGL, 2004-2006) — Fig 1-8 | `analysis\minervini_obsidian\data\book_stock_images\think-and-trade-like-a-champion-figure-1-8-googl-page-34_ohlcv.csv` |
| 7 | Pivot Detection Code | `minervini_dashboard\concepts\pivot_entry.py` |
| 8 | VCP Detection Code | `minervini_dashboard\concepts\vcp.py` |
| 9 | Market-Wide Scanner (cheat area logic) | `tools\minervini_market_wide_scanner.py` |

---

## Overview

**Ticker:** GOOG (Google)
**Date Range:** Aug 2004 — Nov 2007
**Total Entries:** 5 sequential entries on the same stock across multiple bases
**Final Exit:** Nov 8, 2007 (broke below fast moving MA)
**Peak Price:** $18.48 (Nov 6, 2007)
**Exit Price:** ~$17.28 (Nov 8, 2007)
**Book Reference:** *Think and Trade Like a Champion* (Figure 7-14, p136) — *"Google came public in 2004. Stock emerged from a low cheat and then soared 625 percent in 40 months."*

---

## Trade Entry 1: Apr 22, 2005 — VCP Breakout (Weekly Close)

### Setup Structure

**VCP (Oct 2004 → Mar 2005):**

| Week | Range | VRatio | Phase |
|---|---|---|---|
| 2004-10-29 | 15.9% | — | Trend peak $5.02 |
| 2004-11-05 | 19.6% | — | Pullback |
| 2005-03-04 | **4.3%** | **0.74x** | Contraction begins |
| 2005-03-25 | **2.8%** | **0.41x** | **TIGHTEST — VCP climax** |

### Daily Entry Window

| Date | Open | High | Low | Close | Volume | Note |
|---|---|---|---|---|---|---|
| Apr 20 | 4.95 | 4.99 | 4.88 | 4.93 | 620M | Testing $5.02 |
| Apr 21 | 4.99 | **5.11** | 4.96 | 5.09 | 713M | First close above $5.02 |
| **Apr 22** | **5.55** | **5.58** | **5.34** | **5.38** | **1,333M** | **Entry — gap up weekly close** |
| May 3 | 5.53 | **5.68** | 5.51 | 5.63 | 714M | New pivot $5.61 |

### Post-Entry: The Pole (Apr 18 → Jun 20, 2005)

```
Apr 22:  $5.38 ← Entry
May 6:   $5.68 (H=$5.73)
May 27:  $6.63 (H=$6.63)
Jun 10:  $7.04 (H=$7.46) ← POLE TOP (+48%)
Jun 17:  $6.98 ← Pullback begins
```

### Parameters

| Parameter | Value |
|---|---|
| **Pivot** | $5.02 (Oct 2004 weekly high) |
| **Secondary Pivot** | $5.61 (May 3 daily high — consolidation above VCP) |
| **Entry Price** | ~$5.38 (weekly close) |
| **Entry Type** | Momentum gap-up after VCP completion |
| **Pole Range** | $5.02 → $7.46 (+48% in ~8 weeks) |

---

## Trade Entry 2: Oct 21, 2005 — Flag & Pole Breakout (Weekly Close)

### Setup Structure

**Flag Formation (Jun 20 → Oct 21, 2005):**

| Phase | Weeks | Range | Volume | Action |
|---|---|---|---|---|
| Pole | Apr → Jun | $5.02 → $7.46 | Declining | Run |
| Correction | Jun 17 → Jul 29 | 5.7-6.3% | VR=0.78-1.16x | Pullback |
| Dry-up | Aug 5 → Sep 9 | 2.7-6.5% | VR=0.41-0.69x | **Volume drying** |
| Flag tight | Sep → Oct | Tight | VR=0.7-1.1x | Staircase pattern |
| **Breakout** | **Oct 21** | **17.6%** | **VR=1.13x** | **Entry** |

### Daily Entry Window

| Date | Open | High | Low | Close | Volume | Note |
|---|---|---|---|---|---|---|
| Oct 17 | 7.41 | 7.60 | 7.34 | 7.60 | 304M | Flag low |
| Oct 18 | 7.60 | 7.67 | 7.54 | 7.55 | 284M | Tight |
| Oct 19 | 7.57 | 7.72 | 7.57 | 7.69 | 281M | Pushing up |
| Oct 20 | 7.72 | 7.75 | 7.50 | 7.55 | 559M | Rejected near $8 |
| **Oct 21** | **8.61** | **8.63** | **8.29** | **8.47** | **919M** | **Gap up — weekly close entry** |

### Parameters

| Parameter | Value |
|---|---|
| **Pivot** | $8.00 (flag resistance) |
| **Entry Price** | ~$8.47 (weekly close) |
| **Entry Type** | Flag & pole continuation breakout |

---

## Trade Entry 3: Oct 6, 2006 — Classic VCP Pullback Entry (Weekly Close)

### Setup Structure

**VCP (Jan 12 → Oct 20, 2006):**

| Week | Range | VRatio | Note |
|---|---|---|---|
| Jan 13 | 3.1% | 0.93x | Doji at pivot |
| Jan 20 | 19.0% | 1.62x | Shakeout #1 |
| Feb 3 | 18.0% | 1.70x | Shakeout #2 |
| Feb 24 | **4.8%** | 0.65x | **Contraction** |
| Apr 14 | **4.6%** | 0.60x | Tight |
| Jun 16 | **3.7%** | 0.66x | **Tightest — VCP climax** |
| Jun 30 | 4.6% | **0.50x** | First entry candle (doc) |
| Aug 25 | **1.9%** | **0.38x** | **Super tight + dry** |
| Sep 15 | 8.5% | 0.72x | First breakout ($10.21, Bod=98%) |
| Sep 29 | **2.7%** | **0.55x** | **Pullback — super tight** |
| **Oct 6** | **6.0%** | **0.64x** | **Weekly close @ $10.47 — ENTRY** |

### Daily Entry Window

| Date | Open | High | Low | Close | Volume | Note |
|---|---|---|---|---|---|---|
| Sep 25 | 10.10 | 10.20 | 10.02 | 10.06 | 230M | Pullback from Sep 15 breakout |
| Sep 26 | 10.10 | 10.15 | 10.01 | 10.13 | 212M | Tight |
| Sep 27 | 10.12 | 10.24 | 10.02 | 10.04 | 236M | Bouncing at $10 support |
| Sep 28 | 10.06 | 10.14 | 9.98 | 10.05 | 205M | |
| Sep 29 | 10.09 | 10.10 | 10.00 | 10.01 | 133M | Tightest |
| Oct 2 | 10.01 | 10.11 | 9.98 | 10.00 | 147M | Still tight |
| Oct 3 | 9.99 | 10.12 | 9.92 | 10.06 | 219M | |
| **Oct 4** | **10.09** | **10.36** | **10.04** | **10.35** | **267M** | **Daily break above consolidation** |
| Oct 5 | 10.33 | 10.42 | 10.23 | 10.26 | 232M | |
| **Oct 6** | **10.22** | **10.51** | **10.21** | **10.47** | **295M** | **Weekly close entry** |

### Parameters

| Parameter | Value |
|---|---|
| **Pivot** | $10.21 (Sep 15 weekly breakout high) |
| **Entry Price** | ~$10.47 (weekly close) |
| **Entry Type** | Pullback to pivot → weekly close confirmation |
| **VCP Contraction Range** | 19% → 18% → 4.8% → 4.6% → 3.7% |

---

## Trade Entry 4: May 30, 2007 — Base-on-Base Breakout

### Setup Structure

**Base-on-Base (Nov 21, 2006 → May 20, 2007):**

After the Oct 20, 2006 weekly close at $11.45, the stock entered a higher-level consolidation instead of breaking out immediately. This formed a second base above the first one.

### Daily Entry Window

| Date | Open | High | Low | Close | Volume | Note |
|---|---|---|---|---|---|---|
| May 25 | 11.95 | 12.08 | 11.89 | 12.04 | 215M | Tight — testing resistance |
| May 29 | 12.08 | 12.25 | 12.05 | 12.13 | 210M | |
| **May 30** | **12.07** | **12.42** | **12.03** | **12.42** | **291M** | **Breakout close** |
| May 31 | 12.47 | 12.67 | 12.38 | 12.40 | 358M | Held |
| Jun 5 | 12.70 | 12.93 | 12.62 | 12.92 | 419M | Continuation |

### Parameters

| Parameter | Value |
|---|---|
| **Pivot** | ~$12.08-12.25 (base highs) |
| **Entry Price** | ~$12.42 (close) |
| **Entry Type** | Base-on-base breakout |

---

## Trade Entry 5: Sep 18, 2007 — Low Cheat

### Definition of Low Cheat (from this analysis)

> A buy point that appears **within a base** during **tight consolidation** — the stock forms a **staircase pattern** of tiny candles within the base itself, and the entry trigger is when price breaks above this tight staircase, **before** breaking out above the base high.

This is different from a full breakout entry because you enter **within** the base (below the absolute base high), capturing the move before the wider market recognizes the breakout.

### Setup Structure

**Gap-Down Base (Jul 20 → Sep 4, 2007):**

| Date | Action | Range |
|---|---|---|
| Jul 19 | Near high $13.79 | — |
| **Jul 20** | **Gap down to $12.75, close $12.95, vol 714M** | **-6.0%** |
| Jul 23-31 | Recovery from gap | Tight |
| Aug 1-15 | Base building | $12.40-12.86 |
| **Aug 16** | **Lowest point $11.97** | **Base low established** |
| Aug 17-Sep 4 | Gradual recovery | $12.25-13.15 |

**The Staircase (Low Cheat setup, Sep 4-17):**

| Date | Open | High | Low | Close | Volume | Note |
|---|---|---|---|---|---|---|
| Sep 4 | 12.83 | 13.15 | 12.82 | 13.08 | 148M | Recovery above $13 |
| Sep 5 | 13.04 | 13.19 | 13.01 | 13.15 | 133M | Tiny body |
| Sep 6 | 13.18 | 13.20 | 12.91 | 13.04 | 146M | Tight |
| Sep 7 | 12.90 | 12.98 | 12.87 | 12.94 | 147M | Tight |
| Sep 14 | 13.03 | 13.21 | 13.01 | 13.17 | 111M | Tight |
| Sep 17 | 13.11 | 13.18 | 13.05 | 13.08 | 88M | **Tightest + lowest vol** |
| **Sep 18** | **13.11** | **13.38** | **13.06** | **13.33** | **169M** | **Low cheat buy point** |

### Parameters

| Parameter | Value |
|---|---|
| **Base Low** | $11.97 (Aug 16) |
| **Staircase Range** | $12.82-13.21 (tiny candles) |
| **Buy Point** | ~$13.33 (Sep 18 close) |
| **Entry Type** | Low cheat (staircase pattern within base) |

---

## The Final Run & Exit

After Entry 5, the stock ran:

| Date | Close | High | Note |
|---|---|---|---|
| Sep 18 | $13.33 | $13.38 | Entry |
| Sep 21 | $13.95 | $13.97 | |
| Oct 1 | $14.51 | $14.55 | |
| Oct 5 | $14.80 | $14.84 | |
| Oct 8 | $15.18 | $15.20 | |
| Oct 9 | $15.32 | $15.54 | |
| Oct 19 | $16.06 | $16.40 | |
| Oct 23 | $16.83 | $16.88 | |
| Oct 31 | $17.61 | $17.61 | |
| Nov 5 | $18.07 | $18.19 | |
| **Nov 6** | **$18.48** | **$18.48** | **PEAK** |
| Nov 7 | $18.26 | $18.61 | |
| **Nov 8** | **$17.28** | **$18.30** | **EXIT — broke below fast MA** |

**Run from Entry 5:** $13.33 → $18.48 = **+38.6% in ~7 weeks**

---

## Complete Timeline

```
2004-08-19  GOOG IPO (split-adj $2.48)
2004-10-29  First peak at $5.02
    ↓
2005-03-25  VCP climax — range 2.8%, VR=0.41x
2005-04-22  ★ ENTRY 1 @ $5.38 — VCP breakout (weekly close)
    ↓
2005-04 → 2005-06  THE POLE ($5.02 → $7.46, +48%)
    ↓
2005-06 → 2005-10  FLAG / CONSOLIDATION ($7.46 → $7.00-8.00)
2005-10-21  ★ ENTRY 2 @ $8.47 — Flag & pole breakout (weekly close)
    ↓
2006-01-12 → 2006-10  CLASSIC VCP (Jan-Feb shakeouts → tightening)
2006-09-15  First breakout at $10.21
2006-09-29  Pullback tight at $10.01
2006-10-06  ★ ENTRY 3 @ $10.47 — Pullback to pivot, weekly close
    ↓
2006-11 → 2007-05  BASE-ON-BASE consolidation
2007-05-30  ★ ENTRY 4 @ $12.42 — Base-on-base breakout
    ↓
2007-07-20  Gap down to $12.95
2007-08-16  Base low at $11.97
2007-09-04 → 2007-09-17  Staircase pattern (low cheat setup)
2007-09-18  ★ ENTRY 5 @ $13.33 — Low cheat buy point
    ↓
2007-11-06  PEAK at $18.48
2007-11-08  ✕ EXIT @ ~$17.28 — broke below fast MA
```

---

## Key Concepts Identified

| Concept | Where It Appears | Description |
|---|---|---|
| **VCP** | Entries 1 & 3 | Weekly ranges progressively contracting |
| **Flag & Pole** | Entries 1 → 2 | Pole Apr→Jun, Flag Jun→Oct, breakout Oct |
| **Pullback to Pivot** | Entry 3 | Breakout Sep 15 → pullback to $10 → re-entry Oct 6 |
| **Base-on-Base** | Entry 4 | Second base above first base |
| **Low Cheat** | Entry 5 | Staircase of tiny candles within base = buy point before full breakout |
| **Pivot** | All entries | Prior weekly/daily high that price must clear |
| **Price Excess** | Entries 1, 2, 3 | Gap-up on entry day (momentum confirmation) |

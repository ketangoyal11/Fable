---
type: entry-verification-analysis
ticker: ARM
company: "Arm Holdings plc"
date_range: "2026-01-02 – 2026-06-05"
scope: "Minervini-style entry setups — Jan 2026 onwards"
verification_date: "2026-06-07"
data_source: "Yahoo Finance OHLCV"
entry_logic_source: "rmv_minervini_master.pine v2"
---

# ARM — Minervini Entry Detection Verification Report

**Period:** 2026-01-02 to 2026-06-05 (107 trading days)  
**Current Price:** $342.93  
**Stage 2 Uptrend Bars:** 17 / 107 (15.9%)  
**Pivots Detected (tight streak highs):** 3  
**Analysis Date:** 2026-06-07

---

## Executive Summary

| Category | Count | Notes |
|----------|-------|-------|
| Bars under current Pine logic | 3 | Entries that trigger with existing code |
| Bars missed due to known bugs | 13 | Valid entries rejected by buggy thresholds |
| Bars under FIXED logic | 14 | What WOULD trigger if all bugs were patched |

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
| 1 | 2026-04-09 | $150.40 | 1 | 3.4% |
| 2 | 2026-04-17 | $168.35 | 1 | 3.3% |
| 3 | 2026-05-15 | $216.70 | 1 | 3.8% |

---

## 2. Entries Triggered Under CURRENT Pine Logic

| # | Date | Close | Entry Type | VR | Chg% | Pivot | Stop | Stage2 |
|---|------|-------|------------|-----:|------:|------|------|:------:|
| 1 | 2026-04-20 | $175.10 | **BREAKOUT** | 1.33 | 5.02% | $150.40 (2026-04-09) | $144.38 | ❌ |
| 2 | 2026-05-11 | $212.65 | **SPRING** | 1.23 | -0.29% | $150.40 (2026-04-09) | $206.08 | ❌ |
| 3 | 2026-05-20 | $256.73 | **BREAKOUT** | 1.92 | 15.05% | $216.70 (2026-05-15) | $208.03 | ✅ |

### Entry Detail Breakdown

#### 1. BREAKOUT — 2026-04-20 @ $175.10

- **Open:** $167.41 | **High:** $175.32 | **Low:** $164.10
- **Volume:** 8,564,000 | **VR:** 1.33x | **Change:** +5.02%
- **Pivot:** $150.40 (set 2026-04-09)
- **Stop Level:** $144.38 (-17.5% below entry)
- **Stage 2:** No
- **VCP Ratio:** 89.3% (buggy inverted calculation)

#### 2. SPRING — 2026-05-11 @ $212.65

- **Open:** $206.54 | **High:** $215.50 | **Low:** $206.08
- **Volume:** 10,549,500 | **VR:** 1.23x | **Change:** -0.29%
- **Pivot:** $150.40 (set 2026-04-09)
- **Stop Level:** $206.08 (-3.1% below entry)
- **Stage 2:** No
- **VCP Ratio:** 178.7% (buggy inverted calculation)

#### 3. BREAKOUT — 2026-05-20 @ $256.73

- **Open:** $226.54 | **High:** $259.44 | **Low:** $226.09
- **Volume:** 18,297,600 | **VR:** 1.92x | **Change:** +15.05%
- **Pivot:** $216.70 (set 2026-05-15)
- **Stop Level:** $208.03 (-19.0% below entry)
- **Stage 2:** Yes
- **VCP Ratio:** 80.8% (buggy inverted calculation)

---

## 3. Bars That SHOULD Trigger But DON'T (Known Bugs)

| # | Date | Close | Should Be | VR | Chg% | Bug Description | Stop |
|---|------|-------|-----------|-----:|------:|-----------------|------|
| 1 | 2026-04-13 | $157.58 | **BREAKOUT (quiet)** | 0.71 | 5.81% | VR threshold too high (≥1.3 misses quiet breakouts) | $144.38 |
| 2 | 2026-04-14 | $161.22 | **BREAKOUT (quiet)** | 0.91 | 2.31% | VR threshold too high (≥1.3 misses quiet breakouts) | $144.38 |
| 3 | 2026-04-16 | $162.33 | **CHEAT (low VR)** | 0.83 | 1.88% | Cheat entry requires VR ≥ 1.3 (contradictory) | $144.38 |
| 4 | 2026-04-17 | $166.73 | **BREAKOUT (quiet)** | 0.76 | 2.71% | VR threshold too high (≥1.3 misses quiet breakouts) | $144.38 |
| 5 | 2026-04-23 | $204.61 | **SPRING (gap-down from close)** | 2.58 | 4.09% | Spring only checks gap below prior LOW, not prior CLOSE | $192.18 |
| 6 | 2026-05-19 | $223.15 | **SPRING (gap-down from close)** | 1.22 | 3.73% | Spring only checks gap below prior LOW, not prior CLOSE | $206.38 |
| 7 | 2026-05-19 | $223.15 | **SCALE-IN (intraday tag of EMA10)** | 1.22 | 3.73% | EMA10 scale-in proximity too tight (uses close, not intraday low) | $215.82 |
| 8 | 2026-05-19 | $223.15 | **BREAKOUT (quiet)** | 1.22 | 3.73% | VR threshold too high (≥1.3 misses quiet breakouts) | $208.03 |
| 9 | 2026-05-20 | $256.73 | **SCALE-IN (intraday tag of EMA10)** | 1.92 | 15.05% | EMA10 scale-in proximity too tight (uses close, not intraday low) | $223.26 |
| 10 | 2026-05-21 | $298.23 | **SCALE-IN (intraday tag of EMA10)** | 2.20 | 16.16% | EMA10 scale-in proximity too tight (uses close, not intraday low) | $236.89 |
| 11 | 2026-05-22 | $306.51 | **SPRING (gap-down from close)** | 1.38 | 2.78% | Spring only checks gap below prior LOW, not prior CLOSE | $288.21 |
| 12 | 2026-05-22 | $306.51 | **SCALE-IN (intraday tag of EMA10)** | 1.38 | 2.78% | EMA10 scale-in proximity too tight (uses close, not intraday low) | $249.55 |
| 13 | 2026-05-26 | $321.22 | **SCALE-IN (intraday tag of EMA10)** | 1.06 | 4.80% | EMA10 scale-in proximity too tight (uses close, not intraday low) | $262.58 |

---

## 4. Bug-by-Bug Analysis for ARM

### VR threshold too high (≥1.3 misses quiet breakouts)

| Date | Close | VR | Chg% | Stop |
|------|-------|-----:|------:|------|
| 2026-04-13 | $157.58 | 0.71 | 5.81% | $144.38 |
| 2026-04-14 | $161.22 | 0.91 | 2.31% | $144.38 |
| 2026-04-17 | $166.73 | 0.76 | 2.71% | $144.38 |
| 2026-05-19 | $223.15 | 1.22 | 3.73% | $208.03 |

### Cheat entry requires VR ≥ 1.3 (contradictory)

| Date | Close | VR | Chg% | Stop |
|------|-------|-----:|------:|------|
| 2026-04-16 | $162.33 | 0.83 | 1.88% | $144.38 |

### Spring only checks gap below prior LOW, not prior CLOSE

| Date | Close | VR | Chg% | Stop |
|------|-------|-----:|------:|------|
| 2026-04-23 | $204.61 | 2.58 | 4.09% | $192.18 |
| 2026-05-19 | $223.15 | 1.22 | 3.73% | $206.38 |
| 2026-05-22 | $306.51 | 1.38 | 2.78% | $288.21 |

### EMA10 scale-in proximity too tight (uses close, not intraday low)

| Date | Close | VR | Chg% | Stop |
|------|-------|-----:|------:|------|
| 2026-05-19 | $223.15 | 1.22 | 3.73% | $215.82 |
| 2026-05-20 | $256.73 | 1.92 | 15.05% | $223.26 |
| 2026-05-21 | $298.23 | 2.20 | 16.16% | $236.89 |
| 2026-05-22 | $306.51 | 1.38 | 2.78% | $249.55 |
| 2026-05-26 | $321.22 | 1.06 | 4.80% | $262.58 |

---

## 5. What WOULD Trigger Under FIXED Logic

| # | Date | Close | Type | VR | Chg% | Pivot |
|---|------|-------|------|-----:|------:|------|
| 1 | 2026-04-13 | $157.58 | **CHEAT** | 0.71 | 5.81% | $150.40 |
| 2 | 2026-04-14 | $161.22 | **CHEAT** | 0.91 | 2.31% | $150.40 |
| 3 | 2026-04-16 | $162.33 | **CHEAT** | 0.83 | 1.88% | $150.40 |
| 4 | 2026-04-17 | $166.73 | **CHEAT** | 0.76 | 2.71% | $150.40 |
| 5 | 2026-04-20 | $175.10 | **BREAKOUT** | 1.33 | 5.02% | $150.40 |
| 6 | 2026-04-23 | $204.61 | **SPRING** | 2.58 | 4.09% | $150.40 |
| 7 | 2026-05-11 | $212.65 | **SPRING** | 1.23 | -0.29% | $150.40 |
| 8 | 2026-05-19 | $223.15 | **SPRING** | 1.22 | 3.73% | $150.40 |
| 9 | 2026-05-19 | $223.15 | **CHEAT** | 1.22 | 3.73% | $216.70 |
| 10 | 2026-05-20 | $256.73 | **SCALE-IN** | 1.92 | 15.05% | $150.40 |
| 11 | 2026-05-20 | $256.73 | **BREAKOUT** | 1.92 | 15.05% | $216.70 |
| 12 | 2026-05-21 | $298.23 | **SCALE-IN** | 2.20 | 16.16% | $150.40 |
| 13 | 2026-05-22 | $306.51 | **SPRING** | 1.38 | 2.78% | $150.40 |
| 14 | 2026-05-26 | $321.22 | **SCALE-IN** | 1.06 | 4.80% | $150.40 |

---

## 6. Trend Template Check (Current Bar: 2026-06-05)

| Criteria | Status | Value |
|----------|--------|-------|
| Close > 50 SMA | ✅ | $342.93 vs $223.81 |
| Close > 150 SMA | ✅ | $342.93 vs $158.90 |
| Close > 200 SMA | ✅ | $342.93 vs $157.16 |
| 50 SMA > 150 SMA | ✅ | $223.81 vs $158.90 |
| 150 SMA > 200 SMA | ✅ | $158.90 vs $157.16 |
| Stage 2 | ✅ | — |

---

## 7. Cross-Check Against Book Examples

ARM (Arm Holdings) is **not a documented book figure** in Minervini's published works.
This analysis is a forward-looking scan using the Pine Script entry logic.

---

## 8. Key Observations for ARM (Jan–Jun 2026)

- **Massive uptrend:** ARM rallied from ~$114.73 to ~$342.93 (+198.9%) during the analysis period.
- **Low tight-streak count:** In strong parabolic moves, RMV rarely drops below the tight threshold because daily ranges expand.
- **Volume signature:** Several days showed VR > 2.0x, indicating institutional accumulation.
- **Stage 2:** The stock has been in Stage 2 for the majority of the period (all SMAs aligned and rising).
- **Missing entries:** The current Pine script logic produced 3 entry signals. This is because:
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
- **Period:** 2026-01-02 to 2026-06-05
- **Pine Script Reference:** `rmv_minervini_master.pine` v2
- **Python Reference:** `analysis/minervini_obsidian/tools/_buy_points.py`

---

*Report generated by ARM Minervini analysis engine on 2026-06-07*

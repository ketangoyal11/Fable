---
type: book-stock-image
book: "Trade Like a Stock Market Wizard"
figure: "5.20"
page: 104
ticker: "CMG"
yahoo_symbol: "CMG"
date_range: "2011-2012"
extraction_confidence: "caption-with-ticker"
generated: "2026-05-17"
private_source_image: true
---

# Figure 5.20 - CMG - Page 104

## Source Image

Book: [[Trade Like a Stock Market Wizard]]

Caption: Chipotle Mexican Grill (CMG) 2011-2012

![](../assets/book_pages_private/trade-like-a-stock-market-wizard/page_104.png)

## Yahoo OHLCV Rebuild

Download status: `OK`

![](../assets/book_stock_charts/trade-like-a-stock-market-wizard/trade-like-a-stock-market-wizard-figure-5-20-cmg-page-104_yahoo_rebuild.png)

CSV: `data/book_stock_images/trade-like-a-stock-market-wizard-figure-5-20-cmg-page-104_ohlcv.csv`

## Pattern Read

Tags: vcp-or-tightening, volume-dry-up, stage-2-leadership

Concepts: [[Pivot and Entry]], [[Relative Strength Leadership]], [[Stage 2 Uptrend]], [[Trend Template]], [[Volatility Contraction Pattern]], [[Volume Dry-Up and Accumulation]]

The useful clue is contraction: the later portion of the window became tighter than the earlier portion. Volume contraction supports the idea that supply was drying up near the tight area.

## Reconciliation Metrics

| Metric | Value |
|---|---:|
| first_close | 1.7568 |
| last_close | 13.6982 |
| max_gain_pct | 694.55 |
| max_drawdown_from_period_high_pct | -47.15 |
| first_half_depth_pct | 414.42 |
| second_half_depth_pct | 198.49 |
| tightening | True |
| volume_dryup | True |
| best_trend_template_score | 5/5 |
| latest_trend_template_score | 5/5 |

## Trend Template Checks

- close > 50 DMA
- close > 150 DMA
- close > 200 DMA
- 50 DMA > 150 DMA
- 150 DMA > 200 DMA

## Study Questions

- Does the rebuilt OHLCV chart confirm the same structure shown in the book image?
- Was the stock close to a definable pivot, or already extended?
- Did volume dry up before the move, or was supply still obvious?
- Was this a buy lesson, a sell lesson, or a failure-avoidance lesson?
- What would invalidate the setup if this were being traded live?




<!-- STAGE_LIFECYCLE_START -->
## Stage Lifecycle & Base Concept Analysis
> This section analyzes the FULL LIFECYCLE of the stock around the inferred entry — Stage 1 (Accumulation), Stage 2 (Advance), Stage 3 (Distribution), Stage 4 (Decline) — plus deep base concept analysis, VCP footprint, tight footprint, supply dynamics, and contraction timeline.
- Status: `ok`
- Entry date: `2012-02-27`
- Entry price: `7.7778`
### Stage Lifecycle Overview
| Stage | Present | Start Date | End Date | Duration | Key Signal |
|---|---|---|---:|---|---|
| Stage 1 — Accumulation | ✅ | `2010-11-29` | `2011-11-28` | 252 days | Base: deep-chaotic |
| Stage 2 — Advance | ✅ | `2011-11-28` | `2012-06-27` | 146 days | Max gain: 42.9% |
| Stage 3 — Distribution | ✅ | `2012-06-27` | `2012-07-19` | 15 days | climax vol |
| Stage 4 — Decline | ✅ | `2012-07-20` | — | 235 days | Below 200 DMA: False |
### Stage 1 — Accumulation / Base Building
- Base type: `deep-chaotic`
- Lowest price in base: `4.2500`
- Volume pattern: `neutral`
### Stage 2 — Advance / Trend Pivots

- Number of significant pivots during advance: `1`

| Pivot Date | Price |
|---|---:|
| `2012-03-26` | `8.5100` |

#### Trend Template Evolution During Stage 2

| % Through Stage 2 | Date | Score |
|---|---|---:|
| 0% | `2011-11-28` | 6/7 |
| 25% | `2012-01-20` | 7/7 |
| 50% | `2012-03-14` | 7/7 |
| 75% | `2012-05-04` | 6/7 |
| 100% | `2012-06-27` | 6/7 |

### Base Concept Deep-Dive

- Base type: `deep-vcp`
- Base duration: `63 sessions`
- Base depth: `30.1%`
- Base high: `7.8100`
- Base low: `6.0000`
- Resistance touches at base high: `8`
- Support touches at base low: `1`
- Contraction count: `4`
- Contraction quality: `clear-tightening`
- Pivot clarity: `clear-pivot-at-high`
- Pivot distance at entry: `-0.4%`
- Volume dry-up in base: `neutral`
- Volume dry-up ratio: `0.99`
- Tightness at pivot (10d): `3.5%`
- Weekly tightness: `1.1%`

### VCP Footprint

- VCP present: `True`
- VCP quality: `clear-tightening`
- Total contraction depth: `13.8%`
- Final contraction depth: `7.9%`
- Number of contractions: `4`

| Phase | Date | Depth | Volume | Tightness |
|---|---|---:|---:|---:|
| C? | `2011-11-25` | 13.8% | 29080000.0 | 6.8% |
| C? | `2011-12-16` | 11.3% | 18535000.0 | 4.5% |
| C? | `2012-01-10` | 10.0% | 19170000.0 | 3.2% |
| C? | `2012-02-01` | 7.9% | 25300000.0 | 2.9% |

### Tight Footprint

- 10-session tightness at entry: `3.1%`
- 20-session tightness at entry: `6.8%`
- Weekly tightness: `2.9%`
- ATR20 %: `1.57`
- Tightness progression: `improving`

### Supply Analysis

- Supply label: `neutral`
- Volume dry-up ratio: `0.98`
- Distribution volume detected: `False`
- Accumulation volume detected: `False`

### Contraction Timeline

| Phase | Start Date | Depth | Volume | Tightness |
|---|---|---:|---:|---:|
| C1 | `2011-11-25` | 13.8% | 29080000.0 | 6.8% |
| C2 | `2011-12-16` | 11.3% | 18535000.0 | 4.5% |
| C3 | `2012-01-10` | 10.0% | 19170000.0 | 3.2% |
| C4 | `2012-02-01` | 7.9% | 25300000.0 | 2.9% |

### Concept Tie-Back

- Related concepts: [[Base Concept]], [[Stage 2 Uptrend]], [[Trend Template]], [[Stage 3 Distribution]], [[Stage 4 Decline]], [[Volatility Contraction Pattern]], [[Pivot and Entry]]
- Lesson: Stage 1 base was deep-chaotic with 63.7% depth. Stage 2 advance lasted 147 sessions with 1 significant pivots. VCP footprint shows 4 contractions with clear-tightening quality.

<!-- STAGE_LIFECYCLE_END -->
<!-- PRE_ENTRY_SENSE_CHECK_START -->

## Pre-Entry Sense Check

> This section analyzes the chart structure PRIOR to the inferred entry. It answers: What did the setup look like in the weeks and months before the trade? Which Minervini concepts were already visible?

- Status: `ok`
- Entry date: `2012-02-27`
- Pre-entry history available: `442 sessions`

### Trend Template Evolution

| Lookback | Date | Score | Assessment |
|---|---|---:|:---|
| 60 days before | 2011-11-29 | 6/7 | ✅ Stage 2 confirmed |
| 40 days before | 2011-12-28 | 7/7 | ✅ Stage 2 confirmed |
| 20 days before | 2012-01-27 | 7/7 | ✅ Stage 2 confirmed |

### Pre-Entry Context Window

- Context window (last sessions before entry): `150 sessions`
- Range high: `7.7600`
- Range low: `5.4300`
- Total range depth: `42.9%`
- Contraction phases (rolling 21-bar segments): `21.8% -> 27.7% -> 20.4% -> 13.7% -> 13.8% -> 11.8% -> 8.6%`

### Stage 2 Onset

- First sustained Stage 2 date: `2011-03-11`
- Days in Stage 2 before entry: `242`

### Volume Behavior Before Entry

- Volume dry-up label: `neutral`
- Recent/base volume ratio: `0.98`
- Volume spike dates (2.5x avg) in last 40 days: `2012-02-02`

### Tightness Progression

| Lookback | 10-Session Close Tightness |
|---|---:|
| 40 days before | `6.7%` |
| 20 days before | `5.2%` |
| Final 10 sessions before | `3.1%` |
| Final 3 weekly closes | `2.9%` |

### Moving Average Alignment

- 50/150/200 DMA first aligned (50>150>200): `2011-03-11`

### Shakeouts / Tests Before Entry

- No shakeouts or undercut-recover patterns detected in last 40 sessions before entry.

### 52-Week High Context

| Timing | Distance from 52W High |
|---|---:|
| 60 days before | `-10.1%` |
| 20 days before | `-1.0%` |
| At entry | `-0.4%` |

### Concept Tie-Back

- Related concepts: [[Stage 2 Uptrend]], [[Trend Template]], [[Relative Strength Leadership]], [[Volatility Contraction Pattern]], [[Pivot and Entry]]
- Lesson: Stage 2 was established 242 days before entry, confirming leadership context. Total pre-entry range was 42.9% — wide range indicating significant prior movement. Volume did not show clear dry-up — supply may still be present.

<!-- PRE_ENTRY_SENSE_CHECK_END -->
<!-- SEPA_REPLICATION_START -->

## SEPA Trade Replication

> Study note: this reconstructs a likely Minervini-style setup area from the real OHLCV window shown by the book timing. It does not claim to know Minervini's private fill, sizing, or unpublished execution.

- Status: `reconstructed-from-real-ohlcv`
- Setup type: `vcp/contraction-study`
- Confidence: `high`
- Timing source: `2011-2012` from the figure caption and rebuilt OHLCV where available.
- Inferred study entry date: `2012-02-27`
- Inferred study entry price: `7.7778`
- Inferred pivot: `7.7598`
- Inferred stop / invalidation: `7.3206`
- Pivot extension at entry: `0.2%`
- Stop distance / risk: `6.2%`
- Trend Template score at entry: `7/7`

### Tightness And Supply
- 3-part pre-entry contraction depth: `13.8% -> 10.1% -> 8.2%`
- Contraction quality: `clear-tightening`
- 10-session close tightness: `3.1%`
- 3-week close tightness: `2.9%`
- Volume dry-up: `neutral`
- Recent/base median volume ratio: `0.98`
- Leadership proxy: 65-day return 27.3% and 126-day return 34.5%

### Post-Entry Reality Check
- Max gain after 20 sessions: `9.4%`
- Max gain after 60 sessions: `13.8%`
- Max gain after 120 sessions: `13.8%`
- Worst drawdown after 20 sessions: `-0.6%`
- Inferred stop failed within 20 sessions: `False`
- Pivot broadly respected within 20 sessions: `True`

### Concept Tie-Back

- Related concepts: [[Risk First]], [[Volatility Contraction Pattern]], [[Volume Dry-Up and Accumulation]], [[Pivot and Entry]], [[Trend Template]], [[Stage 2 Uptrend]], [[Relative Strength Leadership]]
- Lesson: The reconstructed data suggests price was becoming more controllable before the inferred entry; risk was close enough for a clean SEPA-style test; the pivot was broadly respected after entry.

<!-- SEPA_REPLICATION_END -->

---
type: book-stock-image
book: "Trade Like a Stock Market Wizard"
figure: "9.3"
page: 182
ticker: "AMZN"
yahoo_symbol: "AMZN"
date_range: "2001-2003"
extraction_confidence: "caption-with-ticker"
generated: "2026-05-17"
private_source_image: true
---

# Figure 9.3 - AMZN - Page 182

## Source Image

Book: [[Trade Like a Stock Market Wizard]]

Caption: Amazon (AMZN) vs. the Nasdaq Composite Index, 2001-2003 Amazon (AMZN) turned into a stage 2 uptrend well in advance of the general market, giving investors ample time to prepare for the buy point, which preceded a 240 percent advance in only 12 months

![](../assets/book_pages_private/trade-like-a-stock-market-wizard/page_182.png)

## Yahoo OHLCV Rebuild

Download status: `OK`

![](../assets/book_stock_charts/trade-like-a-stock-market-wizard/trade-like-a-stock-market-wizard-figure-9-3-amzn-page-182_yahoo_rebuild.png)

CSV: `data/book_stock_images/trade-like-a-stock-market-wizard-figure-9-3-amzn-page-182_ohlcv.csv`

## Pattern Read

Tags: vcp-or-tightening, pivot-breakout, volume-dry-up

Concepts: [[Pivot and Entry]], [[Trend Template]], [[Volatility Contraction Pattern]], [[Volume Dry-Up and Accumulation]]

The useful clue is contraction: the later portion of the window became tighter than the earlier portion. The entry lesson is to define the pivot first, then judge whether the real OHLCV breakout left controllable risk. Volume contraction supports the idea that supply was drying up near the tight area.

## Reconciliation Metrics

| Metric | Value |
|---|---:|
| first_close | 4.4688 |
| last_close | 2.3575 |
| max_gain_pct | 2.38 |
| max_drawdown_from_period_high_pct | -93.98 |
| first_half_depth_pct | 1560.62 |
| second_half_depth_pct | 211.83 |
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
- Entry date: `2003-09-18`
- Entry price: `2.3945`
### Stage Lifecycle Overview
| Stage | Present | Start Date | End Date | Duration | Key Signal |
|---|---|---|---:|---|---|
| Stage 1 — Accumulation | ✅ | `2001-09-26` | `2002-09-26` | 252 days | Base: deep-chaotic |
| Stage 2 — Advance | ✅ | `2002-09-26` | `2004-01-30` | 338 days | Max gain: 256.6% |
| Stage 3 — Distribution | ✅ | `2004-04-30` | `2004-06-28` | 39 days | no climax |
| Stage 4 — Decline | ❌ | — | — | — | Not detected |
### Stage 1 — Accumulation / Base Building
- Base type: `deep-chaotic`
- Lowest price in base: `0.2800`
- Volume pattern: `neutral`
### Stage 2 — Advance / Trend Pivots

- Number of significant pivots during advance: `5`

| Pivot Date | Price |
|---|---:|
| `2002-10-24` | `1.0100` |
| `2002-12-02` | `1.2500` |
| `2002-12-23` | `1.1200` |
| `2003-03-21` | `1.4000` |
| `2003-06-02` | `1.8300` |

#### Trend Template Evolution During Stage 2

| % Through Stage 2 | Date | Score |
|---|---|---:|
| 0% | `2002-09-26` | 6/7 |
| 25% | `2003-01-28` | 6/7 |
| 50% | `2003-05-30` | 7/7 |
| 75% | `2003-09-29` | 7/7 |
| 100% | `2004-01-30` | 6/7 |

### Base Concept Deep-Dive

- Base type: `deep-chaotic`
- Base duration: `248 sessions`
- Base depth: `215.5%`
- Base high: `2.4100`
- Base low: `0.7600`
- Resistance touches at base high: `7`
- Support touches at base low: `1`
- Contraction count: `5`
- Contraction quality: `constructive-tightening`
- Pivot clarity: `clear-pivot-at-high`
- Pivot distance at entry: `-0.7%`
- Volume dry-up in base: `neutral`
- Volume dry-up ratio: `1.01`
- Tightness at pivot (10d): `6.0%`
- Weekly tightness: `4.8%`

### VCP Footprint

- VCP present: `True`
- VCP quality: `constructive-tightening`
- Total contraction depth: `63.5%`
- Final contraction depth: `40.4%`
- Number of contractions: `5`

| Phase | Date | Depth | Volume | Tightness |
|---|---|---:|---:|---:|
| C? | `2002-09-25` | 63.5% | 174842000.0 | 13.9% |
| C? | `2002-12-04` | 29.1% | 138858000.0 | 10.5% |
| C? | `2003-02-14` | 47.1% | 142646000.0 | 18.8% |
| C? | `2003-04-28` | 38.9% | 164998000.0 | 10.3% |
| C? | `2003-07-08` | 40.4% | 156644000.0 | 4.7% |

### Tight Footprint

- 10-session tightness at entry: `4.6%`
- 20-session tightness at entry: `8.2%`
- Weekly tightness: `1.8%`
- ATR20 %: `2.85`
- Tightness progression: `improving`

### Supply Analysis

- Supply label: `neutral`
- Volume dry-up ratio: `1.01`
- Distribution volume detected: `False`
- Accumulation volume detected: `False`
- Climax volume dates: `2003-07-23, 2003-07-24`

### Contraction Timeline

| Phase | Start Date | Depth | Volume | Tightness |
|---|---|---:|---:|---:|
| C1 | `2002-09-25` | 63.5% | 174842000.0 | 13.9% |
| C2 | `2002-12-04` | 29.1% | 138858000.0 | 10.5% |
| C3 | `2003-02-14` | 47.1% | 142646000.0 | 18.8% |
| C4 | `2003-04-28` | 38.9% | 164998000.0 | 10.3% |
| C5 | `2003-07-08` | 40.4% | 156644000.0 | 4.7% |

### Concept Tie-Back

- Related concepts: [[Base Concept]], [[Stage 2 Uptrend]], [[Trend Template]], [[Stage 3 Distribution]], [[Volatility Contraction Pattern]], [[Pivot and Entry]]
- Lesson: Stage 1 base was deep-chaotic with 270.2% depth. Stage 2 advance lasted 339 sessions with 5 significant pivots. VCP footprint shows 5 contractions with constructive-tightening quality.

<!-- STAGE_LIFECYCLE_END -->
<!-- PRE_ENTRY_SENSE_CHECK_START -->

## Pre-Entry Sense Check

> This section analyzes the chart structure PRIOR to the inferred entry. It answers: What did the setup look like in the weeks and months before the trade? Which Minervini concepts were already visible?

- Status: `ok`
- Entry date: `2003-09-18`
- Pre-entry history available: `830 sessions`

### Trend Template Evolution

| Lookback | Date | Score | Assessment |
|---|---|---:|:---|
| 60 days before | 2003-06-24 | 7/7 | ✅ Stage 2 confirmed |
| 40 days before | 2003-07-23 | 7/7 | ✅ Stage 2 confirmed |
| 20 days before | 2003-08-20 | 7/7 | ✅ Stage 2 confirmed |

### Pre-Entry Context Window

- Context window (last sessions before entry): `150 sessions`
- Range high: `2.3900`
- Range low: `0.9800`
- Total range depth: `143.5%`
- Contraction phases (rolling 21-bar segments): `27.0% -> 14.9% -> 38.8% -> 17.7% -> 19.8% -> 26.8% -> 20.4%`

### Stage 2 Onset

- First sustained Stage 2 date: `2002-04-24`
- Days in Stage 2 before entry: `354`

### Volume Behavior Before Entry

- Volume dry-up label: `neutral`
- Recent/base volume ratio: `1.01`
- Volume spike dates (2.5x avg) in last 40 days: `2003-07-23, 2003-07-24`

### Tightness Progression

| Lookback | 10-Session Close Tightness |
|---|---:|
| 40 days before | `16.1%` |
| 20 days before | `11.9%` |
| Final 10 sessions before | `4.6%` |
| Final 3 weekly closes | `1.8%` |

### Moving Average Alignment

- 50/150/200 DMA first aligned (50>150>200): `2002-04-29`

### Shakeouts / Tests Before Entry

- `2003-07-23` — undercut-and-recover of SMA50 (low 1.87, close 2.01)

### 52-Week High Context

| Timing | Distance from 52W High |
|---|---:|
| 60 days before | `-4.9%` |
| 20 days before | `-1.0%` |
| At entry | `-0.7%` |

### Concept Tie-Back

- Related concepts: [[Stage 2 Uptrend]], [[Trend Template]], [[Relative Strength Leadership]], [[Volatility Contraction Pattern]], [[Pivot and Entry]]
- Lesson: Stage 2 was established 354 days before entry, confirming leadership context. Total pre-entry range was 143.5% — wide range indicating significant prior movement. Volume did not show clear dry-up — supply may still be present. Found 1 shakeout(s) before entry — test of conviction.

<!-- PRE_ENTRY_SENSE_CHECK_END -->
<!-- SEPA_REPLICATION_START -->

## SEPA Trade Replication

> Study note: this reconstructs a likely Minervini-style setup area from the real OHLCV window shown by the book timing. It does not claim to know Minervini's private fill, sizing, or unpublished execution.

- Status: `reconstructed-from-real-ohlcv`
- Setup type: `pivot-breakout-study`
- Confidence: `high`
- Timing source: `2001-2003` from the figure caption and rebuilt OHLCV where available.
- Inferred study entry date: `2003-09-18`
- Inferred study entry price: `2.3945`
- Inferred pivot: `2.3875`
- Inferred stop / invalidation: `2.2365`
- Pivot extension at entry: `0.3%`
- Stop distance / risk: `7.1%`
- Trend Template score at entry: `7/7`

### Tightness And Supply
- 3-part pre-entry contraction depth: `18.2% -> 27.2% -> 11.3%`
- Contraction quality: `constructive-tightening`
- 10-session close tightness: `4.6%`
- 3-week close tightness: `1.8%`
- Volume dry-up: `neutral`
- Recent/base median volume ratio: `1.01`
- Leadership proxy: 65-day return 33.6% and 126-day return 74.5%

### Post-Entry Reality Check
- Max gain after 20 sessions: `26.1%`
- Max gain after 60 sessions: `27.7%`
- Max gain after 120 sessions: `27.7%`
- Worst drawdown after 20 sessions: `-3.5%`
- Inferred stop failed within 20 sessions: `False`
- Pivot broadly respected within 20 sessions: `True`

### Concept Tie-Back

- Related concepts: [[Risk First]], [[Volatility Contraction Pattern]], [[Volume Dry-Up and Accumulation]], [[Pivot and Entry]], [[Trend Template]], [[Stage 2 Uptrend]], [[Relative Strength Leadership]]
- Lesson: The reconstructed data suggests price was becoming more controllable before the inferred entry; risk was close enough for a clean SEPA-style test; the pivot was broadly respected after entry.

<!-- SEPA_REPLICATION_END -->

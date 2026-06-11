---
type: book-stock-image
book: "Trade Like a Stock Market Wizard"
figure: "7.15"
page: 154
ticker: "HD"
yahoo_symbol: "HD"
date_range: "1992-2008"
extraction_confidence: "caption-with-ticker"
generated: "2026-05-17"
private_source_image: true
---

# Figure 7.15 - HD - Page 154

## Source Image

Book: [[Trade Like a Stock Market Wizard]]

Caption: Home Depot (HD) 1992-2008 Chart of Home Depot (HD) shows that strong, accelerating annual earnings triggered a rapid rise in the stock price, followed by a long, precipitous decline as the earnings growth rate slowed considerably

![](../assets/book_pages_private/trade-like-a-stock-market-wizard/page_154.png)

## Yahoo OHLCV Rebuild

Download status: `OK`

![](../assets/book_stock_charts/trade-like-a-stock-market-wizard/trade-like-a-stock-market-wizard-figure-7-15-hd-page-154_yahoo_rebuild.png)

CSV: `data/book_stock_images/trade-like-a-stock-market-wizard-figure-7-15-hd-page-154_ohlcv.csv`

## Pattern Read

Tags: vcp-or-tightening, failed-breakout-or-stage-4

Concepts: [[Pivot and Entry]], [[Risk First]], [[Sell Rules and Failure Signals]], [[Trend Template]], [[Volatility Contraction Pattern]], [[Volume Dry-Up and Accumulation]]

The useful clue is contraction: the later portion of the window became tighter than the earlier portion. The sell lesson dominates: when price breaks character, the chart can warn before fundamentals are obvious.

## Reconciliation Metrics

| Metric | Value |
|---|---:|
| first_close | 2.8241 |
| last_close | 34.86 |
| max_gain_pct | 2378.69 |
| max_drawdown_from_period_high_pct | -75.64 |
| first_half_depth_pct | 2629.24 |
| second_half_depth_pct | 215.13 |
| tightening | True |
| volume_dryup | False |
| best_trend_template_score | 5/5 |
| latest_trend_template_score | 4/5 |

## Trend Template Checks

- close > 50 DMA
- close > 150 DMA
- close > 200 DMA
- 50 DMA > 150 DMA

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
- Entry date: `1992-08-28`
- Entry price: `8.8125`
### Stage Lifecycle Overview
| Stage | Present | Start Date | End Date | Duration | Key Signal |
|---|---|---|---:|---|---|
| Stage 1 — Accumulation | ✅ | `1996-05-30` | `1997-05-29` | 252 days | Base: shallow-vcp |
| Stage 2 — Advance | ✅ | `1997-05-29` | `1998-09-30` | 338 days | Max gain: 132.9% |
| Stage 3 — Distribution | ✅ | `1998-10-27` | `1999-08-04` | 193 days | climax vol |
| Stage 4 — Decline | ✅ | `1999-08-05` | — | 2489 days | Below 200 DMA: False |
### Stage 1 — Accumulation / Base Building
- Base type: `shallow-vcp`
- Lowest price in base: `10.6100`
- Volume pattern: `late-supply`
### Stage 2 — Advance / Trend Pivots

- Number of significant pivots during advance: `5`

| Pivot Date | Price |
|---|---:|
| `1997-07-31` | `16.6500` |
| `1997-09-17` | `17.9800` |
| `1997-11-03` | `19.1700` |
| `1997-12-04` | `20.1700` |
| `1998-02-23` | `22.9400` |

#### Trend Template Evolution During Stage 2

| % Through Stage 2 | Date | Score |
|---|---|---:|
| 0% | `1997-05-29` | 6/7 |
| 25% | `1997-09-26` | 7/7 |
| 50% | `1998-01-29` | 7/7 |
| 75% | `1998-06-01` | 7/7 |
| 100% | `1998-09-30` | 6/7 |

### Base Concept Deep-Dive

- Base type: `N/A`
- Base duration: `0 sessions`
- Base depth: `N/A`
- Base high: `N/A`
- Base low: `N/A`
- Resistance touches at base high: `0`
- Support touches at base low: `0`
- Contraction count: `0`
- Contraction quality: `N/A`
- Pivot clarity: `N/A`
- Pivot distance at entry: `N/A`
- Volume dry-up in base: `N/A`
- Volume dry-up ratio: `N/A`
- Tightness at pivot (10d): `N/A`
- Weekly tightness: `N/A`

### VCP Footprint

- VCP present: `False`
- No clear VCP pattern detected in the base.

### Tight Footprint

- 10-session tightness at entry: `3.7%`
- 20-session tightness at entry: `4.0%`
- Weekly tightness: `2.0%`
- ATR20 %: `2.02`
- Tightness progression: `improving`

### Supply Analysis

- Supply label: `neutral`
- Volume dry-up ratio: `1.39`
- Distribution volume detected: `False`
- Accumulation volume detected: `False`

### Concept Tie-Back

- Related concepts: [[Base Concept]], [[Stage 2 Uptrend]], [[Trend Template]], [[Stage 3 Distribution]], [[Stage 4 Decline]]
- Lesson: Stage 1 base was shallow-vcp with 29.3% depth. Stage 2 advance lasted 339 sessions with 5 significant pivots.

<!-- STAGE_LIFECYCLE_END -->
<!-- PRE_ENTRY_SENSE_CHECK_START -->

## Pre-Entry Sense Check

> This section analyzes the chart structure PRIOR to the inferred entry. It answers: What did the setup look like in the weeks and months before the trade? Which Minervini concepts were already visible?

- Status: `ok`
- Entry date: `1992-08-28`
- Pre-entry history available: `319 sessions`

### Trend Template Evolution

| Lookback | Date | Score | Assessment |
|---|---|---:|:---|
| 60 days before | 1992-06-04 | 7/7 | ✅ Stage 2 confirmed |
| 40 days before | 1992-07-02 | 7/7 | ✅ Stage 2 confirmed |
| 20 days before | 1992-07-31 | 7/7 | ✅ Stage 2 confirmed |

### Pre-Entry Context Window

- Context window (last sessions before entry): `150 sessions`
- Range high: `8.7900`
- Range low: `6.6100`
- Total range depth: `33.0%`
- Contraction phases (rolling 21-bar segments): `14.1% -> 10.5% -> 12.0% -> 11.4% -> 10.7% -> 14.1% -> 9.9%`

### Stage 2 Onset

- First sustained Stage 2 date: `1992-03-11`
- Days in Stage 2 before entry: `119`

### Volume Behavior Before Entry

- Volume dry-up label: `active-supply`
- Recent/base volume ratio: `1.39`
- No significant volume spikes in last 40 days before entry.

### Tightness Progression

| Lookback | 10-Session Close Tightness |
|---|---:|
| 40 days before | `7.8%` |
| 20 days before | `6.7%` |
| Final 10 sessions before | `3.7%` |
| Final 3 weekly closes | `2.0%` |

### Moving Average Alignment

- 50/150/200 DMA first aligned (50>150>200): `1992-03-11`

### Shakeouts / Tests Before Entry

- No shakeouts or undercut-recover patterns detected in last 40 sessions before entry.

### 52-Week High Context

| Timing | Distance from 52W High |
|---|---:|
| 60 days before | `-2.6%` |
| 20 days before | `-0.7%` |
| At entry | `-0.2%` |

### Concept Tie-Back

- Related concepts: [[Stage 2 Uptrend]], [[Trend Template]], [[Relative Strength Leadership]], [[Volatility Contraction Pattern]], [[Pivot and Entry]], [[Sell Rules and Failure Signals]]
- Lesson: Stage 2 was established 119 days before entry, confirming leadership context. Total pre-entry range was 33.0% — wide range indicating significant prior movement. Volume did not show clear dry-up — supply may still be present.

<!-- PRE_ENTRY_SENSE_CHECK_END -->
<!-- SEPA_REPLICATION_START -->

## SEPA Trade Replication

> Study note: this reconstructs a likely Minervini-style setup area from the real OHLCV window shown by the book timing. It does not claim to know Minervini's private fill, sizing, or unpublished execution.

- Status: `reconstructed-from-real-ohlcv`
- Setup type: `failure/sell-rule-study`
- Confidence: `high`
- Timing source: `1992-2008` from the figure caption and rebuilt OHLCV where available.
- Inferred study entry date: `1992-08-28`
- Inferred study entry price: `8.8125`
- Inferred pivot: `8.7917`
- Inferred stop / invalidation: `8.3125`
- Pivot extension at entry: `0.2%`
- Stop distance / risk: `6.0%`
- Trend Template score at entry: `7/7`

### Tightness And Supply
- 3-part pre-entry contraction depth: `12.8% -> 15.1% -> 7.4%`
- Contraction quality: `constructive-tightening`
- 10-session close tightness: `3.7%`
- 3-week close tightness: `2.0%`
- Volume dry-up: `active-supply`
- Recent/base median volume ratio: `1.39`
- Leadership proxy: 65-day return 14.7% and 126-day return 23.9%

### Post-Entry Reality Check
- Max gain after 20 sessions: `7.8%`
- Max gain after 60 sessions: `14.4%`
- Max gain after 120 sessions: `29.8%`
- Worst drawdown after 20 sessions: `-0.7%`
- Inferred stop failed within 20 sessions: `False`
- Pivot broadly respected within 20 sessions: `True`

### Concept Tie-Back

- Related concepts: [[Risk First]], [[Volatility Contraction Pattern]], [[Volume Dry-Up and Accumulation]], [[Pivot and Entry]], [[Sell Rules and Failure Signals]], [[Trend Template]], [[Stage 2 Uptrend]], [[Relative Strength Leadership]]
- Lesson: Treat this as a sell-rule and failure-recognition study. The important lesson is whether the stock could hold the pivot/base after demand supposedly appeared; a quick loss of the pivot changes the case from entry to defense.

<!-- SEPA_REPLICATION_END -->

---
type: market-example
symbol: "POWERINDIA"
universe: "midsmallcap400"
level: "L2"
entry_date_from_scan: "2026-05-08"
entry_actual_date: "2026-05-08"
generated: "2026-05-17"
---

# POWERINDIA

![](../assets/market_charts/POWERINDIA_entry_progress.png)

## Entry Progress

| Metric | Value |
|---|---:|
| Yahoo symbol | `POWERINDIA.NS` |
| Entry close | 34005.0 |
| Latest close | 32535.0 |
| Current return from entry | -4.32% |
| Max gain after entry | 3.21% |
| Max drawdown after entry | -8.26% |
| Scan risk | 28.68% |
| Scan RS | 95 |
| Scan VCP | 1/3 |
| Entry trend-template score | 7/7 |
| Latest trend-template score | 7/7 |
| Pre-entry pattern quality | loose-or-extended (1/4) |
| Fundamental score | 5/6 |

## Concept Review

- [[Trend Template]]: compare entry score with latest score.
- [[Relative Strength Leadership]]: inspect the RS panel versus NIFTY.
- [[Pivot and Entry]]: judge whether the scan entry was close enough to a definable pivot.
- [[Risk First]]: scan risk above 15-20% needs stricter position sizing or a tighter pattern.
- [[Sell Rules and Failure Signals]]: watch for price losing 50 DMA/200 DMA or breaking the entry structure.

## Pre-Entry Pattern Analysis

120-session pre-entry depth split: 41.8% then 70.0%. ATR20% did not clearly contract into entry. Volume did not dry up near the final window. Entry was -2.7% from the 60-session pre-entry pivot.

| Pattern Metric | Value |
|---|---:|
| First 60-session depth | 41.77% |
| Final 60-session depth | 70.02% |
| ATR20 start | 3.28% |
| ATR20 end | 3.33% |
| Volume dry-up | False |
| Entry distance from 60-session pivot | -2.7% |

## Fundamentals

| Fundamental Metric | Value |
|---|---:|
| Market cap | 1450161864704 |
| Trailing PE | 169.48843 |
| Forward PE | 103.630455 |
| Quarterly revenue growth | 34.07202032328887% |
| Quarterly earnings growth | 399.94262765347105% |
| Annual revenue growth | 22.135815260476765% |
| Annual earnings growth | 134.4486506288924% |
| Profit margins | 0.11545999 |
| Return on equity | None |
| Debt to equity | 1.843 |

### Fundamental Checks Passed

- quarterly revenue growth positive
- quarterly earnings growth positive
- annual revenue growth positive
- annual earnings growth positive
- profit margin positive

## Entry Template Conditions Passed

- close > 50 DMA
- close > 150 DMA
- close > 200 DMA
- 50 DMA > 150 DMA
- 150 DMA > 200 DMA
- near 52w high
- above 52w low

## Latest Template Conditions Passed

- close > 50 DMA
- close > 150 DMA
- close > 200 DMA
- 50 DMA > 150 DMA
- 150 DMA > 200 DMA
- near 52w high
- above 52w low

## Data

CSV: `data/POWERINDIA_ohlcv.csv`

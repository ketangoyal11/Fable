---
type: market-example
symbol: "NAM-INDIA"
universe: "midsmallcap400"
level: "L2"
entry_date_from_scan: "2026-05-08"
entry_actual_date: "2026-05-08"
generated: "2026-05-17"
---

# NAM-INDIA

![](../assets/market_charts/NAM-INDIA_entry_progress.png)

## Entry Progress

| Metric | Value |
|---|---:|
| Yahoo symbol | `NAM-INDIA.NS` |
| Entry close | 1103.4 |
| Latest close | 1100.6 |
| Current return from entry | -0.25% |
| Max gain after entry | 1.31% |
| Max drawdown after entry | -6.74% |
| Scan risk | 27.82% |
| Scan RS | 76 |
| Scan VCP | 1/3 |
| Entry trend-template score | 7/7 |
| Latest trend-template score | 7/7 |
| Pre-entry pattern quality | loose-or-extended (1/4) |
| Fundamental score | 6/6 |

## Concept Review

- [[Trend Template]]: compare entry score with latest score.
- [[Relative Strength Leadership]]: inspect the RS panel versus NIFTY.
- [[Pivot and Entry]]: judge whether the scan entry was close enough to a definable pivot.
- [[Risk First]]: scan risk above 15-20% needs stricter position sizing or a tighter pattern.
- [[Sell Rules and Failure Signals]]: watch for price losing 50 DMA/200 DMA or breaking the entry structure.

## Pre-Entry Pattern Analysis

120-session pre-entry depth split: 26.8% then 39.5%. ATR20% did not clearly contract into entry. Volume did not dry up near the final window. Entry was -0.7% from the 60-session pre-entry pivot.

| Pattern Metric | Value |
|---|---:|
| First 60-session depth | 26.79% |
| Final 60-session depth | 39.51% |
| ATR20 start | 3.2% |
| ATR20 end | 4.07% |
| Volume dry-up | False |
| Entry distance from 60-session pivot | -0.68% |

## Fundamentals

| Fundamental Metric | Value |
|---|---:|
| Market cap | 702501355520 |
| Trailing PE | 46.517326 |
| Forward PE | 33.51824 |
| Quarterly revenue growth | 25.657861164503572% |
| Quarterly earnings growth | 30.254604550379206% |
| Annual revenue growth | 21.430588741600133% |
| Annual earnings growth | 18.88929484837414% |
| Profit margins | 0.52143 |
| Return on equity | 0.34476003 |
| Debt to equity | 1.617 |

### Fundamental Checks Passed

- quarterly revenue growth positive
- quarterly earnings growth positive
- annual revenue growth positive
- annual earnings growth positive
- profit margin positive
- ROE positive

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

CSV: `data/NAM-INDIA_ohlcv.csv`

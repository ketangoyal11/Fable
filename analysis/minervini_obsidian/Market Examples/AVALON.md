---
type: market-example
symbol: "AVALON"
universe: "microcap250"
level: "L2"
entry_date_from_scan: "2026-05-08"
entry_actual_date: "2026-05-08"
generated: "2026-05-17"
---

# AVALON

![](../assets/market_charts/AVALON_entry_progress.png)

## Entry Progress

| Metric | Value |
|---|---:|
| Yahoo symbol | `AVALON.NS` |
| Entry close | 1387.0 |
| Latest close | 1323.1 |
| Current return from entry | -4.61% |
| Max gain after entry | 2.94% |
| Max drawdown after entry | -10.99% |
| Scan risk | 35.37% |
| Scan RS | 72 |
| Scan VCP | 0/3 |
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

120-session pre-entry depth split: 37.7% then 52.5%. ATR20% did not clearly contract into entry. Volume did not dry up near the final window. Entry was 6.2% from the 60-session pre-entry pivot.

| Pattern Metric | Value |
|---|---:|
| First 60-session depth | 37.68% |
| Final 60-session depth | 52.51% |
| ATR20 start | 4.67% |
| ATR20 end | 4.87% |
| Volume dry-up | False |
| Entry distance from 60-session pivot | 6.19% |

## Fundamentals

| Fundamental Metric | Value |
|---|---:|
| Market cap | 88366800896 |
| Trailing PE | 78.75595 |
| Forward PE | 40.918293 |
| Quarterly revenue growth | 48.67029136446015% |
| Quarterly earnings growth | 35.903955979824076% |
| Annual revenue growth | 26.67441107797581% |
| Annual earnings growth | 126.68929783812759% |
| Profit margins | 0.06553 |
| Return on equity | None |
| Debt to equity | 25.091 |

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

CSV: `data/AVALON_ohlcv.csv`

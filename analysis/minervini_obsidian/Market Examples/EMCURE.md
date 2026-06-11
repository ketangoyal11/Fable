---
type: market-example
symbol: "EMCURE"
universe: "midsmallcap400,smallcap250"
level: "L3"
entry_date_from_scan: "2026-05-01"
entry_actual_date: "2026-05-04"
generated: "2026-05-17"
---

# EMCURE

![](../assets/market_charts/EMCURE_entry_progress.png)

## Entry Progress

| Metric | Value |
|---|---:|
| Yahoo symbol | `EMCURE.NS` |
| Entry close | 1793.2 |
| Latest close | 1704.9 |
| Current return from entry | -4.92% |
| Max gain after entry | 2.05% |
| Max drawdown after entry | -9.25% |
| Scan risk | 14.89% |
| Scan RS | 82 |
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

120-session pre-entry depth split: 21.4% then 28.1%. ATR20% did not clearly contract into entry. Volume did not dry up near the final window. Entry was 1.4% from the 60-session pre-entry pivot.

| Pattern Metric | Value |
|---|---:|
| First 60-session depth | 21.36% |
| Final 60-session depth | 28.1% |
| ATR20 start | 3.19% |
| ATR20 end | 4.2% |
| Volume dry-up | False |
| Entry distance from 60-session pivot | 1.37% |

## Fundamentals

| Fundamental Metric | Value |
|---|---:|
| Market cap | 323231219712 |
| Trailing PE | 34.965137 |
| Forward PE | 22.8878 |
| Quarterly revenue growth | 21.749069148477297% |
| Quarterly earnings growth | 28.813962965119046% |
| Annual revenue growth | 16.559568095073995% |
| Annual earnings growth | 35.66968819899843% |
| Profit margins | 0.100439996 |
| Return on equity | 0.19573 |
| Debt to equity | 30.567 |

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

CSV: `data/EMCURE_ohlcv.csv`

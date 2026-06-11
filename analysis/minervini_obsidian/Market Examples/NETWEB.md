---
type: market-example
symbol: "NETWEB"
universe: "midsmallcap400,smallcap250"
level: "L3"
entry_date_from_scan: "2026-05-08"
entry_actual_date: "2026-05-08"
generated: "2026-05-17"
---

# NETWEB

![](../assets/market_charts/NETWEB_entry_progress.png)

## Entry Progress

| Metric | Value |
|---|---:|
| Yahoo symbol | `NETWEB.NS` |
| Entry close | 4422.2 |
| Latest close | 3840.5 |
| Current return from entry | -13.15% |
| Max gain after entry | 1.58% |
| Max drawdown after entry | -14.64% |
| Scan risk | 31.44% |
| Scan RS | 99 |
| Scan VCP | 0/3 |
| Entry trend-template score | 7/7 |
| Latest trend-template score | 7/7 |
| Pre-entry pattern quality | borderline (2/4) |
| Fundamental score | 6/6 |

## Concept Review

- [[Trend Template]]: compare entry score with latest score.
- [[Relative Strength Leadership]]: inspect the RS panel versus NIFTY.
- [[Pivot and Entry]]: judge whether the scan entry was close enough to a definable pivot.
- [[Risk First]]: scan risk above 15-20% needs stricter position sizing or a tighter pattern.
- [[Sell Rules and Failure Signals]]: watch for price losing 50 DMA/200 DMA or breaking the entry structure.

## Pre-Entry Pattern Analysis

120-session pre-entry depth split: 28.5% then 47.6%. ATR20% contracted into entry. Volume did not dry up near the final window. Entry was -0.6% from the 60-session pre-entry pivot.

| Pattern Metric | Value |
|---|---:|
| First 60-session depth | 28.53% |
| Final 60-session depth | 47.6% |
| ATR20 start | 5.74% |
| ATR20 end | 4.34% |
| Volume dry-up | False |
| Entry distance from 60-session pivot | -0.62% |

## Fundamentals

| Fundamental Metric | Value |
|---|---:|
| Market cap | 218680705024 |
| Trailing PE | 105.27686 |
| Forward PE | 50.137077 |
| Quarterly revenue growth | 86.591133266289% |
| Quarterly earnings growth | 65.66071386666042% |
| Annual revenue growth | 90.03682265163127% |
| Annual earnings growth | 80.9355522149256% |
| Profit margins | 0.09426 |
| Return on equity | 0.32834998 |
| Debt to equity | 39.019 |

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

CSV: `data/NETWEB_ohlcv.csv`

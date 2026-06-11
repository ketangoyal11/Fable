---
type: strategy-research
strategy: Staircase Weekly V3
version: staircase_weekly_backtest_v3_full_universe
created: "2026-05-25"
updated: "2026-05-25"
status: canonical-reference
tags:
  - strategy/staircase
  - timeframe/weekly
  - dataset/dhan
  - dataset/yahoo
  - minervini/pyramiding
  - research/source-comparison
aliases:
  - Staircase V3 Full Universe
  - Staircase Weekly V3 Dhan Yahoo Study
  - V3 50 30 20 Staircase
---

# Staircase Weekly V3 Full Universe - Dhan Yahoo Source Study

## Identity

This is the saved canonical version of the high-performing Staircase V3 weekly strategy result.

Use this note when referring to the result with:

- Dhan: 667 stocks with trades, 10,619 positions, +50,295R
- Yahoo Finance: 656 stocks with trades, 19,983 positions, +102,421R
- Scaling: 50/30/20
- Weekly plus daily trend filters
- Global Darvas 40
- Strong candle OFF

This is not Hermes V3. Hermes is a later research system trying to learn from this Staircase version and convert the weekly planning edge into a cleaner daily or multi-timeframe execution loop.

## Source Files

### Dhan full-universe engine

`tools/staircase_weekly_backtest_v3_full_universe.py`

Output:

- `analysis/staircase_dhan/staircase_strategy_weekly_backtest_v3_full_universe.json`
- `analysis/staircase_dhan/staircase_strategy_weekly_backtest_v3_full_universe.xlsx`

### Yahoo full-universe engine

`tools/staircase_weekly_backtest_v3_yfinance_universe.py`

Output:

- `analysis/staircase_dhan/staircase_strategy_weekly_backtest_v3_yfinance_universe.json`
- `analysis/staircase_dhan/staircase_strategy_weekly_backtest_v3_yfinance_universe.xlsx`

### Source comparison

`tools/_compare_sources.py`

This compares the Dhan and Yahoo JSON outputs side by side.

## Strategy Configuration

| Setting | Value |
|---|---:|
| Position scaling | 50/30/20 |
| L1 size | 50% |
| L2 size | 30% |
| L3 size | 20% |
| Min bars between entries | 1 |
| Volume filter | ON |
| Volume rule | Above any 10/20/30-week average |
| Strong candle filter | OFF |
| Stop type | Consolidation Low |
| Stop buffer | 0.2 ATR |
| Take profit | 2R |
| Partial booking | 50% at 2R |
| Weekly TF1 short trend | ON |
| Weekly TF1 long trend | OFF |
| Weekly TF1 Darvas | OFF |
| Daily TF2 short trend | ON |
| Daily TF2 long trend | ON |
| Daily TF2 Darvas | OFF |
| Global Darvas | ON |
| Global Darvas length | 40 |
| Valid days | Removed |
| Point-in-time checks | Yes |

## Entry Logic Summary

The entry signal fires on a weekly bar after warmup when all major conditions align:

- Weekly layer confirms the primary trend context.
- Daily layer confirms point-in-time daily trend health from the latest available daily bar.
- Volume is above at least one of the 10/20/30-week average volume references.
- Global Darvas breakout confirms price has cleared the prior 40-bar body-high box.
- Strong candle is not required.

The philosophy is simple:

Weekly chooses the campaign. Daily confirms the structure. Darvas prevents weak breakouts from being treated as clean continuation.

## Trade Management

### Pyramiding

| Leg | Size | Requirement |
|---|---:|---|
| L1 | 50% | First valid entry signal |
| L2 | 30% | New signal while L1 is at least breakeven/profitable |
| L3 | 20% | New signal while L2 is at least breakeven/profitable |

### Stops and exits

- Initial stop uses the consolidation low.
- Stop tightens as the staircase progresses.
- 50% of each leg is booked at 2R.
- Remaining size rides until trend break, stop hit, or end of data.

### Exit behavior from the refreshed run

| Exit Reason | Dhan Count | Dhan Median R | Yahoo Count | Yahoo Median R |
|---|---:|---:|---:|---:|
| EMA Trend Break | 8,175 | 0.00 | 16,182 | 0.00 |
| SL Hit | 1,561 | -1.16 | 2,659 | -1.15 |
| End of Data | 525 | 0.32 | 472 | 0.38 |
| SMA Trend Break | 358 | -0.07 | 670 | -0.04 |

Main lesson: many exits close near 0R after the partial has already been booked. The edge is the combination of early 2R partials plus letting the remaining half follow the trend.

## Refreshed Full-Universe Results

Run date: 2026-05-25

| Metric | Dhan | Yahoo Finance |
|---|---:|---:|
| Stocks with trades | 667 | 656 |
| Total positions | 10,619 | 19,983 |
| Total R | +50,295.42 | +102,421.39 |
| Avg R / trade | 4.74 | 5.13 |
| Avg return / trade | 32.38% | 27.51% |
| Win rate | 46.9% | 49.4% |
| Partial hit rate | 36% | 39% |
| Median R / stock | 30.64 | 81.92 |
| Mean R / stock | 75.41 | 156.13 |
| Profitable stocks | 551 / 667 | 565 / 656 |
| Profitable stock % | 82.6% | 86.1% |

## Profit Factor Clarification

There are two useful profit factor views:

| Source | Stock-Level R PF | Trade-Level R PF |
|---|---:|---:|
| Dhan | 70.3 | 10.16 |
| Yahoo | 154.0 | 11.10 |

The screenshot value of 70.3 is the stock-level profit factor, calculated from profitable-stock total R versus losing-stock total R.

## R Distribution

### Dhan

| R Bucket | Count | % |
|---|---:|---:|
| >1000R | 4 | 1% |
| 501-1000R | 11 | 2% |
| 101-500R | 98 | 15% |
| 1-100R | 425 | 64% |
| Negative R | 116 | 17% |

### Yahoo Finance

| R Bucket | Count | % |
|---|---:|---:|
| >1000R | 11 | 2% |
| 501-1000R | 32 | 5% |
| 101-500R | 247 | 38% |
| 1-100R | 265 | 40% |
| Negative R | 89 | 14% |

Yahoo shifts the distribution to the right, especially in the 101-500R bucket.

## Top Contributors

### Dhan top 10

| Rank | Stock | Total R |
|---:|---|---:|
| 1 | DIACABS | 6170.43 |
| 2 | AXISCADES | 2863.36 |
| 3 | PGEL | 1202.50 |
| 4 | JAYNECOIND | 1007.78 |
| 5 | LUPIN | 923.15 |
| 6 | CDSL | 710.91 |
| 7 | OIL | 656.97 |
| 8 | APLAPOLLO | 622.06 |
| 9 | TIMETECHNO | 605.15 |
| 10 | MTARTECH | 576.45 |

### Yahoo top 10

| Rank | Stock | Total R |
|---:|---|---:|
| 1 | THERMAX | 4340.73 |
| 2 | INDIAGLYCO | 2612.13 |
| 3 | APLLTD | 2296.85 |
| 4 | BRITANNIA | 1818.88 |
| 5 | VAIBHAVGBL | 1814.90 |
| 6 | GLENMARK | 1752.78 |
| 7 | CANFINHOME | 1509.93 |
| 8 | LUPIN | 1357.53 |
| 9 | GRAPHITE | 1233.76 |
| 10 | JAYNECOIND | 1046.09 |

## Weak Contributors

### Dhan bottom 10

| Rank | Stock | Total R |
|---:|---|---:|
| 1 | TATACHEM | -80.56 |
| 2 | ZEEL | -69.38 |
| 3 | BAYERCROP | -24.83 |
| 4 | PVRINOX | -20.65 |
| 5 | AAVAS | -20.31 |
| 6 | CENTURYPLY | -16.31 |
| 7 | SHREECEM | -16.20 |
| 8 | KSCL | -16.02 |
| 9 | GODREJAGRO | -14.22 |
| 10 | DCBBANK | -12.84 |

### Yahoo bottom 10

| Rank | Stock | Total R |
|---:|---|---:|
| 1 | CHOLAHLDNG | -312.13 |
| 2 | AAVAS | -20.32 |
| 3 | BANDHANBNK | -15.72 |
| 4 | RTNPOWER | -15.16 |
| 5 | GODREJAGRO | -13.99 |
| 6 | AUBANK | -12.56 |
| 7 | NUVAMA | -10.53 |
| 8 | DIACABS | -10.29 |
| 9 | SBICARD | -10.29 |
| 10 | SAPPHIRE | -10.13 |

## Cross-Source Read

| Metric | Value |
|---|---:|
| Common stocks | 653 |
| Only in Dhan | 14 |
| Only in Yahoo | 3 |
| Pearson R | 0.143 |
| Spearman rank R | 0.614 |

Interpretation:

- Rank ordering is reasonably stable.
- Return magnitude is not stable.
- Dhan is the more conservative execution reference.
- Yahoo is useful for robustness checking but its adjusted price history can alter splits, gaps, moving averages, Darvas breaks, and stop behavior.

## Relationship To Minervini

This strategy is not pure SEPA, but it maps well to several Minervini principles:

- Stage 2 trend participation
- Trend template alignment
- Breakout confirmation
- Pyramiding into strength
- Cutting weaker structures through stop/trend-break exits
- Letting major winners carry the portfolio

The main difference is that this system is more mechanical and more tolerant of repeated signals across the same stock campaign.

## Relationship To Hermes

Hermes is the next research layer.

Staircase V3 answers:

What happens if weekly Staircase is traded directly across the full universe?

Hermes asks:

Can we learn from those weekly campaigns and execute better on daily, 1h, or 15m using activation windows, Darvas variants, filters, and per-entry diagnostics?

Important current distinction:

- This note is the canonical Staircase V3 weekly result.
- `research_outputs/hermes_v3/report.md` and `research_outputs/hermes_v3_daily/report.md` are Hermes research outputs, not this exact version.

## Graphify Status

Checked on 2026-05-25:

- `tools/graphify-out/GRAPH_REPORT.md` does not include Hermes.
- `analysis/minervini/graphify-out/GRAPH_REPORT.md` does not include Hermes.
- `analysis/minervini_obsidian/graphify-out/graph.json` and related graphify outputs did not return Hermes matches.

Conclusion: Hermes is implemented in code and reports, but it is not currently represented in the available Graphify knowledge graphs. To make Hermes queryable through Graphify, rerun Graphify over `tools/hermes_v3`, `tools/hermes_v3_daily`, and the relevant `research_outputs/hermes_*` reports.

## Pull-Up Prompt

Use [[Staircase V3 Analysis Pull-Up Prompt]] when you want Codex to reload this analysis, rerun it, compare it with Hermes, or explain the current active goals.


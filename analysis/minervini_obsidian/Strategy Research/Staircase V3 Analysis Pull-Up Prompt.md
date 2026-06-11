---
type: reusable-prompt
created: "2026-05-25"
updated: "2026-05-25"
tags:
  - prompt/staircase
  - prompt/hermes
  - strategy/staircase
  - research/source-comparison
aliases:
  - Staircase Pull-Up Prompt
  - Staircase V3 One Shot Prompt
---

# Staircase V3 Analysis Pull-Up Prompt

Copy this prompt when you want Codex to pull up the Staircase V3 analysis and continue from the correct version.

```text
You are working in:
C:\Users\yugan\OneDrive\Desktop\CLAUDE

First, follow AGENTS.md:
- Try code-review-graph MCP tools first.
- If unavailable, use checked-in Graphify artifacts before raw search.
- Do not scan unrelated folders broadly.

Task:
Pull up the canonical Staircase Weekly V3 Full Universe analysis and explain the current result, source files, and relationship to Hermes.

Canonical Obsidian note:
analysis\minervini_obsidian\Strategy Research\Staircase Weekly V3 Full Universe - Dhan Yahoo Source Study.md

Canonical Staircase scripts:
tools\staircase_weekly_backtest_v3_full_universe.py
tools\staircase_weekly_backtest_v3_yfinance_universe.py
tools\_compare_sources.py

Canonical outputs:
analysis\staircase_dhan\staircase_strategy_weekly_backtest_v3_full_universe.json
analysis\staircase_dhan\staircase_strategy_weekly_backtest_v3_full_universe.xlsx
analysis\staircase_dhan\staircase_strategy_weekly_backtest_v3_yfinance_universe.json
analysis\staircase_dhan\staircase_strategy_weekly_backtest_v3_yfinance_universe.xlsx

Hermes reports to compare only when needed:
research_outputs\hermes_v3\report.md
research_outputs\hermes_v3\combo_sweep\report.md
research_outputs\hermes_v3_daily\report.md

Important identity:
The screenshot result with 667 stocks, 10,619 positions, +50,295R, and stock-level PF 70.3 is NOT Hermes.
It is Staircase Weekly Backtest V3 Full Universe on Dhan:
tools\staircase_weekly_backtest_v3_full_universe.py

Strategy config:
- Scaling 50/30/20
- Volume filter ON, above any 10/20/30-week average
- Strong candle OFF
- Stop type: Consolidation Low
- Weekly TF1: short trend ON, long trend OFF, Darvas OFF
- Daily TF2: short trend ON, long trend ON, Darvas OFF
- Global Darvas ON, length 40
- Valid days removed, point-in-time only

Known refreshed results from 2026-05-25:
Dhan:
- Stocks with trades: 667
- Total positions: 10,619
- Total R: +50,295.42
- Avg R/trade: 4.74
- Win rate: 46.9%
- Partial hit rate: 36%
- Median R/stock: 30.64
- Mean R/stock: 75.41
- Profitable stocks: 551/667, 82.6%
- Stock-level PF: 70.3
- Trade-level R PF: 10.16

Yahoo:
- Stocks with trades: 656
- Total positions: 19,983
- Total R: +102,421.39
- Avg R/trade: 5.13
- Win rate: 49.4%
- Partial hit rate: 39%
- Median R/stock: 81.92
- Mean R/stock: 156.13
- Profitable stocks: 565/656, 86.1%
- Stock-level PF: 154.0
- Trade-level R PF: 11.10

Cross-source:
- Common stocks: 653
- Pearson R: 0.143
- Spearman rank R: 0.614
- Dhan is the conservative execution reference.
- Yahoo is useful for robustness, but adjusted prices change magnitude.

Graphify status:
As of 2026-05-25, Hermes was not present in the available Graphify outputs:
- tools\graphify-out\GRAPH_REPORT.md
- analysis\minervini\graphify-out\GRAPH_REPORT.md
- analysis\minervini_obsidian\graphify-out\graph.json

If I ask to rerun:
Use py -3.12, because plain python may not have numpy.

Commands:
py -3.12 tools\staircase_weekly_backtest_v3_full_universe.py
py -3.12 tools\staircase_weekly_backtest_v3_yfinance_universe.py
py -3.12 tools\_compare_sources.py

Then summarize:
1. Dhan result
2. Yahoo result
3. Source comparison
4. Whether numbers changed
5. What this means for Hermes V3 / Hermes V3 Daily
6. What the next active research goal should be
```


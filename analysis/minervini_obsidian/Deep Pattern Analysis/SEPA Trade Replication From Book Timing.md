---
type: sepa-replication-summary
generated: "2026-05-18"
---

# SEPA Trade Replication From Book Timing

This layer uses the two-book figure timing plus rebuilt OHLCV to infer study entries, pivots, stops, contraction behavior, volume dry-up, and post-entry reality checks.

It is a study reconstruction, not a claim about Minervini's private execution records.

## Coverage

- Total figure cases: 246
- Reconstructed from real OHLCV: 112
- Manual/data-limited cases: 134
- Pivot respected within 20 sessions: 51
- Inferred stop failed within 20 sessions: 25
- Tight/contraction cases from real data: 88
- Volume dry-up cases from real data: 58

## Setup Buckets

| Setup | Cases |
|---|---:|
| manual image-only study | 134 |
| vcp/contraction-study | 51 |
| pivot-breakout-study | 27 |
| failure/sell-rule-study | 14 |
| cheat-entry-study | 10 |
| climax-risk-study | 3 |
| shakeout-reclaim-study | 3 |
| ipo-base-study | 2 |
| stage-2-leadership-study | 1 |
| volume-dry-up-study | 1 |

## Confidence

| Confidence | Cases |
|---|---:|
| low | 134 |
| high | 106 |
| medium | 6 |

## Highest-Quality Study Candidates

| Case | Ticker | Setup | Entry Date | Extension | Risk | Volume | Contractions | 60d Max Gain | Stop Failed 20d |
|---|---|---|---|---:|---:|---|---|---:|---|
| [[Trade Like a Stock Market Wizard - Figure 10-11 - MSFT - page 224]] | MSFT | vcp/contraction-study | 1989-12-05 | -2.8% | 3.6% | moderate-dry-up | 31.2% -> 24.6% -> 17.0% | 20.3% | True |
| [[Trade Like a Stock Market Wizard - Figure 5-8 - WTW - page 92]] | WTW | failure/sell-rule-study | 2010-04-14 | 0.2% | 4.4% | moderate-dry-up | 9.2% -> 14.2% -> 4.2% | 7.8% | False |
| [[Think and Trade Like a Champion - Figure 6-1 - WTW - page 104]] | WTW | vcp/contraction-study | 2010-04-14 | 0.2% | 4.4% | moderate-dry-up | 9.2% -> 14.2% -> 4.2% | 7.8% | False |
| [[Think and Trade Like a Champion - Figure 9-14 - LUV - page 166]] | LUV | vcp/contraction-study | 2014-01-02 | -0.6% | 5.2% | moderate-dry-up | 19.8% -> 11.1% -> 7.2% | 28.0% | False |
| [[Trade Like a Stock Market Wizard - Figure 5-16 - BAC - page 101]] | BAC | failure/sell-rule-study | 2003-01-09 | 0.0% | 6.0% | moderate-dry-up | 33.5% -> 8.7% -> 6.0% | 0.7% | True |
| [[Think and Trade Like a Champion - Figure 7-17 - MSFT - page 138]] | MSFT | vcp/contraction-study | 1990-12-31 | -2.0% | 6.7% | strong-dry-up | 28.0% -> 17.3% -> 10.0% | 50.2% | False |
| [[Trade Like a Stock Market Wizard - Figure 5-17 - VICR - page 102]] | VICR | failure/sell-rule-study | 1991-06-21 | -3.6% | 7.3% | strong-dry-up | 43.8% -> 27.7% -> 21.9% | 41.6% | True |
| [[Trade Like a Stock Market Wizard - Figure 7-6 - VICR - page 145]] | VICR | vcp/contraction-study | 1991-06-21 | -3.6% | 7.3% | strong-dry-up | 43.8% -> 27.7% -> 21.9% | 41.6% | True |
| [[Trade Like a Stock Market Wizard - Figure 5-25 - ILMN - page 108]] | ILMN | failure/sell-rule-study | 2011-01-06 | 0.6% | 7.5% | moderate-dry-up | 19.9% -> 13.5% -> 7.7% | 10.6% | False |
| [[Trade Like a Stock Market Wizard - Figure 5-26 - ILMN - page 109]] | ILMN | vcp/contraction-study | 2011-01-06 | 0.6% | 7.5% | moderate-dry-up | 19.9% -> 13.5% -> 7.7% | 10.6% | False |
| [[Trade Like a Stock Market Wizard - Figure 7-9 - FFIV - page 148]] | FFIV | vcp/contraction-study | 2009-12-31 | -0.2% | 7.6% | strong-dry-up | 29.2% -> 16.3% -> 12.0% | 22.9% | False |
| [[Trade Like a Stock Market Wizard - Figure 9-9 - AMGN - page 190]] | AMGN | vcp/contraction-study | 1990-04-20 | -1.2% | 7.7% | moderate-dry-up | 31.4% -> 16.6% -> 8.9% | 32.8% | False |
| [[Think and Trade Like a Champion - Figure 9-16 - AMGN - page 167]] | AMGN | vcp/contraction-study | 1990-04-20 | -1.2% | 7.7% | moderate-dry-up | 31.4% -> 16.6% -> 8.9% | 32.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 7-2 - URBN - page 137]] | URBN | vcp/contraction-study | 2003-07-03 | -2.0% | 7.9% | moderate-dry-up | 27.1% -> 16.7% -> 11.2% | 45.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 5-6 - AMGN - page 91]] | AMGN | vcp/contraction-study | 1991-05-02 | -1.7% | 8.7% | moderate-dry-up | 44.7% -> 39.5% -> 10.6% | 8.4% | True |
| [[Trade Like a Stock Market Wizard - Figure 5-11 - AMGN - page 96]] | AMGN | failure/sell-rule-study | 1991-05-02 | -1.7% | 8.7% | moderate-dry-up | 44.7% -> 39.5% -> 10.6% | 8.4% | True |
| [[Trade Like a Stock Market Wizard - Figure 8-7 - DKS - page 167]] | DKS | vcp/contraction-study | 2003-11-20 | -0.5% | 9.4% | moderate-dry-up | 13.7% -> 27.2% -> 10.0% | 25.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 10-17 - DKS - page 229]] | DKS | shakeout-reclaim-study | 2003-11-20 | -0.5% | 9.4% | moderate-dry-up | 13.7% -> 27.2% -> 10.0% | 25.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 10-21 - DKS - page 234]] | DKS | vcp/contraction-study | 2003-11-20 | -0.5% | 9.4% | moderate-dry-up | 13.7% -> 27.2% -> 10.0% | 25.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 10-64 - DKS - page 272]] | DKS | vcp/contraction-study | 2003-11-20 | -0.5% | 9.4% | moderate-dry-up | 13.7% -> 27.2% -> 10.0% | 25.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 11-6 - DKS - page 280]] | DKS | pivot-breakout-study | 2003-11-20 | -0.5% | 9.4% | moderate-dry-up | 13.7% -> 27.2% -> 10.0% | 25.8% | False |
| [[Think and Trade Like a Champion - Figure 7-19 - DKS - page 139]] | DKS | vcp/contraction-study | 2003-11-20 | -0.5% | 9.4% | moderate-dry-up | 13.7% -> 27.2% -> 10.0% | 25.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 4-1 - AIG - page 57]] | AIG | vcp/contraction-study | 2000-06-15 | -0.6% | 10.0% | moderate-dry-up | 29.3% -> 20.4% -> 10.7% | 11.7% | False |
| [[Trade Like a Stock Market Wizard - Figure 10-44 - SYK - page 254]] | SYK | pivot-breakout-study | 1995-02-06 | 1.8% | 10.2% | moderate-dry-up | 13.2% -> 10.8% -> 9.0% | 15.9% | False |
| [[Trade Like a Stock Market Wizard - Figure 5-1 - AMGN - page 82]] | AMGN | vcp/contraction-study | 1988-09-29 | 0.4% | 10.2% | moderate-dry-up | 13.9% -> 17.4% -> 9.7% | 3.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 5-4 - AMGN - page 88]] | AMGN | vcp/contraction-study | 1993-12-27 | 0.5% | 10.3% | moderate-dry-up | 24.8% -> 15.0% -> 8.0% | 7.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 5-5 - AMGN - page 90]] | AMGN | failure/sell-rule-study | 1993-12-27 | 0.5% | 10.3% | moderate-dry-up | 24.8% -> 15.0% -> 8.0% | 7.8% | False |
| [[Trade Like a Stock Market Wizard - Figure 10-15 - MGA - page 227]] | MGA | pivot-breakout-study | 2010-11-04 | 0.8% | 10.7% | moderate-dry-up | 20.3% -> 13.0% -> 11.3% | 32.9% | False |
| [[Trade Like a Stock Market Wizard - Figure 10-23 - MGA - page 235]] | MGA | shakeout-reclaim-study | 2010-11-04 | 0.8% | 10.7% | moderate-dry-up | 20.3% -> 13.0% -> 11.3% | 32.9% | False |
| [[Trade Like a Stock Market Wizard - Figure 10-36 - MGA - page 246]] | MGA | vcp/contraction-study | 2010-11-04 | 0.8% | 10.7% | moderate-dry-up | 20.3% -> 13.0% -> 11.3% | 32.9% | False |

## What The Real Data Adds

- The book-image lesson becomes stronger when the reconstructed entry has tight contractions, dry-up, a nearby stop, and post-entry respect for the pivot.
- A stock can be a great leadership example but still a poor entry if the inferred stop is too wide or the move is already extended.
- Failure cases are valuable memory: if a pivot loses support quickly, the setup becomes a sell-rule lesson rather than a buy lesson.
- IPO/new-issue examples should be judged only after the early range begins to settle into a tradable structure.

Related: [[Entry Planning Playbook From Book Images]], [[Deep Pattern Analysis - Two Minervini Books]], [[Volatility Contraction Pattern]], [[Pivot and Entry]], [[Risk First]], [[Sell Rules and Failure Signals]]

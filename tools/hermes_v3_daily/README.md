# Hermes V3 Daily

"Weekly plans the trade. Daily executes the trade."

## Implementation Notes

### How Weekly Entries Are Planned (from staircase_weekly_backtest_v3.py)

The weekly V3 script (Pine Script port) computes entries on weekly bars:

**Weekly Entry Core:**
```
weekly_entry_signal = (
    w_base_core  (EMA9 > EMA21 AND close > EMA21 AND volume_ok AND strong_candle)
    AND w_tf1_ok  (short_term_ok OR long_term_ok, EMA filter, volume, optional Darvas)
    AND m_d_tf2_ok  (daily TF2 passed at Friday's close — point-in-time)
    AND w_global_darvas_ok  (close > prior 40-bar Darvas high)
)
```

**L1/L2/L3 on Weekly:**
- L1 fires when entry_signal is true and no position is open
- L2 fires when L1 is in profit (min_profit >= 0) AND bars spacing met AND entry_signal true
- L3 fires when L2 is in profit AND bars spacing met AND entry_signal true

**Weekly Trend Filters:**
- shortTermStacked: SMA10 > SMA20 > SMA50
- priceAboveShort: close > all short SMAs
- shortTermTrendOK: shortTermStacked AND priceAboveShort
- longTermStacked: SMA50 > SMA100 > SMA200
- sma50Rising, sma100Rising (slope lookback = 5)
- smasRising: sma50Rising AND sma100Rising
- priceAboveLong: close > SMA50, SMA100, SMA200
- majorTrendOK: (longStacked AND smasRising AND priceAboveLong) OR shortTermTrendOK

**Weekly Darvas:**
- Uses body_top (max(open,close)) and body_bottom (min(open,close))
- Global Darvas: 40-bar lookback, shifted by 1 (no lookahead)
- darvas_ok: close > prior_darvas_top

### What Weekly Activation Means

When weekly L1/L2/L3 fires, it creates an **activation window** of N bars (default 20, from
combo sweep findings). During this window, `weekly_active = True` is forward-filled to
daily bars. Daily entries are only permitted when `weekly_active` is true.

This is the key insight: weekly defines WHEN to trade, daily defines HOW.

### What Daily Entries Are Allowed To Do

Daily entries require:
1. **weekly_active == true** (weekly activation window is open)
2. Daily trend conditions (majorTrendOK, EMA9 > EMA21, close > EMA21)
3. Daily breakout (close > prior 20-bar high)
4. 1h/15m trend filter (intraday trend confirmation, point-in-time)
5. Selected Darvas filter passes
6. No strong candle requirement (excluded per design)

Daily pyramiding (L2/L3) requires weekly_active unless configured otherwise.

**Exits continue after weekly_active becomes false** — only entries are gated.

### What Darvas Box Logic Is Used

5 Darvas variants:
- **no_darvas**: No Darvas filter
- **weekly_darvas_gate**: Only enter when weekly Darvas breakout is active
- **daily_darvas_breakout**: Only enter when daily close > prior darvas_high (20-bar)
- **daily_darvas_support**: Only enter when daily close > prior darvas_low (20-bar)
- **weekly_plus_daily_darvas**: Both weekly gate AND daily breakout required

Default for this version: **weekly_plus_daily_darvas** with darvas_len=20.

### What Was Intentionally Excluded

- **Strong Candle Filter**: Removed entirely. No close>open + body% range checks
- **ADX Filter**: Not used in entry signal per design decision
- **15m/1h Entry Bars**: No trades on intraday timeframes. Daily execution only
- **Weekly Deactivation Exit**: Unlike original Hermes V3 engine, positions are NOT
  force-closed when weekly_active becomes false. Only entries are gated.
- **Volume Filter**: Not implemented in this version (kept simple)

### 1h/15m Trend Filter

While entries only happen on daily bars, the daily entry signal is gated by
intraday trend quality. At each daily bar, the 1h and 15m trend states are
checked (point-in-time, no lookahead):
- 1h_trend_ok = 1h short_trend_ok AND 1h major_trend_ok
- 15m_trend_ok = 15m short_trend_ok AND 15m major_trend_ok
- mtf_trend_ok = 1h_trend_ok AND 15m_trend_ok

This ensures daily entries only occur when intraday structure confirms.

### Comparison Baselines

From previous Hermes V3 combo sweep:
- **1d BASELINE**: 506 trades, 17.2% WR, 1.116R avg, 564.70 totalR, PF 2.86
- **1d +DARVAS20_VOL20_CANDLE**: 260 trades, 17.3% WR, 6.413R avg, 1667.48 totalR, PF 14.38

V3 Daily expected to approach or beat the candle-filtered version WITHOUT using
the strong candle filter, by substituting it with weekly activation gating +
intraday trend filters.

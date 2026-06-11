# BITA (Bitauto Holdings Ltd) — Daily Data Entry Windows

## Data Status: NOT AVAILABLE

**Yahoo Finance:** FAILED — "possibly delisted; no timezone found"
**Stooq:** API key required
**Alternative sources:** Not found in any accessible free data source

BITA (Bitauto Holdings Ltd) was acquired by Tencent Holdings in June 2020 and delisted from the NYSE. Historical OHLCV data is no longer available through standard free data providers.

---

## Reconstructed Window from Book Caption

### Figure 1-7 (p33): Follow-Through Sequence

Based on the caption: *"Stock broke out of a base, up 4 out of 5 days; then pulled in for 2 days before moving back into new high ground, then trading up 8 out of 10 days."*

```
Timeline (approximate, not to scale):

Breakout Day:   ★ PIVOT BREAKOUT (vol expansion)
Day 2:          UP
Day 3:          UP
Day 4:          UP
Day 5:          UP (4 out of 5 up)
Day 6:          DOWN ← Pullback day 1
Day 7:          DOWN ← Pullback day 2 (support found)
Day 8:          UP ← Resume / bounce
Day 9:          UP
Day 10:         UP ← New high ground
Day 11:         UP
Day 12:         UP
Day 13:         UP
Day 14:         UP
Day 15:         UP (8 out of 10 up from day 6-15)
```

### Figure 6-5 (p110): VCP Contraction Sequence

```
VCP Structure (approximate, not to scale):

C1: [==============]  -- Deepest contraction (widest range, highest vol)
C2: [===========]     -- Moderate contraction (narrower, lower vol)
C3: [======]          -- Tighter contraction (narrow, low vol)
C4: [===]             -- Tightest contraction (narrowest, lowest vol)
    ★ BREAKOUT        -- Expanding volume
```

---

## Manual Analysis

Since no data is available, use the following resources for manual review:

1. **Source image:** `analysis\minervini_obsidian\Book Stock Images\Think and Trade Like a Champion - Figure 1-7 - BITA - page 33.md`
2. **Source image:** `analysis\minervini_obsidian\Book Stock Images\Think and Trade Like a Champion - Figure 6-5 - BITA - page 110.md`
3. **Private book page images:**
   - `assets/book_pages_private/think-and-trade-like-a-champion/page_033.png`
   - `assets/book_pages_private/think-and-trade-like-a-champion/page_110.png`

### Entry Points (Theoretical)

| # | Date (Approx) | Price (Approx) | Pattern | Source |
|---|---|---|---|---|
| **1** | **Early 2013** | **~VCP Base High** | **VCP Breakout** | **Figure 6-5** |
| **2** | **Early 2013** | **~Base Breakout** | **Follow-Through** | **Figure 1-7** |

---

## Suggested Approach If Data Becomes Available

1. Check other data sources: Polygon.io, Tiingo, or a paid Yahoo Finance API
2. Check historical data on TradingView for BITA
3. If found, the key periods to analyze are:
   - VCP base: ~3-6 months before breakout
   - Entry: breakout day with expanding volume
   - Post-entry: 30-60 days for follow-through confirmation

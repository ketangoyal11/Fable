# Figure 1-1 — AI Training: The Minervini Risk-First Trade Management Framework

> **Source:** *Think and Trade Like a Champion*, Figure 1-1, Page 28
> **Caption:** "Know your trade priorities and how you will limit losses and protect profits as they accumulate."
> **Type:** Conceptual diagram (universal framework — applies to ANY stock, ANY timeframe)
> **Purpose:** Teach an AI to replicate Mark Minervini's pre-trade contingency planning and live-trade priority-shifting logic.

---

## 1. Image Deconstruction — Explicit Annotation Mapping

| Label | Visual Description | Exact Meaning | AI Interpretation |
|---|---|---|---|
| **"Buying Here"** | Arrow pointing to the first upswing breaking above a consolidation low | The exact entry trigger point where commitment occurs | `STATE = ENTRY_TRIGGERED` — buy order executed at or near this price |
| **Line `a`** | Lowest dashed horizontal line, drawn just below the consolidation/base | **Initial stop-loss placement** — the price at which the trade thesis is proven wrong | `RISK_CEILING` — maximum acceptable loss, defined BEFORE entry |
| **Line `b`** | Middle dashed horizontal line, drawn near the entry price area | **Breakeven protection zone** — once reached, priority shifts to not losing money on the trade | `BREAKEVEN_FLOOR` — stop raised to entry price or slightly below |
| **Line `c`** | Highest dashed horizontal line, drawn under a pullback during the uptrend | **Trailing profit-protection stop** — locks in gains while allowing trend continuation | `PROFIT_GUARD` — dynamic stop that rises with each higher low |
| **Stair-step uptrend** | Series of higher highs, higher lows with shallow pullbacks | Healthy trend structure — supply is under control, demand dominates | `TREND_QUALITY = HEALTHY` — each pullback holds above prior swing low |

---

## 2. The Minervini Decision Protocol — Step-by-Step AI Rules

### Phase 0: PRE-ENTRY (Before "Buying Here")

```
RULE 0.1: NO entry is permitted until Line a is defined.
RULE 0.2: Line a MUST be placed below a technically meaningful support level.
RULE 0.3: Position size is calculated backwards from Line a, NOT forwards from target price.

FORMULA:
    RISK_PER_SHARE = ENTRY_PRICE - LINE_A_PRICE
    SHARES_TO_BUY = (ACCOUNT_RISK_LIMIT %) / RISK_PER_SHARE
    
    IF RISK_PER_SHARE > MAX_ACCEPTABLE_RISK:
        THEN SKIP_TRADE = TRUE
        REASON = "Uncontrollable risk — line a too far from entry"
```

**AI Decision Tree:**
```
HAS_LINE_A_BEEN_DEFINED?
    ├── NO → BLOCK_ENTRY. Return: "Define stop loss first."
    └── YES → IS_LINE_A_TECHNICALLY_LOGICAL?
            ├── NO → BLOCK_ENTRY. Return: "Line a must be below support, not arbitrary."
            └── YES → CALCULATE_POSITION_SIZE
                        └── IS_RISK_CONTROLLABLE?
                                ├── NO → SKIP_TRADE
                                └── YES → PROCEED_TO_ENTRY
```

### Phase 1: ENTRY ("Buying Here")

```
RULE 1.1: Entry trigger = price clears a definable pivot, resistance, or base high.
RULE 1.2: Entry MUST be accompanied by volume confirmation (VRatio > 0.8x median).
RULE 1.3: At moment of entry, STATE transitions from MONITORING → POSITION_OPEN.
RULE 1.4: HARD STOP ORDER is placed at Line a immediately upon fill.
```

**State Transition:**
```
STATE: MONITORING
    ↓ (price breaks pivot + volume confirms)
STATE: POSITION_OPEN
    ↓ (simultaneous action)
ACTION: PLACE_STOP_ORDER(price = LINE_A)
PRIORITY_RANK: 1. Protect capital  2. Let trend develop
```

### Phase 2: EARLY ADVANCE (Between Entry and Line b)

```
RULE 2.1: DO NOT move stop to breakeven immediately.
RULE 2.2: Allow stock room to breathe — initial wiggles are normal.
RULE 2.3: Monitor for "pole" behavior: rapid advance with strong volume.
RULE 2.4: IF price retraces to Line a without stopping out → NORMAL.
RULE 2.5: IF price slices through Line a on volume → STOP_HIT. Trade thesis invalid.
```

**AI Priority Engine (Phase 2):**
```
CURRENT_PRIORITY = "LIMIT LOSSES"
SECONDARY_PRIORITY = "ALLOW_TREND_TO_DEVELOP"

IF price >= (ENTRY_PRICE + 2 * RISK_PER_SHARE):
    THEN SET_FLAG = "ready_for_line_b_upgrade"
    
IF price >= (ENTRY_PRICE + 3 * RISK_PER_SHARE) AND volume_dryup_on_pullback:
    THEN EVALUATE_LINE_B_PROMOTION
```

### Phase 3: BREAKEVEN PROTECTION (Line b Activated)

```
RULE 3.1: Line b is activated when stock has built a meaningful cushion above entry.
RULE 3.2: Stop order is moved from Line a to entry price (or 0.5x risk below entry).
RULE 3.3: Priority shifts: capital preservation → breakeven preservation.
RULE 3.4: Psychological rule: "I will not let a winner turn into a loser."
```

**State Transition:**
```
STATE: POSITION_OPEN
    ↓ (stock has advanced 2-3R from entry + first pullback holds well above Line a)
STATE: BREAKEVEN_PROTECTED
    ↓ (simultaneous action)
ACTION: MOVE_STOP_ORDER(price = LINE_B)
PRIORITY_RANK: 1. Protect breakeven  2. Allow further advance
```

**AI Logic for Line b Placement:**
```
LINE_B_OPTIONS:
    A: ENTRY_PRICE (true breakeven)
    B: ENTRY_PRICE - (0.3 * RISK_PER_SHARE) (small profit buffer)
    C: First pullback low after entry (if higher than entry)
    
DEFAULT_SELECTION = A (true breakeven)
OVERRIDE_CONDITION = IF first_pullback_low > ENTRY_price AND tight_consolidation:
                        THEN SELECT_C
```

### Phase 4: PROFIT PROTECTION (Line c Activated)

```
RULE 4.1: Line c is activated when stock has produced a "decent gain" (>3R preferred).
RULE 4.2: Line c is placed below the most recent significant higher low.
RULE 4.3: Line c is dynamic — it moves UP as new higher lows form.
RULE 4.4: NEVER move Line c DOWN. Stops only ratchet upward.
RULE 4.5: IF price hits Line c → EXIT. Do not second-guess. Contingency plan executes.
```

**State Transition:**
```
STATE: BREAKEVEN_PROTECTED
    ↓ (stock has advanced >3R + clear higher-low structure visible)
STATE: PROFIT_PROTECTED
    ↓ (simultaneous action)
ACTION: MOVE_STOP_ORDER(price = LINE_C_DYNAMIC)
UPDATE_RULE: LINE_C = MAX(LINE_C, most_recent_higher_low - buffer)
PRIORITY_RANK: 1. Protect accumulated profits  2. Allow trend continuation
```

**Dynamic Line c Update Logic:**
```
ON_EACH_NEW_HIGHER_LOW:
    NEW_CANDIDATE = swing_low_price - (0.5 * ATR_10)
    IF NEW_CANDIDATE > CURRENT_LINE_C:
        THEN LINE_C = NEW_CANDIDATE
        AND UPDATE_STOP_ORDER
    ELSE:
        MAINTAIN_CURRENT_LINE_C
```

### Phase 5: EXIT (Line c Hit or Trend Death)

```
RULE 5.1: Exit is AUTOMATIC when price touches Line c.
RULE 5.2: No emotional override permitted — contingency plan was pre-committed.
RULE 5.3: Post-exit: immediately evaluate if re-entry setup is forming (new base).
RULE 5.4: Post-exit: log whether exit was at profit, breakeven, or loss for journal.
```

**Exit Classification:**
```
EXIT_PRICE vs ENTRY_PRICE:
    IF EXIT_PRICE >= ENTRY_PRICE + 3*RISK:
        CLASS = "PROFIT_PROTECTION_EXIT" (optimal outcome)
    ELIF EXIT_PRICE >= ENTRY_PRICE:
        CLASS = "BREAKEVEN_OR_SMALL_GAIN_EXIT" (acceptable)
    ELIF EXIT_PRICE >= LINE_A:
        CLASS = "CONTROLLED_LOSS_EXIT" (risk management worked)
    ELSE:
        CLASS = "SLIPPAGE_LOSS_EXIT" (gap through stop — log for review)
```

---

## 3. The Priority-Shift Engine — Core Minervini Mental Model

This is the most critical AI teaching point. Minervini's priorities **change as the trade evolves**:

```
┌─────────────────────────────────────────────────────────────┐
│                    MINERVINI PRIORITY STACK                  │
├─────────────────────────────────────────────────────────────┤
│ PHASE          │ PRIORITY #1          │ PRIORITY #2         │
├─────────────────────────────────────────────────────────────┤
│ Pre-Entry      │ Define Line a        │ Wait for setup      │
│ Entry          │ Execute with stop    │ Confirm volume      │
│ Early Advance  │ Don't move stop early│ Let it breathe      │
│ Line b Zone    │ Protect breakeven    │ Allow further run   │
│ Line c Zone    │ Protect profits      │ Stay in trend       │
│ Exit           │ Execute plan         │ Evaluate re-entry   │
└─────────────────────────────────────────────────────────────┘
```

**AI Instruction:** The priority stack must be explicitly tracked as a state variable. At any moment, the AI must be able to answer: *"What is my #1 priority right now?"*

---

## 4. Contingency Planning Matrix — Pre-Committed Responses

Minervini's key insight from Figure 1-1's caption: **good decisions under fire come from pre-planning, not improvisation.**

| Scenario | Pre-Committed Response | Emotional Trap Prevented |
|---|---|---|
| Stock drops to Line a on Day 1 | Stop executes. Loss is small and planned. | "Maybe it'll bounce back" → holding into bigger loss |
| Stock rallies +5% then pulls back to entry | Stop at Line b (breakeven) executes. No loss. | "I'm green, I should add more" → average up poorly |
| Stock rallies +20%, forms higher low | Move Line c under new higher low. Let it run. | "Take profits now!" → exiting too early |
| Stock gaps down through Line c overnight | Market order exit at open. Accept slippage. | "It'll recover" → holding a broken trend |
| Stock rallies hard, no clear higher low | Trail Line c using 10-day MA or 3-ATR band. | "I don't know where to put my stop" → no protection |

**AI Implementation:**
```python
CONTINGENCY_PLAN = {
    "line_a_hit": {
        "action": "MARKET_EXIT",
        "emotion_override_prevention": "Loss was calculated and acceptable. Thesis wrong. Move on.",
        "reentry_evaluation": "Wait for new base to form. Do not chase."
    },
    "line_b_hit": {
        "action": "STOP_EXIT",
        "emotion_override_prevention": "Breakeven preserved. The trade did not work as hoped. Capital intact.",
        "reentry_evaluation": "If setup re-forms above base, treat as fresh opportunity."
    },
    "line_c_hit": {
        "action": "STOP_EXIT",
        "emotion_override_prevention": "Profit locked in. Trend may continue but your edge is gone.",
        "reentry_evaluation": "If stock builds new base and breaks out again → new entry with new Line a."
    }
}
```

---

## 5. Trend Quality Assessment — Is This a "Figure 1-1" Chart?

Not all charts look like Figure 1-1. The AI must recognize when a chart *matches* this healthy framework and when it does NOT.

### HEALTHY (Figure 1-1 Match):
```
✓ Higher highs, higher lows (each pullback holds above prior swing low)
✓ Pullbacks are shallow relative to advances (typically < 50% retracement)
✓ Volume dries up on pullbacks (supply absent)
✓ Volume expands on advances (demand present)
✓ Swing lows are clearly definable (Line c can be placed logically)
✓ The "stair-step" is visible — not a vertical spike
```

### UNHEALTHY (Figure 1-1 Mismatch — DO NOT Apply Framework Blindly):
```
✗ Lower highs, lower lows → this is distribution/decline, not advance
✗ Deep pullbacks (> 50% of prior advance) → trend weak, stops get hit
✗ Volume expands on declines → supply is active
✗ No definable swing lows → Line c cannot be placed, framework fails
✗ Vertical spike with no base → entry is extended, Line a too far away
✗ WIDE, LOOSE price action → stops cannot be placed with confidence
```

**AI FILTER:**
```
IF chart_does_NOT_match_figure_1_1_structure:
    THEN framework_status = "INAPPLICABLE"
    AND action = "WAIT_FOR_BETTER_SETUP"
    
    EXCEPTION: IPO bases and VCP tightness can compress the "stair-step" 
    into a smaller timeframe, but the principle still holds.
```

---

## 6. Mapping Figure 1-1 to Real GOOG Entries

| GOOG Entry | Line a (Initial Stop) | When Line b Activated | Line c (Final Trailing Stop) | Exit Outcome |
|---|---|---|---|---|
| **Entry 1** Apr 22, 2005 @ $5.38 | ~$4.85 (below VCP low, risk ~$0.53/share) | After May 6 close $5.68 — stop moved to ~$5.30 | Under Jun 17 pullback low ~$6.50 | **Profit** — exited via flag formation, re-entered later |
| **Entry 2** Oct 21, 2005 @ $8.47 | ~$7.50 (flag low, risk ~$0.97/share) | After Oct 23 continuation — stop moved to ~$8.40 | Under Nov pullback low ~$9.80 | **Profit** — base-on-base formed |
| **Entry 3** Oct 6, 2006 @ $10.47 | ~$9.92 (Oct 3 low, risk ~$0.55/share) | After Oct 9 push — stop moved to ~$10.40 | Under Nov 21 pullback low ~$11.20 | **Profit** — base-on-base formed |
| **Entry 4** May 30, 2007 @ $12.42 | ~$11.89 (May 25 low, risk ~$0.53/share) | After Jun 5 continuation — stop moved to ~$12.35 | Under Jul 20 gap-down open ~$12.75 | **Small profit/breakeven** — gap down hit trailing stop |
| **Entry 5** Sep 18, 2007 @ $13.33 | ~$12.75 (Aug 17 gap-up support, risk ~$0.58/share) | After Sep 21 push $13.95 — stop moved to ~$13.30 | Under Nov 7 higher low → fast MA break ~$17.28 | **+38.6% profit** — Line c hit on Nov 8 |

**Teaching Point for AI:** Notice how Entries 1-4 did NOT hit Line c — they transitioned into new bases (flags, VCPs, base-on-base). The framework is not just about exits; it's about **knowing when your capital is at risk and when it's protected**, which allows you to HOLD through consolidations.

---

## 7. The "Under Fire" Psychological Protocol

From the book caption: *"The important role contingency planning plays is that it enables you to make good decisions when you're under fire — when you need it the most."*

This is the **emotional override prevention system**. The AI must treat this as a hard constraint:

```
CONSTRAINT: All decisions at Line a, Line b, and Line c are PRE-COMMITTED.

AT RUNTIME (when price hits any line):
    OVERRIDE_ATTEMPTS_DETECTED = [
        "Maybe it'll bounce back",
        "I'll just give it one more day",
        "The market is down, it's not the stock's fault",
        "I have a feeling it'll recover",
        "I'm down too much to sell now"
    ]
    
    FOR EACH thought IN OVERRIDE_ATTEMPTS_DETECTED:
        IF detected:
            THEN BLOCK_OVERRIDE = TRUE
            AND EXECUTE_PRECOMMITTED_PLAN
```

**AI Behavioral Rule:**
> The AI does not "decide" at the stop-loss point. The AI decided BEFORE entry. The stop-loss point is purely for EXECUTION.

---

## 8. AI Self-Check Questions — The Minervini Diagnostic

Before every entry, the AI must answer these questions in order:

```
[1] WHERE IS LINE a?
    → Must be a specific price, not a range. Must be below support.
    
[2] HOW MUCH AM I RISKING?
    → Must be a specific dollar amount and % of account.
    → IF > 1.25% of account: REJECT entry or reduce size.
    
[3] WHERE WILL LINE b BE?
    → Pre-commit: "When price reaches $X, I move stop to breakeven."
    
[4] WHERE WILL LINE c START?
    → Pre-commit: "When price reaches $Y, I trail under higher lows."
    
[5] WHAT IS THE SCENARIO WHERE I AM WRONG?
    → Describe the chart action that would prove the thesis false.
    → IF you cannot describe it: you do not understand the setup.
    
[6] CAN I AFFORD TO LOSE THIS AMOUNT EMOTIONALLY?
    → If the loss would cause tilt: REDUCE SIZE by 50%.
    → Minervini: "If you're sweating the trade, you're trading too big."
```

---

## 9. Integration with Other Minervini Concepts

| Concept | How Figure 1-1 Uses It | Integration Point |
|---|---|---|
| **SEPA / Trend Template** | Only trade stocks that pass Trend Template → ensures the stair-step structure exists | Pre-filter: no Figure 1-1 framework without Stage 2 uptrend |
| **VCP** | Tight VCP defines the base where "Buying Here" occurs | Line a sits below the VCP low |
| **Pivot** | Entry trigger is a pivot break | "Buying Here" = price clears defined pivot |
| **Volume Dry-Up** | VCP contraction includes volume drying up | Validates that Line a will hold (no supply) |
| **Flag & Pole** | Pole creates the distance to Line b and Line c | Framework accelerates through phases during pole runs |
| **Low Cheat** | Entry within base, before full pivot break | Line a is even tighter because risk is compressed |
| **Base-on-Base** | Stock consolidates instead of hitting Line c | Framework PAUSES — stops don't move, waiting for new breakout |

---

## 10. Summary — The AI Minervini Risk-First Algorithm

```python
def minervini_trade_manager(setup, account):
    """
    AI implementation of Figure 1-1 risk framework.
    Returns: trade_log, exit_signal, psychological_notes
    """
    
    # PHASE 0: PRE-ENTRY
    line_a = calculate_technical_stop(setup)
    risk_per_share = setup.pivot_break_price - line_a
    if risk_per_share <= 0 or risk_per_share > setup.max_acceptable_risk:
        return SKIP_TRADE("Risk undefined or uncontrollable")
    
    position_size = (account.risk_limit_percent * account.equity) / risk_per_share
    line_b = setup.pivot_break_price  # breakeven
    line_c = None  # activated later
    
    # PHASE 1: ENTRY
    execute_buy(setup.pivot_break_price, shares=position_size)
    place_stop_order(line_a)
    state = "POSITION_OPEN"
    priority = "LIMIT_LOSSES"
    
    # PHASE 2+: MONITOR
    for bar in setup.subsequent_bars:
        
        # Check for Line a hit
        if bar.low <= line_a:
            execute_stop_exit()
            return LOG_EXIT("Line a hit — controlled loss", line_a)
        
        # Evaluate Line b promotion
        if state == "POSITION_OPEN" and bar.close >= setup.pivot_break_price + (2.5 * risk_per_share):
            if higher_low_structure_confirmed():
                move_stop_to(line_b)
                state = "BREAKEVEN_PROTECTED"
                priority = "PROTECT_BREAKEVEN"
        
        # Evaluate Line c activation
        if state == "BREAKEVEN_PROTECTED" and bar.close >= setup.pivot_break_price + (4 * risk_per_share):
            line_c = calculate_trailing_stop_under_higher_lows()
            move_stop_to(line_c)
            state = "PROFIT_PROTECTED"
            priority = "PROFIT_PROTECTION"
        
        # Dynamic Line c update
        if state == "PROFIT_PROTECTED":
            new_line_c = update_trailing_stop(bar)
            if new_line_c > line_c:
                line_c = new_line_c
                move_stop_to(line_c)
        
        # Check for Line c hit
        if state == "PROFIT_PROTECTED" and bar.low <= line_c:
            execute_stop_exit()
            return LOG_EXIT("Line c hit — profit protected", line_c)
    
    return ACTIVE_POSITION(state, current_stop)
```

---

## 11. Key Takeaway for AI Training

> **Figure 1-1 is not a chart pattern to memorize. It is a MENTAL OPERATING SYSTEM.**

The AI must internalize:
1. **Risk is defined before entry, not after.**
2. **Priorities shift as the trade evolves.** The same brain that accepted risk at entry must protect profits at the top.
3. **Stops are pre-committed, not decided in real-time.** Real-time decisions under P&L pressure are emotional decisions.
4. **The stair-step structure (higher highs, higher lows) is the visual proof that the framework is working.** If the structure breaks, the framework demands exit.
5. **Contingency planning = trading with a script.** The AI must never improvise at the stop-loss line.

---

*Document generated for AI training purposes. Maps Figure 1-1 conceptual framework to executable trading logic, state machines, and psychological safeguards.*

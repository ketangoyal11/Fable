"""Staircase Strategy Loop - multi-position pyramiding with trend filters."""
import asyncio
import json
import os
import yaml
from datetime import datetime, timezone
from pathlib import Path

from hermes_trading import logger
from hermes_trading.adapters.price import fetch as price_fetch

CONSECUTIVE_FAILURE_LIMIT = 5
LOOP_INTERVAL = 60
MAX_RETRIES = 3


def load_yaml(path):
    with open(path) as fh:
        return yaml.safe_load(fh)


def get_dynamic_sl(cfg, pd):
    return pd.get("dynamic_sl", pd["close"])


async def loop(asset, state_dir: Path):
    strategy_path = state_dir / "strategy.yaml"
    trades_path = state_dir / "trades.jsonl"
    heartbeat_path = state_dir / "heartbeat.json"

    consecutive_failures = 0
    bar_index = 0
    bars_since_last_entry = 999

    pos_count = 0
    last_entry_bar = -999

    entries = [
        {"taken": False, "price": None, "sl": None, "tp": None, "partial_taken": False, "bar": -1},
        {"taken": False, "price": None, "sl": None, "tp": None, "partial_taken": False, "bar": -1},
        {"taken": False, "price": None, "sl": None, "tp": None, "partial_taken": False, "bar": -1},
    ]

    logger.info("staircase_loop_starting", asset=asset)

    while True:
        try:
            strategy = load_yaml(strategy_path)
            entry_cfg = strategy.get("entry", {})
            exit_cfg = strategy.get("exit", {})
            pyramiding_cfg = strategy.get("pyramiding", {})
            min_bars_between = pyramiding_cfg.get("min_bars_between", 3)
            min_profit_for_next = pyramiding_cfg.get("min_profit_for_next", 0.0)

            price_data = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    price_data = price_fetch(asset, strategy=strategy)
                    break
                except Exception as e:
                    logger.warning("price_fetch_retry", attempt=attempt, error=str(e))
                    await asyncio.sleep(2 ** attempt)

            if price_data is None:
                raise RuntimeError("Price adapter exhausted retries")

            bar_index += 1
            bars_since_last_entry += 1
            close = price_data["close"]

            entry_signal = price_data.get("entry_signal", False)
            ema_crossunder = price_data.get("ema_crossunder", False)
            sma_crossunder = price_data.get("sma_crossunder", False)
            trend_break = ema_crossunder or sma_crossunder

            sl_buffer_atr = exit_cfg.get("sl_buffer_atr", 0.2)
            tp_rr = exit_cfg.get("tp_rr", 2.0)
            partial_exits = exit_cfg.get("partial_exits", [0, 0, 0])
            pos_sizes = pyramiding_cfg.get("sizes", [33, 33, 34])

            can_enter = bars_since_last_entry >= min_bars_between

            def pos_pnl(e):
                if not e["taken"] or e["price"] is None or e["price"] == 0:
                    return None
                return (close - e["price"]) / e["price"] * 100

            def can_add(i):
                if i == 0:
                    return pos_count == 0
                prev = entries[i - 1]
                if not prev["taken"]:
                    return False
                pnl = pos_pnl(prev)
                if pnl is None:
                    return False
                return pnl >= min_profit_for_next

            entry_made_this_tick = False

            for i in range(3):
                e = entries[i]
                if e["taken"]:
                    continue
                if pos_count != i:
                    continue
                if not can_enter:
                    continue
                if not can_add(i):
                    continue
                if not entry_signal:
                    continue

                current_sl = get_dynamic_sl(exit_cfg, price_data)
                risk = close - current_sl
                tp = close + risk * tp_rr

                e["taken"] = True
                e["price"] = close
                e["sl"] = current_sl
                e["tp"] = tp
                e["partial_taken"] = False
                e["bar"] = bar_index
                pos_count = i + 1
                last_entry_bar = bar_index
                bars_since_last_entry = 0
                entry_made_this_tick = True

                logger.info("staircase_entry", level=f"L{i+1}", price=close,
                           sl=round(current_sl, 2), tp=round(tp, 2),
                           pct=pos_sizes[i], position_count=pos_count)

                if i >= 1:
                    for j in range(i):
                        entries[j]["sl"] = current_sl

                break

            if not entry_made_this_tick and pos_count > 0:
                trail = None
                if pos_count == 1:
                    trail = price_data.get("trail_sma20", entries[0]["sl"])
                else:
                    trail = price_data.get("trail_sma50", entries[0]["sl"])

                for e in entries:
                    if e["taken"] and trail is not None:
                        e["sl"] = max(e["sl"], trail)

            if pos_count > 0:
                if trend_break:
                    logger.info("trend_break_exit", ema_cross=ema_crossunder,
                               sma_cross=sma_crossunder, close=close)
                    for i, e in enumerate(entries):
                        if e["taken"]:
                            pnl = pos_pnl(e)
                            trade = {
                                "ts": datetime.now(timezone.utc).isoformat(),
                                "asset": asset,
                                "level": f"L{i+1}",
                                "entry_price": e["price"],
                                "exit_price": close,
                                "pnl_pct": round(pnl, 4) if pnl is not None else 0,
                                "exit_reason": f"trend_break_{'ema' if ema_crossunder else 'sma'}",
                                "strategy_version": strategy.get("version", "01"),
                            }
                            with open(trades_path, "a") as tf:
                                tf.write(json.dumps(trade) + "\n")
                            logger.info("staircase_trade_closed", **trade)
                    for e in entries:
                        e["taken"] = False
                        e["price"] = None
                        e["sl"] = None
                        e["tp"] = None
                        e["partial_taken"] = False
                        e["bar"] = -1
                    pos_count = 0
                    continue

                composite_sl = None
                for e in reversed(entries):
                    if e["taken"] and e["sl"] is not None:
                        composite_sl = e["sl"]
                        break

                if composite_sl is not None and close < composite_sl:
                    logger.info("stop_loss_hit", sl=round(composite_sl, 2), close=close)
                    for i, e in enumerate(entries):
                        if e["taken"]:
                            pnl = pos_pnl(e)
                            trade = {
                                "ts": datetime.now(timezone.utc).isoformat(),
                                "asset": asset,
                                "level": f"L{i+1}",
                                "entry_price": e["price"],
                                "exit_price": close,
                                "pnl_pct": round(pnl, 4) if pnl is not None else 0,
                                "exit_reason": "stop_loss",
                                "strategy_version": strategy.get("version", "01"),
                            }
                            with open(trades_path, "a") as tf:
                                tf.write(json.dumps(trade) + "\n")
                            logger.info("staircase_trade_closed", **trade)
                    for e in entries:
                        e["taken"] = False
                        e["price"] = None
                        e["sl"] = None
                        e["tp"] = None
                        e["partial_taken"] = False
                        e["bar"] = -1
                    pos_count = 0
                    continue

                for i, e in enumerate(entries):
                    if not e["taken"]:
                        continue
                    if e["partial_taken"]:
                        continue
                    if e["tp"] is None:
                        continue
                    if partial_exits[i] <= 0:
                        continue
                    if close >= e["tp"]:
                        pnl = pos_pnl(e)
                        trade = {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "asset": asset,
                            "level": f"L{i+1}",
                            "entry_price": e["price"],
                            "exit_price": close,
                            "pnl_pct": round(pnl, 4) if pnl is not None else 0,
                            "exit_reason": "take_profit",
                            "partial_exit_pct": partial_exits[i],
                            "strategy_version": strategy.get("version", "01"),
                        }
                        with open(trades_path, "a") as tf:
                            tf.write(json.dumps(trade) + "\n")
                        logger.info("staircase_partial_tp", **trade)

                        if partial_exits[i] >= 100:
                            e["taken"] = False
                            e["price"] = None
                            e["sl"] = None
                            e["tp"] = None
                            e["partial_taken"] = False
                            e["bar"] = -1
                            pos_count = max(0, pos_count - 1)
                        else:
                            e["partial_taken"] = True

            heartbeat = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "asset": asset,
                "close": close,
                "adx": price_data.get("adx", 0),
                "entry_signal": entry_signal,
                "major_trend_ok": price_data.get("major_trend_ok", False),
                "ema_uptrend": price_data.get("ema_uptrend", False),
                "position_count": pos_count,
                "bars_since_last_entry": bars_since_last_entry,
                "consecutive_failures": consecutive_failures,
                "emergent_exits_since_start": 0,
            }
            with open(heartbeat_path, "w") as hf:
                json.dump(heartbeat, hf)

            consecutive_failures = 0

        except Exception as e:
            consecutive_failures += 1
            logger.error("loop_iteration_failed", error=str(e),
                         consecutive_failures=consecutive_failures)
            if consecutive_failures >= CONSECUTIVE_FAILURE_LIMIT:
                logger.critical("circuit_breaker_tripped",
                               consecutive_failures=consecutive_failures)
                raise

        await asyncio.sleep(LOOP_INTERVAL)

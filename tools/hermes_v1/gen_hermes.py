"""Generate all Hermes Trading Python files using only ASCII."""
import os, pathlib

base = os.path.join(os.environ['USERPROFILE'], 'hermes-trading')
hd = os.path.join(base, 'hermes_trading')
ad = os.path.join(hd, 'adapters')
sd = os.path.join(base, 'state')
os.makedirs(os.path.join(sd, 'history'), exist_ok=True)
os.makedirs(ad, exist_ok=True)

def write(rel, content):
    path = os.path.join(base, rel)
    with open(path, 'w', encoding='ascii') as f:
        f.write(content)
    print(f'  {rel}')

# === hermes_trading/__init__.py ===
write('hermes_trading/__init__.py', """import asyncio
import yaml
import structlog

logger = structlog.get_logger()
""")

# === hermes_trading/run.py ===
write('hermes_trading/run.py', '''"""Hermes Trading Agent - entrypoint."""
import asyncio
import argparse
import sys
import os
import yaml
from pathlib import Path
from hermes_trading.loop import loop
from hermes_trading import logger

STATE_DIR = Path(__file__).resolve().parent.parent / "state"
GOAL_PATH = STATE_DIR / "goal.yaml"

def load_goal():
    with open(GOAL_PATH) as fh:
        return yaml.safe_load(fh)

async def main():
    parser = argparse.ArgumentParser(description="Hermes Trading Agent")
    parser.add_argument("--asset", type=str, help="Override the asset from goal.yaml")
    args = parser.parse_args()

    goal = load_goal()
    asset = args.asset or goal["asset"]
    logger.info("hermes_trading_worker_booting", asset=asset,
                mode=os.environ.get("HERMES_TRADING_MODE", "paper"))

    await loop(asset=asset, state_dir=STATE_DIR)

if __name__ == "__main__":
    asyncio.run(main())
''')

# === hermes_trading/loop.py ===
write('hermes_trading/loop.py', '''"""Async reliability loop - pull data, evaluate strategy, paper trade."""
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

async def loop(asset, state_dir: Path):
    strategy_path = state_dir / "strategy.yaml"
    trades_path = state_dir / "trades.jsonl"
    heartbeat_path = state_dir / "heartbeat.json"

    consecutive_failures = 0
    entry_fired = False
    entry_price = None

    logger.info("loop_starting", asset=asset)

    while True:
        try:
            strategy = load_yaml(strategy_path)
            price_data = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    price_data = await price_fetch(asset)
                    break
                except Exception as e:
                    logger.warning("price_fetch_retry", attempt=attempt, error=str(e))
                    await asyncio.sleep(2 ** attempt)

            if price_data is None:
                raise RuntimeError("Price adapter exhausted retries - no data")

            close = price_data.get("close")
            entry = strategy["entry"]
            indicator = entry["indicator"]
            threshold = entry["threshold"]
            direction = entry["direction"]
            stop_loss_pct = strategy.get("stop_loss_pct", 2.0)
            position_size_r = strategy.get("position_size_r", 0.5)
            rsi_val = price_data.get("rsi", 50)

            if not entry_fired:
                if direction == "long" and rsi_val < threshold:
                    entry_fired = True
                    entry_price = close
                    logger.info("entry_long_fired", rsi=rsi_val, price=close, threshold=threshold)
                elif direction == "short" and rsi_val > (100 - threshold):
                    entry_fired = True
                    entry_price = close
                    logger.info("entry_short_fired", rsi=rsi_val, price=close, threshold=threshold)

            if entry_fired and entry_price is not None:
                pnl_pct = ((close - entry_price) / entry_price) * 100
                if direction == "short":
                    pnl_pct = -pnl_pct
                if pnl_pct <= -stop_loss_pct:
                    trade = {
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "asset": asset,
                        "direction": direction,
                        "entry_price": entry_price,
                        "exit_price": close,
                        "pnl_pct": round(pnl_pct, 4),
                        "indicator": indicator,
                        "threshold": threshold,
                        "stop_loss_pct": stop_loss_pct,
                        "position_size_r": position_size_r,
                        "strategy_version": strategy.get("version", "01"),
                    }
                    with open(trades_path, "a") as tf:
                        tf.write(json.dumps(trade) + "\\n")
                    logger.info("trade_closed", **trade)
                    entry_fired = False
                    entry_price = None

            heartbeat = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "asset": asset,
                "close": close,
                "rsi": rsi_val,
                "entry_fired": entry_fired,
                "consecutive_failures": consecutive_failures,
                "mode": os.environ.get("HERMES_TRADING_MODE", "paper"),
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
''')

# === hermes_trading/reflect.py ===
write('hermes_trading/reflect.py', '''"""Reflection cycle - deterministic fallback and Hermes-driven mode."""
import argparse
import json
import shutil
import subprocess
import yaml
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path(__file__).resolve().parent.parent / "state"
STRATEGY_PATH = STATE_DIR / "strategy.yaml"
TRADES_PATH = STATE_DIR / "trades.jsonl"
HYPOTHESES_PATH = STATE_DIR / "hypotheses.jsonl"
GOAL_PATH = STATE_DIR / "goal.yaml"
HISTORY_DIR = STATE_DIR / "history"


def load_trades(n=25):
    trades = []
    if not TRADES_PATH.exists():
        return trades
    with open(TRADES_PATH) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    trades.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return trades[-n:]


def load_yaml(path):
    with open(path) as fh:
        return yaml.safe_load(fh)


def save_yaml(path, data):
    with open(path, "w") as fh:
        yaml.dump(data, fh, default_flow_style=False)


def bump_version(strategy):
    ver = int(strategy.get("version", "01"))
    return f"{ver + 1:02d}"


def save_history(strategy):
    ver = strategy.get("version", "unknown")
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    dest = HISTORY_DIR / f"v{ver}.yaml"
    shutil.copy(STRATEGY_PATH, dest)


def append_hypothesis(hyp, trades_used, ver):
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "version": ver,
        "hypothesis": hyp,
        "trades_used": trades_used,
    }
    with open(HYPOTHESES_PATH, "a") as fh:
        fh.write(json.dumps(record) + "\\n")


def compute_return(trades):
    if not trades:
        return 0.0, 0.0
    pnls = [t["pnl_pct"] for t in trades]
    total = sum(pnls)
    return total, total / len(pnls)


def compute_drawdown(trades):
    if not trades:
        return 0.0
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        cumulative += t["pnl_pct"]
        peak = max(peak, cumulative)
        dd = peak - cumulative
        max_dd = max(max_dd, dd)
    return max_dd


def fallback_reflect():
    strategy = load_yaml(STRATEGY_PATH)
    goal = load_yaml(GOAL_PATH)
    trades = load_trades(n=goal.get("reflection_every", 10))

    if len(trades) < goal.get("reflection_every", 10):
        print(f"Not enough trades for reflection: {len(trades)}/{goal['reflection_every']}")
        return

    total_return, avg_return = compute_return(trades)
    dd = compute_drawdown(trades)
    target = goal["target_return_30d"] * 100
    max_dd_target = goal["max_drawdown"] * 100

    save_history(strategy)
    ver = bump_version(strategy)
    strategy["version"] = ver

    hypothesis = None
    if total_return < target:
        old_threshold = strategy["entry"]["threshold"]
        strategy["entry"]["threshold"] = max(10, old_threshold - 2)
        hypothesis = (
            f"Return {total_return:.2f}% < target {target}% - "
            f"loosened entry.threshold {old_threshold} -> {strategy['entry']['threshold']}"
        )
    elif dd > max_dd_target:
        old_sl = strategy["stop_loss_pct"]
        strategy["stop_loss_pct"] = round(old_sl + 0.2, 1)
        hypothesis = (
            f"Drawdown {dd:.2f}% > max {max_dd_target}% - "
            f"tightened stop_loss_pct {old_sl} -> {strategy['stop_loss_pct']}"
        )
    else:
        strategy["entry"]["threshold"] = max(10, strategy["entry"]["threshold"] - 1)
        hypothesis = "Performance within bounds - exploratory loosening of entry.threshold by 1"

    save_yaml(STRATEGY_PATH, strategy)
    append_hypothesis(hypothesis, len(trades), ver)
    print(f"Reflection complete - strategy v{ver}")
    print(f"  Hypothesis: {hypothesis}")
    print(f"  Trades analyzed: {len(trades)}")


def hermes_reflect():
    strategy = load_yaml(STRATEGY_PATH)
    goal = load_yaml(GOAL_PATH)
    trades = load_trades(n=25)

    prompt = (
        f"Analyze these {len(trades)} paper trades for {goal['asset']} against goal.yaml.\\n"
        f"Goal: target_return_30d={goal['target_return_30d']*100}%, "
        f"max_drawdown={goal['max_drawdown']*100}%, min_sharpe={goal['min_sharpe']}\\n"
        f"Current strategy:\\n{yaml.dump(strategy, default_flow_style=False)}\\n"
        f"Recent trades:\\n{json.dumps(trades, indent=2)}\\n"
        "Generate 1-3 hypotheses. Each must name exactly ONE variable in strategy.yaml. "
        "Return the best hypothesis as a JSON object: "
        '{"variable": "...", "old_value": ..., "new_value": ..., '
        '"reasoning": "...", "confidence": 0.0}'
    )

    result = subprocess.run(["hermes", "--prompt", prompt],
                          capture_output=True, text=True, timeout=120)
    print(result.stdout)
    if result.stderr:
        print("HERMES STDERR:", result.stderr)

    save_history(strategy)
    ver = bump_version(strategy)
    strategy["version"] = ver

    try:
        response = result.stdout.strip()
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            hyp_json = json.loads(response[start:end])
        else:
            raise ValueError("No JSON found in Hermes output")
    except Exception as e:
        print(f"Hermes parse failed - using fallback. Error: {e}")
        fallback_reflect()
        return

    variable = hyp_json["variable"]
    parts = variable.split(".")
    if len(parts) == 2:
        strategy[parts[0]][parts[1]] = hyp_json["new_value"]
    else:
        strategy[variable] = hyp_json["new_value"]

    hypothesis_text = (
        f"{variable} {hyp_json['old_value']} -> {hyp_json['new_value']}: "
        f"{hyp_json['reasoning']} (confidence: {hyp_json['confidence']})"
    )
    save_yaml(STRATEGY_PATH, strategy)
    append_hypothesis(hypothesis_text, len(trades), ver)
    print(f"Reflection complete - strategy v{ver}")
    print(f"  {hypothesis_text}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes Reflection Cycle")
    parser.add_argument("--fallback", action="store_true", help="Use deterministic fallback")
    parser.add_argument("--hermes", action="store_true", help="Use Hermes as subprocess")
    args = parser.parse_args()

    if args.hermes:
        hermes_reflect()
    else:
        fallback_reflect()
''')

# === hermes_trading/score.py ===
write('hermes_trading/score.py', '''"""Score trades against goal.yaml - returns float in [-1, +1]."""
import math
import numpy as np


def score(trades: list, goal: dict) -> float:
    if not trades:
        return 0.0

    pnls = [t["pnl_pct"] for t in trades]
    realised_return = sum(pnls)
    target_return = goal["target_return_30d"] * 100

    rolling_peak = 0.0
    rolling_cumulative = 0.0
    max_dd = 0.0
    for p in pnls:
        rolling_cumulative += p
        rolling_peak = max(rolling_peak, rolling_cumulative)
        dd = rolling_peak - rolling_cumulative
        max_dd = max(max_dd, dd)
    max_dd_target = goal["max_drawdown"] * 100

    if len(pnls) > 1:
        excess = np.mean(pnls)
        std = np.std(pnls, ddof=1)
        sharpe = (excess / std) * math.sqrt(252) if std > 0 else 0.0
    else:
        sharpe = 0.0
    min_sharpe = goal["min_sharpe"]

    return_score = min(1.0, max(-1.0,
        realised_return / target_return if target_return else realised_return))
    dd_score = max(-1.0, 1.0 - (max_dd / max_dd_target if max_dd_target else 0))
    sharpe_score = min(1.0, max(-1.0,
        sharpe / min_sharpe if min_sharpe else sharpe))

    composite = 0.5 * return_score + 0.3 * dd_score + 0.2 * sharpe_score
    return round(max(-1.0, min(1.0, composite)), 4)
''')

# === adapters/__init__.py ===
write('hermes_trading/adapters/__init__.py', 'from hermes_trading.adapters import price, onchain, news, macro\n')

# === adapters/price.py ===
write('hermes_trading/adapters/price.py', '''"""Price adapter - pulls OHLCV + RSI from Yahoo Finance."""
import aiohttp
import numpy as np

SCHEMA_VERSION = "1.0"


class SchemaError(Exception):
    pass


def compute_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes[-period - 1:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return float(100.0 - (100.0 / (1.0 + rs)))


async def fetch(asset="XAU/USDT"):
    if "XAU" in asset:
        symbol = "GC=F"
    elif "BTC" in asset:
        symbol = "BTC-USD"
    elif "ETH" in asset:
        symbol = "ETH-USD"
    elif "SOL" in asset:
        symbol = "SOL-USD"
    else:
        symbol = asset.replace("/", "-")

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                raise RuntimeError(f"No price data for {asset}")

            quotes = result[0].get("indicators", {}).get("quote", [{}])[0]
            closes = [c for c in quotes.get("close", []) if c is not None]

            if not closes:
                raise RuntimeError(f"No close prices for {asset}")

            close = closes[-1]
            open_price = quotes.get("open", [0])[-1] or close
            high = quotes.get("high", [0])[-1] or close
            low = quotes.get("low", [0])[-1] or close
            volume = quotes.get("volume", [0])[-1] or 0

            rsi = compute_rsi(closes)

            return {
                "schema_version": SCHEMA_VERSION,
                "asset": asset,
                "open": float(open_price),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume),
                "rsi": round(rsi, 2),
            }
''')

# === adapters/onchain.py ===
write('hermes_trading/adapters/onchain.py', '''"""On-chain adapter - placeholder for Glassnode/CryptoQuant."""
SCHEMA_VERSION = "1.0"


class SchemaError(Exception):
    pass


async def fetch(asset="XAU/USDT"):
    return {
        "schema_version": SCHEMA_VERSION,
        "asset": asset,
        "active_addresses": None,
        "transaction_count": None,
        "exchange_inflow": None,
    }
''')

# === adapters/news.py ===
write('hermes_trading/adapters/news.py', '''"""News adapter - placeholder for NewsAPI / GDELT."""
SCHEMA_VERSION = "1.0"


class SchemaError(Exception):
    pass


async def fetch(asset="XAU/USDT"):
    return {
        "schema_version": SCHEMA_VERSION,
        "asset": asset,
        "sentiment": 0.0,
        "headlines": [],
    }
''')

# === adapters/macro.py ===
write('hermes_trading/adapters/macro.py', '''"""Macro adapter - placeholder for FRED / economic calendar."""
SCHEMA_VERSION = "1.0"


class SchemaError(Exception):
    pass


async def fetch(asset="XAU/USDT"):
    return {
        "schema_version": SCHEMA_VERSION,
        "asset": asset,
        "dxy": None,
        "us10y": None,
        "vix": None,
    }
''')

print("All Python files generated successfully.")

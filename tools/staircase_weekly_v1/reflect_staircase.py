"""Reflection cycle for Staircase strategy.
Tunable knobs:
  entry.adx_threshold    - raise to filter harder, lower for more entries
  exit.sl_buffer_atr     - higher = wider stop, lower = tighter stop
  exit.tp_rr             - reward:risk ratio
  exit.sl_type           - consolidation_low | sma50 | sma200
  pyramiding.min_bars_between  - spacing between entries
  pyramiding.min_profit_for_next - profit required to pyramid
  exit.partial_exits     - [L1%, L2%, L3%] 0=none, 100=full
"""
import argparse
import json
import shutil
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
    ver = strategy.get("version", "01")
    try:
        return f"{int(ver) + 1:02d}"
    except (ValueError, TypeError):
        return "02"


def save_history(strategy):
    ver = strategy.get("version", "unknown")
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(STRATEGY_PATH, HISTORY_DIR / f"v{ver}.yaml")


def append_hypothesis(hyp, trades_used, ver):
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "version": ver,
        "hypothesis": hyp,
        "trades_used": trades_used,
    }
    with open(HYPOTHESES_PATH, "a") as fh:
        fh.write(json.dumps(record) + "\n")


def compute_return(trades):
    if not trades:
        return 0.0, 0.0
    pnls = [t["pnl_pct"] for t in trades]
    return sum(pnls), sum(pnls) / len(pnls)


def compute_drawdown(trades):
    if not trades:
        return 0.0
    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0
    for t in trades:
        cumulative += t["pnl_pct"]
        peak = max(peak, cumulative)
        max_dd = max(max_dd, peak - cumulative)
    return max_dd


def compute_winrate(trades):
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t["pnl_pct"] > 0)
    return wins / len(trades)


def fallback_reflect():
    strategy = load_yaml(STRATEGY_PATH)
    goal = load_yaml(GOAL_PATH)
    trades = load_trades(n=goal.get("reflection_every", 10))

    if len(trades) < goal.get("reflection_every", 10):
        print(f"Not enough trades: {len(trades)}/{goal['reflection_every']}")
        return

    total_return, avg_return = compute_return(trades)
    dd = compute_drawdown(trades)
    winrate = compute_winrate(trades)
    target = goal["target_return_30d"] * 100
    max_dd_target = goal["max_drawdown"] * 100

    print(f"Trades: {len(trades)} | Return: {total_return:.2f}% | Win: {winrate:.1%} | DD: {dd:.2f}%")

    save_history(strategy)
    ver = bump_version(strategy)
    strategy["version"] = ver

    entry = strategy.setdefault("entry", {})
    exit_cfg = strategy.setdefault("exit", {})
    pyramiding = strategy.setdefault("pyramiding", {})

    hypothesis = None

    if total_return < target:
        if winrate < 0.35:
            old_adx = entry.get("adx_threshold", 20)
            new_adx = min(old_adx + 3, 40)
            entry["adx_threshold"] = new_adx
            hypothesis = (
                f"Return {total_return:.2f}% < {target}%, win {winrate:.1%} - "
                f"tightened adx_threshold {old_adx} -> {new_adx}"
            )
        else:
            old_rr = exit_cfg.get("tp_rr", 2.0)
            new_rr = round(old_rr + 0.5, 1)
            exit_cfg["tp_rr"] = new_rr
            hypothesis = (
                f"Return {total_return:.2f}% < {target}%, win {winrate:.1%} - "
                f"raised tp_rr {old_rr} -> {new_rr}"
            )
    elif dd > max_dd_target:
        old_buf = exit_cfg.get("sl_buffer_atr", 0.2)
        new_buf = round(old_buf - 0.05, 2)
        new_buf = max(0.05, new_buf)
        exit_cfg["sl_buffer_atr"] = new_buf
        hypothesis = (
            f"Drawdown {dd:.2f}% > {max_dd_target}% - "
            f"tightened sl_buffer_atr {old_buf} -> {new_buf}"
        )
    elif winrate > 0.5:
        old_rr = exit_cfg.get("tp_rr", 2.0)
        new_rr = round(old_rr + 0.5, 1)
        exit_cfg["tp_rr"] = new_rr
        hypothesis = (
            f"Win rate {winrate:.1%} healthy - "
            f"raised tp_rr {old_rr} -> {new_rr}"
        )
    else:
        old_adx = entry.get("adx_threshold", 20)
        new_adx = max(old_adx - 2, 10)
        entry["adx_threshold"] = new_adx
        hypothesis = (
            f"Performance within bounds - "
            f"loosened adx_threshold {old_adx} -> {new_adx}"
        )

    save_yaml(STRATEGY_PATH, strategy)
    append_hypothesis(hypothesis, len(trades), ver)
    print(f"Reflection v{ver}: {hypothesis}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Staircase Reflection Cycle")
    parser.add_argument("--fallback", action="store_true", help="Use deterministic fallback")
    args = parser.parse_args()
    fallback_reflect()

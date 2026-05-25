"""Hermes V1 Orchestrator — weekly + daily bias, LTF entries only when both agree."""
import sys, os, yaml, json, hashlib
import pandas as pd
from pathlib import Path
from hermes_v1_scanner import VaultScanner
from hermes_v1_weekly import WeeklyEngine
from hermes_v1_lower_tf import LowerTFEngine
from hermes_v1_backtester import Backtester
from hermes_v1_reporter import Reporter
from hermes_v1_indicators import compute_all_indicators, compute_staircase_signals


CACHE_DIR = Path(os.path.dirname(__file__)).parent / "research_outputs" / "cache"


def cache_key(symbol, tf):
    return hashlib.md5(f"{symbol}_{tf}".encode()).hexdigest()


def load_or_compute(symbol, tf, scanner, weekly_engine, force=False):
    """Load from cache or run staircase + return enriched df with activation_zone."""
    ck = cache_key(symbol, tf)
    path = CACHE_DIR / f"{ck}_{tf}.parquet"
    if not force and path.exists():
        return pd.read_parquet(path)

    df = scanner.load_dataframe(symbol, tf)
    df, _ = weekly_engine.run(df)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)
    return df


def daily_bullish_bias(df_d_enriched):
    """Daily is 'bullish' when EMA9 > EMA21 AND close > EMA21 AND close > SMA50.
    This is a simplified daily trend filter - not the full staircase entry signal."""
    d = df_d_enriched
    has_all = all(c in d.columns for c in ["ema_fast", "ema_slow", "close", "sma50"])
    if not has_all:
        return pd.Series(False, index=d.index)

    ema_ok = d["ema_fast"] > d["ema_slow"]
    above_ema = d["close"] > d["ema_slow"]
    above_sma50 = d["close"] > d["sma50"]
    return (ema_ok & above_ema & above_sma50).fillna(False)


def main():
    config_path = Path(__file__).parent / "config.yaml"
    print("HERMES V1")
    print("Config:", config_path)

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    scanner = VaultScanner(str(config_path))
    registry = scanner.scan()
    ready = {k: v for k, v in registry.items() if v["status"] == "ready"}
    ready = dict(list(ready.items())[:50])  # LIMIT FOR SPEED
    print(f"Stocks: {len(registry)} total, {len(ready)} processing (limited)")

    weekly_engine = WeeklyEngine(str(config_path))
    ltf_engine = LowerTFEngine(str(config_path))
    output_dir = Path(os.getcwd()).parent / "research_outputs"
    backtester = Backtester(str(config_path), str(output_dir))
    reporter = Reporter(str(output_dir))

    all_trades = []
    results_by_symbol = {}
    trades_by_entry_type = {}

    for symbol, info in ready.items():
        print(f"\n--- {symbol} ---")
        try:
            # 1. Compute weekly + daily staircase (cached)
            df_w = load_or_compute(symbol, "1wk", scanner, weekly_engine)
            activation_bars = df_w["activation_zone"].sum()

            has_daily = "1d" in info.get("timeframes", [])
            day_bias = None
            if has_daily:
                df_d = load_or_compute(symbol, "1d", scanner, weekly_engine)
                day_bias = daily_bullish_bias(df_d)
                day_bullish = day_bias.sum()
            else:
                day_bullish = 0

            print(f"  Weekly: {len(df_w)} bars | Weekly active: {activation_bars} | Daily bullish: {day_bullish}")

            symbol_results = {}
            for tf in cfg["lower_tf_entries"]["timeframes"]:
                if tf not in info["timeframes"]:
                    continue

                df_tf = scanner.load_dataframe(symbol, tf)
                # Build combined bias: weekly_active resampled + daily_bullish resampled => AND
                wa_tf = df_w["activation_zone"].reindex(df_tf.index, method="ffill").fillna(False)
                combined_bias = wa_tf.astype(bool).copy()

                if has_daily and day_bias is not None and tf != "1d":
                    db_tf = day_bias.reindex(df_tf.index, method="ffill").fillna(False)
                    combined_bias = combined_bias & db_tf.astype(bool)

                active_count = combined_bias.sum()
                if active_count == 0:
                    print(f"  {tf}: 0 active bars, skipping")
                    symbol_results[tf] = {"total_trades": 0, "win_rate": 0, "avg_r": 0, "total_return": 0,
                                          "profit_factor": 0, "max_drawdown": 0, "sharpe": 0}
                    continue

                df_tf_enriched, df_tf_signals = ltf_engine.run(df_tf, combined_bias)
                if not df_tf_signals.empty:
                    print(f"  {tf}: {active_count} active, {len(df_tf_signals)} signals")
                    trades = backtester.backtest_entry(df_tf_enriched, df_tf_signals)
                    stats = backtester.aggregate(trades)
                    symbol_results[tf] = stats
                    for t in trades:
                        t["symbol"] = symbol
                        all_trades.append(t)
                        etype = t.get("entry_type", "unknown")
                        trades_by_entry_type.setdefault(etype, []).append(t)
                    print(f"    {stats['total_trades']} trades, {stats['win_rate']:.1%} WR, {stats['avg_r']:.2f}R, {stats['total_return']:.2f}%")
                else:
                    print(f"  {tf}: {active_count} active, 0 signals")
                    symbol_results[tf] = {"total_trades": 0, "win_rate": 0, "avg_r": 0, "total_return": 0,
                                          "profit_factor": 0, "max_drawdown": 0, "sharpe": 0}

            results_by_symbol[symbol] = symbol_results
        except Exception as e:
            import traceback
            traceback.print_exc()

    if all_trades:
        backtester.save_trades(all_trades, "all_trades.csv")
    reporter.summary_report(results_by_symbol)
    reporter.entry_type_breakdown(trades_by_entry_type)
    reporter.save_all_csvs(all_trades, [])
    print(f"\nDONE — {len(all_trades)} trades across {len(ready)} stocks")


if __name__ == "__main__":
    main()

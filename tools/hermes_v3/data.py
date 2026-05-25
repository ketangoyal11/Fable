"""Hermes V3 Data Loader — multi-source OHLCV loading.

Priority: local parquet > yahoo finance (1d/1wk) > error.
For 1h/15m: local parquet only (yahoo doesn't provide reliable intraday history).
"""
import os
import pandas as pd
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


def load_parquet(vault_path, symbol, timeframe):
    """Load OHLCV from local parquet vault.

    Expected path: {vault_path}/{symbol}/{symbol}_{timeframe}.parquet
    """
    fp = Path(vault_path) / symbol / f"{symbol}_{timeframe}.parquet"
    if not fp.exists():
        return None

    df = pd.read_parquet(fp)

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime").sort_index()
    elif "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()

    required = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return None
    return df[required].copy()


def load_yahoo(symbol, period="max"):
    """Load daily data from Yahoo Finance. Returns DataFrame or None."""
    try:
        import yfinance as yf
    except ImportError:
        return None

    yf_sym = f"{symbol}.NS"
    try:
        ticker = yf.Ticker(yf_sym)
        hist = ticker.history(period=period, auto_adjust=False)
        if len(hist) == 0:
            return None
        hist = hist.reset_index()
        hist.columns = [c.lower().replace(" ", "_") for c in hist.columns]
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        hist = hist.rename(columns={hist.columns[0]: "date"})
        hist["date"] = pd.to_datetime(hist["date"]).dt.tz_localize(None)
        df = hist[["date", "open", "high", "low", "close", "volume"]].copy()
        df["volume"] = df["volume"].fillna(0)
        df = df.set_index("date").sort_index()
        return df
    except Exception:
        return None


def resample_to_timeframe(df_daily, tf):
    """Resample daily data to a target timeframe string ('1wk', '1h', '15m', etc.).

    For weekly: resample by Friday. For intraday: this is not a true resample
    from daily data, so return None for 1h/15m.
    """
    if tf == "1wk":
        return df_daily.resample("W-FRI").agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum"
        }).dropna()
    if tf == "1d":
        return df_daily
    return None


def load_data(symbol, timeframe, cfg, allow_yahoo=True):
    """Load OHLCV data for a symbol/timeframe.

    Returns DataFrame with columns [open, high, low, close, volume],
    DateTimeIndex sorted ascending, or None if unavailable.
    """
    vault = cfg["data"]["vault_path"]

    # 1. Try local parquet
    df = load_parquet(vault, symbol, timeframe)
    if df is not None and len(df) >= 50:
        return df

    # 2. For daily/weekly, try Yahoo
    if allow_yahoo and timeframe in ("1d", "1wk"):
        df_daily = load_yahoo(symbol)
        if df_daily is not None and len(df_daily) >= 50:
            if timeframe == "1d":
                return df_daily
            elif timeframe == "1wk":
                return resample_to_timeframe(df_daily, "1wk")

    # 3. For intraday, try Yahoo daily → resample only for 1d backfill
    return None


def discover_symbols(vault_path, required_timeframes=None):
    """Discover symbols that have data in the vault.

    Returns dict: {symbol: {"timeframes": [list], "status": "ready"|"incomplete"}}
    """
    vault = Path(vault_path)
    if not vault.exists():
        return {}

    if required_timeframes is None:
        required_timeframes = ["1wk", "1d"]

    registry = {}
    for d in sorted(vault.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        symbol = d.name
        files = {}
        for tf in required_timeframes:
            fp = d / f"{symbol}_{tf}.parquet"
            if fp.exists():
                files[tf] = str(fp)

        timeframes = list(files.keys())
        has_weekly = "1wk" in files
        has_daily = "1d" in files
        status = "ready" if (has_weekly and has_daily) else "incomplete"
        registry[symbol] = {
            "symbol": symbol,
            "timeframes": timeframes,
            "has_weekly": has_weekly,
            "has_daily": has_daily,
            "status": status,
        }
    return registry


def get_symbol_list(registry, status="ready", max_stocks=None):
    """Get list of symbols from registry, optionally filtered and limited."""
    filtered = [k for k, v in registry.items() if v["status"] == status]
    if max_stocks:
        filtered = filtered[:max_stocks]
    return filtered

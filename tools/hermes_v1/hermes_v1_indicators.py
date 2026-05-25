"""Hermes V1 Indicators Engine — vectorized computation for backtest performance."""
import numpy as np
import pandas as pd


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def sma(series, period):
    return series.rolling(window=period).mean()


def compute_atr(df, period=14):
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        (high - low),
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()


def compute_adx(df, period=14):
    high, low, close = df["high"], df["low"], df["close"]
    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    atr = compute_atr(df, period)
    atr_s = pd.Series(atr, index=df.index)
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(span=period, adjust=False).mean() / atr_s.replace(0, 1e-9)
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(span=period, adjust=False).mean() / atr_s.replace(0, 1e-9)
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9))
    adx = dx.ewm(span=period, adjust=False).mean()
    return adx, plus_di, minus_di


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-9)
    return 100.0 - (100.0 / (1.0 + rs))


def rolling_highest(series, period):
    return series.rolling(window=period).max()


def rolling_lowest(series, period):
    return series.rolling(window=period).min()


def compute_all_indicators(df, cfg):
    """Compute all Staircase indicators on a dataframe. Returns enriched df."""
    entry_cfg = cfg.get("staircase_weekly", {})
    ema_f = entry_cfg.get("ema_fast", 9)
    ema_s = entry_cfg.get("ema_slow", 21)
    adx_len = entry_cfg.get("adx_length", 14)
    breakout_lb = entry_cfg.get("breakout_lookback", 20)
    slope_lb = entry_cfg.get("slope_lookback", 5)

    df = df.copy()
    df["ema_fast"] = ema(df["close"], ema_f)
    df["ema_slow"] = ema(df["close"], ema_s)
    df["sma10"] = sma(df["close"], 10)
    df["sma20"] = sma(df["close"], 20)
    df["sma50"] = sma(df["close"], 50)
    df["sma100"] = sma(df["close"], 100)
    df["sma200"] = sma(df["close"], 200)
    df["atr14"] = compute_atr(df, 14)
    df["adx"], df["di_plus"], df["di_minus"] = compute_adx(df, adx_len)
    df["rsi14"] = compute_rsi(df["close"], 14)
    df["high_20"] = rolling_highest(df["high"], breakout_lb)
    df["low_5"] = rolling_lowest(df["low"], 5)
    df["volume_sma20"] = sma(df["volume"], 20)

    return df


def compute_staircase_signals(df, cfg):
    """Add boolean signal columns for the full Staircase strategy."""
    entry_cfg = cfg.get("staircase_weekly", {})
    adx_thresh = entry_cfg.get("adx_threshold", 20.0)
    slope_lb = entry_cfg.get("slope_lookback", 5)

    df = df.copy()
    df["sma50_rising"] = df["sma50"] > df["sma50"].shift(slope_lb)
    df["sma100_rising"] = df["sma100"] > df["sma100"].shift(slope_lb)
    df["sma200_rising"] = df["sma200"] > df["sma200"].shift(slope_lb)

    df["st_stacked"] = (df["sma10"] > df["sma20"]) & (df["sma20"] > df["sma50"])
    df["price_above_st"] = (df["close"] > df["sma10"]) & (df["close"] > df["sma20"]) & (df["close"] > df["sma50"])
    df["st_trend_ok"] = df["st_stacked"] & df["price_above_st"]

    df["lt_stacked"] = (df["sma50"] > df["sma100"]) & (df["sma100"] > df["sma200"])
    df["smas_rising"] = df["sma50_rising"] & df["sma100_rising"]
    df["price_above_lt"] = (df["close"] > df["sma50"]) & (df["close"] > df["sma100"]) & (df["close"] > df["sma200"])
    df["major_trend_ok"] = (df["lt_stacked"] & df["smas_rising"] & df["price_above_lt"]) | df["st_trend_ok"]

    df["ema_uptrend"] = df["ema_fast"] > df["ema_slow"]
    df["price_above_ema"] = df["close"] > df["ema_slow"]
    df["green_bar"] = df["close"] > df["open"]
    df["adx_ok"] = df["adx"] >= adx_thresh

    df["prev_high_20"] = df["high_20"].shift(1)
    df["breakout"] = (df["close"] > df["prev_high_20"]) & df["green_bar"]

    df["entry_signal"] = (
        df["major_trend_ok"] & df["ema_uptrend"] & df["price_above_ema"] &
        df["breakout"] & df["adx_ok"]
    )

    df["ema_crossunder"] = (df["ema_fast"].shift(1) >= df["ema_slow"].shift(1)) & (df["ema_fast"] < df["ema_slow"])
    df["sma_crossunder"] = (df["sma50"].shift(1) >= df["sma100"].shift(1)) & (df["sma50"] < df["sma100"])

    return df

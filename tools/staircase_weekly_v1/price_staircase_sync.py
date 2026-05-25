"""Price adapter - synchronous OHLCV fetcher with Staircase indicators."""
import json
import random
import time
import urllib.request
import numpy as np

SCHEMA_VERSION = "2.0"


def _ema(data, period):
    if len(data) < period or period <= 0:
        return [float(data[-1])] * len(data) if data else []
    result = [float(data[0])]
    k = 2.0 / (period + 1)
    for i in range(1, len(data)):
        result.append(float(data[i]) * k + result[-1] * (1 - k))
    return result


def _sma(data, period):
    if len(data) < period or period <= 0:
        return [float(0)] * len(data) if data else []
    result = []
    for i in range(len(data)):
        if i < period - 1:
            result.append(float(sum(data[:i + 1]) / (i + 1)))
        else:
            result.append(float(sum(data[i - period + 1:i + 1]) / period))
    return result


def _compute_rsi(closes, period=14):
    if len(closes) < period + 1:
        return [50.0] * len(closes) if closes else []
    result = [50.0] * period
    deltas = np.diff(closes)
    for i in range(period, len(closes)):
        s = deltas[i - period:i]
        avg_g = float(np.mean(np.where(s > 0, s, 0)))
        avg_l = float(np.mean(np.where(s < 0, -s, 0)))
        if avg_l == 0:
            result.append(100.0)
        else:
            result.append(float(100.0 - (100.0 / (1.0 + avg_g / avg_l))))
    return result


def _compute_atr(highs, lows, closes, period=14):
    n = len(closes)
    if n < 2:
        return [0.0] * n
    tr = []
    for i in range(1, n):
        tr.append(max(highs[i] - lows[i],
                      abs(highs[i] - closes[i - 1]),
                      abs(lows[i] - closes[i - 1])))
    if not tr:
        return [0.0] * n
    if len(tr) < period:
        atr = [float(np.mean(tr))]
    else:
        atr = [float(np.mean(tr[:period]))]
        for i in range(period, len(tr)):
            atr.append((atr[-1] * (period - 1) + tr[i]) / period)
    pad = n - len(atr)
    return [atr[0]] * pad + atr


def _compute_adx(highs, lows, closes, period=14):
    n = len(closes)
    if n < period + 1:
        return ([20.0] * n, [20.0] * n, [20.0] * n)
    tr, pdm, ndm = [], [], []
    for i in range(1, n):
        tr.append(max(highs[i] - lows[i],
                      abs(highs[i] - closes[i - 1]),
                      abs(lows[i] - closes[i - 1])))
        up = highs[i] - highs[i - 1]
        dn = lows[i - 1] - lows[i]
        pdm.append(up if (up > dn and up > 0) else 0.0)
        ndm.append(dn if (dn > up and dn > 0) else 0.0)
    if len(tr) < period:
        return ([20.0] * n, [20.0] * n, [20.0] * n)

    atr_arr = [float(np.mean(tr[:period]))]
    pdm_ema = [float(np.mean(pdm[:period]))]
    ndm_ema = [float(np.mean(ndm[:period]))]
    for i in range(period, len(tr)):
        atr_arr.append((atr_arr[-1] * (period - 1) + tr[i]) / period)
        pdm_ema.append((pdm_ema[-1] * (period - 1) + pdm[i]) / period)
        ndm_ema.append((ndm_ema[-1] * (period - 1) + ndm[i]) / period)

    di_p, di_m, dx_vals = [], [], []
    for i in range(len(atr_arr)):
        a = atr_arr[i] if atr_arr[i] != 0 else 1e-9
        dp = (pdm_ema[i] / a) * 100
        dm = (ndm_ema[i] / a) * 100
        di_p.append(dp)
        di_m.append(dm)
        s = dp + dm
        dx_vals.append(abs(dp - dm) / s * 100 if s > 0 else 0.0)

    if len(dx_vals) >= period:
        adx_res = [float(np.mean(dx_vals[:period]))] * (period - 1)
        for i in range(period - 1, len(dx_vals)):
            adx_res.append((adx_res[-1] * (period - 1) + dx_vals[i]) / period)
    else:
        adx_res = [float(np.mean(dx_vals))] * len(dx_vals)

    pad_di = n - len(di_p)
    pad_adx = n - len(adx_res)
    return (pad_di * [20.0] + di_p, pad_di * [20.0] + di_m, pad_adx * [20.0] + adx_res)


def _highest(data, period, n):
    result = []
    for i in range(n):
        lo = max(0, i - period + 1)
        result.append(float(max(data[lo:i + 1])))
    return result


def _lowest(data, period, n):
    result = []
    for i in range(n):
        lo = max(0, i - period + 1)
        result.append(float(min(data[lo:i + 1])))
    return result


def fetch(asset="XAU/USDT", strategy=None):
    if strategy is None:
        strategy = {}

    entry_cfg = strategy.get("entry", {})
    exit_cfg = strategy.get("exit", {})

    ema_fast_len = entry_cfg.get("ema_fast", 9)
    ema_slow_len = entry_cfg.get("ema_slow", 21)
    adx_len = entry_cfg.get("adx_length", 14)
    adx_thresh = entry_cfg.get("adx_threshold", 20.0)
    breakout_lb = entry_cfg.get("breakout_lookback", 20)
    slope_lb = entry_cfg.get("slope_lookback", 5)
    sl_type = exit_cfg.get("sl_type", "consolidation_low")
    sl_buffer = exit_cfg.get("sl_buffer_atr", 0.2)

    if "XAU" in asset:
        symbol = "GC=F"
    else:
        symbol = asset.replace("/", "-")

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=2d"
    headers = {"User-Agent": "Mozilla/5.0"}

    data = None
    for attempt in range(3):
        time.sleep(random.uniform(1, 2) * (attempt + 1))
        try:
            req = urllib.request.Request(url, headers=headers)
            raw = urllib.request.urlopen(req, timeout=15)
            data = json.loads(raw.read())
            break
        except Exception:
            continue

    if data is None:
        raise RuntimeError(f"Yahoo Finance unavailable after 3 retries for {asset}")

    result = data.get("chart", {}).get("result", [])
    if not result:
        raise RuntimeError(f"No price data for {asset}")

    quotes = result[0].get("indicators", {}).get("quote", [{}])[0]
    opens = [o for o in quotes.get("open", []) if o is not None]
    highs = [h for h in quotes.get("high", []) if h is not None]
    lows = [l for l in quotes.get("low", []) if l is not None]
    closes = [c for c in quotes.get("close", []) if c is not None]
    volumes = [v if v is not None else 0 for v in quotes.get("volume", [])]

    mn = min(len(opens), len(highs), len(lows), len(closes))
    opens = opens[-mn:]
    highs = highs[-mn:]
    lows = lows[-mn:]
    closes = closes[-mn:]
    volumes = volumes[-mn:] if volumes else [0] * mn

    if len(closes) < 200:
        raise RuntimeError(f"Insufficient data: {len(closes)} bars")

    n = len(closes)

    ema_fast = _ema(closes, ema_fast_len)
    ema_slow = _ema(closes, ema_slow_len)
    sma10 = _sma(closes, 10)
    sma20 = _sma(closes, 20)
    sma50 = _sma(closes, 50)
    sma100 = _sma(closes, 100)
    sma200 = _sma(closes, 200)
    rsi_arr = _compute_rsi(closes, 14)
    atr_arr = _compute_atr(highs, lows, closes, 14)
    di_p_arr, di_m_arr, adx_arr = _compute_adx(highs, lows, closes, adx_len)

    h20 = _highest(highs, breakout_lb, n)
    l5 = _lowest(lows, 5, n)

    i = n - 1
    si = max(0, i - slope_lb)

    sma50_rising = sma50[i] > sma50[si]
    sma100_rising = sma100[i] > sma100[si]
    sma200_rising = sma200[i] > sma200[si]

    st_stacked = sma10[i] > sma20[i] > sma50[i]
    price_above_st = closes[i] > sma10[i] and closes[i] > sma20[i] and closes[i] > sma50[i]
    st_trend_ok = st_stacked and price_above_st

    lt_stacked = sma50[i] > sma100[i] > sma200[i]
    smas_rising = sma50_rising and sma100_rising
    price_above_lt = closes[i] > sma50[i] and closes[i] > sma100[i] and closes[i] > sma200[i]
    major_trend_ok = (lt_stacked and smas_rising and price_above_lt) or st_trend_ok

    ema_up = ema_fast[i] > ema_slow[i]
    price_above_ema = closes[i] > ema_slow[i]
    green_bar = closes[i] > opens[i]

    prev_h = h20[i - 1] if i > 0 else h20[i]
    breakout = closes[i] > prev_h and green_bar
    adx_ok = adx_arr[i] >= adx_thresh
    entry_signal = major_trend_ok and ema_up and price_above_ema and breakout and adx_ok

    ema_xu = ema_fast[i - 1] >= ema_slow[i - 1] and ema_fast[i] < ema_slow[i] if i > 0 else False
    sma_xu = sma50[i - 1] >= sma100[i - 1] and sma50[i] < sma100[i] if i > 0 else False

    atr = atr_arr[i]
    if sl_type == "sma50":
        dyn_sl = sma50[i] - atr * sl_buffer
    elif sl_type == "sma200":
        dyn_sl = sma200[i] - atr * sl_buffer
    else:
        dyn_sl = l5[i] - atr * sl_buffer

    return {
        "schema_version": SCHEMA_VERSION,
        "asset": asset,
        "open": float(opens[i]) if opens[i] is not None else float(closes[i]),
        "high": float(highs[i]) if highs[i] is not None else float(closes[i]),
        "low": float(lows[i]) if lows[i] is not None else float(closes[i]),
        "close": float(closes[i]),
        "volume": float(volumes[i]) if i < len(volumes) and volumes[i] is not None else 0.0,
        "rsi": round(float(rsi_arr[i]), 2),
        "adx": round(float(adx_arr[i]), 2),
        "di_plus": round(float(di_p_arr[i]), 2),
        "di_minus": round(float(di_m_arr[i]), 2),
        "atr": round(atr, 2),
        "ema_fast": round(float(ema_fast[i]), 2),
        "ema_slow": round(float(ema_slow[i]), 2),
        "sma10": round(float(sma10[i]), 2),
        "sma20": round(float(sma20[i]), 2),
        "sma50": round(float(sma50[i]), 2),
        "sma100": round(float(sma100[i]), 2),
        "sma200": round(float(sma200[i]), 2),
        "sma50_rising": sma50_rising,
        "sma100_rising": sma100_rising,
        "sma200_rising": sma200_rising,
        "short_term_trend_ok": st_trend_ok,
        "long_term_stacked": lt_stacked,
        "smas_rising": smas_rising,
        "price_above_long_smas": price_above_lt,
        "major_trend_ok": major_trend_ok,
        "ema_uptrend": ema_up,
        "price_above_ema": price_above_ema,
        "green_bar": green_bar,
        "breakout_high": round(float(prev_h), 2),
        "breakout": breakout,
        "adx_ok": adx_ok,
        "entry_signal": entry_signal,
        "ema_crossunder": ema_xu,
        "sma_crossunder": sma_xu,
        "dynamic_sl": round(dyn_sl, 2),
        "trail_sma20": round(float(sma20[i] - atr * sl_buffer), 2),
        "trail_sma50": round(float(sma50[i] - atr * sl_buffer), 2),
    }

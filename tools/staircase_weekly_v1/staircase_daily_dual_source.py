#!/usr/bin/env python3
"""
Staircase Strategy Daily Dual-Source Scanner
=============================================
Runs the full staircase L1/L2/L3 entry simulation on DAILY bars
using BOTH Dhan API and Yahoo Finance data for the same symbols.
Compares: entries found, entry dates, prices, and divergences.
"""
from __future__ import annotations

import io
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests
import yfinance as yf

IST = timezone(timedelta(hours=5, minutes=30))

# ═════════════════════════════════════════════════════════════════════════════
# SETTINGS (matches scan_staircase_dhan.py + Pine script)
# ═════════════════════════════════════════════════════════════════════════════

EMA1_LEN, EMA2_LEN = 9, 21
SMA10_LEN, SMA20_LEN = 10, 20
SMA50_LEN, SMA100_LEN, SMA200_LEN = 50, 100, 200
SLOPE_LEN = 5
ATR_LEN = 14
SL_BUFFER = 0.2
RISK_REWARD_L1 = 2.0
RISK_REWARD_L2 = 2.0
RISK_REWARD_L3 = 2.0
MIN_PROFIT_FOR_NEXT = 0.0
MIN_BARS_BETWEEN = 3
USE_STRONG_CANDLE = False
USE_VOLUME_FILTER = False
TF_DARVAS_UPPER_LEN = 15
TF_DARVAS_LOWER_LEN = 15
TF_VALID_DAYS = 2.0
TF_USE_DARVAS = True
TF_USE_SHORT = True
TF_USE_LONG = True
GLOBAL_DARVAS_ON = True
GLOBAL_DARVAS_LEN = 40
DATA_YEARS = 4
WEEKS_LOOKBACK = 4

# Nifty 50 symbols for quick test
UNIVERSE = "nifty50"
NIFTY_50_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv"
SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
DHAN_BASE = "https://api.dhan.co"

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "analysis" / "staircase_daily_dual"


# ═════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═════════════════════════════════════════════════════════════════════════════

def dhan_headers() -> dict:
    token = os.getenv("DHAN_ACCESS_TOKEN", "").strip()
    client = os.getenv("DHAN_CLIENT_ID", "").strip()
    if not token or not client:
        raise RuntimeError("Set DHAN_ACCESS_TOKEN and DHAN_CLIENT_ID env vars")
    return {"access-token": token, "client-id": client, "Content-Type": "application/json"}


def load_nifty50_symbols() -> list[str]:
    resp = requests.get(NIFTY_50_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    return sorted(df["Symbol"].astype(str).str.strip().str.upper().tolist())

def load_watchlist_symbols(csv_path: str) -> list[str]:
    """Load symbols from AP watchlist CSV."""
    df = pd.read_csv(csv_path)
    col = "symbol" if "symbol" in df.columns else df.columns[0]
    symbols = df[col].astype(str).str.strip().str.upper().tolist()
    return [s for s in symbols if s and s != "SYMBOL"]


def load_security_map() -> dict[str, str]:
    resp = requests.get(SCRIP_MASTER_URL, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    master = pd.read_csv(io.StringIO(resp.text), low_memory=False)
    out = {}
    for _, row in master.iterrows():
        if str(row.get("SEM_EXM_EXCH_ID", "")).strip().upper() == "NSE" \
           and str(row.get("SEM_SEGMENT", "")).strip().upper() == "E" \
           and str(row.get("SEM_SERIES", "")).strip().upper() == "EQ":
            sym = str(row["SEM_TRADING_SYMBOL"]).strip().upper()
            sid = str(row["SEM_SMST_SECURITY_ID"]).strip()
            if sym and sid:
                out.setdefault(sym, sid)
    return out


def fetch_dhan_daily(security_id: str, from_date: str, to_date: str) -> pd.DataFrame | None:
    payload = {
        "securityId": security_id,
        "exchangeSegment": "NSE_EQ",
        "instrument": "EQUITY",
        "expiryCode": 0,
        "oi": False,
        "fromDate": from_date,
        "toDate": to_date,
    }
    try:
        r = requests.post(f"{DHAN_BASE}/v2/charts/historical", json=payload,
                          headers=dhan_headers(), timeout=30)
        if r.status_code >= 400:
            return None
        data = r.json()
        ts = data.get("timestamp") or []
        if not ts:
            return None
        rows = []
        for i in range(min(len(ts), len(data.get("open", [])), len(data.get("close", [])))):
            rows.append({
                "date": pd.Timestamp(datetime.fromtimestamp(int(ts[i]), tz=IST)),
                "open": float(data["open"][i]),
                "high": float(data["high"][i]),
                "low": float(data["low"][i]),
                "close": float(data["close"][i]),
                "volume": float(data["volume"][i]) if i < len(data.get("volume", [])) else 0.0,
            })
        df = pd.DataFrame(rows)
        if df.empty:
            return None
        df = df.drop_duplicates("date").set_index("date").sort_index()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception:
        return None


def fetch_yahoo_daily(symbol: str, years: int = 4) -> pd.DataFrame | None:
    yf_sym = f"{symbol}.NS"
    try:
        ticker = yf.Ticker(yf_sym)
        hist = ticker.history(period=f"{years}y", auto_adjust=False)
        if len(hist) < 100:
            return None
        df = hist.reset_index()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        col_map = {c: c.lower().replace(" ", "_") for c in df.columns}
        df = df.rename(columns=col_map)
        date_col = "date" if "date" in df.columns else df.columns[0]
        if date_col != "date":
            df = df.rename(columns={date_col: "date"})
        df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_convert("Asia/Kolkata").dt.tz_localize(None)
        required = ["date", "open", "high", "low", "close", "volume"]
        df = df[[c for c in required if c in df.columns]].copy()
        df["volume"] = df["volume"].fillna(0)
        return df.set_index("date").sort_index()
    except Exception as e:
        return None


# ═════════════════════════════════════════════════════════════════════════════
# INDICATORS
# ═════════════════════════════════════════════════════════════════════════════

def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=window).mean()


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - prev).abs(),
                    (df["low"] - prev).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    f = df.copy()
    if f.index.tz is not None:
        f.index = f.index.tz_localize(None)
    c = f["close"]
    f["ema9"] = ema(c, EMA1_LEN)
    f["ema21"] = ema(c, EMA2_LEN)
    f["ema10"] = ema(c, 10)
    f["ema20"] = ema(c, 20)
    f["ema50"] = ema(c, 50)
    f["ema100"] = ema(c, 100)
    f["ema200"] = ema(c, 200)
    f["sma50"] = sma(c, 50)
    f["sma100"] = sma(c, 100)
    f["atr"] = calc_atr(f, ATR_LEN)

    # Volume
    f["vol10"] = sma(f["volume"], 10)
    f["vol20"] = sma(f["volume"], 20)
    f["vol30"] = sma(f["volume"], 30)
    f["volume_ok"] = (f["volume"] > f["vol10"]) | (f["volume"] > f["vol20"]) | (f["volume"] > f["vol30"])

    # Strong candle
    cr = f["high"] - f["low"]
    f["strong_candle"] = (
        (f["close"] > f["open"])
        & ((f["close"] - f["open"]).abs() / cr.replace(0, np.nan) * 100 >= 60.0)
        & ((f["high"] - f["close"]) / cr.replace(0, np.nan) * 100 <= 20.0)
    )

    # Darvas box on body
    body_top = f[["open", "close"]].max(axis=1)
    body_bot = f[["open", "close"]].min(axis=1)
    f["darvas_top"] = body_top.rolling(GLOBAL_DARVAS_LEN, min_periods=GLOBAL_DARVAS_LEN).max().shift(1)
    f["darvas_bot"] = body_bot.rolling(GLOBAL_DARVAS_LEN, min_periods=GLOBAL_DARVAS_LEN).min().shift(1)
    f["darvas_ok"] = f["close"] > f["darvas_top"]

    # Base entry conditions
    f["base_ema_ok"] = (f["ema9"] > f["ema21"]) & (f["close"] > f["ema21"])
    f["base_volume_ok"] = ~pd.Series(USE_VOLUME_FILTER, index=f.index) | f["volume_ok"]
    f["base_strong_ok"] = ~pd.Series(USE_STRONG_CANDLE, index=f.index) | f["strong_candle"]
    f["base_ok"] = f["base_ema_ok"] & f["base_volume_ok"] & f["base_strong_ok"]

    # Global Darvas
    f["global_darvas_ok"] = ~pd.Series(GLOBAL_DARVAS_ON, index=f.index) | f["darvas_ok"]

    # TF gate (same as chart — daily on daily)
    f["tf_short"] = (f["ema10"] > f["ema20"]) & (f["ema20"] > f["ema50"]) & (c > f["ema10"]) & (c > f["ema20"]) & (c > f["ema50"])
    f["tf_long"] = ((f["ema50"] > f["ema100"]) & (f["ema100"] > f["ema200"])
                    & (f["ema50"] > f["ema50"].shift(SLOPE_LEN))
                    & (f["ema100"] > f["ema100"].shift(SLOPE_LEN))
                    & (c > f["ema50"]) & (c > f["ema100"]) & (c > f["ema200"]))
    f["tf_ema_ok"] = (f["ema9"] > f["ema21"]) & (c > f["ema21"])

    # TF Darvas (smaller box)
    tf_body_top = f[["open", "close"]].max(axis=1)
    tf_body_bot = f[["open", "close"]].min(axis=1)
    f["tf_darvas_top"] = tf_body_top.rolling(TF_DARVAS_UPPER_LEN, min_periods=TF_DARVAS_UPPER_LEN).max().shift(1)
    f["tf_darvas_bot"] = tf_body_bot.rolling(TF_DARVAS_LOWER_LEN, min_periods=TF_DARVAS_LOWER_LEN).min().shift(1)
    f["tf_darvas_ok"] = f["close"] > f["tf_darvas_top"]

    # Build TF signal with valid-days window
    f["tf_raw_signal"] = (
        (~pd.Series(TF_USE_SHORT, index=f.index) | f["tf_short"])
        & (~pd.Series(TF_USE_LONG, index=f.index) | f["tf_long"])
        & f["tf_ema_ok"]
        & f["base_volume_ok"]
        & (~pd.Series(not TF_USE_DARVAS, index=f.index) | f["tf_darvas_ok"])
    )

    signal_times = pd.Series(pd.NaT, index=f.index, dtype="datetime64[ns]")
    signal_times.loc[f["tf_raw_signal"]] = signal_times.loc[f["tf_raw_signal"]].index
    f["last_signal"] = signal_times.ffill()
    f["signal_age_days"] = (f.index.to_series() - f["last_signal"]).dt.total_seconds() / 86400.0
    f["tf_required_ok"] = f["signal_age_days"].notna() & (f["signal_age_days"] <= TF_VALID_DAYS) & (c >= f["ema100"])
    f["tf_entry_darvas_ok"] = f["tf_darvas_ok"] & (c > f["tf_darvas_top"])

    timeframe_ok = f["tf_required_ok"] & f["tf_entry_darvas_ok"]

    f["entry_signal"] = f["base_ok"] & timeframe_ok & f["global_darvas_ok"]

    # Crossunders for exit
    f["ema_crossunder"] = (f["ema9"].shift(1) > f["ema21"].shift(1)) & (f["ema9"] < f["ema21"])
    f["sma_crossunder"] = (f["sma50"].shift(1) > f["sma100"].shift(1)) & (f["sma50"] < f["sma100"])

    return f


# ═════════════════════════════════════════════════════════════════════════════
# SIMULATOR — L1/L2/L3 on daily bars
# ═════════════════════════════════════════════════════════════════════════════

def simulate(symbol: str, df: pd.DataFrame, source: str, since_date: pd.Timestamp) -> list[dict]:
    d = add_indicators(df)
    entries = []
    pos_count = 0
    last_entry_bar = -10_000
    ep = {1: np.nan, 2: np.nan, 3: np.nan}
    sl = {1: np.nan, 2: np.nan, 3: np.nan}
    tp = {1: np.nan, 2: np.nan, 3: np.nan}
    eb = {1: -1, 2: -1, 3: -1}
    pt = {1: False, 2: False, 3: False}

    rows = list(d.iterrows())
    for i, (ts, row) in enumerate(rows):
        close = row["close"]

        def pnl(level):
            return (close - ep[level]) / ep[level] * 100 if not np.isnan(ep[level]) else -999

        # Composite SL
        composite_sl = np.nan
        if pos_count >= 3 and not np.isnan(sl[3]):
            composite_sl = sl[3]
        elif pos_count >= 2 and not np.isnan(sl[2]):
            composite_sl = sl[2]
        elif pos_count >= 1 and not np.isnan(sl[1]):
            composite_sl = sl[1]

        # Trend break / SL exit
        if pos_count > 0:
            for lvl in (1, 2, 3):
                if not pt[lvl] and not np.isnan(tp[lvl]) and close >= tp[lvl]:
                    pt[lvl] = True
            ema_break = i > 0 and rows[i-1][1]["ema9"] >= rows[i-1][1]["ema21"] and row["ema9"] < row["ema21"]
            sma_break = i > 0 and rows[i-1][1]["sma50"] >= rows[i-1][1]["sma100"] and row["sma50"] < row["sma100"]
            if (not np.isnan(composite_sl) and close < composite_sl) or ema_break or sma_break:
                pos_count = 0
                ep = {1: np.nan, 2: np.nan, 3: np.nan}
                sl = {1: np.nan, 2: np.nan, 3: np.nan}
                tp = {1: np.nan, 2: np.nan, 3: np.nan}
                eb = {1: -1, 2: -1, 3: -1}
                pt = {1: False, 2: False, 3: False}
                continue

        can_enter_new = (i - last_entry_bar) >= MIN_BARS_BETWEEN
        if not row["entry_signal"] or not can_enter_new:
            continue

        current_sl_level = d["low"].iloc[max(0, i-4):i+1].min() - row["atr"] * SL_BUFFER
        if not np.isfinite(current_sl_level):
            continue

        # Determine level
        if pos_count == 0:
            level = 1
        elif pos_count == 1 and i > eb[1] and pnl(1) >= MIN_PROFIT_FOR_NEXT:
            level = 2
        elif pos_count == 2 and i > eb[2] and pnl(2) >= MIN_PROFIT_FOR_NEXT:
            level = 3
        else:
            continue

        rr = [0, RISK_REWARD_L1, RISK_REWARD_L2, RISK_REWARD_L3][level]
        ep[level] = float(close)
        sl[level] = float(current_sl_level)
        eb[level] = i
        tp[level] = ep[level] + (ep[level] - sl[level]) * rr
        pt[level] = False
        if level == 2:
            sl[1] = float(current_sl_level)
        elif level == 3:
            sl[1] = float(current_sl_level)
            sl[2] = float(current_sl_level)
        pos_count = level
        last_entry_bar = i

        if ts >= since_date:
            entries.append({
                "symbol": symbol,
                "source": source,
                "entry_date": ts.strftime("%Y-%m-%d"),
                "level": f"L{level}",
                "close": round(float(close), 2),
                "sl": round(float(sl[level]), 2),
                "tp": round(float(tp[level]), 2),
            })

    return entries


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Max symbols to scan")
    parser.add_argument("--weeks", type=int, default=WEEKS_LOOKBACK, help="Weeks lookback for entries")
    parser.add_argument("--yahoo-only", action="store_true", help="Skip Dhan, run Yahoo only")
    parser.add_argument("--watchlist", type=str, default="", help="Path to watchlist CSV (full NSE scan)")
    parser.add_argument("--universe", type=str, default="nifty50", help="nifty50 or watchlist")
    args = parser.parse_args()

    print("=" * 70)
    print("STAIRCASE DAILY DUAL-SOURCE (Dhan vs Yahoo)")
    source_label = "Yahoo only" if args.yahoo_only else "Dhan + Yahoo"
    print(f"Universe: {args.universe}  |  Lookback: {args.weeks} weeks  |  Source: {source_label}")
    print("=" * 70)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    to_date = datetime.now(IST).strftime("%Y-%m-%d")
    from_date = (datetime.now(IST) - timedelta(days=DATA_YEARS * 365)).strftime("%Y-%m-%d")
    since = pd.Timestamp((datetime.now(IST) - timedelta(weeks=args.weeks)).date())

    if args.watchlist or args.universe == "watchlist":
        wl_path = args.watchlist or r"AP\analysis\nse_90d_scan_runs\yahoo_fresh_20260523\ap_nse_watchlist.csv"
        symbols = load_watchlist_symbols(wl_path)
    else:
        symbols = load_nifty50_symbols()
    if args.limit:
        symbols = symbols[:args.limit]
    security_map = {}
    if not args.yahoo_only:
        print(f"Starting security master download...")
        security_map = load_security_map()
    print(f"Symbols to scan: {len(symbols)} (source: {'Yahoo only' if args.yahoo_only else 'Dhan + Yahoo'})")

    all_entries: list[dict] = []
    errors_dhan = 0
    errors_yahoo = 0
    sleep = 0.3

    for idx, symbol in enumerate(symbols, start=1):
        # Dhan
        dhan_entries = []
        if not args.yahoo_only:
            sec = security_map.get(symbol)
            if sec:
                try:
                    dhan_df = fetch_dhan_daily(sec, from_date, to_date)
                    time.sleep(sleep)
                    if dhan_df is not None and len(dhan_df) >= 100:
                        dhan_entries = simulate(symbol, dhan_df, "Dhan", since)
                except Exception as e:
                    errors_dhan += 1
                    print(f"[{idx:02d}] {symbol}: Dhan ERROR ({e})")

        # Yahoo
        yahoo_entries = []
        try:
            yahoo_df = fetch_yahoo_daily(symbol, DATA_YEARS)
            if yahoo_df is not None and len(yahoo_df) >= 100:
                yahoo_entries = simulate(symbol, yahoo_df, "Yahoo", since)
        except Exception as e:
            errors_yahoo += 1
            print(f"[{idx:02d}] {symbol}: Yahoo ERROR ({e})")

        total = len(dhan_entries) + len(yahoo_entries)
        if total > 0:
            print(f"[{idx:02d}] {symbol:15s} Dhan={len(dhan_entries):>2d}  Yahoo={len(yahoo_entries):>2d}")
        all_entries.extend(dhan_entries)
        all_entries.extend(yahoo_entries)

    print(f"\n{'='*70}")
    print(f"TOTAL ENTRIES: {len(all_entries)} (Dhan errors: {errors_dhan}, Yahoo errors: {errors_yahoo})")
    print(f"{'='*70}")

    if not all_entries:
        print("No entries found.")
        return

    df_e = pd.DataFrame(all_entries)

    # ── Side-by-side comparison ──────────────────────────────────────────
    dhan = df_e[df_e["source"] == "Dhan"].set_index(["symbol", "entry_date", "level"])
    yahoo = df_e[df_e["source"] == "Yahoo"].set_index(["symbol", "entry_date", "level"])

    dhan_keys = set(dhan.index)
    yahoo_keys = set(yahoo.index)
    common = dhan_keys & yahoo_keys
    only_dhan = dhan_keys - yahoo_keys
    only_yahoo = yahoo_keys - dhan_keys

    print(f"\nEntries found by BOTH sources: {len(common)}")
    print(f"Entries ONLY in Dhan:         {len(only_dhan)}")
    print(f"Entries ONLY in Yahoo:        {len(only_yahoo)}")

    # ── Price comparison on common entries ──────────────────────────────
    if common:
        dhan_common = dhan.loc[list(common)][["close", "sl", "tp"]]
        yahoo_common = yahoo.loc[list(common)][["close", "sl", "tp"]]
        diff = (dhan_common - yahoo_common).abs()
        print(f"\nPrice differences on {len(common)} common entries:")
        print(f"  Close: mean={diff['close'].mean():.2f}  max={diff['close'].max():.2f}")
        print(f"  SL:    mean={diff['sl'].mean():.2f}  max={diff['sl'].max():.2f}")
        print(f"  TP:    mean={diff['tp'].mean():.2f}  max={diff['tp'].max():.2f}")

    # ── Only-Dhan entries detail ─────────────────────────────────────────
    if only_dhan:
        print(f"\n-- Entries ONLY in Dhan ({len(only_dhan)}) --")
        od = dhan.loc[list(only_dhan)].reset_index()
        print(od.to_string(index=False))

    # ── Only-Yahoo entries detail ────────────────────────────────────────
    if only_yahoo:
        print(f"\n-- Entries ONLY in Yahoo ({len(only_yahoo)}) --")
        oy = yahoo.loc[list(only_yahoo)].reset_index()
        print(oy.to_string(index=False))

    # ── Save outputs ─────────────────────────────────────────────────────
    stamp = datetime.now(IST).strftime("%Y%m%d_%H%M")
    csv_path = OUT_DIR / f"staircase_daily_dual_{stamp}.csv"
    df_e.to_csv(csv_path, index=False)
    print(f"\nFull CSV: {csv_path}")

    # Summary JSON for programmatic comparison
    summary = {
        "timestamp": datetime.now(IST).isoformat(),
        "universe": UNIVERSE,
        "total_entries": len(all_entries),
        "dhan_entries": len(dhan),
        "yahoo_entries": len(yahoo),
        "common": len(common),
        "only_dhan": len(only_dhan),
        "only_yahoo": len(only_yahoo),
        "dhan_errors": errors_dhan,
        "yahoo_errors": errors_yahoo,
        "only_dhan_entries": [{"symbol": s, "date": d, "level": l}
                              for s, d, l in only_dhan],
        "only_yahoo_entries": [{"symbol": s, "date": d, "level": l}
                               for s, d, l in only_yahoo],
    }
    json_path = OUT_DIR / f"staircase_daily_dual_{stamp}.json"
    json_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"Summary JSON: {json_path}")


if __name__ == "__main__":
    main()

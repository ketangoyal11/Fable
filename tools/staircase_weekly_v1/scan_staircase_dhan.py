from __future__ import annotations

import argparse
import csv
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


IST = timezone(timedelta(hours=5, minutes=30))
DHAN_BASE = "https://api.dhan.co"
SCRIP_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
NIFTY_50_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv"
INDEX_URLS = {
    "nifty50": NIFTY_50_URL,
    "midsmallcap400": "https://nsearchives.nseindia.com/content/indices/ind_niftymidsmallcap400list.csv",
    "smallcap250": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
    "microcap250": "https://nsearchives.nseindia.com/content/indices/ind_niftymicrocap250_list.csv",
}


@dataclass(frozen=True)
class Settings:
    ema1_len: int = 9
    ema2_len: int = 21
    sma10_len: int = 10
    sma20_len: int = 20
    sma50_len: int = 50
    sma100_len: int = 100
    sma200_len: int = 200
    slope_len: int = 5
    sl_buffer: float = 0.2
    risk_reward_l1: float = 2.0
    risk_reward_l2: float = 2.0
    risk_reward_l3: float = 2.0
    min_profit_for_next_entry: float = 0.0
    min_bars_between_entries: int = 3
    use_strong_entry_candle: bool = True
    use_volume_filter: bool = False
    min_entry_body_range_pct: float = 60.0
    max_entry_close_from_high_pct: float = 20.0
    tf_valid_days: float = 2.0
    tf_darvas_upper_len: int = 15
    tf_darvas_lower_len: int = 15
    tf_use_darvas: bool = True
    tf_use_short_trend: bool = True
    tf_use_long_trend: bool = True
    global_darvas1_on: bool = False
    global_darvas1_len: int = 20


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def headers() -> dict[str, str]:
    return {
        "access-token": require_env("DHAN_ACCESS_TOKEN"),
        "client-id": require_env("DHAN_CLIENT_ID"),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def get_text(url: str, *, retries: int = 3) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=45, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            return response.text
        except Exception as exc:
            last_error = exc
            time.sleep(1.0 + attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_index_symbols(universe: str) -> list[str]:
    url = INDEX_URLS.get(universe)
    if not url:
        raise RuntimeError(f"Unsupported universe: {universe}")
    frame = pd.read_csv(io.StringIO(get_text(url)))
    if "Symbol" not in frame.columns:
        raise RuntimeError(f"{universe} CSV did not contain a Symbol column")
    return sorted(frame["Symbol"].astype(str).str.strip().str.upper().tolist())


def load_security_map() -> dict[str, str]:
    master = pd.read_csv(io.StringIO(get_text(SCRIP_MASTER_URL)), low_memory=False)
    out: dict[str, str] = {}
    for _, row in master.iterrows():
        exchange = str(row.get("SEM_EXM_EXCH_ID") or "").strip().upper()
        segment = str(row.get("SEM_SEGMENT") or "").strip().upper()
        series = str(row.get("SEM_SERIES") or "").strip().upper()
        trading_symbol = str(row.get("SEM_TRADING_SYMBOL") or "").strip().upper()
        security_id = str(row.get("SEM_SMST_SECURITY_ID") or "").strip()
        if exchange == "NSE" and segment == "E" and series == "EQ" and trading_symbol and security_id:
            out.setdefault(trading_symbol, security_id)
    return out


def parse_dhan_frame(data: dict[str, Any]) -> pd.DataFrame:
    timestamps = data.get("timestamp") or data.get("start_Time") or []
    opens = data.get("open") or []
    highs = data.get("high") or []
    lows = data.get("low") or []
    closes = data.get("close") or []
    volumes = data.get("volume") or []
    count = min(len(timestamps), len(opens), len(highs), len(lows), len(closes))
    rows: list[dict[str, Any]] = []
    for idx in range(count):
        rows.append(
            {
                "timestamp": datetime.fromtimestamp(int(timestamps[idx]), tz=IST),
                "open": float(opens[idx]),
                "high": float(highs[idx]),
                "low": float(lows[idx]),
                "close": float(closes[idx]),
                "volume": float(volumes[idx]) if idx < len(volumes) else 0.0,
            }
        )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.drop_duplicates("timestamp").set_index("timestamp").sort_index()


def post_dhan(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{DHAN_BASE}{path}", json=payload, headers=headers(), timeout=45)
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}: {response.text[:300]}")
    data = response.json()
    if isinstance(data, dict) and data.get("status") == "failure":
        raise RuntimeError(json.dumps(data)[:500])
    return data


def fetch_daily(security_id: str, from_date: str, to_date: str) -> pd.DataFrame:
    payload = {
        "securityId": security_id,
        "exchangeSegment": "NSE_EQ",
        "instrument": "EQUITY",
        "expiryCode": 0,
        "oi": False,
        "fromDate": from_date,
        "toDate": to_date,
    }
    return parse_dhan_frame(post_dhan("/v2/charts/historical", payload))


def fetch_intraday_15(security_id: str, from_dt: datetime, to_dt: datetime) -> pd.DataFrame:
    payload = {
        "securityId": security_id,
        "exchangeSegment": "NSE_EQ",
        "instrument": "EQUITY",
        "interval": "15",
        "oi": False,
        "fromDate": from_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "toDate": to_dt.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return parse_dhan_frame(post_dhan("/v2/charts/intraday", payload))


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=period).mean()


def atr(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = frame["close"].shift(1)
    tr = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - prev_close).abs(),
            (frame["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def add_chart_indicators(frame: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    f = frame.copy()
    f["ema9"] = ema(f["close"], settings.ema1_len)
    f["ema21"] = ema(f["close"], settings.ema2_len)
    f["ema10"] = ema(f["close"], settings.sma10_len)
    f["ema20"] = ema(f["close"], settings.sma20_len)
    f["ema50"] = ema(f["close"], settings.sma50_len)
    f["ema100"] = ema(f["close"], settings.sma100_len)
    f["ema200"] = ema(f["close"], settings.sma200_len)
    f["sma10"] = sma(f["close"], settings.sma10_len)
    f["sma20"] = sma(f["close"], settings.sma20_len)
    f["sma50"] = sma(f["close"], settings.sma50_len)
    f["sma100"] = sma(f["close"], settings.sma100_len)
    f["sma200"] = sma(f["close"], settings.sma200_len)
    f["atr14"] = atr(f, 14)
    f["vol10"] = sma(f["volume"], 10)
    f["vol20"] = sma(f["volume"], 20)
    f["vol30"] = sma(f["volume"], 30)
    f["volume_ok"] = (
        (f["volume"] > f["vol10"])
        | (f["volume"] > f["vol20"])
        | (f["volume"] > f["vol30"])
    ).fillna(False)
    candle_range = f["high"] - f["low"]
    f["strong_candle"] = (
        (f["close"] > f["open"])
        & ((f["close"] - f["open"]).abs() / candle_range.replace(0, np.nan) * 100 >= settings.min_entry_body_range_pct)
        & ((f["high"] - f["close"]) / candle_range.replace(0, np.nan) * 100 <= settings.max_entry_close_from_high_pct)
    ).fillna(False)
    return f


def add_tf_state(frame: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    f = frame.copy()
    close = f["close"]
    f["ema9"] = ema(close, settings.ema1_len)
    f["ema21"] = ema(close, settings.ema2_len)
    f["ema10"] = ema(close, settings.sma10_len)
    f["ema20"] = ema(close, settings.sma20_len)
    f["ema50"] = ema(close, settings.sma50_len)
    f["ema100"] = ema(close, settings.sma100_len)
    f["ema200"] = ema(close, settings.sma200_len)
    body_top = f[["open", "close"]].max(axis=1)
    body_bottom = f[["open", "close"]].min(axis=1)
    f["darvas_top"] = body_top.rolling(settings.tf_darvas_upper_len, min_periods=settings.tf_darvas_upper_len).max().shift(1)
    f["darvas_bottom"] = body_bottom.rolling(settings.tf_darvas_lower_len, min_periods=settings.tf_darvas_lower_len).min().shift(1)
    f["vol10"] = sma(f["volume"], 10)
    f["vol20"] = sma(f["volume"], 20)
    f["vol30"] = sma(f["volume"], 30)
    volume_ok = (
        (f["volume"] > f["vol10"])
        | (f["volume"] > f["vol20"])
        | (f["volume"] > f["vol30"])
    ).fillna(False)
    short_ok = (f["ema10"] > f["ema20"]) & (f["ema20"] > f["ema50"]) & (close > f["ema10"]) & (close > f["ema20"]) & (close > f["ema50"])
    long_ok = (
        (f["ema50"] > f["ema100"])
        & (f["ema100"] > f["ema200"])
        & (f["ema50"] > f["ema50"].shift(settings.slope_len))
        & (f["ema100"] > f["ema100"].shift(settings.slope_len))
        & (close > f["ema50"])
        & (close > f["ema100"])
        & (close > f["ema200"])
    )
    ema_ok = (f["ema9"] > f["ema21"]) & (close > f["ema21"])
    darvas_ok = (~pd.Series(settings.tf_use_darvas, index=f.index)) | (f["darvas_top"].notna() & f["darvas_bottom"].notna() & (close > f["darvas_top"]))
    short_filter_ok = (~pd.Series(settings.tf_use_short_trend, index=f.index)) | short_ok
    long_filter_ok = (~pd.Series(settings.tf_use_long_trend, index=f.index)) | long_ok
    volume_filter_ok = (~pd.Series(settings.use_volume_filter, index=f.index)) | volume_ok
    signal = darvas_ok & short_filter_ok & long_filter_ok & ema_ok & volume_filter_ok
    signal_times = pd.Series(pd.NaT, index=f.index, dtype="datetime64[ns, UTC]")
    signal_times.loc[signal] = signal_times.loc[signal].index
    f["last_signal_time"] = signal_times.ffill()
    f["signal_age_days"] = (f.index.to_series() - f["last_signal_time"]).dt.total_seconds() / 86400.0
    f["tf_required_ok"] = f["signal_age_days"].notna() & (f["signal_age_days"] <= settings.tf_valid_days) & (close >= f["ema100"])
    f["tf_darvas_ok"] = darvas_ok
    return f


def latest_tf_for_bar(tf: pd.DataFrame, bar_ts: pd.Timestamp) -> pd.Series | None:
    cutoff = pd.Timestamp(bar_ts.date(), tz=IST) + pd.Timedelta(hours=23, minutes=59)
    eligible = tf.loc[:cutoff]
    if eligible.empty:
        return None
    return eligible.iloc[-1]


def calc_tp(entry: float, sl: float, rr: float) -> float:
    return entry + (entry - sl) * rr


def resample_weekly(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.resample("W-FRI")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
    )


def add_global_darvas(frame: pd.DataFrame, settings: Settings) -> pd.DataFrame:
    f = frame.copy()
    body_top = f[["open", "close"]].max(axis=1)
    body_bottom = f[["open", "close"]].min(axis=1)
    f["global_darvas1_top"] = body_top.rolling(settings.global_darvas1_len, min_periods=settings.global_darvas1_len).max().shift(1)
    f["global_darvas1_bottom"] = body_bottom.rolling(settings.global_darvas1_len, min_periods=settings.global_darvas1_len).min().shift(1)
    f["global_darvas1_ok"] = (
        (~pd.Series(settings.global_darvas1_on, index=f.index))
        | (f["global_darvas1_top"].notna() & f["global_darvas1_bottom"].notna() & (f["close"] > f["global_darvas1_top"]))
    )
    return f


def simulate(symbol: str, base: pd.DataFrame, tf1: pd.DataFrame, settings: Settings, since_date: datetime.date) -> dict[str, Any]:
    d = add_global_darvas(add_chart_indicators(base, settings), settings)
    t = add_tf_state(tf1, settings)
    position_count = 0
    last_entry_idx = -10_000
    entries: list[dict[str, Any]] = []
    entry_price = {1: np.nan, 2: np.nan, 3: np.nan}
    entry_sl = {1: np.nan, 2: np.nan, 3: np.nan}
    entry_tp = {1: np.nan, 2: np.nan, 3: np.nan}
    entry_bar = {1: -1, 2: -1, 3: -1}
    partial_taken = {1: False, 2: False, 3: False}

    rows = list(d.iterrows())
    for i, (ts, row) in enumerate(rows):
        tf_row = latest_tf_for_bar(t, ts)
        tf_required_ok = bool(tf_row is not None and tf_row["tf_required_ok"])
        tf_entry_darvas_ok = bool(
            tf_row is not None
            and tf_row["tf_darvas_ok"]
            and (not settings.tf_use_darvas or row["close"] > tf_row["darvas_top"])
        )
        timeframe_ok = tf_required_ok and tf_entry_darvas_ok
        chart_volume_ok = bool((not settings.use_volume_filter) or row["volume_ok"])
        strong_ok = bool((not settings.use_strong_entry_candle) or row["strong_candle"])
        global_darvas_ok = bool(row["global_darvas1_ok"])
        base_ok = bool(row["ema9"] > row["ema21"] and row["close"] > row["ema21"] and chart_volume_ok and strong_ok)
        entry_signal = base_ok and timeframe_ok and global_darvas_ok

        # Position state and exits, matching the Pine order closely enough for end-of-day scan.
        composite_sl = np.nan
        if position_count >= 3 and not np.isnan(entry_sl[3]):
            composite_sl = entry_sl[3]
        elif position_count >= 2 and not np.isnan(entry_sl[2]):
            composite_sl = entry_sl[2]
        elif position_count >= 1 and not np.isnan(entry_sl[1]):
            composite_sl = entry_sl[1]

        if position_count > 0:
            for level in (1, 2, 3):
                if not partial_taken[level] and not np.isnan(entry_tp[level]) and row["close"] >= entry_tp[level]:
                    partial_taken[level] = True
            ema_trend_break = i > 0 and rows[i - 1][1]["ema9"] >= rows[i - 1][1]["ema21"] and row["ema9"] < row["ema21"]
            sma_trend_break = i > 0 and rows[i - 1][1]["ema50"] >= rows[i - 1][1]["ema100"] and row["ema50"] < row["ema100"]
            if (not np.isnan(composite_sl) and row["close"] < composite_sl) or ema_trend_break or sma_trend_break:
                position_count = 0
                entry_price = {1: np.nan, 2: np.nan, 3: np.nan}
                entry_sl = {1: np.nan, 2: np.nan, 3: np.nan}
                entry_tp = {1: np.nan, 2: np.nan, 3: np.nan}
                entry_bar = {1: -1, 2: -1, 3: -1}
                partial_taken = {1: False, 2: False, 3: False}

        can_enter_new = i - last_entry_idx >= settings.min_bars_between_entries
        current_sl = d["low"].iloc[max(0, i - 4): i + 1].min() - row["atr14"] * settings.sl_buffer
        consolidation_sl = current_sl
        if not np.isfinite(current_sl):
            continue

        if entry_signal and can_enter_new and position_count == 0:
            level = 1
        elif entry_signal and can_enter_new and position_count == 1 and i > entry_bar[1] and (row["close"] - entry_price[1]) / entry_price[1] * 100 >= settings.min_profit_for_next_entry:
            level = 2
        elif entry_signal and can_enter_new and position_count == 2 and i > entry_bar[2] and (row["close"] - entry_price[2]) / entry_price[2] * 100 >= settings.min_profit_for_next_entry:
            level = 3
        else:
            level = 0

        if level:
            entry_price[level] = float(row["close"])
            entry_sl[level] = float(current_sl)
            entry_bar[level] = i
            entry_tp[level] = calc_tp(float(row["close"]), float(current_sl), [0, settings.risk_reward_l1, settings.risk_reward_l2, settings.risk_reward_l3][level])
            partial_taken[level] = False
            if level == 2:
                entry_sl[1] = float(consolidation_sl)
            elif level == 3:
                entry_sl[1] = float(consolidation_sl)
                entry_sl[2] = float(consolidation_sl)
            position_count = level
            last_entry_idx = i
            if ts.date() >= since_date:
                entries.append(
                    {
                        "symbol": symbol,
                        "entry_date": ts.date().isoformat(),
                        "level": f"L{level}",
                        "close": round(float(row["close"]), 2),
                        "sl": round(float(entry_sl[level]), 2),
                        "tp": round(float(entry_tp[level]), 2),
                        "tf_signal_age_days": round(float(tf_row["signal_age_days"]), 3) if tf_row is not None and pd.notna(tf_row["signal_age_days"]) else "",
                        "tf_darvas_top": round(float(tf_row["darvas_top"]), 2) if tf_row is not None and pd.notna(tf_row["darvas_top"]) else "",
                        "global_darvas1_top": round(float(row["global_darvas1_top"]), 2) if pd.notna(row["global_darvas1_top"]) else "",
                    }
                )

    latest = d.iloc[-1]
    return {
        "symbol": symbol,
        "entries": entries,
        "latest_close": round(float(latest["close"]), 2),
        "latest_date": d.index[-1].date().isoformat(),
    }


def write_outputs(results: list[dict[str, Any]], out_dir: Path, universe: str) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(IST).strftime("%Y%m%d_%H%M")
    rows = [entry for result in results for entry in result["entries"]]
    csv_path = out_dir / f"staircase_dhan_{universe}_entries_{stamp}.csv"
    summary_path = out_dir / f"staircase_dhan_{universe}_summary_{stamp}.md"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["symbol", "entry_date", "level", "close", "sl", "tp", "tf_signal_age_days", "tf_darvas_top", "global_darvas1_top"],
        )
        writer.writeheader()
        writer.writerows(rows)

    by_symbol: dict[str, list[str]] = {}
    for row in rows:
        by_symbol.setdefault(row["symbol"], []).append(row["level"])
    l1 = sorted(symbol for symbol, levels in by_symbol.items() if "L1" in levels and "L2" not in levels and "L3" not in levels)
    l2 = sorted(symbol for symbol, levels in by_symbol.items() if "L2" in levels and "L3" not in levels)
    all3 = sorted(symbol for symbol, levels in by_symbol.items() if "L3" in levels)

    lines = [
        f"# Staircase SMA Dhan {universe} Scan",
        "",
        f"Generated: {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}",
        "",
        f"Symbols with any entry: {len(by_symbol)}",
        f"L1 only: {', '.join(l1) if l1 else 'None'}",
        f"L2 reached: {', '.join(l2) if l2 else 'None'}",
        f"L1+L2+L3 reached: {', '.join(all3) if all3 else 'None'}",
        "",
        "| Symbol | Date | Level | Close | SL | TP | TF age days | Global Darvas top |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['symbol']} | {row['entry_date']} | {row['level']} | {row['close']} | {row['sl']} | {row['tp']} | {row['tf_signal_age_days']} | {row['global_darvas1_top']} |"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path, summary_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan NSE index universes for Staircase SMA entries using Dhan data.")
    parser.add_argument("--weeks", type=int, default=5)
    parser.add_argument("--sleep", type=float, default=0.45)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--universe",
        choices=sorted(INDEX_URLS),
        default="nifty50",
        help="NSE index universe to scan.",
    )
    parser.add_argument("--weekly-base-daily-tf-preset", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=Path("analysis") / "staircase_dhan")
    args = parser.parse_args()
    load_dotenv()

    settings = Settings(
        use_strong_entry_candle=not args.weekly_base_daily_tf_preset,
        use_volume_filter=args.weekly_base_daily_tf_preset,
        tf_use_darvas=not args.weekly_base_daily_tf_preset,
        tf_use_short_trend=True,
        tf_use_long_trend=True,
        global_darvas1_on=args.weekly_base_daily_tf_preset,
        global_darvas1_len=20,
    )
    today = datetime.now(IST).date()
    since = today - timedelta(weeks=args.weeks)
    daily_from = (today - timedelta(days=900)).isoformat()
    to_date = today.isoformat()

    symbols = load_index_symbols(args.universe)
    if args.limit:
        symbols = symbols[: args.limit]
    security_map = load_security_map()
    results: list[dict[str, Any]] = []
    failures: list[str] = []

    print(f"Scanning {len(symbols)} {args.universe} symbols from {since.isoformat()} to {to_date}", flush=True)
    consecutive_auth_failures = 0
    for idx, symbol in enumerate(symbols, start=1):
        sec = security_map.get(symbol)
        if not sec:
            failures.append(f"{symbol}: no Dhan security id")
            continue
        try:
            daily = fetch_daily(sec, daily_from, to_date)
            time.sleep(args.sleep)
            base = resample_weekly(daily) if args.weekly_base_daily_tf_preset else daily
            tf1 = daily if args.weekly_base_daily_tf_preset else fetch_intraday_15(sec, datetime.now(IST) - timedelta(days=88), datetime.now(IST))
            if not args.weekly_base_daily_tf_preset:
                time.sleep(args.sleep)
            if daily.empty or tf1.empty or base.empty:
                failures.append(f"{symbol}: empty daily/tf/base response")
                continue
            result = simulate(symbol, base, tf1, settings, since)
            results.append(result)
            consecutive_auth_failures = 0
            print(f"[{idx:02d}/{len(symbols)}] {symbol}: {len(result['entries'])} entries", flush=True)
        except Exception as exc:
            failures.append(f"{symbol}: {exc}")
            print(f"[{idx:02d}/{len(symbols)}] {symbol}: failed ({exc})", flush=True)
            if "401" in str(exc) or "Invalid_Authentication" in str(exc):
                consecutive_auth_failures += 1
                if consecutive_auth_failures >= 3:
                    print("Stopping early after 3 consecutive authentication failures.", flush=True)
                    break
            else:
                consecutive_auth_failures = 0

    csv_path, summary_path = write_outputs(results, args.out_dir, args.universe)
    print(f"Wrote {csv_path}")
    print(f"Wrote {summary_path}")
    if failures:
        fail_path = args.out_dir / f"staircase_dhan_{args.universe}_failures.txt"
        fail_path.write_text("\n".join(failures) + "\n", encoding="utf-8")
        print(f"Failures: {len(failures)} written to {fail_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

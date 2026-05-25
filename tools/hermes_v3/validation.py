#!/usr/bin/env python3
"""Hermes V3 Validation — verify indicator correctness and no-lookahead."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import yaml
from hermes_v3.indicators import compute_all_indicators
from hermes_v3.darvas import compute_darvas
from hermes_v3.data import load_data


def validate():
    cfg_path = Path(__file__).parent / "config.yaml"
    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    errors = []

    # Load a known symbol for testing
    df = load_data("RELIANCE", "1wk", cfg)
    if df is None:
        print("WARN: RELIANCE weekly data not found, trying symbols...")
        from hermes_v3.data import discover_symbols, get_symbol_list
        reg = discover_symbols(cfg["data"]["vault_path"])
        syms = get_symbol_list(reg, "ready", max_stocks=1)
        if syms:
            df = load_data(syms[0], "1wk", cfg)
        if df is None:
            print("ERROR: No data available for validation")
            return 1

    print(f"Validation on {len(df)} bars")

    # 1. Indicator computation
    print("\n1. Computing indicators...")
    df = compute_all_indicators(df, cfg, prefix="")
    required_cols = ["ema9", "ema21", "sma10", "sma20", "sma50", "sma100", "sma200",
                     "atr14", "adx", "di_plus", "di_minus",
                     "short_stacked", "short_trend_ok", "long_stacked", "smas_rising",
                     "major_trend_ok", "ema_uptrend", "price_above_ema",
                     "high_20", "prev_high_20", "breakout", "adx_ok", "entry_signal",
                     "dynamic_sl", "trail_sma20_sl", "trail_sma50_sl",
                     "ema_crossunder", "sma_crossunder", "trend_break"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        errors.append(f"Missing indicator columns: {missing}")
    else:
        print("  All required columns present")

    # 2. Breakout uses previous rolling high — recalculate from scratch
    print("\n2. Verifying breakout uses previous high (no lookahead)...")
    high_20_full = df["high"].rolling(20, min_periods=20).max()
    prev_should_be = high_20_full.shift(1)
    valid = ~df["prev_high_20"].isna() & ~prev_should_be.isna()
    match = ((df["prev_high_20"].fillna(-1) == prev_should_be.fillna(-1)) |
             (df["prev_high_20"].isna() & prev_should_be.isna())).sum()
    total = len(df)
    if total > 0 and match / total < 0.99:
        errors.append(f"prev_high_20 mismatch: {match}/{total} match")
    else:
        print(f"  prev_high_20 matches: {match}/{total}")

    # 3. ATR is positive
    print("\n3. Verifying ATR values...")
    atr_neg = (df["atr14"].dropna() <= 0).sum()
    if atr_neg > 0:
        errors.append(f"ATR has {atr_neg} non-positive values")
    else:
        print("  ATR all positive")

    # 4. ADX range
    print("\n4. Verifying ADX range...")
    adx = df["adx"].dropna()
    print(f"  ADX range: {adx.min():.1f} - {adx.max():.1f}, mean={adx.mean():.1f}")

    # 5. Entry signal fires correctly
    print("\n5. Entry signal breakdown...")
    sig_count = df["entry_signal"].sum()
    print(f"  Entry signals: {sig_count} out of {len(df)} bars")
    if sig_count > 0:
        # Verify each component
        for comp in ["major_trend_ok", "ema_uptrend", "price_above_ema", "breakout", "adx_ok"]:
            val_count = (df["entry_signal"] & ~df[comp]).sum()
            if val_count > 0:
                errors.append(f"entry_signal true but {comp} is false in {val_count} bars")

    # 6. Darvas no-lookahead
    print("\n6. Verifying Darvas box no-lookahead...")
    for darvas_len in [5, 10, 20]:
        d = compute_darvas(df, darvas_len, prefix="dv_")
        # darvas_high should be the body top max of prior N bars, shifted by 1
        body_top = df[["open", "close"]].max(axis=1)
        expected = body_top.rolling(darvas_len, min_periods=darvas_len).max().shift(1)
        match = ((d["dv_high"].fillna(-1) == expected.fillna(-1)) |
                 (d["dv_high"].isna() & expected.isna())).sum()
        total = len(d)
        if total > 0 and match / total < 0.99:
            errors.append(f"Darvas high mismatch for len={darvas_len}: {match}/{total}")
        else:
            print(f"  Darvas len={darvas_len} high matches: {match}/{total}")

    # 7. Crossunder detection
    print("\n7. Verifying crossunder detection...")
    ema9 = df["ema9"]
    ema21_val = df["ema21"]
    actual_crossunder = (ema9.shift(1) >= ema21_val.shift(1)) & (ema9 < ema21_val)
    match = (df["ema_crossunder"].fillna(False) == actual_crossunder.fillna(False)).sum()
    total = len(df)
    if match / total < 0.99:
        errors.append(f"ema_crossunder mismatch: {match}/{total}")
    else:
        print(f"  EMA crossunder matches: {match}/{total}")

    # 8. Dynamic SL consistency
    print("\n8. Verifying dynamic SL...")
    sl_type = cfg["strategy"]["sl_type"]
    print(f"  SL type: {sl_type}")
    sl_null = df["dynamic_sl"].isna().sum()
    print(f"  SL NaN count: {sl_null} / {len(df)}")

    # 9. Consolidation tracking
    print("\n9. Verifying consolidation tracking...")
    in_consol = df["consolidating"].sum()
    print(f"  Consolidating bars: {in_consol} ({in_consol/len(df)*100:.1f}%)")
    if in_consol > 0:
        max_streak = df["consol_count"].max()
        print(f"  Max consolidation streak: {max_streak}")

    # 10. majorTrendOK matches Pine logic
    print("\n10. Verifying majorTrendOK = (long+rising+above) OR shortTrendOK...")
    expected_major = (
        (df["long_stacked"] & df["smas_rising"] & df["price_above_long"])
        | df["short_trend_ok"]
    )
    match = (df["major_trend_ok"].fillna(False) == expected_major.fillna(False)).sum()
    if match / len(df) < 0.99:
        errors.append(f"major_trend_ok mismatch: {match}/{len(df)}")
    else:
        print(f"  major_trend_ok matches: {match}/{len(df)}")

    if errors:
        print(f"\n{len(errors)} ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print("\nAll validations passed!")
        return 0


if __name__ == "__main__":
    sys.exit(validate())

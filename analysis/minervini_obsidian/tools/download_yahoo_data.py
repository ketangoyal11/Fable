#!/usr/bin/env python3
"""
Unified Yahoo Finance Data Downloader for Minervini Analysis
=============================================================

Downloads daily OHLCV data for any ticker and saves it to the standard
Minervini analysis directory structure:
    analysis/minervini_obsidian/Indian Stocks/<TICKER>/<TICKER>_ohlcv.csv

Usage:
    python download_yahoo_data.py <TICKER> [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--period PERIOD]

Examples:
    python download_yahoo_data.py ARM
    python download_yahoo_data.py ARM --start 2024-01-01
    python download_yahoo_data.py ARM --period 2y
    python download_yahoo_data.py RELIANCE.NS --start 2023-01-01
    python download_yahoo_data.py TCS.NS --period 5y

Parameters:
    TICKER          Stock ticker (e.g., ARM, AAPL, RELIANCE.NS, TCS.NS)
    --start         Start date (default: 2 years ago)
    --end           End date (default: today)
    --period        Yahoo period string (e.g., 1y, 2y, 5y, 10y, max).
                    If set, overrides --start and --end.
    --outdir        Custom output directory (default: analysis/minervini_obsidian/Indian Stocks/)
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

try:
    import yfinance as yf
except ImportError:
    print("[err] yfinance not installed. Run: pip install yfinance")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("[err] pandas not installed. Run: pip install pandas")
    sys.exit(1)


def get_project_root():
    """Get the project root directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # tools/ is inside minervini_obsidian/
    return os.path.join(script_dir, "..")


def download_ticker(ticker, start=None, end=None, period=None, outdir=None):
    """Download OHLCV data for a ticker and save to CSV."""
    
    if outdir is None:
        project_root = get_project_root()
        outdir = os.path.join(project_root, "Indian Stocks", ticker.upper())
    
    os.makedirs(outdir, exist_ok=True)
    
    csv_path = os.path.join(outdir, f"{ticker.upper()}_ohlcv.csv")
    
    print(f"\n  -> Ticker: {ticker.upper()}")
    print(f"  -> Output: {csv_path}")
    
    # Download
    try:
        if period:
            print(f"  -> Period: {period}")
            df = yf.download(ticker, period=period, progress=False)
        else:
            print(f"  -> Range: {start} to {end}")
            df = yf.download(ticker, start=start, end=end, progress=False)
    except Exception as e:
        print(f"[err] Download failed: {e}")
        return None
    
    if df.empty:
        print("[err] No data returned. Check ticker symbol.")
        return None
    
    # Handle MultiIndex columns (yfinance >= 0.2.x returns MultiIndex)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    
    # Save
    df.to_csv(csv_path)
    
    # Summary
    print(f"\n  {'='*60}")
    print(f"  DOWNLOAD COMPLETE")
    print(f"  {'='*60}")
    print(f"  Bars:        {len(df)}")
    print(f"  Date range:  {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"  Open:        ${float(df['Open'].iloc[0]):.2f}")
    print(f"  High:        ${float(df['High'].max()):.2f}")
    print(f"  Low:         ${float(df['Low'].min()):.2f}")
    print(f"  Close:       ${float(df['Close'].iloc[-1]):.2f}")
    print(f"  Avg Volume:  {int(df['Volume'].mean()):,}")
    print(f"  File:        {csv_path}")
    print(f"  {'='*60}")
    
    return csv_path


def main():
    parser = argparse.ArgumentParser(
        description="Download Yahoo Finance OHLCV data for Minervini analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., ARM, AAPL, RELIANCE.NS)")
    parser.add_argument("--start", default=None, help="Start date (YYYY-MM-DD). Default: 2 years ago")
    parser.add_argument("--end", default=None, help="End date (YYYY-MM-DD). Default: today")
    parser.add_argument("--period", default=None, help="Yahoo period (e.g., 1y, 2y, 5y, max). Overrides --start/--end")
    parser.add_argument("--outdir", default=None, help="Custom output directory")
    
    args = parser.parse_args()
    
    # Default date range: 2 years ago to today
    if args.period is None and args.start is None:
        args.start = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
    if args.period is None and args.end is None:
        args.end = datetime.now().strftime("%Y-%m-%d")
    
    download_ticker(
        ticker=args.ticker,
        start=args.start,
        end=args.end,
        period=args.period,
        outdir=args.outdir
    )


if __name__ == "__main__":
    main()

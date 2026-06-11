"""Extract APOLLO OHLCV data (2020-2026) for Minervini analysis + compute SMAs"""

import csv
from datetime import datetime

rows = []
with open("data/yfinance_universe/history/APOLLO.csv", "r") as f:
    reader = csv.DictReader(f)
    for r in reader:
        try:
            d = datetime.strptime(r["Date"][:10], "%Y-%m-%d")
            if d >= datetime(2020, 1, 1):
                rows.append({
                    "date": r["Date"][:10],
                    "open": float(r["Open"]),
                    "high": float(r["High"]),
                    "low": float(r["Low"]),
                    "close": float(r["Close"]),
                    "volume": int(float(r["Volume"])) if r["Volume"] else 0,
                })
        except:
            pass

# Compute SMAs
closes = [r["close"] for r in rows]
volumes = [r["volume"] for r in rows]

def sma(data, period):
    return [sum(data[i-period:i])/period if i >= period else None for i in range(len(data))]

sma50 = sma(closes, 50)
sma150 = sma(closes, 150)
sma200 = sma(closes, 200)
vol_sma50 = sma(volumes, 50)

# Print header
print("Date,Open,High,Low,Close,Volume,SMA50,SMA150,SMA200,VolSMA50")

for i, r in enumerate(rows):
    print(f"{r['date']},{r['open']:.2f},{r['high']:.2f},{r['low']:.2f},{r['close']:.2f},{r['volume']},{sma50[i] if sma50[i] else ''},{sma150[i] if sma150[i] else ''},{sma200[i] if sma200[i] else ''},{vol_sma50[i] if vol_sma50[i] else ''}")

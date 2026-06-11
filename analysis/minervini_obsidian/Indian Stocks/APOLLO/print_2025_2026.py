"""Print 2025-2026 data in readable format"""
import csv

rows = []
with open("data/yfinance_universe/history/APOLLO.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["Date"][:4] in ["2025", "2026"]:
            rows.append(r)

for r in rows:
    date = r["Date"][:10]
    c = float(r["Close"]) if r["Close"] else 0
    h = float(r["High"]) if r["High"] else 0
    l = float(r["Low"]) if r["Low"] else 0
    o = float(r["Open"]) if r["Open"] else 0
    v = int(float(r["Volume"])) if r["Volume"] else 0
    print(f"{date}: O={o:.2f} H={h:.2f} L={l:.2f} C={c:.2f} V={v:,}")

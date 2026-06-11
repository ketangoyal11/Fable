"""Check Entry 4 and Entry 5 pivot dates more carefully"""
import csv

rows = []
with open("data/yfinance_universe/history/APOLLO.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append(r)

# Check Jun 13, 2023 pivot
print("=== MAY-JUN 2023 — BASE AND PIVOT ===")
for r in rows:
    d = r["Date"][:10]
    if "2023-05-01" <= d <= "2023-06-30":
        c = float(r["Close"]) if r["Close"] else 0
        h = float(r["High"]) if r["High"] else 0
        l = float(r["Low"]) if r["Low"] else 0
        o = float(r["Open"]) if r["Open"] else 0
        v = int(float(r["Volume"])) if r["Volume"] else 0
        print(f"{d}: O={o:.2f} H={h:.2f} L={l:.2f} C={c:.2f} V={v}")

print()
print("=== OCT 25 - NOV 10 2023 — ENTRY 5 PIVOT ===")
for r in rows:
    d = r["Date"][:10]
    if d >= "2023-10-25" and d <= "2023-11-10":
        c = float(r["Close"]) if r["Close"] else 0
        h = float(r["High"]) if r["High"] else 0
        l = float(r["Low"]) if r["Low"] else 0
        o = float(r["Open"]) if r["Open"] else 0
        v = int(float(r["Volume"])) if r["Volume"] else 0
        print(f"{d}: O={o:.2f} H={h:.2f} L={l:.2f} C={c:.2f} V={v}")

print()
print("=== JUL-NOV 2020 — Check if Entry 2 had a real base ===")
for r in rows:
    d = r["Date"][:10]
    if d >= "2020-06-01" and d <= "2020-11-30":
        c = float(r["Close"]) if r["Close"] else 0
        h = float(r["High"]) if r["High"] else 0
        l = float(r["Low"]) if r["Low"] else 0
        v = int(float(r["Volume"])) if r["Volume"] else 0
        print(f"{d}: H={h:.2f} L={l:.2f} C={c:.2f} V={v}")

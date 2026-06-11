"""Detailed VCP check for 2025 buy points - check base structure"""
import csv

rows = []
with open("data/yfinance_universe/history/APOLLO.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append(r)

# Check May 9, 2025 base (Feb-May 2025)
print("=== BASE FOR MAY 9, 2025 (Feb-May 2025) ===")
for r in rows:
    d = r["Date"][:10]
    if d >= "2025-02-01" and d <= "2025-05-10":
        c = float(r["Close"]) if r["Close"] else 0
        h = float(r["High"]) if r["High"] else 0
        l = float(r["Low"]) if r["Low"] else 0
        o = float(r["Open"]) if r["Open"] else 0
        v = int(float(r["Volume"])) if r["Volume"] else 0
        print(f"{d}: O={o:.2f} H={h:.2f} L={l:.2f} C={c:.2f} V={v}")

print()
print("=== BASE FOR AUG 22, 2025 (Jun-Aug 2025) ===")
for r in rows:
    d = r["Date"][:10]
    if d >= "2025-06-01" and d <= "2025-08-25":
        c = float(r["Close"]) if r["Close"] else 0
        h = float(r["High"]) if r["High"] else 0
        l = float(r["Low"]) if r["Low"] else 0
        o = float(r["Open"]) if r["Open"] else 0
        v = int(float(r["Volume"])) if r["Volume"] else 0
        print(f"{d}: O={o:.2f} H={h:.2f} L={l:.2f} C={c:.2f} V={v}")

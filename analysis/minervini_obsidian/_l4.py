import yfinance as yf, pandas as pd, json
df = yf.download(NETWEB.NS, period=1mo, interval=1d)
df.columns = [c[0] for c in df.columns]
vol50 = df[Volume].rolling(50).mean()
for idx, row in df.tail(20).iterrows():
    x = str(idx.date())
    rng = row[High] - row[Low]
    bp = round(abs(row[Close] - row[Open]) / rng * 100, 1) if rng > 0 else 0
    prev = df[Close].shift(1).loc[idx] if idx != df.index[0] else None
    if prev and prev > 0:
        gp = round((row[Open] / prev - 1) * 100, 2)
        rp = round((row[Close] / prev - 1) * 100, 2)
    else:
        gp = rp = 0
    av = vol50.loc[idx]
    vr = round(row[Volume] / av, 2) if av and av > 0 else 0
    print(x, O:, round(row[Open],1), H:, round(row[High],1), L:, round(row[Low],1), C:, round(row[Close],1), V:, int(row[Volume]), BP:, bp, GP:, gp, RP:, rp, VR:, vr)
    if vr > 2:
        print( VOL SPIKE, vr, x)

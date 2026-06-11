import yfinance as yf, pandas as pd, json
df = yf.download('NETWEB.NS', period='6mo', interval='1d')
df.columns = [c[0] for c in df.columns]
df = df.tail(120)
res = {}
for idx, row in df.iterrows():
    x = str(idx.date())
    rng = row['High'] - row['Low']
    bp = round(abs(row['Close'] - row['Open']) / rng * 100, 1) if rng > 0 else 0
    prev = df['Close'].shift(1).loc[idx]
    if pd.notna(prev):
        gp = round((row['Open'] / prev - 1) * 100, 2)
        rp = round((row['Close'] / prev - 1) * 100, 2)
    else:
        gp = rp = 0
    av = df['Volume'].rolling(50).mean().loc[idx]
    vr = round(row['Volume'] / av, 2) if pd.notna(av) and av > 0 else 1.0
    res[x] = {'O': row['Open'], 'H': row['High'], 'L': row['Low'], 'C': row['Close'], 'V': int(row['Volume']), 'BP': bp, 'GP': gp, 'RP': rp, 'VR': vr}
print(json.dumps(res, indent=2))

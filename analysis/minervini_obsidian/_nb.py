import yfinance, pandas
import json
df = yfinance.download("NETWEB.NS", period="6mo", interval="1d")
df.columns = [c[0] for c in df.columns]
df = df.tail(120)
dict = {}
for idx, row in df.iterrows():
    x = str(idx.date())
    dict[x] = {'O": row["Open"], 'H': row["High"], 'L': row["Low"], 'C': row["Close"], 'V': row["Volume"]}
    if (row["High"] - row["Low"]) > 0:
        dict[x]['BP'] = round(abs(row["Close"] - row["Open"]) / (row["High"] - row["Low"]) * 100, 1)
    else:
        dict[x]['BP'] = 0
    if pd.notna(df["Close"].shift(1).loc[idx]):
        dict[x]['GP'] = round((row["Open"] / df["Close"].shift(1).loc[idx] - 1) * 100, 2)
        dict[x]['RP'] = round((row["Close"] / df["Close"].shift(1).loc[idx] - 1) * 100, 2)
    else:
        dict[x]['GP'] = dict[x]['RP'] = 0
    avc = df["Volume"].rolling(50).mean().loc[idx]
    dict[x]['VR'] = round(row["Volume"] / avc, 2) if pd.notna(avc) and avc > 0 else 1
print(json.dumps(dict, indent=2))
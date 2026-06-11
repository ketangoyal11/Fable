"""Fetch MU (recent), IONS (2014), GPRE (2013+2014) data from Yahoo."""
import yfinance as yf, os

outdir = os.path.join(os.path.dirname(__file__), "..", "data")

# 1. MU - last 1 year
print("Fetching MU (last year)...")
mu = yf.download("MU", period="1y", progress=False)
mu_path = os.path.join(outdir, "MU_recent_ohlcv.csv")
mu.to_csv(mu_path)
print(f"  {len(mu)} bars -> {os.path.basename(mu_path)}")
print(f"  Range: {mu.index[0].strftime('%Y-%m-%d')} to {mu.index[-1].strftime('%Y-%m-%d')}")
print(f"  Price: ${float(mu['Close'].iloc[-1]):.2f} (last)")
print(f"  High: ${float(mu['High'].max()):.2f}  Low: ${float(mu['Low'].min()):.2f}")

# 2. IONS - 2014
print("\nFetching IONS (2014)...")
ions = yf.download("IONS", start="2014-01-01", end="2014-12-31", progress=False)
ions_path = os.path.join(outdir, "IONS_2014_ohlcv.csv")
ions.to_csv(ions_path)
print(f"  IONS 2014: {len(ions)} bars -> {os.path.basename(ions_path)}")
print(f"  Range: {ions.index[0].strftime('%Y-%m-%d')} to {ions.index[-1].strftime('%Y-%m-%d')}")
if len(ions) > 0:
    print(f"  Price: ${float(ions['Close'].iloc[-1]):.2f} (last)")
    print(f"  High: ${float(ions['High'].max()):.2f}  Low: ${float(ions['Low'].min()):.2f}")

# Also check if the ticker returns empty (ISIS delisted, IONS might not go back that far)
if len(ions) == 0:
    print("  WARNING: IONS returned NO data for 2014. Trying IONS with max period...")
    ions_all = yf.download("IONS", period="max", progress=False)
    if len(ions_all) > 0:
        first_d = ions_all.index[0].strftime('%Y-%m-%d')
        last_d = ions_all.index[-1].strftime('%Y-%m-%d')
        print(f"  IONS max available: {first_d} to {last_d}")
        # Save it anyway
        ions_all.to_csv(os.path.join(outdir, "IONS_all_ohlcv.csv"))
        print(f"  Saved to IONS_all_ohlcv.csv ({len(ions_all)} bars)")

# 3. GPRE - full and 2013
print("\nFetching GPRE (2013)...")
gpre_2013 = yf.download("GPRE", start="2013-01-01", end="2013-12-31", progress=False)
gpre_2013_path = os.path.join(outdir, "GPRE_2013_ohlcv.csv")
gpre_2013.to_csv(gpre_2013_path)
print(f"  GPRE 2013: {len(gpre_2013)} bars")
if len(gpre_2013) > 0:
first_d = gpre_2013.index[0].strftime('%Y-%m-%d')
last_d = gpre_2013.index[-1].strftime('%Y-%m-%d')
print(f"  Range: {first_d} to {last_d}")
print(f"  Price: ${float(gpre_2013['Close'].iloc[-1]):.2f} (last)")

print("\nDone.")

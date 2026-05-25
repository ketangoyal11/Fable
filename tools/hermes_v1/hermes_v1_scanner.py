"""Hermes V1 Scanner — watches data vault, detects new stock data, dispatches to engines."""
import os
import json
import yaml
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path


class VaultScanner:
    def __init__(self, config_path):
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)
        self.vault_path = Path(self.cfg["vault"]["path"])
        self.timeframes = self.cfg["vault"]["timeframes"]
        self.file_pattern = self.cfg["vault"]["file_pattern"]
        self.state_file = self.vault_path / "_progress.json"
        self.state = self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {"completed": {}, "total_symbols": 0, "started_symbols": [], "scans": []}

    def _save_state(self):
        self.state["_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, default=str)

    def discover_stocks(self):
        stocks = []
        for d in sorted(self.vault_path.iterdir()):
            if d.is_dir() and not d.name.startswith("_"):
                stocks.append(d.name)
        return stocks

    def discover_files(self, symbol):
        folder = self.vault_path / symbol
        if not folder.exists():
            return {}
        files = {}
        for tf in self.timeframes:
            pattern = self.file_pattern.format(symbol=symbol, timeframe=tf)
            path = folder / pattern
            if path.exists():
                files[tf] = str(path)
        return files

    def scan(self):
        stocks = self.discover_stocks()
        self.state["total_symbols"] = len(stocks)
        registry = {}

        for symbol in stocks:
            files = self.discover_files(symbol)
            has_weekly = "1wk" in files
            has_all = all(tf in files for tf in self.timeframes)
            status = "ready" if (has_weekly and len(files) >= 3) else "incomplete"
            registry[symbol] = {
                "symbol": symbol,
                "files": files,
                "timeframes": list(files.keys()),
                "has_weekly": has_weekly,
                "has_all": has_all,
                "status": status,
            }

        self._save_state()
        return registry

    def load_dataframe(self, symbol, timeframe):
        path = self.vault_path / symbol / f"{symbol}_{timeframe}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"No data for {symbol} {timeframe}: {path}")
        df = pd.read_parquet(path)

        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.set_index("datetime").sort_index()

        required = ["open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing column {col} in {symbol} {timeframe}")

        df["symbol"] = symbol
        df["timeframe"] = timeframe
        return df

    def is_new(self, symbol, timeframe):
        key = f"{symbol}__{timeframe}"
        return key not in self.state.get("completed", {})

    def mark_scanned(self, symbol, timeframe):
        key = f"{symbol}__{timeframe}"
        self.state.setdefault("completed", {})[key] = datetime.now(timezone.utc).isoformat()
        self._save_state()


if __name__ == "__main__":
    import sys
    s = VaultScanner(sys.argv[1] if len(sys.argv) > 1 else "hermes_v1_config.yaml")
    reg = s.scan()
    ready = {k: v for k, v in reg.items() if v["status"] == "ready"}
    incomplete = {k: v for k, v in reg.items() if v["status"] != "ready"}
    print(f"Total: {len(reg)} | Ready: {len(ready)} | Incomplete: {len(incomplete)}")
    for sym, info in ready.items():
        print(f"  {sym}: {info['timeframes']}")

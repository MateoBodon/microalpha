#!/usr/bin/env python3
"""Fetch public daily data via yfinance for a small universe and write CSVs.

Usage:
  python scripts/fetch_public_data.py SPY AAPL MSFT --out data
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def fetch(symbols: list[str], outdir: Path, start: str = "2005-01-01") -> None:
    try:
        import yfinance as yf
    except ImportError as e:
        raise SystemExit("Please install yfinance: pip install yfinance") from e

    outdir.mkdir(parents=True, exist_ok=True)
    for s in symbols:
        df = yf.download(s, start=start, auto_adjust=True, progress=False)
        if df.empty:
            print(f"No data for {s}")
            continue
        df = df.rename(columns={"Close": "close", "Volume": "volume"})
        df = df[["close", "volume"]]
        df.to_csv(outdir / f"{s}.csv")
        print(f"Wrote {s} -> {outdir/(s+'.csv')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+", help="Tickers to fetch")
    ap.add_argument("--out", default="data", help="Output directory")
    ap.add_argument("--start", default="2005-01-01")
    args = ap.parse_args()

    fetch(args.symbols, Path(args.out), start=args.start)


if __name__ == "__main__":
    main()



#!/usr/bin/env python3
"""Prepare CRSP daily equities from WRDS to CSV per-symbol.

This script expects WRDS credentials to be supplied via environment variables or
interactive login. It writes one CSV per symbol with columns [close, volume].

Usage (example):
  python scripts/wrds_crsp_prep.py --universe sp500_2020.txt --out data_sp500
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd


def load_universe(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def export_symbol(df: pd.DataFrame, symbol: str, outdir: Path) -> None:
    if df.empty:
        return
    series = df.rename(columns={"prc": "close", "vol": "volume"})[["close", "volume"]]
    outdir.mkdir(parents=True, exist_ok=True)
    series.to_csv(outdir / f"{symbol}.csv")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", required=True, help="Path to text file of symbols")
    ap.add_argument("--out", required=True, help="Output directory for CSVs")
    ap.add_argument("--start", default="2005-01-01")
    args = ap.parse_args()

    symbols = load_universe(Path(args.universe))
    outdir = Path(args.out)

    try:
        import wrds
    except ImportError as e:
        raise SystemExit("Please install wrds: pip install wrds") from e

    db = wrds.Connection()
    for s in symbols:
        try:
            q = db.get_table(library="crsp", table="dsf", columns=["date", "permno", "prc", "vol"], obs=None, where=f"t.symbol='{s}'")
        except Exception:
            # Fallback simple query
            q = db.raw_sql(
                f"SELECT date, prc, vol FROM crsp.dsf WHERE ticker = '{s}' AND date >= '{args.start}' ORDER BY date"
            )
        q = q.set_index(pd.to_datetime(q["date"]))
        export_symbol(q, s, outdir)
        print(f"Exported {s}")


if __name__ == "__main__":
    main()



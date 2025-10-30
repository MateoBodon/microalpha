#!/usr/bin/env python3
"""Guided ETL for WRDS/CRSP daily equities to Microalpha CSVs.

This script is a template. It does NOT include credentials or data pulls.
Steps:
 1) Use WRDS Python API to query CRSP daily prices (adjusted for splits/dividends).
 2) Filter universe monthly (e.g., top 1000 by market cap) and persist symbol lists.
 3) For each symbol, write `<data_root>/<SYMBOL>.csv` with datetime index and `close` column.
 4) Optionally emit `sectors.json` mapping symbols to sectors for sector caps.

Example output format (per symbol CSV):
    Date,close
    2018-01-02,100.0
    2018-01-03,100.5

Keep raw WRDS credentials and raw data outside the repo.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Template for WRDS/CRSP ETL")
    ap.add_argument("--out", required=True, help="Output data directory")
    args = ap.parse_args()

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    print("This is a template. Implement WRDS queries and write symbol CSVs here.")


if __name__ == "__main__":
    main()

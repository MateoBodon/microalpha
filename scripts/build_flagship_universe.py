#!/usr/bin/env python3
"""Construct monthly flagship universes using liquidity and price filters.

The script consumes cleaned symbol files (``data_sp500_enriched``) and
metadata from ``metadata/sp500_enriched.csv`` to produce a set of
rebalance-ready universes.  Each output CSV enumerates the symbols that pass
liquidity/price/sector checks for a given rebalance date, along with their
latest statistics (adv, market-cap proxy, sector, etc.).

Usage
-----
    python scripts/build_flagship_universe.py \
        --data-dir data_sp500_enriched \
        --metadata metadata/sp500_enriched.csv \
        --out-dir artifacts/universe/flagship \
        --min-dollar-volume 5000000 \
        --min-price 5 \
        --top-n 450 \
        --max-sector-weight 0.25

Outputs
-------
1. ``artifacts/universe/flagship/all.csv`` – concatenated universe across all
   rebalance dates.
2. ``artifacts/universe/flagship/FLAGSHIP_<YYYY-MM-DD>.csv`` per month.
3. ``reports/flagship_universe_summary.json`` summarising coverage and
   universe sizes.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

TRADING_DAYS_MONTH = 21


def load_metadata(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(
            f"metadata file {path} not found; run scripts/augment_sp500.py first"
        )
    df = pd.read_csv(path)
    expected = {
        "symbol",
        "sector",
        "market_cap_proxy",
        "adv_20",
        "adv_63",
        "adv_126",
        "latest_close",
    }
    if not expected.issubset(set(df.columns)):
        missing = expected.difference(df.columns)
        raise SystemExit(f"metadata {path} missing columns: {missing}")
    df["symbol"] = df["symbol"].str.upper()
    return df


def compute_monthly_snapshots(symbol: str, df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per month with liquidity stats and last available price."""
    frame = df.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame.sort_values("timestamp", inplace=True)
    frame["dollar_volume"] = frame["close"] * frame["volume"]
    frame["adv_20"] = frame["dollar_volume"].rolling(20, min_periods=1).mean()
    frame["adv_63"] = frame["dollar_volume"].rolling(63, min_periods=1).mean()
    frame["adv_126"] = frame["dollar_volume"].rolling(126, min_periods=1).mean()
    frame["price_ma_20"] = frame["close"].rolling(20, min_periods=1).mean()

    frame["rebalance"] = frame["timestamp"].dt.to_period("M").dt.to_timestamp("M")
    monthly = frame.groupby("rebalance").tail(1)
    monthly = monthly[
        [
            "rebalance",
            "close",
            "adv_20",
            "adv_63",
            "adv_126",
            "price_ma_20",
            "timestamp",
        ]
    ]
    monthly.rename(
        columns={
            "close": "close",
            "adv_20": "adv_20",
            "adv_63": "adv_63",
            "adv_126": "adv_126",
            "price_ma_20": "price_ma_20",
        },
        inplace=True,
    )
    monthly.insert(0, "symbol", symbol)
    return monthly


def load_symbol_data(symbol: str, data_dir: Path) -> pd.DataFrame:
    path = data_dir / f"{symbol}.csv"
    if not path.exists():
        raise FileNotFoundError(f"missing cleaned file for symbol {symbol} ({path})")
    df = pd.read_csv(path)
    if "timestamp" not in df.columns:
        raise ValueError(f"{path} missing 'timestamp' column")
    return df


def enforce_sector_cap(df: pd.DataFrame, max_sector_weight: float) -> pd.DataFrame:
    if max_sector_weight <= 0 or max_sector_weight >= 1:
        return df
    counts: Dict[str, int] = defaultdict(int)
    max_per_sector = max(1, int(len(df) * max_sector_weight))
    selected = []
    for _, row in df.iterrows():
        sector = row.get("sector", "UNKNOWN")
        if counts[sector] < max_per_sector:
            selected.append(row)
            counts[sector] += 1
    return pd.DataFrame(selected)


def build_universe(
    metadata: pd.DataFrame,
    data_dir: Path,
    out_dir: Path,
    min_dollar_volume: float,
    min_price: float,
    top_n: int,
    max_sector_weight: float,
    start_date: pd.Timestamp | None,
    end_date: pd.Timestamp | None,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    all_snapshots: List[pd.DataFrame] = []
    universe_sizes: Dict[str, int] = {}

    for record in metadata.itertuples():
        symbol = record.symbol
        df = load_symbol_data(symbol, data_dir)
        df_snap = compute_monthly_snapshots(symbol, df)
        df_snap["sector"] = record.sector
        df_snap["market_cap_proxy"] = record.market_cap_proxy
        all_snapshots.append(df_snap)

    combined = pd.concat(all_snapshots, ignore_index=True)

    if start_date is not None:
        combined = combined.loc[combined["rebalance"] >= start_date]
    if end_date is not None:
        combined = combined.loc[combined["rebalance"] <= end_date]

    combined = combined.loc[
        (combined["adv_20"] >= min_dollar_volume) & (combined["close"] >= min_price)
    ]

    records = []
    for rebalance_date, group in combined.groupby("rebalance"):
        subset = group.sort_values("adv_20", ascending=False)
        if top_n > 0:
            subset = subset.head(top_n)
        subset = enforce_sector_cap(subset, max_sector_weight)
        subset = subset.assign(adv_rank=np.arange(1, len(subset) + 1))
        subset.insert(1, "date", subset["rebalance"].dt.strftime("%Y-%m-%d"))
        subset.drop(columns=["rebalance"], inplace=True)
        universe_sizes[rebalance_date.strftime("%Y-%m-%d")] = len(subset)

        out_path = out_dir / f"FLAGSHIP_{rebalance_date.strftime('%Y-%m-%d')}.csv"
        subset.to_csv(out_path, index=False)
        records.append(subset)

    all_universe = pd.concat(records, ignore_index=True) if records else pd.DataFrame()
    return all_universe, universe_sizes


def main() -> None:
    parser = argparse.ArgumentParser(description="Build flagship momentum universe")
    parser.add_argument("--data-dir", type=Path, default=Path("data_sp500_enriched"))
    parser.add_argument(
        "--metadata", type=Path, default=Path("metadata/sp500_enriched.csv")
    )
    parser.add_argument("--out-dir", type=Path, default=Path("data/flagship_universe"))
    parser.add_argument("--min-dollar-volume", type=float, default=5_000_000.0)
    parser.add_argument("--min-price", type=float, default=5.0)
    parser.add_argument("--top-n", type=int, default=450)
    parser.add_argument(
        "--max-sector-weight",
        type=float,
        default=0.25,
        help="Maximum fraction of universe per sector (0 disables)",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("reports/flagship_universe_summary.json"),
    )
    parser.add_argument("--start-date", type=str, default=None)
    parser.add_argument("--end-date", type=str, default=None)
    args = parser.parse_args()

    metadata = load_metadata(args.metadata)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    start_date = pd.to_datetime(args.start_date) if args.start_date else None
    end_date = pd.to_datetime(args.end_date) if args.end_date else None

    all_universe, universe_sizes = build_universe(
        metadata=metadata,
        data_dir=args.data_dir,
        out_dir=args.out_dir,
        min_dollar_volume=args.min_dollar_volume,
        min_price=args.min_price,
        top_n=args.top_n,
        max_sector_weight=args.max_sector_weight,
        start_date=start_date,
        end_date=end_date,
    )

    all_path = args.out_dir / "all.csv"
    all_universe.to_csv(all_path, index=False)

    summary = {
        "rebalance_dates": len(universe_sizes),
        "average_size": float(np.mean(list(universe_sizes.values())))
        if universe_sizes
        else 0,
        "min_size": min(universe_sizes.values()) if universe_sizes else 0,
        "max_size": max(universe_sizes.values()) if universe_sizes else 0,
        "parameters": {
            "min_dollar_volume": args.min_dollar_volume,
            "min_price": args.min_price,
            "top_n": args.top_n,
            "max_sector_weight": args.max_sector_weight,
            "start_date": args.start_date,
            "end_date": args.end_date,
        },
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2))

    print(f"Universe files written to {args.out_dir}")
    print(f"Concatenated universe: {all_path}")
    print(f"Summary: {args.summary_output}")


if __name__ == "__main__":
    main()

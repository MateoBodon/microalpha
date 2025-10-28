#!/usr/bin/env python3
"""Clean raw S&P500 panel and attach sector/market-cap metadata.

This script rewrites (or mirrors) the contents of ``data_sp500`` into a
clean directory with forward-filled volumes, positive liquidity, and basic
liquidity statistics.  It also emits symbol-level metadata that is consumed
by the flagship momentum universe builder.

Usage
-----
    python scripts/augment_sp500.py \
        --source data_sp500 \
        --dest data_sp500_enriched \
        --sector-map metadata/sp500_constituents.csv \
        --sector-map metadata/sp500_sector_overrides.csv \
        --metadata-output metadata/sp500_enriched.csv \
        --summary-output reports/data_sp500_cleaning.json

The script accepts multiple ``--sector-map`` arguments.  Each map must be a
CSV containing at least ``symbol`` and ``sector`` columns (case insensitive).
If no sector information is found for a ticker, the sector is marked as
``UNKNOWN`` and can be updated later.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

TRADING_DAYS_YEAR = 252
TRADING_DAYS_MONTH = 21


@dataclass
class SymbolStats:
    symbol: str
    start: str
    end: str
    rows: int
    sector: str
    industry: Optional[str]
    latest_close: float
    latest_volume: float
    adv_20: float
    adv_63: float
    adv_126: float
    market_cap_proxy: float
    volume_replaced: int
    volume_nonpositive: int


def load_sector_maps(paths: Iterable[Path]) -> Dict[str, Dict[str, str]]:
    mapping: Dict[str, Dict[str, str]] = {}
    for path in paths:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        columns = {c.lower(): c for c in df.columns}
        if "symbol" not in columns or "sector" not in columns:
            raise ValueError(f"sector map {path} missing required columns")
        for _, row in df.iterrows():
            symbol = str(row[columns["symbol"]]).strip().upper()
            if not symbol:
                continue
            sector = str(row[columns["sector"]]).strip()
            industry = None
            if "industry" in columns:
                industry = str(row[columns["industry"]]).strip()
            record = mapping.setdefault(
                symbol, {"sector": sector, "industry": industry or ""}
            )
            # Let later files override earlier ones.
            record["sector"] = sector or record["sector"]
            if industry:
                record["industry"] = industry
    return mapping


def compute_market_cap_proxy(df: pd.DataFrame) -> float:
    latest_close = float(df["close"].iloc[-1])
    # Use long-run median volume as a proxy for float * turnover assumption.
    median_volume = float(df["volume"].tail(TRADING_DAYS_YEAR).median())
    if pd.isna(median_volume) or median_volume <= 0:
        median_volume = float(df["volume"].tail(TRADING_DAYS_MONTH).median())
    if pd.isna(median_volume) or median_volume <= 0:
        median_volume = float(df["volume"].mean())
    if pd.isna(median_volume) or median_volume <= 0:
        median_volume = 1.0
    # Assume roughly one month of turnover to approximate outstanding shares.
    shares_proxy = median_volume * TRADING_DAYS_MONTH
    return float(latest_close * shares_proxy)


def clean_volume(series: pd.Series) -> tuple[pd.Series, int, int]:
    vol = series.astype("float64")
    replaced = int(vol.isna().sum())
    nonpositive = int((vol <= 0).sum())
    vol = vol.where(vol > 0)
    vol = vol.ffill().bfill()
    if vol.isna().any():
        vol = vol.fillna(vol.rolling(21, min_periods=1).mean())
    if vol.isna().any():
        vol = vol.fillna(vol.median())
    vol = vol.fillna(1.0)
    vol = vol.clip(lower=1.0)
    replaced = int(replaced + nonpositive)
    return vol.astype(series.dtype), replaced, nonpositive


def process_symbol(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    df.rename(columns={date_col: "timestamp"}, inplace=True)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df["close"] = df["close"].astype("float64")
    return df


def build_metadata_for_symbol(
    df: pd.DataFrame,
    sector_record: Optional[Dict[str, str]],
    volume_replaced: int,
    nonpositive_volume: int,
) -> SymbolStats:
    adv_20 = float(
        (df["close"] * df["volume"]).rolling(20, min_periods=1).mean().iloc[-1]
    )
    adv_63 = float(
        (df["close"] * df["volume"]).rolling(63, min_periods=1).mean().iloc[-1]
    )
    adv_126 = float(
        (df["close"] * df["volume"]).rolling(126, min_periods=1).mean().iloc[-1]
    )
    market_cap_proxy = compute_market_cap_proxy(df)

    sector = "UNKNOWN"
    industry = ""
    if sector_record:
        sector = sector_record.get("sector") or sector
        industry = sector_record.get("industry") or ""

    return SymbolStats(
        symbol=df.attrs["symbol"],
        start=str(df["timestamp"].iloc[0].date()),
        end=str(df["timestamp"].iloc[-1].date()),
        rows=len(df),
        sector=sector,
        industry=industry or None,
        latest_close=float(df["close"].iloc[-1]),
        latest_volume=float(df["volume"].iloc[-1]),
        adv_20=adv_20,
        adv_63=adv_63,
        adv_126=adv_126,
        market_cap_proxy=float(market_cap_proxy),
        volume_replaced=volume_replaced,
        volume_nonpositive=nonpositive_volume,
    )


def write_metadata(path: Path, stats: List[SymbolStats]) -> None:
    data = []
    for item in stats:
        data.append(
            {
                "symbol": item.symbol,
                "start": item.start,
                "end": item.end,
                "rows": item.rows,
                "sector": item.sector,
                "industry": item.industry or "",
                "latest_close": item.latest_close,
                "latest_volume": item.latest_volume,
                "adv_20": item.adv_20,
                "adv_63": item.adv_63,
                "adv_126": item.adv_126,
                "market_cap_proxy": item.market_cap_proxy,
                "volume_replaced": item.volume_replaced,
                "volume_nonpositive": item.volume_nonpositive,
            }
        )
    df = pd.DataFrame(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.sort_values("symbol", inplace=True)
    df.to_csv(path, index=False)


def write_summary(path: Path, stats: List[SymbolStats]) -> None:
    summary = {
        "symbols": len(stats),
        "global_start": min(s.start for s in stats),
        "global_end": max(s.end for s in stats),
        "sectors": sorted({s.sector for s in stats}),
        "missing_sector": sorted({s.symbol for s in stats if s.sector == "UNKNOWN"}),
        "volume_fixes": {
            s.symbol: {
                "replaced": s.volume_replaced,
                "nonpositive": s.volume_nonpositive,
            }
            for s in stats
            if s.volume_replaced or s.volume_nonpositive
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean S&P500 panel and emit metadata")
    parser.add_argument("--source", type=Path, default=Path("data_sp500"))
    parser.add_argument("--dest", type=Path, default=Path("data_sp500_enriched"))
    parser.add_argument("--sector-map", type=Path, action="append", default=[])
    parser.add_argument(
        "--metadata-output", type=Path, default=Path("metadata/sp500_enriched.csv")
    )
    parser.add_argument(
        "--summary-output", type=Path, default=Path("reports/data_sp500_cleaning.json")
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Rewrite source files instead of creating a new directory",
    )
    args = parser.parse_args()

    if not args.source.exists():
        raise SystemExit(f"source directory {args.source} not found")

    sector_map = load_sector_maps(args.sector_map)

    dest_dir = args.source if args.in_place else args.dest
    dest_dir.mkdir(parents=True, exist_ok=True)

    stats: List[SymbolStats] = []

    for path in sorted(args.source.glob("*.csv")):
        df = process_symbol(path)
        df.attrs["symbol"] = path.stem.upper()

        cleaned_volume, replaced, nonpositive = clean_volume(df["volume"])
        df["volume"] = cleaned_volume
        sector_record = sector_map.get(df.attrs["symbol"])

        stat = build_metadata_for_symbol(df, sector_record, replaced, nonpositive)
        stats.append(stat)

        output_path = dest_dir / path.name
        df.to_csv(output_path, index=False)

    write_metadata(args.metadata_output, stats)
    write_summary(args.summary_output, stats)
    print(f"Processed {len(stats)} symbols -> {dest_dir}")
    print(f"Metadata written to {args.metadata_output}")
    print(f"Summary written to {args.summary_output}")


if __name__ == "__main__":
    main()

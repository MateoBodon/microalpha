#!/usr/bin/env python3
"""Construct WRDS flagship momentum signals for analytics and tearsheets."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Final

import pandas as pd

DEFAULT_LOOKBACK_MONTHS: Final[int] = 12
DEFAULT_SKIP_MONTHS: Final[int] = 1
DEFAULT_MIN_ADV: Final[float] = 30_000_000.0


def _wrds_universe_path(path: str | None) -> Path:
    """Resolve the flagship universe CSV location.

    The path can be supplied explicitly via ``--universe``. Otherwise the
    ``WRDS_DATA_ROOT`` environment variable must be set so we can locate the
    canonical ``universes/flagship_sector_neutral.csv`` snapshot.
    """

    if path:
        candidate = Path(path).expanduser().resolve()
    else:
        root = os.environ.get("WRDS_DATA_ROOT")
        if not root:
            raise SystemExit("Set WRDS_DATA_ROOT or pass --universe explicitly")
        candidate = Path(root).expanduser().resolve() / "universes" / "flagship_sector_neutral.csv"
    if not candidate.exists():
        raise SystemExit(f"Universe CSV not found: {candidate}")
    return candidate


def _validate_inputs(lookback_months: int, skip_months: int, min_adv: float) -> None:
    if lookback_months <= 0:
        raise SystemExit("lookback-months must be positive")
    if skip_months < 0:
        raise SystemExit("skip-months cannot be negative")
    if min_adv <= 0:
        raise SystemExit("min-adv must be positive")


def _build_signals(
    universe_path: Path,
    output_path: Path,
    *,
    lookback_months: int = DEFAULT_LOOKBACK_MONTHS,
    skip_months: int = DEFAULT_SKIP_MONTHS,
    min_adv: float = DEFAULT_MIN_ADV,
) -> Path:
    """Generate cross-sectional momentum scores and realized returns per as-of date."""

    _validate_inputs(lookback_months, skip_months, min_adv)

    df = pd.read_csv(universe_path)
    required = {"symbol", "date", "close"}
    missing = required.difference(df.columns)
    if missing:
        raise SystemExit(f"Universe CSV missing columns: {sorted(missing)}")

    df = df.copy()
    df["symbol"] = df["symbol"].astype(str).str.upper()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"])
    if df.empty:
        raise SystemExit("Universe CSV contains no valid rows after cleaning")

    if "sector" not in df.columns:
        df["sector"] = "UNKNOWN"
    df["sector"] = df["sector"].fillna("UNKNOWN").astype(str)

    adv_source = "adv_20" if "adv_20" in df.columns else None
    if adv_source:
        df[adv_source] = pd.to_numeric(df[adv_source], errors="coerce")
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    grouped = df.groupby("symbol", sort=False)
    recent = grouped["close"].shift(skip_months)
    past = grouped["close"].shift(skip_months + lookback_months)
    forward = grouped["close"].shift(-1)

    df["score"] = (recent / past) - 1.0
    df["forward_return"] = (forward / df["close"]) - 1.0
    if adv_source:
        df["adv"] = df[adv_source]
    else:
        df["adv"] = float("nan")

    mask = df["score"].notna() & df["forward_return"].notna()
    mask &= (~df["score"].isin([float("inf"), float("-inf")]))
    mask &= (~df["forward_return"].isin([float("inf"), float("-inf")]))
    adv_filter = df["adv"].fillna(min_adv) >= min_adv
    mask &= adv_filter

    signals = df.loc[mask, ["date", "symbol", "score", "forward_return", "adv", "sector"]].copy()
    signals = signals.rename(columns={"date": "as_of"})
    signals["as_of"] = signals["as_of"].dt.strftime("%Y-%m-%d")
    if signals.empty:
        raise SystemExit("No signals survived filtering; check lookback/min-adv parameters")

    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    signals.to_csv(output_path, index=False)
    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--universe",
        default=None,
        help="Path to flagship universe CSV (default: <WRDS_DATA_ROOT>/universes/flagship_sector_neutral.csv)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination CSV for signals (e.g. artifacts/.../signals.csv)",
    )
    parser.add_argument("--lookback-months", type=int, default=DEFAULT_LOOKBACK_MONTHS)
    parser.add_argument("--skip-months", type=int, default=DEFAULT_SKIP_MONTHS)
    parser.add_argument("--min-adv", type=float, default=DEFAULT_MIN_ADV)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    universe_path = _wrds_universe_path(args.universe)
    output_path = Path(args.output)
    output = _build_signals(
        universe_path,
        output_path,
        lookback_months=int(args.lookback_months),
        skip_months=int(args.skip_months),
        min_adv=float(args.min_adv),
    )
    print(f"Signals written to {output}")


__all__ = ["_build_signals", "main"]


if __name__ == "__main__":
    main()

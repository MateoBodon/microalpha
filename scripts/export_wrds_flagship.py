#!/usr/bin/env python3
"""Export CRSP daily OHLCV + metadata for the flagship WRDS universe."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import wrds

START_DATE = "2000-01-03"
END_DATE = "2025-06-30"
REQUIRED_COLUMNS = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "shares_out",
    "ret",
)


def _wrds_root() -> Path:
    try:
        root = Path(os.environ["WRDS_DATA_ROOT"]).expanduser().resolve()
    except KeyError as exc:
        raise SystemExit("WRDS_DATA_ROOT is not set in the environment") from exc
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load_universe(root: Path) -> pd.Series:
    universe_csv = root / "universes/flagship_sector_neutral.csv"
    if not universe_csv.exists():
        raise SystemExit(f"Universe file missing: {universe_csv}")
    symbols = (
        pd.read_csv(universe_csv)["symbol"]
        .astype(str)
        .str.upper()
        .dropna()
        .unique()
    )
    if len(symbols) == 0:
        raise SystemExit("Universe file has no symbols")
    return pd.Series(symbols)


def _fetch_dsf(conn: wrds.Connection, tickers: list[str]) -> pd.DataFrame:
    query = """
        SELECT n.ticker,
               s.date,
               s.openprc AS open,
               s.bidlo AS low,
               s.askhi AS high,
               s.prc AS close,
               s.vol AS volume,
               s.shrout AS shares_out,
               s.ret
        FROM crsp.dsf s
        JOIN crsp.dsenames n
          ON s.permno = n.permno
         AND s.date BETWEEN n.namedt AND n.nameendt
        WHERE s.date BETWEEN %(start)s AND %(end)s
          AND n.ticker = ANY(%(tickers)s)
        ORDER BY n.ticker, s.date
    """
    params = {"start": START_DATE, "end": END_DATE, "tickers": tickers}
    data = conn.raw_sql(query, params=params, date_cols=["date"])
    if data.empty:
        raise SystemExit("WRDS query returned no rows; check credentials/universe")
    return data


def _write_per_symbol(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for ticker, frame in df.groupby("ticker"):
        path = out_dir / f"{ticker}.csv"
        frame = frame.sort_values("date").assign(timestamp=frame["date"].astype("datetime64[ns]"))
        payload = frame[["timestamp", "open", "high", "low", "close", "volume", "shares_out", "ret"]]
        payload.to_csv(path, index=False)
        missing = [col for col in REQUIRED_COLUMNS if col not in payload.columns]
        if missing:
            raise SystemExit(f"Missing required columns {missing} when writing {path}")


def _write_metadata(dsf: pd.DataFrame, meta_csv: Path) -> None:
    latest = dsf.sort_values("date").groupby("ticker").tail(1).copy()
    latest["market_cap"] = latest["close"].abs() * latest["shares_out"].abs()
    latest = latest.rename(
        columns={
            "ticker": "symbol",
            "date": "last_date",
            "close": "last_price",
            "shares_out": "last_shares_out",
        }
    )
    latest["sector"] = "UNKNOWN"
    meta_csv.parent.mkdir(parents=True, exist_ok=True)
    latest[
        [
            "symbol",
            "last_date",
            "last_price",
            "last_shares_out",
            "market_cap",
            "sector",
        ]
    ].to_csv(meta_csv, index=False)


def main() -> None:
    root = _wrds_root()
    tickers = _load_universe(root).tolist()
    print(f"Universe tickers: {len(tickers)}")

    conn = wrds.Connection(wrds_username=os.environ.get("WRDS_USERNAME"))
    try:
        dsf = _fetch_dsf(conn, tickers)
        _write_per_symbol(dsf, root / "crsp/daily_csv")
        _write_metadata(dsf, root / "meta/crsp_security_metadata.csv")
    finally:
        conn.close()

    print("Export complete ->", root)


if __name__ == "__main__":
    main()

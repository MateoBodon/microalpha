#!/usr/bin/env python3
"""Export CRSP daily OHLCV + metadata for the flagship WRDS universe."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as pa_ds
import wrds

from microalpha.wrds import WRDS_HOST, has_pgpass_credentials, pgpass_path

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
    "dlret",
    "total_return",
)
CSV_SUBDIR = "crsp/daily_csv"
PARQUET_SUBDIR = "crsp/dsf"
META_SUBDIR = "meta"
REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "data/wrds/manifest.json"

GICS_SECTORS = {
    "10": "Energy",
    "15": "Materials",
    "20": "Industrials",
    "25": "Consumer Discretionary",
    "30": "Consumer Staples",
    "35": "Health Care",
    "40": "Financials",
    "45": "Information Technology",
    "50": "Communication Services",
    "55": "Utilities",
    "60": "Real Estate",
}


@dataclass
class ExportStats:
    rows: int
    start: str
    end: str


def _wrds_root() -> Path:
    raw = os.environ.get("WRDS_DATA_ROOT")
    if not raw:
        raise SystemExit("WRDS_DATA_ROOT is not set in the environment")
    root = Path(raw).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _ensure_pgpass() -> None:
    if has_pgpass_credentials():
        return
    path = pgpass_path()
    if not path.exists():
        raise SystemExit(f"Expected WRDS credentials via {path}")
    try:
        mode = path.stat().st_mode & 0o777
    except OSError as exc:  # pragma: no cover - filesystem edge case
        raise SystemExit(f"Unable to stat {path}: {exc}") from exc
    raise SystemExit(f"{path} must contain WRDS entry with 600 perms (found {oct(mode)})")


def _resolve_wrds_username() -> str | None:
    env_user = os.environ.get("WRDS_USERNAME")
    if env_user:
        return env_user
    path = pgpass_path()
    if not path.exists():
        return None
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            fields = stripped.split(":")
            if len(fields) < 4:
                continue
            host_field = fields[0]
            if host_field in {"*", WRDS_HOST} or host_field.endswith("wharton.upenn.edu"):
                return fields[3]
    except OSError:  # pragma: no cover - filesystem edge cases
        return None
    return None


def _load_universe(root: Path) -> list[str]:
    universe_csv = root / "universes/flagship_sector_neutral.csv"
    if not universe_csv.exists():
        raise SystemExit(f"Universe file missing: {universe_csv}")
    symbols = (
        pd.read_csv(universe_csv)["symbol"].astype(str).str.upper().dropna().unique().tolist()
    )
    if not symbols:
        raise SystemExit("Universe file has no symbols")
    return symbols


def _fetch_dsf(conn: wrds.Connection, tickers: list[str]) -> pd.DataFrame:
    query = """
        SELECT n.ticker,
               s.permno,
               s.permco,
               n.exchcd,
               n.shrcd,
               n.siccd,
               s.date,
               s.openprc AS open,
               s.bidlo AS low,
               s.askhi AS high,
               s.prc AS close,
               s.vol AS volume,
               s.shrout AS shares_out,
               s.ret,
               dl.dlret
        FROM crsp.dsf s
        JOIN crsp.dsenames n
          ON s.permno = n.permno
         AND s.date BETWEEN n.namedt AND COALESCE(n.nameendt, '9999-12-31')
        LEFT JOIN crsp.dsedelist dl
          ON s.permno = dl.permno
         AND s.date = dl.dlstdt
        WHERE s.date BETWEEN %(start)s AND %(end)s
          AND n.ticker = ANY(%(tickers)s)
        ORDER BY n.ticker, s.date
    """
    params = {"start": START_DATE, "end": END_DATE, "tickers": tickers}
    data = conn.raw_sql(query, params=params, date_cols=["date"])
    if data.empty:
        raise SystemExit("WRDS query returned no rows; check credentials/universe")
    return data


def _fetch_gics(conn: wrds.Connection, permnos: Iterable[int]) -> pd.DataFrame:
    permnos = list({int(p) for p in permnos})
    if not permnos:
        return pd.DataFrame()
    query = """
        SELECT l.lpermno AS permno,
               l.gvkey,
               l.linkdt,
               l.linkenddt,
               c.gsector,
               c.gsubind
        FROM crsp.ccmxpf_linktable l
        JOIN comp.company c ON l.gvkey = c.gvkey
        WHERE l.lpermno = ANY(%(permnos)s)
          AND l.linktype IN ('LC','LN','LU','LX')
          AND l.linkprim IN ('C','P')
          AND COALESCE(l.linkenddt, '9999-12-31') >= %(start)s::date
          AND COALESCE(l.linkdt, '1900-01-01') <= %(end)s::date
        ORDER BY l.lpermno, COALESCE(l.linkenddt, '9999-12-31') DESC
    """
    params = {"permnos": permnos, "start": START_DATE, "end": END_DATE}
    return conn.raw_sql(query, params=params, date_cols=["linkdt", "linkenddt"])


def _apply_return_logic(dsf: pd.DataFrame) -> pd.DataFrame:
    df = dsf.copy()
    df["ret"] = pd.to_numeric(df["ret"], errors="coerce")
    df["dlret"] = pd.to_numeric(df["dlret"], errors="coerce")
    ret = df["ret"].fillna(0.0)
    dlret = df["dlret"].fillna(0.0)
    df["total_return"] = (1.0 + ret) * (1.0 + dlret) - 1.0
    df["timestamp"] = pd.to_datetime(df["date"])
    return df


def _write_per_symbol(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for ticker, frame in df.groupby("ticker"):
        path = out_dir / f"{ticker}.csv"
        payload = frame[[*REQUIRED_COLUMNS]].copy()
        payload.to_csv(path, index=False)
        missing = [col for col in REQUIRED_COLUMNS if col not in payload.columns]
        if missing:
            raise SystemExit(f"Missing required columns {missing} when writing {path}")


def _write_parquet(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset = df.copy()
    dataset["year"] = dataset["timestamp"].dt.year.astype(int)
    dataset["symbol"] = dataset["ticker"].astype(str)
    columns = [
        "timestamp",
        "symbol",
        "permno",
        "permco",
        "exchcd",
        "shrcd",
        "siccd",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "shares_out",
        "ret",
        "dlret",
        "total_return",
    ]
    table = pa.Table.from_pandas(dataset[columns + ["year"]], preserve_index=False)
    partitioning = pa_ds.partitioning(
        pa.schema([("year", pa.int16()), ("symbol", pa.string())]),
        flavor="hive",
    )
    pa_ds.write_dataset(
        table,
        base_dir=str(out_dir),
        format="parquet",
        partitioning=partitioning,
        existing_data_behavior="overwrite_or_ignore",
    )


def _map_gics(code: float | int | str | None) -> str:
    if code is None or code is pd.NA:
        return "UNKNOWN"
    if isinstance(code, float) and pd.isna(code):
        return "UNKNOWN"
    if isinstance(code, str) and not code.strip():
        return "UNKNOWN"
    try:
        text = str(int(float(code))).zfill(2)
    except (TypeError, ValueError):
        return "UNKNOWN"
    return GICS_SECTORS.get(text[:2], "UNKNOWN")


def _write_metadata(dsf: pd.DataFrame, gics_df: pd.DataFrame, meta_path: Path) -> pd.DataFrame:
    latest = dsf.sort_values("date").groupby("ticker").tail(1).copy()
    latest["market_cap"] = latest["close"].abs() * latest["shares_out"].abs()
    gics_df = gics_df.rename(columns={"gsector": "gics_sector"}) if not gics_df.empty else gics_df
    latest = latest.merge(gics_df[["permno", "gics_sector"]], on="permno", how="left")
    latest["sector"] = latest["gics_sector"].apply(_map_gics)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "ticker",
        "permno",
        "permco",
        "exchcd",
        "shrcd",
        "siccd",
        "gics_sector",
        "sector",
        "date",
        "close",
        "shares_out",
        "market_cap",
    ]
    payload = latest[columns].rename(
        columns={
            "ticker": "symbol",
            "date": "last_date",
            "close": "last_price",
            "shares_out": "last_shares_out",
        }
    )
    payload.to_csv(meta_path, index=False)
    return payload


def _write_manifest(stats: ExportStats, num_symbols: int, csv_dir: Path, parquet_dir: Path, meta_path: Path) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "window": {"start": stats.start, "end": stats.end},
        "rows": stats.rows,
        "symbols": num_symbols,
        "outputs": {
            "csv_root": str(csv_dir),
            "parquet_root": str(parquet_dir),
            "metadata_csv": str(meta_path),
        },
    }
    MANIFEST_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    _ensure_pgpass()
    root = _wrds_root()
    tickers = _load_universe(root)
    print(f"Universe tickers: {len(tickers)}")

    conn = wrds.Connection(wrds_username=_resolve_wrds_username())
    try:
        dsf = _fetch_dsf(conn, tickers)
        dsf = _apply_return_logic(dsf)
        gics_df = _fetch_gics(conn, dsf["permno"].unique())
    finally:
        conn.close()

    csv_dir = root / CSV_SUBDIR
    parquet_dir = root / PARQUET_SUBDIR
    meta_path = root / META_SUBDIR / "crsp_security_metadata.csv"

    _write_per_symbol(dsf, csv_dir)
    _write_parquet(dsf, parquet_dir)
    metadata = _write_metadata(dsf, gics_df, meta_path)

    stats = ExportStats(
        rows=int(len(dsf)),
        start=str(dsf["date"].min().date()),
        end=str(dsf["date"].max().date()),
    )
    _write_manifest(stats, metadata.shape[0], csv_dir, parquet_dir, meta_path)
    print("Export complete ->", root)


if __name__ == "__main__":
    main()

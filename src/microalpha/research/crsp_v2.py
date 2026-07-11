"""CRSP CIZ/DSF-v2 provenance and portfolio-construction primitives.

The full flagship adapter uses these functions to keep source verification,
point-in-time identity resolution, delisting semantics, universe construction,
and capacity accounting independently testable.  Nothing in this module reads
the sealed holdout unless a caller explicitly supplies those rows.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
import yaml


class CRSPV2Error(ValueError):
    """Raised when a CRSP-v2 evidence or integrity contract is violated."""


def sha256_file(path: str | Path, *, chunk_size: int = 1 << 20) -> str:
    """Return a streaming SHA-256 digest without loading the file into memory."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def load_protocol(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate a flagship protocol YAML document."""

    protocol_path = Path(path).expanduser().resolve()
    payload = yaml.safe_load(protocol_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CRSPV2Error("Flagship protocol must be a YAML mapping")
    if payload.get("schema_version") != "microalpha-flagship-protocol/v1":
        raise CRSPV2Error("Unsupported flagship protocol schema")
    if not payload.get("protocol_id"):
        raise CRSPV2Error("Flagship protocol is missing protocol_id")
    return payload


def protocol_sha256(path: str | Path) -> str:
    """Hash the exact protocol bytes used for a decision or derived artifact."""

    return sha256_file(path)


def _assert_digest(path: Path, expected: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise CRSPV2Error(
            f"SHA-256 mismatch for {path}: expected {expected}, observed {observed}"
        )


def _load_json_manifest(spec: Mapping[str, Any]) -> tuple[Path, dict[str, Any]]:
    path = Path(str(spec["path"])).expanduser().resolve()
    if not path.is_file():
        raise CRSPV2Error(f"Manifest not found: {path}")
    _assert_digest(path, str(spec["sha256"]))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CRSPV2Error(f"Manifest must contain a JSON object: {path}")
    return path, payload


def _item_path(item: Mapping[str, Any]) -> Path:
    path = Path(str(item.get("path") or "")).expanduser().resolve()
    if not path.is_file():
        raise CRSPV2Error(f"Manifested data file not found: {path}")
    expected_size = int(item.get("size_bytes") or 0)
    observed_size = path.stat().st_size
    if expected_size and observed_size != expected_size:
        raise CRSPV2Error(
            f"Size mismatch for {path}: expected {expected_size}, observed "
            f"{observed_size}"
        )
    return path


def _gzip_header(path: Path) -> list[str]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        row = next(csv.reader([handle.readline()]), [])
    return [value.strip() for value in row]


def _assert_columns(path: Path, required: Sequence[str]) -> None:
    header = set(_gzip_header(path))
    missing = sorted(set(required).difference(header))
    if missing:
        raise CRSPV2Error(f"{path} is missing required columns: {missing}")


def _items_for(
    manifest: Mapping[str, Any], table: str, *, status: str = "ok"
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in manifest.get("items", [])
        if item.get("table") == table and item.get("status") == status
    ]


def _audit_primary_wrds(spec: Mapping[str, Any]) -> dict[str, Any]:
    manifest_path, manifest = _load_json_manifest(spec)
    table = str(spec["table"])
    partition_spec = spec["partitions"]
    start = int(partition_spec["start"])
    end = int(partition_spec["end"])
    expected_partitions = [f"year={year}" for year in range(start, end + 1)]
    items = _items_for(manifest, table)
    by_partition: dict[str, dict[str, Any]] = {}
    for item in items:
        partition = str(item.get("partition"))
        if partition in by_partition:
            raise CRSPV2Error(f"Duplicate {table} partition: {partition}")
        by_partition[partition] = item
    missing = sorted(set(expected_partitions).difference(by_partition))
    if missing:
        raise CRSPV2Error(f"Missing {table} partitions: {missing}")
    selected = [by_partition[partition] for partition in expected_partitions]
    paths: list[Path] = []
    for item in selected:
        path = _item_path(item)
        _assert_columns(path, list(spec["required_columns"]))
        paths.append(path)
    rows = sum(int(item.get("rows") or 0) for item in selected)
    compressed_bytes = sum(int(item.get("size_bytes") or 0) for item in selected)
    expected_rows = int(partition_spec["expected_rows"])
    expected_bytes = int(partition_spec["expected_compressed_bytes"])
    if rows != expected_rows:
        raise CRSPV2Error(f"{table} row total {rows} != expected {expected_rows}")
    if compressed_bytes != expected_bytes:
        raise CRSPV2Error(
            f"{table} compressed bytes {compressed_bytes} != expected "
            f"{expected_bytes}"
        )
    if len(selected) != int(partition_spec["expected_count"]):
        raise CRSPV2Error("Unexpected primary partition count")

    side_summary: dict[str, Any] = {}
    for side_spec in spec.get("side_tables", []):
        side_table = str(side_spec["table"])
        side_items = _items_for(manifest, side_table)
        if len(side_items) != 1:
            raise CRSPV2Error(
                f"Expected one successful {side_table} item, found {len(side_items)}"
            )
        side_item = side_items[0]
        side_path = _item_path(side_item)
        _assert_columns(side_path, list(side_spec["required_columns"]))
        rows_observed = int(side_item.get("rows") or 0)
        if rows_observed != int(side_spec["expected_rows"]):
            raise CRSPV2Error(f"Unexpected {side_table} row count")
        side_summary[side_table] = {
            "path": str(side_path),
            "rows": rows_observed,
            "size_bytes": side_path.stat().st_size,
        }

    return {
        "manifest": str(manifest_path),
        "manifest_sha256": str(spec["sha256"]),
        "global_failure_count": int(manifest.get("failure_count") or 0),
        "table": table,
        "partition_count": len(selected),
        "partition_start": expected_partitions[0],
        "partition_end": expected_partitions[-1],
        "rows": rows,
        "compressed_bytes": compressed_bytes,
        "paths": [str(path) for path in paths],
        "side_tables": side_summary,
    }


def _audit_single_wrds_table(spec: Mapping[str, Any]) -> dict[str, Any]:
    manifest_path, manifest = _load_json_manifest(spec)
    table = str(spec["table"])
    items = _items_for(manifest, table)
    if len(items) != 1:
        raise CRSPV2Error(f"Expected one successful {table} item, found {len(items)}")
    item = items[0]
    path = _item_path(item)
    _assert_columns(path, list(spec["required_columns"]))
    rows = int(item.get("rows") or 0)
    if rows != int(spec["expected_rows"]):
        raise CRSPV2Error(f"Unexpected {table} row count")
    return {
        "manifest": str(manifest_path),
        "manifest_sha256": str(spec["sha256"]),
        "global_failure_count": int(manifest.get("failure_count") or 0),
        "table": table,
        "path": str(path),
        "rows": rows,
        "size_bytes": path.stat().st_size,
    }


def _audit_public_sources(spec: Mapping[str, Any]) -> dict[str, Any]:
    manifest_spec = spec["acquisition_manifest"]
    manifest_path = Path(str(manifest_spec["path"])).expanduser().resolve()
    if not manifest_path.is_file():
        raise CRSPV2Error(f"Public acquisition manifest not found: {manifest_path}")
    _assert_digest(manifest_path, str(manifest_spec["sha256"]))
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        manifest_rows = list(csv.DictReader(handle))
    rows_by_path = {
        str(Path(row["local_path"]).resolve()): row for row in manifest_rows
    }

    files: list[dict[str, Any]] = []
    for file_spec in spec.get("files", []):
        path = Path(str(file_spec["path"])).expanduser().resolve()
        if not path.is_file():
            raise CRSPV2Error(f"Public source not found: {path}")
        _assert_digest(path, str(file_spec["sha256"]))
        manifest_row = rows_by_path.get(str(path))
        if manifest_row is None:
            raise CRSPV2Error(f"Public source is absent from manifest: {path}")
        if manifest_row.get("sha256") != str(file_spec["sha256"]):
            raise CRSPV2Error(f"Manifest digest disagrees for {path}")
        if manifest_row.get("validation_status") != "downloaded_hash_ok":
            raise CRSPV2Error(f"Public source lacks downloaded_hash_ok: {path}")
        files.append(
            {
                "role": str(file_spec["role"]),
                "path": str(path),
                "sha256": str(file_spec["sha256"]),
                "size_bytes": path.stat().st_size,
            }
        )
    return {
        "manifest": str(manifest_path),
        "manifest_sha256": str(manifest_spec["sha256"]),
        "files": files,
    }


def audit_source_protocol(path: str | Path) -> dict[str, Any]:
    """Verify all predeclared source manifests without reading data outcomes."""

    protocol_path = Path(path).expanduser().resolve()
    protocol = load_protocol(protocol_path)
    dataset = protocol["dataset"]
    wrds = dataset["wrds"]
    return {
        "protocol_id": str(protocol["protocol_id"]),
        "protocol_path": str(protocol_path),
        "protocol_sha256": protocol_sha256(protocol_path),
        "dataset_id": str(dataset["id"]),
        "primary": _audit_primary_wrds(wrds["primary_manifest"]),
        "market": _audit_single_wrds_table(wrds["market_manifest"]),
        "public": _audit_public_sources(dataset["public"]),
        "holdout_outcomes_read": False,
    }


def _window_bounds(
    protocol: Mapping[str, Any],
) -> list[tuple[str, pd.Timestamp, pd.Timestamp]]:
    windows = protocol["windows"]
    ordered: list[tuple[str, pd.Timestamp, pd.Timestamp]] = []
    for name in ("warmup", "training", "validation", "final_holdout"):
        window = windows[name]
        start = pd.Timestamp(window["start"])
        end = pd.Timestamp(window["end"])
        if end < start:
            raise CRSPV2Error(f"{name} ends before it starts")
        ordered.append((name, start, end))
    for previous, current in zip(ordered, ordered[1:]):
        if previous[2] >= current[1]:
            raise CRSPV2Error(
                f"Overlapping split windows: {previous[0]} and {current[0]}"
            )
    return ordered


def label_split(value: Any, protocol: Mapping[str, Any]) -> str:
    """Map a date to the exact manifest-bound campaign split."""

    timestamp = pd.Timestamp(value)
    for name, start, end in _window_bounds(protocol):
        if start <= timestamp <= end:
            return name
    return "outside"


def resolve_point_in_time_names(
    daily: pd.DataFrame,
    names: pd.DataFrame,
) -> pd.DataFrame:
    """Resolve exactly one stocknames-v2 row for each daily observation."""

    required_daily = {"permno", "dlycaldt"}
    required_names = {"permno", "namedt", "nameenddt"}
    if missing := required_daily.difference(daily.columns):
        raise CRSPV2Error(f"Daily rows missing columns: {sorted(missing)}")
    if missing := required_names.difference(names.columns):
        raise CRSPV2Error(f"Stocknames rows missing columns: {sorted(missing)}")

    left = daily.copy().reset_index(drop=True)
    if left.duplicated(["permno", "dlycaldt"]).any():
        raise CRSPV2Error("Daily permno/date keys are not unique")
    left["_row_id"] = np.arange(len(left))
    left["dlycaldt"] = pd.to_datetime(left["dlycaldt"], errors="raise")

    right = names.copy()
    right["namedt"] = pd.to_datetime(right["namedt"], errors="raise")
    right["nameenddt"] = pd.to_datetime(right["nameenddt"], errors="coerce")
    name_columns = [column for column in right.columns if column != "permno"]
    right = right.rename(columns={column: f"name_{column}" for column in name_columns})

    joined = left.merge(right, on="permno", how="left", validate="many_to_many")
    within = joined["name_namedt"].le(joined["dlycaldt"])
    within &= joined["name_nameenddt"].isna() | joined["name_nameenddt"].ge(
        joined["dlycaldt"]
    )
    matched = joined.loc[within].copy()
    counts = matched.groupby("_row_id").size().reindex(left["_row_id"], fill_value=0)
    bad = counts[counts != 1]
    if not bad.empty:
        raise CRSPV2Error(
            f"Point-in-time stocknames match count is not one for {len(bad)} rows"
        )

    compare_columns = (
        "ticker",
        "primaryexch",
        "conditionaltype",
        "tradingstatusflg",
        "sharetype",
        "securitytype",
        "securitysubtype",
        "usincflg",
        "siccd",
    )
    for column in compare_columns:
        name_column = f"name_{column}"
        if column not in matched.columns or name_column not in matched.columns:
            continue
        if column == "siccd":
            lhs = pd.to_numeric(matched[column], errors="coerce")
            rhs = pd.to_numeric(matched[name_column], errors="coerce")
        else:
            lhs = matched[column].astype("string")
            rhs = matched[name_column].astype("string")
        mismatch = lhs.notna() & rhs.notna() & lhs.ne(rhs)
        if mismatch.any():
            raise CRSPV2Error(
                f"Daily and point-in-time stocknames disagree for {column}"
            )
    return (
        matched.sort_values("_row_id").drop(columns=["_row_id"]).reset_index(drop=True)
    )


def reconcile_ciz_delisting_returns(
    daily: pd.DataFrame,
    delists: pd.DataFrame,
    *,
    atol: float = 5e-7,
) -> pd.DataFrame:
    """Audit CIZ delisting pseudo-days and use ``dlyret`` exactly once.

    CRSP CIZ represents a delisting return on a ``dlydelflg=Y`` pseudo-day.
    ``stkdelists.delret`` is therefore a reconciliation source, not an
    additional return to compound.
    """

    required_daily = {"permno", "dlycaldt", "dlydelflg", "dlyret"}
    required_delists = {"permno", "deldlydt", "delret"}
    if missing := required_daily.difference(daily.columns):
        raise CRSPV2Error(f"Daily rows missing columns: {sorted(missing)}")
    if missing := required_delists.difference(delists.columns):
        raise CRSPV2Error(f"Delisting rows missing columns: {sorted(missing)}")

    frame = daily.copy()
    frame["dlycaldt"] = pd.to_datetime(frame["dlycaldt"], errors="raise")
    if frame.duplicated(["permno", "dlycaldt"]).any():
        raise CRSPV2Error("Daily permno/date keys are not unique")

    audit = delists.copy()
    audit["deldlydt"] = pd.to_datetime(audit["deldlydt"], errors="coerce")
    audit = audit.dropna(subset=["deldlydt"])
    if audit.duplicated(["permno", "deldlydt"]).any():
        raise CRSPV2Error("Delisting permno/deldlydt keys are not unique")
    columns = ["permno", "deldlydt", "delret"]
    for optional in ("delretmisstype", "delistingdt"):
        if optional in audit.columns:
            columns.append(optional)
    audit = audit[columns]

    merged = frame.merge(
        audit,
        left_on=["permno", "dlycaldt"],
        right_on=["permno", "deldlydt"],
        how="left",
        validate="one_to_one",
    )
    flagged = merged["dlydelflg"].astype("string").eq("Y")
    if merged.loc[flagged, "deldlydt"].isna().any():
        raise CRSPV2Error("A CIZ delisting pseudo-day lacks a stkdelists match")

    source = pd.to_numeric(merged.loc[flagged, "dlyret"], errors="coerce")
    audit_return = pd.to_numeric(merged.loc[flagged, "delret"], errors="coerce")
    one_missing = source.isna() ^ audit_return.isna()
    if one_missing.any():
        raise CRSPV2Error("CIZ dlyret and stkdelists.delret missingness disagrees")
    numeric = source.notna() & audit_return.notna()
    if numeric.any() and not np.allclose(
        source.loc[numeric], audit_return.loc[numeric], rtol=0.0, atol=atol
    ):
        raise CRSPV2Error("CIZ dlyret and stkdelists.delret disagree")

    if "dlyretmissflg" in merged.columns and "delretmisstype" in merged.columns:
        lhs = merged.loc[flagged, "dlyretmissflg"].astype("string")
        rhs = merged.loc[flagged, "delretmisstype"].astype("string")
        mismatch = lhs.notna() & rhs.notna() & lhs.ne(rhs)
        if mismatch.any():
            raise CRSPV2Error("CIZ and stkdelists missing-return codes disagree")

    merged["total_return"] = pd.to_numeric(merged["dlyret"], errors="coerce")
    merged["delisting_return_reconciled"] = flagged
    return merged


FF12_LABELS = {
    1: "NoDur",
    2: "Durbl",
    3: "Manuf",
    4: "Enrgy",
    5: "Chems",
    6: "BusEq",
    7: "Telcm",
    8: "Utils",
    9: "Shops",
    10: "Hlth",
    11: "Money",
    12: "Other",
}


def _in_ranges(value: int, ranges: Sequence[tuple[int, int]]) -> bool:
    return any(lower <= value <= upper for lower, upper in ranges)


def ff12_industry(sic: Any) -> str:
    """Map a SIC code to the standard Fama-French 12-industry grouping."""

    try:
        value = int(float(sic))
    except (TypeError, ValueError):
        return FF12_LABELS[12]
    groups: list[tuple[int, Sequence[tuple[int, int]]]] = [
        (
            1,
            (
                (100, 999),
                (2000, 2399),
                (2700, 2749),
                (2770, 2799),
                (3100, 3199),
                (3940, 3989),
            ),
        ),
        (
            2,
            (
                (2500, 2519),
                (2590, 2599),
                (3630, 3659),
                (3710, 3711),
                (3714, 3714),
                (3716, 3716),
                (3750, 3751),
                (3792, 3792),
                (3900, 3939),
                (3990, 3999),
            ),
        ),
        (
            3,
            (
                (2520, 2589),
                (2600, 2699),
                (2750, 2769),
                (3000, 3099),
                (3200, 3569),
                (3580, 3629),
                (3700, 3709),
                (3712, 3713),
                (3715, 3715),
                (3717, 3749),
                (3752, 3791),
                (3793, 3799),
                (3830, 3839),
                (3860, 3899),
            ),
        ),
        (4, ((1200, 1399), (2900, 2999))),
        (5, ((2800, 2829), (2840, 2899))),
        (6, ((3570, 3579), (3660, 3692), (3694, 3699), (3810, 3829), (7370, 7379))),
        (7, ((4800, 4899),)),
        (8, ((4900, 4949),)),
        (9, ((5000, 5999), (7200, 7299), (7600, 7699))),
        (10, ((2830, 2839), (3693, 3693), (3840, 3859), (8000, 8099))),
        (11, ((6000, 6999),)),
    ]
    for group, ranges in groups:
        if _in_ranges(value, ranges):
            return FF12_LABELS[group]
    return FF12_LABELS[12]


def build_point_in_time_universe(
    frame: pd.DataFrame,
    rules: Mapping[str, Any],
) -> pd.DataFrame:
    """Apply lagged point-in-time eligibility rules to a formation snapshot."""

    required = {
        "permno",
        "formation_date",
        "sharetype",
        "securitytype",
        "securitysubtype",
        "usincflg",
        "primaryexch",
        "conditionaltype",
        "tradingstatusflg",
        "price",
        "market_cap_usd",
        "adv_60_usd",
        "history_months",
        "siccd",
    }
    if missing := required.difference(frame.columns):
        raise CRSPV2Error(f"Universe frame missing columns: {sorted(missing)}")
    if frame.duplicated(["formation_date", "permno"]).any():
        raise CRSPV2Error("Formation-date/permno keys are not unique")

    eligible = frame.copy()
    categorical = (
        "sharetype",
        "securitytype",
        "securitysubtype",
        "usincflg",
        "primaryexch",
        "conditionaltype",
        "tradingstatusflg",
    )
    mask = pd.Series(True, index=eligible.index)
    for column in categorical:
        mask &= eligible[column].isin(list(rules[column]))
    mask &= pd.to_numeric(eligible["price"], errors="coerce").ge(
        float(rules["minimum_price"])
    )
    mask &= pd.to_numeric(eligible["market_cap_usd"], errors="coerce").ge(
        float(rules["minimum_market_cap_usd"])
    )
    mask &= pd.to_numeric(eligible["adv_60_usd"], errors="coerce").ge(
        float(rules["minimum_60d_median_dollar_volume_usd"])
    )
    mask &= pd.to_numeric(eligible["history_months"], errors="coerce").ge(
        int(rules["minimum_return_history_months"])
    )
    eligible = eligible.loc[mask].copy()
    eligible["industry"] = eligible["siccd"].map(ff12_industry)
    return eligible.sort_values(["formation_date", "industry", "permno"])


def industry_neutral_weights(
    snapshot: pd.DataFrame,
    *,
    score_column: str = "score",
    weighting: str = "equal",
    volatility_column: str = "volatility_126d",
    sleeve_fraction: float = 0.10,
    target_gross: float = 1.0,
    max_industry_gross_weight: float,
    max_single_name_weight: float | None = None,
) -> pd.Series:
    """Construct industry-neutral weights under required name/industry caps."""

    required = {"permno", "industry", score_column}
    if missing := required.difference(snapshot.columns):
        raise CRSPV2Error(f"Snapshot missing columns: {sorted(missing)}")
    if snapshot["permno"].duplicated().any():
        raise CRSPV2Error("Snapshot permno keys are not unique")
    if weighting not in {"equal", "inverse_vol_126d"}:
        raise CRSPV2Error(f"Unsupported weighting: {weighting}")
    if weighting == "inverse_vol_126d" and volatility_column not in snapshot:
        raise CRSPV2Error(f"Snapshot missing {volatility_column}")
    if not 0.0 < sleeve_fraction <= 0.5:
        raise CRSPV2Error("sleeve_fraction must be in (0, 0.5]")
    if target_gross <= 0.0:
        raise CRSPV2Error("target_gross must be positive")
    if max_industry_gross_weight <= 0.0:
        raise CRSPV2Error("max_industry_gross_weight must be positive")
    if max_single_name_weight is not None and max_single_name_weight <= 0.0:
        raise CRSPV2Error("max_single_name_weight must be positive")

    groups: list[tuple[str, pd.DataFrame, pd.DataFrame, int]] = []
    for industry, group in snapshot.groupby("industry", sort=True):
        ranked = group.dropna(subset=[score_column]).sort_values(
            [score_column, "permno"], ascending=[False, True]
        )
        count = len(ranked)
        sleeve_count = min(max(int(math.floor(count * sleeve_fraction)), 1), count // 2)
        if sleeve_count < 1:
            continue
        longs = ranked.head(sleeve_count)
        shorts = ranked.tail(sleeve_count)
        groups.append((str(industry), longs, shorts, count))
    if not groups:
        raise CRSPV2Error("No industry contains enough securities for two sleeves")

    industry_raw = pd.Series(
        {industry: float(count) for industry, _, _, count in groups}, dtype=float
    )
    industry_caps = pd.Series(
        {
            industry: min(
                max_industry_gross_weight,
                (
                    2.0 * len(longs) * max_single_name_weight
                    if max_single_name_weight is not None
                    else max_industry_gross_weight
                ),
            )
            for industry, longs, _, _ in groups
        },
        dtype=float,
    )
    industry_allocations = _variable_capped_allocation(
        industry_raw,
        industry_caps,
        total=target_gross,
        cap_label="Industry gross/name",
    )
    weights: dict[Any, float] = {}
    for industry, longs, shorts, _ in groups:
        industry_gross = float(industry_allocations.loc[industry])
        for sleeve, sign in ((longs, 1.0), (shorts, -1.0)):
            if weighting == "equal":
                raw = pd.Series(1.0, index=sleeve.index)
            else:
                volatility = pd.to_numeric(sleeve[volatility_column], errors="coerce")
                if volatility.isna().any() or volatility.le(0.0).any():
                    raise CRSPV2Error("Inverse-volatility inputs must be positive")
                raw = 1.0 / volatility
            allocation = _capped_allocation(
                raw,
                total=industry_gross * 0.5,
                cap=max_single_name_weight,
                cap_label="Single-name",
            )
            for row_index, weight in allocation.items():
                permno = sleeve.loc[row_index, "permno"]
                weights[permno] = sign * float(weight)

    result = pd.Series(weights, dtype=float).sort_index()
    if not np.isclose(result.abs().sum(), target_gross, atol=1e-12):
        raise CRSPV2Error("Constructed weights miss target gross exposure")
    industry_by_permno = snapshot.set_index("permno")["industry"]
    industry_net = result.groupby(industry_by_permno.reindex(result.index)).sum()
    if not np.allclose(industry_net.to_numpy(), 0.0, atol=1e-12):
        raise CRSPV2Error("Constructed weights are not industry neutral")
    industry_gross = result.abs().groupby(
        industry_by_permno.reindex(result.index)
    ).sum()
    if industry_gross.max() > max_industry_gross_weight + 1e-12:
        raise CRSPV2Error("Constructed weights exceed the industry gross cap")
    if max_single_name_weight is not None and result.abs().max() > (
        max_single_name_weight + 1e-12
    ):
        raise CRSPV2Error("Constructed weights exceed the single-name cap")
    return result


def _capped_allocation(
    raw: pd.Series,
    *,
    total: float,
    cap: float | None,
    cap_label: str,
) -> pd.Series:
    """Normalize positive scores to a target, redistributing any capped excess."""

    values = pd.to_numeric(raw, errors="coerce").astype(float)
    if values.isna().any() or values.le(0.0).any() or total < 0.0:
        raise CRSPV2Error("Allocation inputs must be finite and positive")
    if cap is None:
        return values / values.sum() * total
    if len(values) * cap + 1e-12 < total:
        raise CRSPV2Error(f"{cap_label} cap is infeasible for the allocation")

    allocation = pd.Series(0.0, index=values.index)
    remaining = values.index
    remaining_total = float(total)
    while len(remaining):
        proposed = values.loc[remaining] / values.loc[remaining].sum() * remaining_total
        over = proposed.gt(cap + 1e-15)
        if not over.any():
            allocation.loc[remaining] = proposed
            break
        capped = proposed.index[over]
        allocation.loc[capped] = cap
        remaining_total -= cap * len(capped)
        remaining = remaining.difference(capped, sort=False)
    if not np.isclose(allocation.sum(), total, atol=1e-12):
        raise CRSPV2Error("Capped allocation misses its sleeve target")
    return allocation


def _variable_capped_allocation(
    raw: pd.Series,
    caps: pd.Series,
    *,
    total: float,
    cap_label: str,
) -> pd.Series:
    """Normalize positive scores under item-specific caps by water-filling."""

    values = pd.to_numeric(raw, errors="coerce").astype(float)
    limits = pd.to_numeric(caps.reindex(values.index), errors="coerce").astype(float)
    if (
        values.isna().any()
        or values.le(0.0).any()
        or limits.isna().any()
        or limits.le(0.0).any()
        or total < 0.0
    ):
        raise CRSPV2Error("Allocation inputs and variable caps must be positive")
    if float(limits.sum()) + 1e-12 < total:
        raise CRSPV2Error(f"{cap_label} caps are infeasible for the allocation")

    allocation = pd.Series(0.0, index=values.index)
    remaining = values.index
    remaining_total = float(total)
    while len(remaining):
        proposed = values.loc[remaining] / values.loc[remaining].sum() * remaining_total
        over = proposed.gt(limits.loc[remaining] + 1e-15)
        if not over.any():
            allocation.loc[remaining] = proposed
            break
        capped = proposed.index[over]
        allocation.loc[capped] = limits.loc[capped]
        remaining_total -= float(limits.loc[capped].sum())
        remaining = remaining.difference(capped, sort=False)
    if not np.isclose(allocation.sum(), total, atol=1e-12):
        raise CRSPV2Error("Variable-capped allocation misses its target")
    return allocation


def one_way_turnover(previous: pd.Series, target: pd.Series) -> float:
    """Return standard one-way turnover, one half of absolute weight changes."""

    index = previous.index.union(target.index)
    delta = target.reindex(index, fill_value=0.0) - previous.reindex(
        index, fill_value=0.0
    )
    return 0.5 * float(delta.abs().sum())


@dataclass(frozen=True)
class CapacityResult:
    executed_weights: pd.Series
    requested_turnover: float
    executed_turnover: float
    requested_trade_dollars: float
    executed_trade_dollars: float
    fill_ratio: float
    constrained_names: tuple[Any, ...]


def apply_trade_capacity(
    previous: pd.Series,
    target: pd.Series,
    adv_usd: pd.Series,
    *,
    capital_usd: float,
    max_participation: float,
    max_single_name_weight: float | None = None,
) -> CapacityResult:
    """Clip rebalance deltas to a percentage of lagged ADV and report turnover."""

    if capital_usd <= 0 or not 0.0 < max_participation <= 1.0:
        raise CRSPV2Error("Invalid capital or participation constraint")
    index = previous.index.union(target.index).union(adv_usd.index)
    previous_aligned = previous.reindex(index, fill_value=0.0).astype(float)
    target_aligned = target.reindex(index, fill_value=0.0).astype(float)
    if max_single_name_weight is not None:
        if max_single_name_weight <= 0.0:
            raise CRSPV2Error("max_single_name_weight must be positive")
        if target_aligned.abs().gt(max_single_name_weight + 1e-12).any():
            raise CRSPV2Error(
                "Target exceeds the single-name cap; cap it during construction"
            )
    adv = pd.to_numeric(adv_usd.reindex(index), errors="coerce")
    if adv.isna().any() or adv.lt(0.0).any():
        raise CRSPV2Error("ADV must be present and non-negative for every name")

    requested_delta = target_aligned - previous_aligned
    maximum_delta = adv * float(max_participation) / float(capital_usd)
    executed_delta = requested_delta.clip(lower=-maximum_delta, upper=maximum_delta)
    executed = previous_aligned + executed_delta
    constrained = tuple(index[executed_delta.abs() + 1e-15 < requested_delta.abs()])
    requested_dollars = float(requested_delta.abs().sum() * capital_usd)
    executed_dollars = float(executed_delta.abs().sum() * capital_usd)
    fill_ratio = executed_dollars / requested_dollars if requested_dollars else 1.0
    return CapacityResult(
        executed_weights=executed,
        requested_turnover=0.5 * float(requested_delta.abs().sum()),
        executed_turnover=0.5 * float(executed_delta.abs().sum()),
        requested_trade_dollars=requested_dollars,
        executed_trade_dollars=executed_dollars,
        fill_ratio=fill_ratio,
        constrained_names=constrained,
    )


def apply_constrained_trade_capacity(
    previous: pd.Series,
    target: pd.Series,
    adv_usd: pd.Series,
    industry: pd.Series,
    *,
    capital_usd: float,
    max_participation: float,
    max_single_name_weight: float,
    max_industry_gross_weight: float,
) -> CapacityResult:
    """Execute as close to target as capacity permits while preserving risk caps.

    The linear program minimizes absolute target tracking error subject to
    per-name participation bounds, the single-name cap, exact industry net
    neutrality, and the industry gross cap. This prevents independent clipping
    from turning a neutral target into an unintended directional portfolio.
    """

    try:
        from scipy.optimize import linprog
    except ImportError as exc:  # pragma: no cover - optional research dependency
        raise CRSPV2Error(
            "scipy is required for constrained CRSP-v2 execution"
        ) from exc
    if (
        capital_usd <= 0.0
        or not 0.0 < max_participation <= 1.0
        or max_single_name_weight <= 0.0
        or max_industry_gross_weight <= 0.0
    ):
        raise CRSPV2Error("Invalid constrained execution limits")

    index = previous.index.union(target.index).union(adv_usd.index)
    previous_aligned = previous.reindex(index, fill_value=0.0).astype(float)
    target_aligned = target.reindex(index, fill_value=0.0).astype(float)
    adv = pd.to_numeric(adv_usd.reindex(index), errors="coerce")
    groups = industry.reindex(index)
    if adv.isna().any() or adv.le(0.0).any():
        raise CRSPV2Error("Positive ADV is required for constrained execution")
    if groups.isna().any():
        raise CRSPV2Error("Point-in-time industry is required for every active name")
    if target_aligned.abs().gt(max_single_name_weight + 1e-12).any():
        raise CRSPV2Error("Target exceeds the single-name cap")

    maximum_delta = adv * float(max_participation) / float(capital_usd)
    lower = np.maximum(
        previous_aligned.to_numpy() - maximum_delta.to_numpy(),
        -max_single_name_weight,
    )
    upper = np.minimum(
        previous_aligned.to_numpy() + maximum_delta.to_numpy(),
        max_single_name_weight,
    )
    if np.any(lower > upper + 1e-15):
        raise CRSPV2Error("Capacity cannot restore an existing single-name cap breach")

    n = len(index)
    # Variables are executed weights x, target deviations d >= |x-target|,
    # and gross auxiliaries g >= |x|.
    objective = np.concatenate(
        [np.zeros(n), np.ones(n), np.full(n, 1e-9, dtype=float)]
    )
    rows: list[np.ndarray] = []
    rhs: list[float] = []
    target_values = target_aligned.to_numpy()
    for position in range(n):
        row = np.zeros(3 * n)
        row[position] = 1.0
        row[n + position] = -1.0
        rows.append(row)
        rhs.append(float(target_values[position]))

        row = np.zeros(3 * n)
        row[position] = -1.0
        row[n + position] = -1.0
        rows.append(row)
        rhs.append(float(-target_values[position]))

        row = np.zeros(3 * n)
        row[position] = 1.0
        row[2 * n + position] = -1.0
        rows.append(row)
        rhs.append(0.0)

        row = np.zeros(3 * n)
        row[position] = -1.0
        row[2 * n + position] = -1.0
        rows.append(row)
        rhs.append(0.0)

    unique_industries = sorted(str(value) for value in groups.unique())
    equality_rows: list[np.ndarray] = []
    for group in unique_industries:
        mask = groups.astype(str).eq(group).to_numpy()
        gross_row = np.zeros(3 * n)
        gross_row[2 * n :][mask] = 1.0
        rows.append(gross_row)
        rhs.append(float(max_industry_gross_weight))

        net_row = np.zeros(3 * n)
        net_row[:n][mask] = 1.0
        equality_rows.append(net_row)

    result = linprog(
        objective,
        A_ub=np.vstack(rows),
        b_ub=np.asarray(rhs),
        A_eq=np.vstack(equality_rows),
        b_eq=np.zeros(len(equality_rows)),
        bounds=[*(zip(lower, upper)), *([(0.0, None)] * (2 * n))],
        method="highs",
    )
    if not result.success:
        raise CRSPV2Error(f"Constrained execution is infeasible: {result.message}")

    executed = pd.Series(result.x[:n], index=index, dtype=float)
    executed.loc[executed.abs().lt(1e-14)] = 0.0
    delta = executed - previous_aligned
    requested_delta = target_aligned - previous_aligned
    requested_dollars = float(requested_delta.abs().sum() * capital_usd)
    executed_dollars = float(delta.abs().sum() * capital_usd)
    fill_ratio = executed_dollars / requested_dollars if requested_dollars else 1.0
    constrained = tuple(index[(executed - target_aligned).abs().gt(1e-10)])

    industry_net = executed.groupby(groups.astype(str)).sum()
    industry_gross = executed.abs().groupby(groups.astype(str)).sum()
    if industry_net.abs().max() > 1e-9:
        raise CRSPV2Error("Constrained execution missed industry neutrality")
    if industry_gross.max() > max_industry_gross_weight + 1e-9:
        raise CRSPV2Error("Constrained execution breached industry gross")
    if executed.abs().max() > max_single_name_weight + 1e-9:
        raise CRSPV2Error("Constrained execution breached the name cap")
    if (delta.abs() - maximum_delta).max() > 1e-9:
        raise CRSPV2Error("Constrained execution breached participation")

    return CapacityResult(
        executed_weights=executed,
        requested_turnover=0.5 * float(requested_delta.abs().sum()),
        executed_turnover=0.5 * float(delta.abs().sum()),
        requested_trade_dollars=requested_dollars,
        executed_trade_dollars=executed_dollars,
        fill_ratio=fill_ratio,
        constrained_names=constrained,
    )


def estimate_rebalance_cost(
    previous: pd.Series,
    executed: pd.Series,
    adv_usd: pd.Series,
    full_spread_bps: pd.Series,
    *,
    capital_usd: float,
    commission_bps_each_side: float,
    impact_bps_at_one_percent_adv: float,
    annual_short_borrow_bps: float,
    holding_days: int,
    fallback_full_spread_bps: float | None = None,
) -> dict[str, float]:
    """Estimate commission, half-spread, square-root impact, and borrow costs."""

    index = previous.index.union(executed.index)
    previous_aligned = previous.reindex(index, fill_value=0.0).astype(float)
    executed_aligned = executed.reindex(index, fill_value=0.0).astype(float)
    adv = pd.to_numeric(adv_usd.reindex(index), errors="coerce")
    spreads = pd.to_numeric(full_spread_bps.reindex(index), errors="coerce")
    if adv.isna().any() or adv.le(0.0).any():
        raise CRSPV2Error("Positive ADV is required for cost estimation")
    missing_spreads = spreads.isna()
    if missing_spreads.any():
        if fallback_full_spread_bps is None:
            raise CRSPV2Error("Missing spreads require a predeclared fallback")
        spreads = spreads.fillna(float(fallback_full_spread_bps))
    if spreads.lt(0.0).any():
        raise CRSPV2Error("Non-negative full spreads are required")

    trade_dollars = (executed_aligned - previous_aligned).abs() * capital_usd
    participation = trade_dollars / adv
    commission = trade_dollars * float(commission_bps_each_side) / 10_000.0
    spread = trade_dollars * (spreads / 2.0) / 10_000.0
    impact_bps = float(impact_bps_at_one_percent_adv) * np.sqrt(participation / 0.01)
    impact = trade_dollars * impact_bps.fillna(0.0) / 10_000.0
    short_notional = float(executed_aligned.clip(upper=0.0).abs().sum() * capital_usd)
    borrow = (
        short_notional
        * float(annual_short_borrow_bps)
        / 10_000.0
        * int(holding_days)
        / 365.0
    )
    components = {
        "commission_dollars": float(commission.sum()),
        "spread_dollars": float(spread.sum()),
        "impact_dollars": float(impact.sum()),
        "borrow_dollars": float(borrow),
        "one_way_turnover": one_way_turnover(previous_aligned, executed_aligned),
        "fallback_spread_count": float(missing_spreads.sum()),
    }
    components["total_cost_dollars"] = sum(
        components[key]
        for key in (
            "commission_dollars",
            "spread_dollars",
            "impact_dollars",
            "borrow_dollars",
        )
    )
    components["total_cost_bps_of_capital"] = (
        components["total_cost_dollars"] / capital_usd * 10_000.0
    )
    return components

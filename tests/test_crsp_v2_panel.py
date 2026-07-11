from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path

import duckdb
import pytest
import yaml

import microalpha.research.crsp_v2_panel as panel_module
from microalpha.research.crsp_v2 import (
    CRSPV2Error,
    audit_source_protocol,
    protocol_sha256,
)
from microalpha.research.crsp_v2_panel import build_monthly_panel

DAILY_COLUMNS = [
    "permno",
    "permco",
    "siccd",
    "sharetype",
    "securitytype",
    "securitysubtype",
    "usincflg",
    "primaryexch",
    "conditionaltype",
    "tradingstatusflg",
    "dlycaldt",
    "dlydelflg",
    "dlyprc",
    "dlycap",
    "dlyret",
    "dlyretmissflg",
    "dlyvol",
    "dlyprcvol",
    "dlyclose",
    "dlybid",
    "dlyask",
    "dlyopen",
    "ticker",
    "shrout",
]

NAME_COLUMNS = [
    "permno",
    "permco",
    "namedt",
    "nameenddt",
    "ticker",
    "primaryexch",
    "conditionaltype",
    "tradingstatusflg",
    "sharetype",
    "securitytype",
    "securitysubtype",
    "usincflg",
    "siccd",
]

DELIST_COLUMNS = [
    "permno",
    "delistingdt",
    "delret",
    "delretmisstype",
    "deldlydt",
]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_gzip_csv(
    path: Path, fieldnames: list[str], rows: list[dict[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _daily_row(date: str, return_value: float, *, delisting: bool = False) -> dict:
    attributes: dict[str, object] = {
        "permno": 10001,
        "permco": 5001,
        "siccd": 3571,
        "sharetype": "NS",
        "securitytype": "EQTY",
        "securitysubtype": "COM",
        "usincflg": "Y",
        "primaryexch": "N",
        "conditionaltype": "RW",
        "tradingstatusflg": "A",
        "dlycaldt": date,
        "dlydelflg": "Y" if delisting else "N",
        "dlyprc": 20.0,
        "dlycap": 500000.0,
        "dlyret": return_value,
        "dlyretmissflg": "",
        "dlyvol": 500000,
        "dlyprcvol": 10000000.0,
        "dlyclose": 20.0,
        "dlybid": 19.99,
        "dlyask": 20.01,
        "dlyopen": 20.0,
        "ticker": "TEST",
        "shrout": 25000,
    }
    if delisting:
        for column in (
            "permco",
            "siccd",
            "sharetype",
            "securitytype",
            "securitysubtype",
            "usincflg",
            "primaryexch",
            "conditionaltype",
            "tradingstatusflg",
            "ticker",
        ):
            attributes[column] = ""
    return attributes


def _fixture_protocol(
    tmp_path: Path,
    *,
    duplicate_name_state: str | None = None,
    missing_name_coverage: bool = False,
) -> Path:
    year_2022 = tmp_path / "dsf_v2" / "year=2022" / "data.csv.gz"
    year_2023 = tmp_path / "dsf_v2" / "year=2023" / "data.csv.gz"
    _write_gzip_csv(
        year_2022,
        DAILY_COLUMNS,
        [
            _daily_row("2022-12-29", 0.01),
            _daily_row("2022-12-30", 0.02),
        ],
    )
    _write_gzip_csv(
        year_2023,
        DAILY_COLUMNS,
        [
            _daily_row("2023-01-02", 0.10),
            _daily_row("2023-01-03", -0.50, delisting=True),
        ],
    )

    primary_name_row = {
        "permno": 10001,
        "permco": 5001,
        "namedt": "2000-01-01",
        "nameenddt": "2021-12-31" if missing_name_coverage else "2023-01-02",
        "ticker": "TEST",
        "primaryexch": "N",
        "conditionaltype": "RW",
        "tradingstatusflg": "A",
        "sharetype": "NS",
        "securitytype": "EQTY",
        "securitysubtype": "COM",
        "usincflg": "Y",
        "siccd": 3571,
    }
    name_rows = [
        primary_name_row,
        {
            "permno": 99999,
            "permco": 9999,
            "namedt": "2023-06-01",
            "nameenddt": "2023-12-31",
            "ticker": "SEALED_NAME_SENTINEL",
            "primaryexch": "Q",
            "conditionaltype": "RW",
            "tradingstatusflg": "A",
            "sharetype": "NS",
            "securitytype": "EQTY",
            "securitysubtype": "COM",
            "usincflg": "Y",
            "siccd": 6021,
        },
    ]
    if duplicate_name_state is not None:
        duplicate = dict(primary_name_row)
        if duplicate_name_state == "conflicting":
            duplicate["ticker"] = "CONFLICT"
        elif duplicate_name_state != "equivalent":
            raise ValueError("unknown duplicate_name_state")
        name_rows.append(duplicate)

    names_path = tmp_path / "stocknames_v2" / "data.csv.gz"
    _write_gzip_csv(
        names_path,
        NAME_COLUMNS,
        name_rows,
    )
    delists_path = tmp_path / "stkdelists" / "data.csv.gz"
    _write_gzip_csv(
        delists_path,
        DELIST_COLUMNS,
        [
            {
                "permno": 10001,
                "delistingdt": "2023-01-02",
                "delret": -0.50,
                "delretmisstype": "",
                "deldlydt": "2023-01-03",
            },
            {
                "permno": 99999,
                "delistingdt": "2023-11-29",
                "delret": "SEALED_DELIST_SENTINEL",
                "delretmisstype": "SEALED",
                "deldlydt": "2023-11-30",
            },
        ],
    )

    primary_manifest_path = tmp_path / "primary_manifest.json"
    primary_manifest = {
        "failure_count": 0,
        "items": [
            {
                "table": "dsf_v2",
                "partition": "year=2022",
                "status": "ok",
                "path": str(year_2022),
                "rows": 2,
                "size_bytes": year_2022.stat().st_size,
            },
            {
                "table": "dsf_v2",
                "partition": "year=2023",
                "status": "ok",
                "path": str(year_2023),
                "rows": 2,
                "size_bytes": year_2023.stat().st_size,
            },
            {
                "table": "stocknames_v2",
                "status": "ok",
                "path": str(names_path),
                "rows": len(name_rows),
                "size_bytes": names_path.stat().st_size,
            },
            {
                "table": "stkdelists",
                "status": "ok",
                "path": str(delists_path),
                "rows": 2,
                "size_bytes": delists_path.stat().st_size,
            },
        ],
    }
    primary_manifest_path.write_text(json.dumps(primary_manifest), encoding="utf-8")

    dsi_path = tmp_path / "dsi" / "data.csv.gz"
    _write_gzip_csv(
        dsi_path,
        ["date", "vwretd", "ewretd", "sprtrn"],
        [{"date": "2022-12-30", "vwretd": 0.001, "ewretd": 0.002, "sprtrn": 0.001}],
    )
    market_manifest_path = tmp_path / "market_manifest.json"
    market_manifest_path.write_text(
        json.dumps(
            {
                "failure_count": 0,
                "items": [
                    {
                        "table": "dsi",
                        "status": "ok",
                        "path": str(dsi_path),
                        "rows": 1,
                        "size_bytes": dsi_path.stat().st_size,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    public_files: list[dict[str, str]] = []
    public_dir = tmp_path / "public"
    public_dir.mkdir()
    for role in ("ff5_daily", "momentum_daily", "momentum_deciles_monthly"):
        path = public_dir / f"{role}.zip"
        path.write_bytes(f"synthetic-{role}".encode())
        public_files.append({"role": role, "path": str(path), "sha256": _digest(path)})
    public_manifest_path = tmp_path / "downloads_manifest.csv"
    with public_manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["local_path", "sha256", "validation_status"]
        )
        writer.writeheader()
        for item in public_files:
            writer.writerow(
                {
                    "local_path": item["path"],
                    "sha256": item["sha256"],
                    "validation_status": "downloaded_hash_ok",
                }
            )

    protocol = {
        "schema_version": "microalpha-flagship-protocol/v1",
        "protocol_id": "synthetic-crsp-v2-integration",
        "dataset": {
            "id": "synthetic-fixture-only",
            "wrds": {
                "primary_manifest": {
                    "path": str(primary_manifest_path),
                    "sha256": _digest(primary_manifest_path),
                    "table": "dsf_v2",
                    "partitions": {
                        "start": 2022,
                        "end": 2023,
                        "expected_count": 2,
                        "expected_rows": 4,
                        "expected_compressed_bytes": (
                            year_2022.stat().st_size + year_2023.stat().st_size
                        ),
                    },
                    "required_columns": DAILY_COLUMNS,
                    "side_tables": [
                        {
                            "table": "stocknames_v2",
                            "expected_rows": len(name_rows),
                            "required_columns": NAME_COLUMNS,
                        },
                        {
                            "table": "stkdelists",
                            "expected_rows": 2,
                            "required_columns": DELIST_COLUMNS,
                        },
                    ],
                },
                "market_manifest": {
                    "path": str(market_manifest_path),
                    "sha256": _digest(market_manifest_path),
                    "table": "dsi",
                    "expected_rows": 1,
                    "required_columns": ["date", "vwretd", "ewretd", "sprtrn"],
                },
            },
            "public": {
                "acquisition_manifest": {
                    "path": str(public_manifest_path),
                    "sha256": _digest(public_manifest_path),
                },
                "files": public_files,
            },
        },
        "windows": {
            "warmup": {"start": "2019-01-01", "end": "2019-12-31"},
            "training": {"start": "2020-01-01", "end": "2020-12-31"},
            "validation": {"start": "2021-01-01", "end": "2022-12-31"},
            "final_holdout": {"start": "2023-01-01", "end": "2023-12-31"},
        },
        "candidate_grid": {
            "signals": ["mom_12_2"],
            "weighting": ["equal"],
        },
        "universe": {
            "filters_at_formation_date": {
                "sharetype": ["NS"],
                "securitytype": ["EQTY"],
                "securitysubtype": ["COM"],
                "usincflg": ["Y"],
                "primaryexch": ["N"],
                "conditionaltype": ["RW"],
                "tradingstatusflg": ["A"],
                "minimum_price": 0.0,
                "minimum_market_cap_usd": 0.0,
                "minimum_60d_median_dollar_volume_usd": 0.0,
                "minimum_return_history_months": 0,
            }
        },
    }
    protocol_path = tmp_path / "protocol.yaml"
    protocol_path.write_text(yaml.safe_dump(protocol), encoding="utf-8")
    return protocol_path


def test_adapter_is_manifest_bound_and_holdout_gated(tmp_path: Path) -> None:
    protocol_path = _fixture_protocol(tmp_path)
    audit = audit_source_protocol(protocol_path)
    assert audit["primary"]["partition_count"] == 2
    assert audit["holdout_outcomes_read"] is False

    selection_path = tmp_path / "selection.parquet"
    selection_manifest = build_monthly_panel(protocol_path, selection_path)
    assert selection_manifest["source_partition_count"] == 1
    assert selection_manifest["holdout_headers_verified"] is True
    access = selection_manifest["access_contract"]
    assert access["primary_holdout_partitions_opened_for_outcome_rows"] is False
    assert access["primary_post_validation_rows_materialized"] == 0
    assert access["side_table_source_bytes_scan_scope"] == (
        "full_files_for_date_key_filter"
    )
    assert access["post_validation_stocknames_rows_materialized"] == 0
    assert access["post_validation_delisting_rows_materialized"] == 0
    assert selection_manifest["side_table_materialization"] == {
        "stocknames_v2": {
            "rows": 1,
            "max_namedt": "2000-01-01",
            "max_effective_nameenddt": "2022-12-31",
            "daily_rows_without_date_valid_name": 0,
            "daily_rows_with_overlapping_name_history": 0,
            "maximum_date_valid_name_matches": 1,
            "attribute_resolution": (
                "CIZ daily row is authoritative; stocknames_v2 is a "
                "date-coverage and overlap audit only"
            ),
        },
        "stkdelists": {"rows": 0, "max_deldlydt": None},
    }
    selection_rows = duckdb.sql(
        f"SELECT split, formation_date, history_months "
        f"FROM read_parquet('{selection_path}')"
    ).fetchall()
    assert len(selection_rows) == 1
    assert selection_rows[0][0] == "validation"
    assert str(selection_rows[0][1]) == "2022-12-31"
    assert selection_rows[0][2] == 0

    final_path = tmp_path / "final.parquet"
    with pytest.raises(CRSPV2Error, match="frozen model"):
        build_monthly_panel(protocol_path, final_path, stage="final")

    frozen_model_path = tmp_path / "selected_model.json"
    frozen_model_path.write_text(
        json.dumps(
            {
                "protocol_id": "synthetic-crsp-v2-integration",
                "protocol_sha256": protocol_sha256(protocol_path),
                "validation_complete": True,
                "selected_candidate": {
                    "signal": "mom_12_2",
                    "weighting": "equal",
                },
                "frozen_at_utc": "2026-07-10T21:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    final_manifest = build_monthly_panel(
        protocol_path,
        final_path,
        stage="final",
        frozen_model_path=frozen_model_path,
    )
    assert final_manifest["source_partition_count"] == 2
    final_access = final_manifest["access_contract"]
    assert final_access["primary_holdout_partitions_opened_for_outcome_rows"] is True
    assert final_access["primary_post_validation_rows_materialized"] == 2
    assert final_access["post_validation_stocknames_rows_materialized"] == 1
    assert final_access["post_validation_delisting_rows_materialized"] == 1
    assert final_manifest["side_table_materialization"]["stocknames_v2"][
        "rows"
    ] == 1
    assert final_manifest["side_table_materialization"]["stkdelists"]["rows"] == 1
    final_row = duckdb.sql(f"""
        SELECT monthly_total_return, delisting_pseudo_days, history_months
        FROM read_parquet('{final_path}')
        WHERE split = 'final_holdout'
        """).fetchone()
    assert final_row[0] == pytest.approx(-0.45)
    assert final_row[1] == 1
    assert final_row[2] == 1


def test_equivalent_overlapping_name_states_are_reported(tmp_path: Path) -> None:
    protocol_path = _fixture_protocol(tmp_path, duplicate_name_state="equivalent")
    manifest = build_monthly_panel(protocol_path, tmp_path / "selection.parquet")

    stocknames = manifest["side_table_materialization"]["stocknames_v2"]
    assert stocknames["rows"] == 2
    assert stocknames["daily_rows_with_overlapping_name_history"] == 2
    assert stocknames["maximum_date_valid_name_matches"] == 2


def test_conflicting_name_history_never_overrides_authoritative_ciz_row(
    tmp_path: Path,
) -> None:
    protocol_path = _fixture_protocol(tmp_path, duplicate_name_state="conflicting")
    output_path = tmp_path / "selection.parquet"

    manifest = build_monthly_panel(protocol_path, output_path)

    stocknames = manifest["side_table_materialization"]["stocknames_v2"]
    assert stocknames["daily_rows_with_overlapping_name_history"] == 2
    assert duckdb.sql(
        f"SELECT ticker FROM read_parquet('{output_path}')"
    ).fetchone()[0] == "TEST"


def test_missing_date_valid_name_coverage_fails_closed(tmp_path: Path) -> None:
    protocol_path = _fixture_protocol(tmp_path, missing_name_coverage=True)
    output_path = tmp_path / "selection.parquet"

    with pytest.raises(CRSPV2Error, match="stocknames coverage failed"):
        build_monthly_panel(protocol_path, output_path)
    assert not output_path.exists()


def test_adapter_refuses_to_clobber_panel_or_manifest(tmp_path: Path) -> None:
    protocol_path = _fixture_protocol(tmp_path)
    output_path = tmp_path / "selection.parquet"
    output_path.write_bytes(b"existing-panel")

    with pytest.raises(CRSPV2Error, match="Refusing to overwrite"):
        build_monthly_panel(protocol_path, output_path)
    assert output_path.read_bytes() == b"existing-panel"

    output_path.unlink()
    manifest_path = output_path.with_suffix(".parquet.manifest.json")
    manifest_path.write_text("existing-manifest", encoding="utf-8")
    with pytest.raises(CRSPV2Error, match="Refusing to overwrite"):
        build_monthly_panel(protocol_path, output_path)
    assert not output_path.exists()
    assert manifest_path.read_text(encoding="utf-8") == "existing-manifest"


def test_failed_staged_build_never_publishes_partial_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol_path = _fixture_protocol(tmp_path)
    output_path = tmp_path / "selection.parquet"
    manifest_path = output_path.with_suffix(".parquet.manifest.json")
    real_sha256_file = panel_module.sha256_file

    def fail_on_staged_output(path: str | Path, **kwargs: object) -> str:
        candidate = Path(path)
        if candidate.name == output_path.name and ".staging-" in candidate.parent.name:
            raise RuntimeError("injected failure after staged COPY")
        return real_sha256_file(path, **kwargs)

    monkeypatch.setattr(panel_module, "sha256_file", fail_on_staged_output)
    with pytest.raises(RuntimeError, match="injected failure"):
        build_monthly_panel(protocol_path, output_path)

    assert not output_path.exists()
    assert not manifest_path.exists()


def test_pair_publication_rolls_back_if_second_link_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staged_output = tmp_path / "staged.parquet"
    staged_manifest = tmp_path / "staged.manifest.json"
    output_path = tmp_path / "published.parquet"
    manifest_path = tmp_path / "published.parquet.manifest.json"
    staged_output.write_bytes(b"panel")
    staged_manifest.write_text("{}", encoding="utf-8")
    real_link = panel_module.os.link
    call_count = 0

    def fail_second_link(source: Path, destination: Path) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise OSError("injected manifest publication failure")
        real_link(source, destination)

    monkeypatch.setattr(panel_module.os, "link", fail_second_link)
    with pytest.raises(CRSPV2Error, match="could not be published"):
        panel_module._publish_artifact_pair_no_clobber(
            staged_output,
            output_path,
            staged_manifest,
            manifest_path,
        )

    assert not output_path.exists()
    assert not manifest_path.exists()
    assert staged_output.read_bytes() == b"panel"
    assert staged_manifest.read_text(encoding="utf-8") == "{}"

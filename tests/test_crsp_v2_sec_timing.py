from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import pytest
import yaml

from microalpha.research import crsp_v2_sec_timing as timing_module
from microalpha.research.crsp_v2 import CRSPV2Error, sha256_file
from microalpha.research.crsp_v2_sec_timing import (
    AGGREGATE_COVERAGE_COLUMNS,
    build_sec_timing_scores,
    evaluate_sec_timing_coverage_gate,
    extract_first_filed_sec_timing,
    load_sec_timing_contract,
    run_sec_timing_return_free_coverage,
)


def _write_submissions(tmp_path: Path) -> Path:
    path = tmp_path / "submissions.zip"
    cik = "0000000001"
    payload = {
        "cik": cik,
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0000000001-15-000001",
                    "0000000001-16-000001",
                    "0000000001-16-999999",
                    "0000000001-17-000001",
                ],
                "filingDate": [
                    "2015-03-01",
                    "2016-02-19",
                    "2016-03-10",
                    "2017-08-18",
                ],
                "reportDate": [
                    "2014-12-31",
                    "2015-12-31",
                    "2015-12-31",
                    "2016-12-31",
                ],
                "acceptanceDateTime": [
                    "2015-03-01T21:00:00.000Z",
                    "2016-02-19T21:00:00.000Z",
                    "2016-03-10T21:00:00.000Z",
                    "2017-08-18T21:00:00.000Z",
                ],
                "form": ["10-K", "10-K", "10-K/A", "10-K"],
                "isXBRL": [1, 1, 1, 1],
            },
            "files": [],
        },
    }
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(f"CIK{cik}.json", json.dumps(payload))
    return path


def test_timing_extractor_uses_original_acceptance_and_fails_closed_on_outlier(
    tmp_path: Path,
) -> None:
    submissions = _write_submissions(tmp_path)
    features, audit = extract_first_filed_sec_timing(
        submissions,
        [1],
        minimum_report_date="2014-01-01",
        maximum_acceptance_timestamp="2017-12-31T23:59:59Z",
    )

    assert len(features) == 1
    row = features.iloc[0]
    assert row["accession"] == "0000000001-16-000001"
    assert row["reporting_delay_days"] == 50
    assert row["prior_reporting_delay_days"] == 60
    assert row["reporting_timeliness_level"] == pytest.approx(-50.0)
    assert row["reporting_timeliness_change"] == pytest.approx(10.0)
    assert row["availability_date"] == pd.Timestamp("2016-02-19")
    assert row["expiry_date"] == pd.Timestamp("2017-08-19")
    assert audit["first_filed_10k_rows"] == 3
    assert audit["consecutive_timing_pairs"] == 1
    assert audit["post_cutoff_filing_rows_selected"] == 0
    assert audit["return_columns_projected"] is False


def _write_score_fixture(tmp_path: Path) -> tuple[pd.DataFrame, Path, Path, Path]:
    company_path = tmp_path / "company.parquet"
    pd.DataFrame(
        {
            "gvkey": [f"{number:06d}" for number in range(1, 5)],
            "cik": [f"{number:010d}" for number in range(1, 5)],
        }
    ).to_parquet(company_path, index=False)
    link_path = tmp_path / "links.parquet"
    pd.DataFrame(
        [
            {
                "gvkey": f"{number:06d}",
                "linkprim": "P",
                "linktype": "LU",
                "lpermno": number,
                "linkdt": pd.Timestamp("2000-01-01"),
                "linkenddt": pd.NaT,
            }
            for number in range(1, 5)
        ]
    ).to_parquet(link_path, index=False)
    panel_path = tmp_path / "panel.parquet"
    panel_rows = []
    for date in pd.date_range("2016-12-31", "2022-11-30", freq="ME"):
        for number in range(1, 5):
            panel_rows.append(
                {
                    "permno": number,
                    "formation_date": date,
                    "industry": "One",
                    "eligible_at_formation": True,
                    "monthly_total_return": 99.0,
                }
            )
    pd.DataFrame(panel_rows).to_parquet(panel_path, index=False)

    feature_rows = []
    for year in range(2016, 2023):
        for number in range(1, 5):
            availability = pd.Timestamp(f"{year}-02-15")
            if number == 4 and year == 2016:
                availability = pd.Timestamp("2017-01-15")
            feature_rows.append(
                {
                    "cik": f"{number:010d}",
                    "accession": f"{number}-{year}",
                    "report_date": pd.Timestamp(f"{year - 1}-12-31"),
                    "acceptance_timestamp": availability.tz_localize("UTC"),
                    "availability_date": availability,
                    "expiry_date": availability + pd.DateOffset(months=18),
                    "reporting_delay_days": 100 - number,
                    "prior_reporting_delay_days": 100,
                    "reporting_timeliness_level": float(number),
                    "reporting_timeliness_change": float(number),
                }
            )
    return pd.DataFrame(feature_rows), company_path, link_path, panel_path


def test_timing_scores_use_only_metadata_and_exact_acceptance(tmp_path: Path) -> None:
    features, company, links, panel = _write_score_fixture(tmp_path)
    protocol = {"windows": {"validation": {"start": "2017-01-01", "end": "2022-12-31"}}}
    frame, coverage, audit = build_sec_timing_scores(
        features, company, links, panel, protocol
    )

    december = frame.loc[frame["formation_date"].eq("2016-12-31")]
    scores = december.set_index("permno")["sec_reporting_timeliness_quality"]
    assert scores.loc[3] > scores.loc[2] > scores.loc[1]
    assert pd.isna(scores.loc[4])
    assert "monthly_total_return" not in frame.columns
    assert len(coverage) == 72
    assert audit["return_columns_projected"] is False
    assert audit["validation_outcomes_read"] is False
    assert audit["final_holdout_outcomes_read"] is False


def test_contract_disables_validation_and_rejects_direction_change(
    tmp_path: Path,
) -> None:
    source = Path("docs/strategy/MICROALPHA_SEC_REPORTING_TIMELINESS_20260711.yaml")
    contract = load_sec_timing_contract(source)
    assert contract["execution_contract"]["validation_run_permitted"] is False
    assert contract["access_contract"]["validation_outcomes_read"] is False

    changed = dict(contract)
    changed["frozen_mechanism"] = dict(contract["frozen_mechanism"])
    changed["frozen_mechanism"]["raw_features"] = dict(
        contract["frozen_mechanism"]["raw_features"]
    )
    changed["frozen_mechanism"]["raw_features"]["reporting_timeliness_change"] = (
        "current reporting-delay days minus prior reporting-delay days"
    )
    path = tmp_path / "changed.yaml"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(CRSPV2Error, match="definitions or directions"):
        load_sec_timing_contract(path)


def _aggregate_coverage(*, minimum_names: int = 600) -> pd.DataFrame:
    rows = []
    for offset, date in enumerate(pd.date_range("2016-12-31", "2022-11-30", freq="ME")):
        rows.append(
            {
                "formation_date": date,
                "base_eligible_names": 800 + offset,
                "complete_names": minimum_names if offset == 0 else 650 + offset,
                "ambiguous_ccm_rows": 0,
                "complete_industries": 12,
            }
        )
    return pd.DataFrame(rows, columns=AGGREGATE_COVERAGE_COLUMNS)


def _write_bounded_runner_contract(tmp_path: Path) -> tuple[Path, dict[str, Path]]:
    source = Path("docs/strategy/MICROALPHA_SEC_REPORTING_TIMELINESS_20260711.yaml")
    contract = yaml.safe_load(source.read_text(encoding="utf-8"))
    protocol = tmp_path / "protocol.yaml"
    protocol.write_text(
        yaml.safe_dump(
            {
                "schema_version": "microalpha-flagship-protocol/v1",
                "protocol_id": "synthetic-return-free-proof",
                "windows": {"validation": {"start": "2017-01-01", "end": "2022-12-31"}},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    paths = {
        "base_protocol": protocol,
        "selection_panel": tmp_path / "selection.parquet",
        "selection_panel_manifest": tmp_path / "selection.parquet.manifest.json",
        "company_cik_bridge": tmp_path / "company.parquet",
        "ccm_link_history": tmp_path / "links.parquet",
        "submissions_zip": tmp_path / "submissions.zip",
    }
    for name, path in paths.items():
        if name != "base_protocol":
            path.write_bytes(f"bounded-{name}\n".encode())
    frozen = contract["frozen_inputs"]
    frozen["base_protocol_path"] = str(protocol)
    frozen["base_protocol_sha256"] = sha256_file(protocol)
    frozen["selection_panel"].update(
        {
            "path": str(paths["selection_panel"]),
            "sha256": sha256_file(paths["selection_panel"]),
            "size_bytes": paths["selection_panel"].stat().st_size,
            "manifest_sha256": sha256_file(paths["selection_panel_manifest"]),
        }
    )
    for key in ("company_cik_bridge", "ccm_link_history", "submissions_zip"):
        frozen[key].update(
            {
                "path": str(paths[key]),
                "sha256": sha256_file(paths[key]),
                "size_bytes": paths[key].stat().st_size,
            }
        )
    contract_path = tmp_path / "contract.yaml"
    contract_path.write_text(
        yaml.safe_dump(contract, sort_keys=False), encoding="utf-8"
    )
    return contract_path, paths


def _patch_bounded_runner(
    monkeypatch: pytest.MonkeyPatch,
    contract_path: Path,
    paths: dict[str, Path],
    coverage: pd.DataFrame,
    *,
    post_cutoff_rows: int = 0,
) -> None:
    checks = {
        "base_protocol_sha256": sha256_file(paths["base_protocol"]),
        "selection_panel_sha256": sha256_file(paths["selection_panel"]),
        "selection_panel_manifest_sha256": sha256_file(
            paths["selection_panel_manifest"]
        ),
        "company_cik_bridge_sha256": sha256_file(paths["company_cik_bridge"]),
        "ccm_link_history_sha256": sha256_file(paths["ccm_link_history"]),
        "submissions_zip_sha256": sha256_file(paths["submissions_zip"]),
    }
    monkeypatch.setattr(
        timing_module,
        "verify_sec_timing_sources",
        lambda _path: {
            "schema_version": "microalpha-sec-timing-source-audit/v1",
            "contract_path": str(contract_path),
            "contract_sha256": sha256_file(contract_path),
            "checks": checks,
            "panel_columns_projected": [],
            "return_columns_projected": False,
            "validation_outcomes_read": False,
            "final_holdout_outcomes_read": False,
        },
    )
    synthetic_ciks = [f"{number:010d}" for number in range(1, 3107)]
    monkeypatch.setattr(
        timing_module,
        "_target_ciks",
        lambda *_args: (
            synthetic_ciks,
            {
                "target_ciks": 3106,
                "eligible_permno_gvkey_pairs": 3106,
                "pairs_with_cik": 3106,
                "pairs_without_cik": 0,
                "panel_return_column_projected": False,
                "target_cik_values": ["TARGET_IDENTIFIER_MUST_NOT_PERSIST"],
            },
        ),
    )
    monkeypatch.setattr(
        timing_module,
        "extract_first_filed_sec_timing",
        lambda *_args, **_kwargs: (
            pd.DataFrame({"synthetic_metadata_only": [1]}),
            {
                "submissions_archive_member_count": 981230,
                "requested_ciks": 3106,
                "supplemental_members_opened": 1313,
                "first_filed_10k_rows": 21_719,
                "report_dates_with_multiple_original_10ks": 0,
                "consecutive_timing_pairs": 18_000,
                "maximum_selected_acceptance_timestamp": ("2022-11-30T20:00:00+00:00"),
                "post_cutoff_filing_rows_selected": post_cutoff_rows,
                "return_columns_projected": False,
                "accession_values": ["ACCESSION_IDENTIFIER_MUST_NOT_PERSIST"],
            },
        ),
    )
    synthetic_sensitive_frame = pd.DataFrame(
        {
            "permno": [999999],
            "cik": ["0000999999"],
            "accession": ["SYNTHETIC_IDENTIFIER_MUST_NOT_PERSIST"],
        }
    )
    monkeypatch.setattr(
        timing_module,
        "build_sec_timing_scores",
        lambda *_args, **_kwargs: (
            synthetic_sensitive_frame,
            coverage.copy(),
            {
                "coverage_formation_months": 72,
                "minimum_complete_names": int(coverage["complete_names"].min()),
                "median_complete_names": float(coverage["complete_names"].median()),
                "maximum_complete_names": int(coverage["complete_names"].max()),
                "minimum_complete_industries": int(
                    coverage["complete_industries"].min()
                ),
                "ambiguous_ccm_rows": 0,
                "minimum_formation_date": "2016-12-31",
                "maximum_formation_date": "2022-11-30",
                "maximum_scored_acceptance_timestamp": ("2022-11-30T20:00:00+00:00"),
                "selected_rows_available_after_formation": 0,
                "selected_rows_expired_before_formation": 0,
                "panel_columns_projected": [
                    "permno",
                    "formation_date",
                    "industry",
                    "eligible_at_formation",
                ],
                "return_columns_projected": False,
                "validation_outcomes_read": False,
                "final_holdout_outcomes_read": False,
                "identifier_rows": ["FRAME_IDENTIFIER_MUST_NOT_PERSIST"],
            },
        ),
    )


def test_return_free_coverage_runner_requires_memory_lane_admission(
    tmp_path: Path,
) -> None:
    output = tmp_path / "must-not-exist"
    with pytest.raises(CRSPV2Error, match="memory-lane admission"):
        run_sec_timing_return_free_coverage(tmp_path / "missing.yaml", output)
    assert not output.exists()


def test_return_free_coverage_runner_writes_deterministic_aggregate_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract_path, paths = _write_bounded_runner_contract(tmp_path)
    coverage = _aggregate_coverage()
    _patch_bounded_runner(monkeypatch, contract_path, paths, coverage)
    first = tmp_path / "first"
    second = tmp_path / "second"
    stamp = "2026-07-11T22:00:00+00:00"

    result = run_sec_timing_return_free_coverage(
        contract_path,
        first,
        memory_lane_admitted=True,
        generated_at_utc=stamp,
    )
    repeated = run_sec_timing_return_free_coverage(
        contract_path,
        second,
        memory_lane_admitted=True,
        generated_at_utc=stamp,
    )

    expected_files = {
        "aggregate_coverage.csv",
        "source_manifest.json",
        "chronology_audit.json",
        "coverage_gate.json",
        "result_manifest.json",
    }
    assert {path.name for path in first.iterdir()} == expected_files
    assert {path.name for path in second.iterdir()} == expected_files
    assert result["coverage_gate_passed"] is True
    assert repeated["validation_readmission_granted"] is False
    assert result["return_columns_projected"] is False
    aggregate = pd.read_csv(first / "aggregate_coverage.csv")
    assert list(aggregate.columns) == AGGREGATE_COVERAGE_COLUMNS
    assert len(aggregate) == 72
    assert "SYNTHETIC_IDENTIFIER_MUST_NOT_PERSIST" not in "".join(
        path.read_text(encoding="utf-8") for path in first.iterdir()
    )
    persisted = "".join(path.read_text(encoding="utf-8") for path in first.iterdir())
    assert "TARGET_IDENTIFIER_MUST_NOT_PERSIST" not in persisted
    assert "ACCESSION_IDENTIFIER_MUST_NOT_PERSIST" not in persisted
    assert "FRAME_IDENTIFIER_MUST_NOT_PERSIST" not in persisted
    manifest = json.loads((first / "result_manifest.json").read_text())
    assert set(manifest["artifacts"]) == expected_files - {"result_manifest.json"}
    for name, receipt in manifest["artifacts"].items():
        assert receipt["sha256"] == sha256_file(first / name)
        assert receipt["size_bytes"] == (first / name).stat().st_size
    assert {name: sha256_file(first / name) for name in sorted(expected_files)} == {
        name: sha256_file(second / name) for name in sorted(expected_files)
    }
    with pytest.raises(CRSPV2Error, match="Refusing to overwrite"):
        run_sec_timing_return_free_coverage(
            contract_path, first, memory_lane_admitted=True
        )


def test_return_free_coverage_gate_records_threshold_failure() -> None:
    contract = load_sec_timing_contract(
        "docs/strategy/MICROALPHA_SEC_REPORTING_TIMELINESS_20260711.yaml"
    )
    protocol = yaml.safe_load(
        Path("docs/strategy/MICROALPHA_FLAGSHIP_20260710.yaml").read_text(
            encoding="utf-8"
        )
    )
    receipt = evaluate_sec_timing_coverage_gate(
        _aggregate_coverage(minimum_names=499),
        contract,
        protocol,
        source_digests_verified=True,
    )

    assert receipt["gate_passed"] is False
    assert receipt["failures"] == ["minimum_complete_names_each_formation_month"]
    assert receipt["validation_run_permitted"] is False


@pytest.mark.parametrize("shape", ["reordered", "duplicated"])
def test_return_free_coverage_requires_exact_column_order(shape: str) -> None:
    contract = load_sec_timing_contract(
        "docs/strategy/MICROALPHA_SEC_REPORTING_TIMELINESS_20260711.yaml"
    )
    protocol = yaml.safe_load(
        Path("docs/strategy/MICROALPHA_FLAGSHIP_20260710.yaml").read_text(
            encoding="utf-8"
        )
    )
    coverage = _aggregate_coverage()
    if shape == "reordered":
        coverage = coverage[list(reversed(AGGREGATE_COVERAGE_COLUMNS))]
    else:
        coverage = pd.concat([coverage, coverage[["complete_names"]]], axis=1)

    with pytest.raises(CRSPV2Error, match="exactly once in frozen order"):
        evaluate_sec_timing_coverage_gate(
            coverage, contract, protocol, source_digests_verified=True
        )


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("complete_names", float("nan"), "finite nonnegative integer"),
        ("base_eligible_names", -1, "finite nonnegative integer"),
        ("complete_industries", 1.5, "finite nonnegative integer"),
        ("complete_names", 900, "internally invalid"),
    ],
)
def test_return_free_coverage_rejects_invalid_aggregate_counts(
    column: str, value: float, message: str
) -> None:
    contract = load_sec_timing_contract(
        "docs/strategy/MICROALPHA_SEC_REPORTING_TIMELINESS_20260711.yaml"
    )
    protocol = yaml.safe_load(
        Path("docs/strategy/MICROALPHA_FLAGSHIP_20260710.yaml").read_text(
            encoding="utf-8"
        )
    )
    coverage = _aggregate_coverage()
    coverage[column] = coverage[column].astype(float)
    coverage.loc[0, column] = value

    with pytest.raises(CRSPV2Error, match=message):
        evaluate_sec_timing_coverage_gate(
            coverage, contract, protocol, source_digests_verified=True
        )


def test_return_free_coverage_requires_verified_source_digests() -> None:
    contract = load_sec_timing_contract(
        "docs/strategy/MICROALPHA_SEC_REPORTING_TIMELINESS_20260711.yaml"
    )
    protocol = yaml.safe_load(
        Path("docs/strategy/MICROALPHA_FLAGSHIP_20260710.yaml").read_text(
            encoding="utf-8"
        )
    )
    receipt = evaluate_sec_timing_coverage_gate(
        _aggregate_coverage(),
        contract,
        protocol,
        source_digests_verified=False,
    )

    assert receipt["gate_passed"] is False
    assert receipt["failures"] == ["exact_source_digests_match"]


def test_return_free_runner_fails_closed_before_output_on_cutoff_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract_path, paths = _write_bounded_runner_contract(tmp_path)
    _patch_bounded_runner(
        monkeypatch,
        contract_path,
        paths,
        _aggregate_coverage(),
        post_cutoff_rows=1,
    )
    output = tmp_path / "must-not-exist"

    with pytest.raises(CRSPV2Error, match="no_post_cutoff_filing_selected"):
        run_sec_timing_return_free_coverage(
            contract_path, output, memory_lane_admitted=True
        )
    assert not output.exists()


def test_contract_rejects_frozen_coverage_gate_change(tmp_path: Path) -> None:
    source = Path("docs/strategy/MICROALPHA_SEC_REPORTING_TIMELINESS_20260711.yaml")
    contract = deepcopy(yaml.safe_load(source.read_text(encoding="utf-8")))
    contract["future_return_free_coverage_gate"][
        "minimum_complete_names_each_formation_month"
    ] = 499
    changed = tmp_path / "changed.yaml"
    changed.write_text(yaml.safe_dump(contract), encoding="utf-8")

    with pytest.raises(CRSPV2Error, match="coverage gate changed"):
        load_sec_timing_contract(changed)

from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import pytest

from microalpha.research.crsp_v2 import CRSPV2Error
from microalpha.research.crsp_v2_sec_timing import (
    build_sec_timing_scores,
    extract_first_filed_sec_timing,
    load_sec_timing_contract,
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
    protocol = {
        "windows": {
            "validation": {"start": "2017-01-01", "end": "2022-12-31"}
        }
    }
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

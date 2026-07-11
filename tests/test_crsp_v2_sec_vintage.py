from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import pytest

from microalpha.research.crsp_v2 import CRSPV2Error
from microalpha.research.crsp_v2_sec_vintage import (
    _build_sec_vintage_frame,
    extract_first_filed_sec_features,
    run_sec_vintage_mechanism,
)


def _submission_payload(cik: str, accessions: list[str]) -> dict:
    return {
        "cik": cik,
        "filings": {
            "recent": {
                "accessionNumber": [*accessions, f"{cik}-16-999999"],
                "filingDate": ["2015-02-15", "2016-02-15", "2016-03-01"],
                "reportDate": ["2014-12-31", "2015-12-31", "2015-12-31"],
                "acceptanceDateTime": [
                    "2015-02-15T21:00:00.000Z",
                    "2016-02-15T21:00:00.000Z",
                    "2016-03-01T21:00:00.000Z",
                ],
                "form": ["10-K", "10-K", "10-K/A"],
                "isXBRL": [1, 1, 1],
            },
            "files": [],
        },
    }


def _fact_row(
    accession: str,
    end: str,
    value: float,
    *,
    start: str | None = None,
    form: str = "10-K",
) -> dict:
    row = {
        "end": end,
        "val": value,
        "accn": accession,
        "form": form,
        "filed": "2016-02-15",
        "fy": 2015,
        "fp": "FY",
    }
    if start is not None:
        row["start"] = start
    return row


def _write_sec_archives(
    tmp_path: Path, *, ambiguous_net_income: bool = False
) -> tuple[Path, Path]:
    companyfacts_path = tmp_path / "companyfacts.zip"
    submissions_path = tmp_path / "submissions.zip"
    with ZipFile(submissions_path, "w", compression=ZIP_DEFLATED) as archive:
        for number in range(1, 5):
            cik = f"{number:010d}"
            accessions = [f"{cik}-15-000001", f"{cik}-16-000001"]
            archive.writestr(
                f"CIK{cik}.json",
                json.dumps(_submission_payload(cik, accessions)),
            )

    with ZipFile(companyfacts_path, "w", compression=ZIP_DEFLATED) as archive:
        for number in range(1, 5):
            cik = f"{number:010d}"
            old_accession = f"{cik}-15-000001"
            current_accession = f"{cik}-16-000001"
            amendment_accession = f"{cik}-16-999999"
            later_accession = f"{cik}-17-000001"
            old_assets = 100.0
            new_assets = 100.0 + number
            old_income = 5.0
            new_income = 5.0 + number
            old_cash = 6.0
            new_cash = 6.0 + 2.0 * number
            net_rows = [
                _fact_row(
                    old_accession,
                    "2014-12-31",
                    old_income,
                    start="2014-01-01",
                ),
                _fact_row(
                    current_accession,
                    "2015-12-31",
                    new_income,
                    start="2015-01-01",
                ),
                _fact_row(
                    amendment_accession,
                    "2015-12-31",
                    999.0,
                    start="2015-01-01",
                    form="10-K/A",
                ),
                _fact_row(
                    later_accession,
                    "2015-12-31",
                    777.0,
                    start="2015-01-01",
                ),
            ]
            if ambiguous_net_income and number == 1:
                net_rows.append(
                    _fact_row(
                        current_accession,
                        "2015-12-31",
                        123.0,
                        start="2015-01-01",
                    )
                )
            facts = {
                "cik": int(cik),
                "facts": {
                    "us-gaap": {
                        "Assets": {
                            "units": {
                                "USD": [
                                    _fact_row(
                                        old_accession, "2014-12-31", old_assets
                                    ),
                                    _fact_row(
                                        current_accession, "2015-12-31", new_assets
                                    ),
                                ]
                            }
                        },
                        "NetIncomeLoss": {"units": {"USD": net_rows}},
                        "NetCashProvidedByUsedInOperatingActivities": {
                            "units": {
                                "USD": [
                                    _fact_row(
                                        old_accession,
                                        "2014-12-31",
                                        old_cash,
                                        start="2014-01-01",
                                    ),
                                    _fact_row(
                                        current_accession,
                                        "2015-12-31",
                                        new_cash,
                                        start="2015-01-01",
                                    ),
                                ]
                            }
                        },
                    }
                },
            }
            archive.writestr(f"CIK{cik}.json", json.dumps(facts))
    return companyfacts_path, submissions_path


def test_extractor_uses_only_values_in_first_original_accession(
    tmp_path: Path,
) -> None:
    companyfacts, submissions = _write_sec_archives(tmp_path)
    features, audit = extract_first_filed_sec_features(
        companyfacts,
        submissions,
        [1, 2, 3, 4],
        minimum_report_date="2014-01-01",
        maximum_acceptance_timestamp="2016-12-31T23:59:59Z",
    )

    assert len(features) == 4
    first = features.set_index("cik").loc["0000000001"]
    assert first["accession"] == "0000000001-16-000001"
    assert first["net_income"] == pytest.approx(6.0)
    assert first["earnings_surprise"] == pytest.approx(0.01)
    assert first["cashflow_surprise"] == pytest.approx(0.02)
    assert first["cash_conversion"] == pytest.approx(0.02)
    assert first["asset_discipline"] == pytest.approx(-0.01)
    assert first["availability_date"] == pd.Timestamp("2016-02-15")
    assert audit["post_cutoff_filing_rows_selected"] == 0
    assert audit["fact_resolution_counts"]["net_income:ok"] == 8


def test_extractor_fails_closed_on_conflicting_same_period_values(
    tmp_path: Path,
) -> None:
    companyfacts, submissions = _write_sec_archives(
        tmp_path, ambiguous_net_income=True
    )
    features, audit = extract_first_filed_sec_features(
        companyfacts,
        submissions,
        [1, 2, 3, 4],
        minimum_report_date="2014-01-01",
        maximum_acceptance_timestamp="2016-12-31T23:59:59Z",
    )

    assert set(features["cik"]) == {"0000000002", "0000000003", "0000000004"}
    assert audit["fact_resolution_counts"][
        "net_income:ambiguous_matching_period"
    ] == 1


def _write_frame_fixture(tmp_path: Path) -> tuple[pd.DataFrame, Path, Path, Path]:
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
    for date in pd.date_range("2016-12-31", "2022-12-31", freq="ME"):
        for number in range(1, 5):
            panel_rows.append(
                {
                    "permno": number,
                    "formation_date": date,
                    "industry": "One",
                    "eligible_at_formation": True,
                    "price": 50.0,
                    "market_cap_usd": 100_000_000.0,
                    "adv_60_usd": 100_000_000.0,
                    "volatility_126d": 0.02,
                    "full_spread_bps": 10.0,
                    "monthly_total_return": 0.01,
                    "delisting_pseudo_days": 0,
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
                    "earnings_surprise": float(number),
                    "cashflow_surprise": float(number),
                    "cash_conversion": float(number),
                    "asset_discipline": float(number),
                }
            )
    return pd.DataFrame(feature_rows), company_path, link_path, panel_path


def test_frame_enforces_acceptance_and_ranks_without_projecting_returns(
    tmp_path: Path,
) -> None:
    features, company, links, panel = _write_frame_fixture(tmp_path)
    protocol = {
        "windows": {
            "validation": {"start": "2017-01-01", "end": "2022-12-31"}
        }
    }
    frame, coverage, audit = _build_sec_vintage_frame(
        features,
        company,
        links,
        panel,
        protocol,
        include_outcomes=False,
    )

    december = frame.loc[frame["formation_date"].eq("2016-12-31")]
    scores = december.set_index("permno")["sec_cash_earnings_acceleration"]
    assert scores.loc[3] > scores.loc[2] > scores.loc[1]
    assert pd.isna(scores.loc[4])
    assert frame["monthly_total_return"].isna().all()
    assert frame["formation_date"].max() == pd.Timestamp("2022-12-31")
    assert len(coverage) == 72
    assert audit["panel_return_column_projected"] is False
    assert audit["post_2022_sec_fact_rows_selected"] == 0
    assert audit["final_holdout_outcomes_read"] is False


def test_sec_vintage_publication_refuses_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "preserve"
    marker.write_text("yes", encoding="utf-8")
    with pytest.raises(CRSPV2Error, match="Refusing to overwrite"):
        run_sec_vintage_mechanism(tmp_path / "contract.yaml", output)
    assert marker.read_text(encoding="utf-8") == "yes"

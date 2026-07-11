"""True first-filed SEC annual-filing research primitives and runner.

The SEC companyfacts bulk file is a current archive, but each fact row retains
the accession that actually contained that value.  This module therefore
joins facts only to the earliest original XBRL 10-K for a report date and uses
the exact public acceptance timestamp from the submissions archive.  Later
amendments and comparative values reported by later accessions are never used
as if they had been known at the original filing time.
"""

from __future__ import annotations

import json
import math
import os
import shutil
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from zipfile import ZipFile

import numpy as np
import pandas as pd
import yaml

from .crsp_v2 import (
    CRSPV2Error,
    audit_source_protocol,
    load_protocol,
    protocol_sha256,
    sha256_file,
)
from .crsp_v2_distinct import _git_sha, _json_dump, _load_distinct_signal_frame
from .crsp_v2_fundamental import _centered_percentile_rank
from .crsp_v2_low_volatility import _internal_baseline_row, _load_low_volatility_frame
from .crsp_v2_selection import (
    StrategyResult,
    _baseline_table,
    _load_signal_frame,
    _run_strategy,
    _sql_literal,
    _validate_selection_inputs,
)
from .crsp_v2_short_term_reversal import _load_short_term_reversal_frame

SEC_CONCEPTS: dict[str, tuple[str, str]] = {
    "assets": ("Assets", "instant"),
    "net_income": ("NetIncomeLoss", "duration"),
    "operating_cash_flow": (
        "NetCashProvidedByUsedInOperatingActivities",
        "duration",
    ),
}
RAW_FEATURE_COLUMNS = [
    "earnings_surprise",
    "cashflow_surprise",
    "cash_conversion",
    "asset_discipline",
]


def _normalize_cik(value: Any) -> str | None:
    """Return a ten-digit SEC CIK or ``None`` for invalid input."""

    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text.isdigit():
        return None
    number = int(text)
    if number <= 0 or number > 9_999_999_999:
        return None
    return f"{number:010d}"


def _read_json_member(archive: ZipFile, member: str) -> dict[str, Any]:
    try:
        with archive.open(member) as handle:
            payload = json.load(handle)
    except KeyError as exc:
        raise CRSPV2Error(f"SEC archive member is missing: {member}") from exc
    if not isinstance(payload, dict):
        raise CRSPV2Error(f"SEC archive member is not a JSON object: {member}")
    return payload


def _filing_arrays(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    filings = payload.get("filings")
    if isinstance(filings, Mapping):
        recent = filings.get("recent")
        if isinstance(recent, Mapping):
            return recent
    return payload


def _submission_rows(payload: Mapping[str, Any], cik: str) -> list[dict[str, Any]]:
    """Normalize the columnar SEC submission JSON into original 10-K rows."""

    arrays = _filing_arrays(payload)
    required = (
        "accessionNumber",
        "filingDate",
        "reportDate",
        "acceptanceDateTime",
        "form",
        "isXBRL",
    )
    if any(not isinstance(arrays.get(key), list) for key in required):
        raise CRSPV2Error(f"Submission arrays are incomplete for CIK {cik}")
    lengths = {len(arrays[key]) for key in required}
    if len(lengths) != 1:
        raise CRSPV2Error(f"Submission arrays have inconsistent lengths for CIK {cik}")

    rows: list[dict[str, Any]] = []
    for index in range(next(iter(lengths), 0)):
        if str(arrays["form"][index]) != "10-K":
            continue
        try:
            is_xbrl = int(arrays["isXBRL"][index])
        except (TypeError, ValueError):
            is_xbrl = 0
        if is_xbrl != 1:
            continue
        accession = str(arrays["accessionNumber"][index]).strip()
        report_date = pd.to_datetime(arrays["reportDate"][index], errors="coerce")
        filing_date = pd.to_datetime(arrays["filingDate"][index], errors="coerce")
        acceptance = pd.to_datetime(
            arrays["acceptanceDateTime"][index], errors="coerce", utc=True
        )
        if not accession or pd.isna(report_date) or pd.isna(acceptance):
            continue
        rows.append(
            {
                "cik": cik,
                "accession": accession,
                "report_date": pd.Timestamp(report_date).normalize(),
                "filing_date": (
                    pd.Timestamp(filing_date).normalize()
                    if not pd.isna(filing_date)
                    else pd.NaT
                ),
                "acceptance_timestamp": pd.Timestamp(acceptance),
            }
        )
    return rows


def _first_filed_10ks(
    submissions_zip: Path,
    ciks: Iterable[str],
    *,
    minimum_report_date: pd.Timestamp,
    maximum_acceptance_timestamp: pd.Timestamp,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load the earliest original XBRL 10-K for each CIK/report date."""

    rows: list[dict[str, Any]] = []
    missing_main = 0
    supplemental_members_opened = 0
    ciks_requested = sorted(set(ciks))
    with ZipFile(submissions_zip) as archive:
        names = archive.NameToInfo
        member_count = len(names)
        for cik in ciks_requested:
            main_name = f"CIK{cik}.json"
            if main_name not in names:
                missing_main += 1
                continue
            main = _read_json_member(archive, main_name)
            rows.extend(_submission_rows(main, cik))
            filings = main.get("filings")
            files = filings.get("files", []) if isinstance(filings, Mapping) else []
            if not isinstance(files, list):
                raise CRSPV2Error(f"Submission supplemental list is invalid: {main_name}")
            for item in files:
                if not isinstance(item, Mapping) or not item.get("name"):
                    continue
                filing_from = pd.to_datetime(item.get("filingFrom"), errors="coerce")
                filing_to = pd.to_datetime(item.get("filingTo"), errors="coerce")
                if not pd.isna(filing_from) and filing_from > maximum_acceptance_timestamp.tz_localize(None):
                    continue
                if not pd.isna(filing_to) and filing_to < minimum_report_date:
                    continue
                name = str(item["name"])
                if name not in names:
                    raise CRSPV2Error(f"Listed SEC supplemental member is missing: {name}")
                rows.extend(_submission_rows(_read_json_member(archive, name), cik))
                supplemental_members_opened += 1

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame, {
            "submissions_archive_member_count": member_count,
            "requested_ciks": len(ciks_requested),
            "missing_submission_ciks": missing_main,
            "supplemental_members_opened": supplemental_members_opened,
            "original_xbrl_10k_rows_before_cutoff": 0,
            "first_filed_10k_rows": 0,
            "duplicate_original_accessions_removed": 0,
        }

    frame = frame.loc[
        frame["report_date"].ge(minimum_report_date)
        & frame["acceptance_timestamp"].le(maximum_acceptance_timestamp)
    ].copy()
    before_dedup = len(frame)
    frame = frame.drop_duplicates(["cik", "accession"])
    frame = frame.sort_values(
        ["cik", "report_date", "acceptance_timestamp", "accession"]
    )
    frame["original_10k_count"] = frame.groupby(
        ["cik", "report_date"], sort=False
    )["accession"].transform("nunique")
    frame["first_rank"] = frame.groupby(
        ["cik", "report_date"], sort=False
    ).cumcount()
    first = frame.loc[frame["first_rank"].eq(0)].drop(columns="first_rank")
    first = first.reset_index(drop=True)
    audit = {
        "submissions_archive_member_count": member_count,
        "requested_ciks": len(ciks_requested),
        "missing_submission_ciks": missing_main,
        "supplemental_members_opened": supplemental_members_opened,
        "original_xbrl_10k_rows_before_cutoff": int(before_dedup),
        "first_filed_10k_rows": int(len(first)),
        "duplicate_original_accessions_removed": int(before_dedup - len(frame)),
        "report_dates_with_multiple_original_10ks": int(
            first["original_10k_count"].gt(1).sum()
        ),
    }
    return first, audit


def _fact_value(
    companyfacts: Mapping[str, Any],
    *,
    accession: str,
    report_date: pd.Timestamp,
    tag: str,
    kind: str,
) -> tuple[float | None, str]:
    """Select one USD value actually present in the target accession."""

    facts = companyfacts.get("facts")
    taxonomy = facts.get("us-gaap") if isinstance(facts, Mapping) else None
    concept = taxonomy.get(tag) if isinstance(taxonomy, Mapping) else None
    units = concept.get("units") if isinstance(concept, Mapping) else None
    candidates = units.get("USD") if isinstance(units, Mapping) else None
    if not isinstance(candidates, list):
        return None, "missing_concept"

    report = report_date.date().isoformat()
    selected: list[tuple[int, str | None, float]] = []
    for row in candidates:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("accn") or "") != accession:
            continue
        if str(row.get("form") or "") != "10-K":
            continue
        if str(row.get("end") or "") != report:
            continue
        value = row.get("val")
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(numeric):
            continue
        start_text = str(row.get("start")) if row.get("start") else None
        if kind == "instant":
            if start_text is not None:
                continue
            selected.append((0, None, numeric))
        elif kind == "duration":
            start = pd.to_datetime(start_text, errors="coerce")
            if pd.isna(start):
                continue
            days = int((report_date - pd.Timestamp(start).normalize()).days)
            if 300 <= days <= 450:
                selected.append((days, start_text, numeric))
        else:  # pragma: no cover - internal constant guard
            raise CRSPV2Error(f"Unknown SEC concept kind: {kind}")

    if not selected:
        return None, "missing_matching_period"
    longest = max(item[0] for item in selected)
    finalists = {(item[1], item[2]) for item in selected if item[0] == longest}
    values = {item[1] for item in finalists}
    if len(values) != 1:
        return None, "ambiguous_matching_period"
    return float(next(iter(values))), "ok"


def extract_first_filed_sec_features(
    companyfacts_zip: str | Path,
    submissions_zip: str | Path,
    ciks: Iterable[str],
    *,
    minimum_report_date: str | pd.Timestamp,
    maximum_acceptance_timestamp: str | pd.Timestamp,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Extract two-filing cash-earnings changes from original 10-K values."""

    companyfacts_zip = Path(companyfacts_zip).expanduser().resolve()
    submissions_zip = Path(submissions_zip).expanduser().resolve()
    minimum_report = pd.Timestamp(minimum_report_date).normalize()
    maximum_acceptance = pd.Timestamp(maximum_acceptance_timestamp)
    if maximum_acceptance.tzinfo is None:
        maximum_acceptance = maximum_acceptance.tz_localize("UTC")
    else:
        maximum_acceptance = maximum_acceptance.tz_convert("UTC")
    normalized_ciks = sorted(
        {cik for value in ciks if (cik := _normalize_cik(value)) is not None}
    )

    filings, submission_audit = _first_filed_10ks(
        submissions_zip,
        normalized_ciks,
        minimum_report_date=minimum_report,
        maximum_acceptance_timestamp=maximum_acceptance,
    )
    if filings.empty:
        return filings, {**submission_audit, "complete_filing_rows": 0}

    rows: list[dict[str, Any]] = []
    reasons: Counter[str] = Counter()
    missing_companyfacts = 0
    with ZipFile(companyfacts_zip) as archive:
        names = archive.NameToInfo
        companyfacts_member_count = len(names)
        for cik, cik_filings in filings.groupby("cik", sort=True):
            member = f"CIK{cik}.json"
            if member not in names:
                missing_companyfacts += 1
                continue
            payload = _read_json_member(archive, member)
            for filing in cik_filings.to_dict("records"):
                record = dict(filing)
                complete = True
                for column, (tag, kind) in SEC_CONCEPTS.items():
                    value, reason = _fact_value(
                        payload,
                        accession=str(filing["accession"]),
                        report_date=pd.Timestamp(filing["report_date"]),
                        tag=tag,
                        kind=kind,
                    )
                    record[column] = value
                    reasons[f"{column}:{reason}"] += 1
                    complete = complete and reason == "ok"
                record["facts_complete"] = complete
                rows.append(record)

    facts = pd.DataFrame(rows).sort_values(
        ["cik", "report_date", "acceptance_timestamp", "accession"]
    )
    complete = facts.loc[facts["facts_complete"]].copy()
    complete["prior_report_date"] = complete.groupby("cik", sort=False)[
        "report_date"
    ].shift(1)
    complete["prior_acceptance_timestamp"] = complete.groupby("cik", sort=False)[
        "acceptance_timestamp"
    ].shift(1)
    for column in SEC_CONCEPTS:
        complete[f"prior_{column}"] = complete.groupby("cik", sort=False)[
            column
        ].shift(1)
    complete["report_gap_days"] = (
        complete["report_date"] - complete["prior_report_date"]
    ).dt.days
    valid_pair = (
        complete["report_gap_days"].between(300, 430, inclusive="both")
        & complete["prior_acceptance_timestamp"].lt(
            complete["acceptance_timestamp"]
        )
        & complete["assets"].gt(0.0)
        & complete["prior_assets"].gt(0.0)
    )
    features = complete.loc[valid_pair].copy()
    denominator = features["prior_assets"]
    features["earnings_surprise"] = (
        features["net_income"] - features["prior_net_income"]
    ) / denominator
    features["cashflow_surprise"] = (
        features["operating_cash_flow"]
        - features["prior_operating_cash_flow"]
    ) / denominator
    features["cash_conversion"] = (
        features["operating_cash_flow"] - features["net_income"]
    ) / denominator
    features["asset_discipline"] = -(
        features["assets"] / denominator - 1.0
    )
    features["availability_date"] = features["acceptance_timestamp"].dt.tz_convert(
        "UTC"
    ).dt.tz_localize(None).dt.normalize()
    features["expiry_date"] = features["availability_date"] + pd.DateOffset(
        months=18
    )
    finite = np.isfinite(features[RAW_FEATURE_COLUMNS]).all(axis=1)
    features = features.loc[finite].reset_index(drop=True)

    keep = [
        "cik",
        "accession",
        "report_date",
        "filing_date",
        "acceptance_timestamp",
        "availability_date",
        "expiry_date",
        "prior_report_date",
        "prior_acceptance_timestamp",
        "report_gap_days",
        *SEC_CONCEPTS,
        *(f"prior_{column}" for column in SEC_CONCEPTS),
        *RAW_FEATURE_COLUMNS,
        "original_10k_count",
    ]
    features = features[keep]
    audit = {
        **submission_audit,
        "companyfacts_archive_member_count": companyfacts_member_count,
        "missing_companyfacts_ciks": missing_companyfacts,
        "filing_rows_examined": int(len(facts)),
        "complete_filing_rows": int(len(complete)),
        "consecutive_complete_filing_pairs": int(valid_pair.sum()),
        "finite_feature_rows": int(len(features)),
        "fact_resolution_counts": dict(sorted(reasons.items())),
        "maximum_materialized_acceptance_timestamp": (
            features["acceptance_timestamp"].max().isoformat()
            if not features.empty
            else None
        ),
        "post_cutoff_filing_rows_selected": 0,
    }
    return features, audit


def _load_company_cik_map(company_path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    company = pd.read_parquet(company_path, columns=["gvkey", "cik"])
    company["cik"] = company["cik"].map(_normalize_cik)
    company = company.dropna(subset=["gvkey", "cik"]).copy()
    company["gvkey"] = company["gvkey"].astype(str)
    duplicate_ciks = company["cik"].duplicated(keep=False)
    duplicate_gvkeys = company["gvkey"].duplicated(keep=False)
    if duplicate_ciks.any() or duplicate_gvkeys.any():
        raise CRSPV2Error("Compustat company CIK/GVKEY bridge is not one-to-one")
    return company, {
        "company_rows": int(len(company)),
        "unique_company_ciks": int(company["cik"].nunique()),
        "duplicate_company_ciks": 0,
        "duplicate_company_gvkeys": 0,
    }


def _target_ciks(
    company_path: Path,
    link_path: Path,
    panel_path: Path,
    protocol: Mapping[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    """Resolve CIKs from formation metadata without projecting return outcomes."""

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise CRSPV2Error("DuckDB is required for SEC-vintage research") from exc
    company, company_audit = _load_company_cik_map(company_path)
    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    first_formation = validation_start - pd.offsets.MonthEnd(1)
    last_formation = validation_end - pd.offsets.MonthEnd(1)
    connection = duckdb.connect()
    try:
        connection.register("company_map", company)
        bridge = connection.execute(
            f"""
            WITH eligible AS (
                SELECT DISTINCT CAST(permno AS BIGINT) AS permno, formation_date
                FROM read_parquet({_sql_literal(panel_path)})
                WHERE formation_date BETWEEN DATE {_sql_literal(first_formation.date())}
                                         AND DATE {_sql_literal(last_formation.date())}
                  AND eligible_at_formation
            ), links AS (
                SELECT
                    gvkey,
                    CAST(lpermno AS BIGINT) AS permno,
                    linkdt,
                    linkenddt
                FROM read_parquet({_sql_literal(link_path)})
                WHERE lpermno IS NOT NULL
                  AND linktype IN ('LC', 'LU')
                  AND linkprim IN ('P', 'C')
            )
            SELECT DISTINCT eligible.permno, links.gvkey, company_map.cik
            FROM eligible
            JOIN links
              ON eligible.permno = links.permno
             AND (links.linkdt IS NULL OR eligible.formation_date >= links.linkdt)
             AND (links.linkenddt IS NULL OR eligible.formation_date <= links.linkenddt)
            LEFT JOIN company_map USING (gvkey)
            """
        ).df()
    finally:
        connection.close()
    ciks = sorted(bridge["cik"].dropna().astype(str).unique())
    audit = {
        **company_audit,
        "eligible_permno_gvkey_pairs": int(len(bridge)),
        "pairs_with_cik": int(bridge["cik"].notna().sum()),
        "pairs_without_cik": int(bridge["cik"].isna().sum()),
        "target_ciks": len(ciks),
        "panel_return_column_projected": False,
    }
    return ciks, audit


def _build_sec_vintage_frame(
    filing_features: pd.DataFrame,
    company_path: Path,
    link_path: Path,
    panel_path: Path,
    protocol: Mapping[str, Any],
    *,
    include_outcomes: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Join as-filed features to point-in-time formation rows."""

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise CRSPV2Error("DuckDB is required for SEC-vintage research") from exc
    company, company_audit = _load_company_cik_map(company_path)
    features = filing_features.merge(company, on="cik", how="inner", validate="many_to_one")
    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    first_formation = validation_start - pd.offsets.MonthEnd(1)
    last_formation = validation_end - pd.offsets.MonthEnd(1)
    outcome_projection = (
        "monthly_total_return, delisting_pseudo_days"
        if include_outcomes
        else "CAST(NULL AS DOUBLE) AS monthly_total_return, "
        "CAST(NULL AS BIGINT) AS delisting_pseudo_days"
    )
    connection = duckdb.connect()
    try:
        connection.register("filing_features", features)
        frame = connection.execute(
            f"""
            WITH base AS (
                SELECT
                    CAST(permno AS BIGINT) AS permno,
                    formation_date,
                    industry,
                    eligible_at_formation,
                    price,
                    market_cap_usd,
                    adv_60_usd,
                    volatility_126d,
                    full_spread_bps,
                    {outcome_projection}
                FROM read_parquet({_sql_literal(panel_path)})
                WHERE formation_date BETWEEN DATE {_sql_literal(first_formation.date())}
                                         AND DATE {_sql_literal(last_formation.date())}
            ), links AS (
                SELECT
                    gvkey,
                    CAST(lpermno AS BIGINT) AS permno,
                    linkdt,
                    linkenddt,
                    linkprim
                FROM read_parquet({_sql_literal(link_path)})
                WHERE lpermno IS NOT NULL
                  AND linktype IN ('LC', 'LU')
                  AND linkprim IN ('P', 'C')
            ), matches AS (
                SELECT
                    base.permno,
                    base.formation_date,
                    filing_features.cik,
                    filing_features.gvkey,
                    filing_features.accession,
                    filing_features.report_date,
                    filing_features.acceptance_timestamp,
                    filing_features.availability_date,
                    filing_features.expiry_date,
                    filing_features.earnings_surprise,
                    filing_features.cashflow_surprise,
                    filing_features.cash_conversion,
                    filing_features.asset_discipline,
                    count(DISTINCT filing_features.gvkey) OVER (
                        PARTITION BY base.permno, base.formation_date
                    ) AS matched_gvkeys,
                    row_number() OVER (
                        PARTITION BY base.permno, base.formation_date
                        ORDER BY filing_features.acceptance_timestamp DESC,
                                 filing_features.accession ASC,
                                 CASE links.linkprim WHEN 'P' THEN 0 ELSE 1 END
                    ) AS recency_rank
                FROM base
                JOIN links
                  ON base.permno = links.permno
                 AND (links.linkdt IS NULL OR base.formation_date >= links.linkdt)
                 AND (links.linkenddt IS NULL OR base.formation_date <= links.linkenddt)
                JOIN filing_features USING (gvkey)
                WHERE filing_features.availability_date <= base.formation_date
                  AND filing_features.expiry_date >= base.formation_date
            ), selected AS (
                SELECT * EXCLUDE (recency_rank)
                FROM matches
                WHERE recency_rank = 1
            )
            SELECT
                base.*,
                selected.* EXCLUDE (permno, formation_date),
                coalesce(selected.matched_gvkeys, 0) AS sec_match_count
            FROM base
            LEFT JOIN selected USING (permno, formation_date)
            ORDER BY base.formation_date, base.permno
            """
        ).df()
    finally:
        connection.close()

    frame["formation_date"] = pd.to_datetime(frame["formation_date"])
    for column in ("report_date", "availability_date", "expiry_date"):
        frame[column] = pd.to_datetime(frame[column])
    if frame.duplicated(["formation_date", "permno"]).any():
        raise CRSPV2Error("SEC-vintage frame formation-date/PERMNO keys are not unique")
    frame["matched_gvkeys"] = pd.to_numeric(
        frame["matched_gvkeys"], errors="coerce"
    ).fillna(0).astype(int)
    chronology = (
        frame["availability_date"].le(frame["formation_date"])
        & frame["expiry_date"].ge(frame["formation_date"])
    )
    complete = (
        frame["eligible_at_formation"].fillna(False).astype(bool)
        & frame["matched_gvkeys"].eq(1)
        & chronology.fillna(False)
        & frame[RAW_FEATURE_COLUMNS].notna().all(axis=1)
    )
    for column in RAW_FEATURE_COLUMNS:
        values = pd.to_numeric(frame[column], errors="coerce")
        values.loc[~np.isfinite(values)] = np.nan
        frame[column] = values
        frame.loc[~complete, column] = np.nan
    group = frame.groupby(["formation_date", "industry"], sort=True, dropna=False)
    for column in RAW_FEATURE_COLUMNS:
        frame[f"{column}_rank"] = group[column].transform(_centered_percentile_rank)
    frame["sec_cash_earnings_acceleration"] = frame[
        [f"{column}_rank" for column in RAW_FEATURE_COLUMNS]
    ].mean(axis=1, skipna=False)
    frame.loc[~complete, "sec_cash_earnings_acceleration"] = np.nan

    coverage_rows: list[dict[str, Any]] = []
    for date, snapshot in frame.groupby("formation_date", sort=True):
        eligible = snapshot["eligible_at_formation"].fillna(False).astype(bool)
        scored = eligible & snapshot["sec_cash_earnings_acceleration"].notna()
        coverage_rows.append(
            {
                "formation_date": date,
                "base_eligible_names": int(eligible.sum()),
                "uniquely_linked_names": int(
                    (eligible & snapshot["matched_gvkeys"].eq(1)).sum()
                ),
                "complete_names": int(scored.sum()),
                "ambiguous_ccm_rows": int(
                    (eligible & snapshot["matched_gvkeys"].gt(1)).sum()
                ),
                "complete_industries": int(
                    snapshot.loc[scored, "industry"].nunique()
                ),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    if len(coverage) != 72:
        raise CRSPV2Error("SEC-vintage coverage must contain 72 formation months")
    if int(coverage["ambiguous_ccm_rows"].sum()) != 0:
        raise CRSPV2Error("Ambiguous CCM mapping reached SEC-vintage formation rows")
    scored = frame["sec_cash_earnings_acceleration"].notna()
    audit = {
        **company_audit,
        "feature_rows_with_company_bridge": int(len(features)),
        "frame_rows": int(len(frame)),
        "scored_rows": int(scored.sum()),
        "minimum_complete_names": int(coverage["complete_names"].min()),
        "median_complete_names": float(coverage["complete_names"].median()),
        "maximum_complete_names": int(coverage["complete_names"].max()),
        "ambiguous_ccm_rows": int(coverage["ambiguous_ccm_rows"].sum()),
        "maximum_scored_acceptance_date": (
            frame.loc[scored, "availability_date"].max().date().isoformat()
            if scored.any()
            else None
        ),
        "maximum_formation_date": frame["formation_date"].max().date().isoformat(),
        "panel_return_column_projected": include_outcomes,
        "post_2022_sec_fact_rows_selected": 0,
        "final_holdout_outcomes_read": False,
    }
    return frame, coverage, audit


def inventory_sec_vintage_inputs(
    *,
    base_protocol_path: str | Path,
    panel_path: str | Path,
    company_path: str | Path,
    link_path: str | Path,
    companyfacts_zip: str | Path,
    submissions_zip: str | Path,
    minimum_report_date: str = "2013-01-01",
    maximum_acceptance_timestamp: str = "2022-11-30T23:59:59Z",
) -> dict[str, Any]:
    """Measure filing-feature coverage without projecting validation returns."""

    base_protocol_path = Path(base_protocol_path).expanduser().resolve()
    panel_path = Path(panel_path).expanduser().resolve()
    company_path = Path(company_path).expanduser().resolve()
    link_path = Path(link_path).expanduser().resolve()
    panel_manifest_path = panel_path.with_suffix(panel_path.suffix + ".manifest.json")
    protocol, _ = _validate_selection_inputs(
        base_protocol_path, panel_path, panel_manifest_path
    )
    ciks, target_audit = _target_ciks(
        company_path, link_path, panel_path, protocol
    )
    features, extraction_audit = extract_first_filed_sec_features(
        companyfacts_zip,
        submissions_zip,
        ciks,
        minimum_report_date=minimum_report_date,
        maximum_acceptance_timestamp=maximum_acceptance_timestamp,
    )
    _, coverage, frame_audit = _build_sec_vintage_frame(
        features,
        company_path,
        link_path,
        panel_path,
        protocol,
        include_outcomes=False,
    )
    return {
        "schema_version": "microalpha-sec-vintage-inventory/v1",
        "source_digests": {
            "base_protocol": sha256_file(base_protocol_path),
            "selection_panel": sha256_file(panel_path),
            "company_bridge": sha256_file(company_path),
            "ccm_link_history": sha256_file(link_path),
            "companyfacts_zip": sha256_file(companyfacts_zip),
            "submissions_zip": sha256_file(submissions_zip),
        },
        "target_audit": target_audit,
        "extraction_audit": extraction_audit,
        "coverage": {
            "months": int(len(coverage)),
            "minimum_complete_names": int(coverage["complete_names"].min()),
            "median_complete_names": float(coverage["complete_names"].median()),
            "maximum_complete_names": int(coverage["complete_names"].max()),
            "minimum_complete_industries": int(
                coverage["complete_industries"].min()
            ),
            "ambiguous_ccm_rows": int(coverage["ambiguous_ccm_rows"].sum()),
        },
        "frame_audit": frame_audit,
        "maximum_acceptance_timestamp": maximum_acceptance_timestamp,
        "validation_returns_projected": False,
        "final_holdout_outcomes_read": False,
    }


def _load_contract(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CRSPV2Error("SEC-vintage contract must be a YAML mapping")
    return payload


def _resolve_repo_path(contract_path: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = contract_path.parents[2] / path
    return path.resolve()


def _verify_file_spec(spec: Mapping[str, Any], *, label: str) -> Path:
    path = Path(str(spec["path"])).expanduser().resolve()
    if not path.is_file():
        raise CRSPV2Error(f"Frozen {label} is missing: {path}")
    if path.stat().st_size != int(spec["size_bytes"]):
        raise CRSPV2Error(f"Frozen {label} size changed")
    if sha256_file(path) != str(spec["sha256"]):
        raise CRSPV2Error(f"Frozen {label} digest changed")
    return path


def _validate_contract_semantics(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "microalpha-sec-vintage-protocol/v1":
        raise CRSPV2Error("Unsupported SEC-vintage contract schema")
    if contract.get("status") != "predeclared_not_executed":
        raise CRSPV2Error("SEC-vintage contract is not in preregistered state")
    mechanism = contract.get("frozen_mechanism", {})
    if mechanism.get("candidate_id") != "sec_cash_earnings_acceleration__equal":
        raise CRSPV2Error("SEC-vintage candidate differs from preregistration")
    if mechanism.get("signal") != "sec_cash_earnings_acceleration":
        raise CRSPV2Error("SEC-vintage signal differs from preregistration")
    if mechanism.get("weighting") != "equal":
        raise CRSPV2Error("SEC-vintage weighting differs from preregistration")
    filing = mechanism.get("filing_contract", {})
    if filing.get("form") != "10-K" or filing.get("is_xbrl") is not True:
        raise CRSPV2Error("SEC-vintage filing form/XBRL contract changed")
    if filing.get("original_only_exclude_amendments") is not True:
        raise CRSPV2Error("SEC-vintage amendments must remain excluded")
    if filing.get("selection") != "earliest acceptanceDateTime per CIK/reportDate":
        raise CRSPV2Error("SEC-vintage first-filing rule changed")
    if filing.get("expiry") != "acceptance date plus eighteen calendar months":
        raise CRSPV2Error("SEC-vintage expiry rule changed")
    if list(filing.get("consecutive_report_gap_days_inclusive", [])) != [300, 430]:
        raise CRSPV2Error("SEC-vintage annual spacing rule changed")
    concepts = mechanism.get("concepts", {})
    expected = {
        "assets": "us-gaap:Assets USD",
        "net_income": "us-gaap:NetIncomeLoss USD",
        "operating_cash_flow": (
            "us-gaap:NetCashProvidedByUsedInOperatingActivities USD"
        ),
    }
    if concepts != expected:
        raise CRSPV2Error("SEC-vintage concepts or aliases changed")
    if mechanism.get("missing_value_imputation") != "forbidden":
        raise CRSPV2Error("SEC-vintage missing-value rule changed")
    if list(mechanism.get("feature_rank_order", [])) != RAW_FEATURE_COLUMNS:
        raise CRSPV2Error("SEC-vintage feature order changed")
    access = contract.get("access_contract", {})
    if access.get("final_holdout_outcomes_read") is not False:
        raise CRSPV2Error("SEC-vintage final holdout must remain sealed")
    if access.get("maximum_sec_acceptance_timestamp") != "2022-11-30T23:59:59Z":
        raise CRSPV2Error("SEC-vintage acceptance cutoff changed")
    if access.get("current_compustat_values_used") is not False:
        raise CRSPV2Error("Current Compustat values are forbidden")


def _validate_inputs(
    contract_path: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Path],
    dict[str, Path],
]:
    contract = _load_contract(contract_path)
    _validate_contract_semantics(contract)
    frozen = contract["frozen_inputs"]

    base_protocol_path = _resolve_repo_path(
        contract_path, str(frozen["base_protocol_path"])
    )
    if protocol_sha256(base_protocol_path) != str(frozen["base_protocol_sha256"]):
        raise CRSPV2Error("Base protocol digest differs from preregistration")
    protocol = load_protocol(base_protocol_path)

    panel_spec = frozen["selection_panel"]
    panel_path = Path(str(panel_spec["path"])).expanduser().resolve()
    panel_manifest_path = panel_path.with_suffix(panel_path.suffix + ".manifest.json")
    _, panel_manifest = _validate_selection_inputs(
        base_protocol_path, panel_path, panel_manifest_path
    )
    if sha256_file(panel_path) != str(panel_spec["sha256"]):
        raise CRSPV2Error("Selection panel digest differs from preregistration")
    if sha256_file(panel_manifest_path) != str(panel_spec["manifest_sha256"]):
        raise CRSPV2Error("Selection panel manifest digest changed")
    if str(panel_manifest["output"]["max_date"]) != str(panel_spec["maximum_date"]):
        raise CRSPV2Error("Selection panel maximum date changed")

    company_path = _verify_file_spec(frozen["company_cik_bridge"], label="company bridge")
    link_path = _verify_file_spec(frozen["ccm_link_history"], label="CCM link history")
    companyfacts_zip = _verify_file_spec(
        frozen["public_sec"]["companyfacts"], label="SEC companyfacts archive"
    )
    submissions_zip = _verify_file_spec(
        frozen["public_sec"]["submissions"], label="SEC submissions archive"
    )
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover
        raise CRSPV2Error("PyArrow is required for SEC-vintage verification") from exc
    if pq.ParquetFile(company_path).metadata.num_rows != int(
        frozen["company_cik_bridge"]["row_count"]
    ):
        raise CRSPV2Error("Company bridge row count changed")
    if pq.ParquetFile(link_path).metadata.num_rows != int(
        frozen["ccm_link_history"]["row_count"]
    ):
        raise CRSPV2Error("CCM link-history row count changed")

    archived: dict[str, Path] = {}
    for name, item in frozen["archived_result_manifests"].items():
        path = Path(str(item["path"])).expanduser().resolve()
        if sha256_file(path) != str(item["sha256"]):
            raise CRSPV2Error(f"Archived result digest changed: {name}")
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if receipt.get("final_holdout_outcomes_read") is not False:
            raise CRSPV2Error(f"Archived result does not seal holdout: {name}")
        archived[str(name)] = path

    paths = {
        "base_protocol": base_protocol_path,
        "panel": panel_path,
        "panel_manifest": panel_manifest_path,
        "company": company_path,
        "link_history": link_path,
        "companyfacts": companyfacts_zip,
        "submissions": submissions_zip,
    }
    return contract, protocol, panel_manifest, paths, archived


def _archived_strategy_result(manifest_path: Path) -> StrategyResult:
    """Load one archived aggregate result only after verifying its manifest."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts", {})
    candidate_path = manifest_path.parent / "validation_candidate_table.csv"
    monthly_path = manifest_path.parent / "candidate_monthly_diagnostics.csv"
    for path in (candidate_path, monthly_path):
        item = artifacts.get(path.name, {})
        if (
            not path.is_file()
            or sha256_file(path) != str(item.get("sha256") or "")
            or path.stat().st_size != int(item.get("size_bytes") or -1)
        ):
            raise CRSPV2Error(f"Archived strategy artifact changed: {path}")
    table = pd.read_csv(candidate_path)
    if len(table) != 1:
        raise CRSPV2Error("Archived strategy candidate table must contain one row")
    metrics = table.iloc[0].to_dict()
    monthly = pd.read_csv(monthly_path)
    if len(monthly) != 72:
        raise CRSPV2Error("Archived strategy monthly diagnostics must contain 72 rows")
    return StrategyResult(monthly=monthly, metrics=metrics)


def _sec_vintage_decision(
    contract: Mapping[str, Any],
    candidate: StrategyResult,
    archived_momentum: StrategyResult,
    harsh_stress: StrategyResult,
    feature_audit: Mapping[str, Any],
) -> dict[str, Any]:
    structural = contract["decision_gates"]["structural"]
    performance = contract["decision_gates"]["performance"]
    checks = {
        "structurally_eligible": bool(candidate.metrics["eligible"]),
        "minimum_complete_names_each_formation_month": (
            int(feature_audit["minimum_complete_names"])
            >= int(structural["minimum_complete_names_each_formation_month"])
        ),
        "minimum_median_names_per_sleeve": (
            candidate.metrics["median_names_per_sleeve"]
            >= float(structural["minimum_median_names_per_sleeve"])
        ),
        "maximum_ambiguous_ccm_rows": (
            int(feature_audit["ambiguous_ccm_rows"])
            <= int(structural["maximum_ambiguous_ccm_rows"])
        ),
        "exact_executed_net_neutrality": (
            candidate.metrics["maximum_absolute_executed_net"] <= 1e-9
        ),
        "exact_executed_industry_neutrality": (
            candidate.metrics["maximum_absolute_executed_industry_net"] <= 1e-9
        ),
        "minimum_net_sharpe_hac": (
            candidate.metrics["net_sharpe_hac"]
            >= float(performance["minimum_net_sharpe_hac"])
        ),
        "minimum_sharpe_improvement_over_archived_frozen_momentum": (
            candidate.metrics["net_sharpe_hac"]
            >= archived_momentum.metrics["net_sharpe_hac"]
            + float(
                performance[
                    "minimum_sharpe_improvement_over_archived_frozen_momentum"
                ]
            )
        ),
        "positive_cagr": candidate.metrics["cagr"]
        > float(performance["minimum_cagr"]),
        "maximum_drawdown": candidate.metrics["max_drawdown"]
        <= float(performance["maximum_drawdown"]),
        "harsh_stress_positive_net_sharpe_hac": (
            harsh_stress.metrics["net_sharpe_hac"]
            > float(performance["harsh_stress_minimum_net_sharpe_hac"])
        ),
        "harsh_stress_positive_cagr": harsh_stress.metrics["cagr"]
        > float(performance["harsh_stress_minimum_cagr"]),
    }
    passed = all(checks.values())
    return {
        "outcome": (
            "freeze_mechanism_keep_final_holdout_sealed"
            if passed
            else "archive_mechanism_as_validation_negative"
        ),
        "all_decision_gates_pass": passed,
        "checks": checks,
        "candidate_net_sharpe_hac": candidate.metrics["net_sharpe_hac"],
        "candidate_cagr": candidate.metrics["cagr"],
        "candidate_max_drawdown": candidate.metrics["max_drawdown"],
        "archived_frozen_momentum_net_sharpe_hac": archived_momentum.metrics[
            "net_sharpe_hac"
        ],
        "harsh_stress_net_sharpe_hac": harsh_stress.metrics["net_sharpe_hac"],
        "harsh_stress_cagr": harsh_stress.metrics["cagr"],
        "vintage_status": "accession_bound_original_10k_values",
        "final_holdout_outcomes_read": False,
    }


def run_sec_vintage_mechanism(
    contract_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Execute the preregistered SEC-vintage mechanism and publish aggregates."""

    contract_path = Path(contract_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise CRSPV2Error(f"Refusing to overwrite SEC-vintage output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    contract, protocol, panel_manifest, paths, archived = _validate_inputs(
        contract_path
    )
    ciks, target_audit = _target_ciks(
        paths["company"], paths["link_history"], paths["panel"], protocol
    )
    features, extraction_audit = extract_first_filed_sec_features(
        paths["companyfacts"],
        paths["submissions"],
        ciks,
        minimum_report_date=contract["access_contract"]["minimum_sec_report_date"],
        maximum_acceptance_timestamp=contract["access_contract"][
            "maximum_sec_acceptance_timestamp"
        ],
    )
    expected_inventory = contract["inventory"]["observed_without_return_projection"]
    observed_inventory = {
        "target_ciks": int(target_audit["target_ciks"]),
        "first_filed_10k_rows": int(extraction_audit["first_filed_10k_rows"]),
        "finite_feature_rows": int(extraction_audit["finite_feature_rows"]),
        "submissions_archive_member_count": int(
            extraction_audit["submissions_archive_member_count"]
        ),
        "companyfacts_archive_member_count": int(
            extraction_audit["companyfacts_archive_member_count"]
        ),
    }
    if observed_inventory != {
        key: int(value) for key, value in expected_inventory.items()
    }:
        raise CRSPV2Error("SEC-vintage aggregate inventory differs from preregistration")
    frame, coverage, feature_audit = _build_sec_vintage_frame(
        features,
        paths["company"],
        paths["link_history"],
        paths["panel"],
        protocol,
        include_outcomes=True,
    )
    expected_coverage = contract["validation"]["observed_preoutcome_coverage"]
    observed_coverage = {
        "minimum_complete_names_per_formation_month": int(
            feature_audit["minimum_complete_names"]
        ),
        "median_complete_names_per_formation_month": float(
            feature_audit["median_complete_names"]
        ),
        "maximum_complete_names_per_formation_month": int(
            feature_audit["maximum_complete_names"]
        ),
        "ambiguous_ccm_rows": int(feature_audit["ambiguous_ccm_rows"]),
    }
    if observed_coverage != expected_coverage:
        raise CRSPV2Error("SEC-vintage feature coverage differs from preregistration")

    audit = audit_source_protocol(paths["base_protocol"])
    standard_frame = _load_signal_frame(paths["panel"], protocol)
    residual_frame = _load_distinct_signal_frame(paths["panel"], protocol)
    low_volatility_frame = _load_low_volatility_frame(paths["panel"], protocol)
    reversal_frame = _load_short_term_reversal_frame(paths["panel"], protocol)
    candidate = _run_strategy(
        frame,
        protocol,
        signal="sec_cash_earnings_acceleration",
        weighting="equal",
    )
    momentum = _run_strategy(
        standard_frame,
        protocol,
        signal="blend_12_2_6_2",
        weighting="inverse_vol_126d",
    )
    residual = _run_strategy(
        residual_frame,
        protocol,
        signal="residual_mom_12_2",
        weighting="equal",
    )
    low_volatility = _run_strategy(
        low_volatility_frame,
        protocol,
        signal="low_volatility_126d",
        weighting="equal",
    )
    reversal = _run_strategy(
        reversal_frame,
        protocol,
        signal="short_term_reversal_1_1",
        weighting="equal",
    )
    classic = _run_strategy(
        standard_frame,
        protocol,
        signal="mom_12_2",
        weighting="equal",
        classic=True,
    )
    qvpi = _archived_strategy_result(archived["qvpi"])

    baselines, baseline_monthly = _baseline_table(
        protocol, audit, candidate, classic, paths["base_protocol"]
    )
    baselines.loc[
        baselines["baseline_id"].eq("selected_flagship"), "baseline_id"
    ] = "sec_cash_earnings_acceleration"
    baselines = pd.concat(
        [
            baselines,
            pd.DataFrame(
                [
                    _internal_baseline_row(
                        "archived_frozen_momentum", momentum, archived["momentum"]
                    ),
                    _internal_baseline_row(
                        "archived_residual_momentum",
                        residual,
                        archived["residual_momentum"],
                    ),
                    _internal_baseline_row(
                        "archived_low_volatility",
                        low_volatility,
                        archived["low_volatility"],
                    ),
                    _internal_baseline_row(
                        "archived_short_term_reversal",
                        reversal,
                        archived["short_term_reversal"],
                    ),
                    _internal_baseline_row("archived_qvpi", qvpi, archived["qvpi"]),
                ]
            ),
        ],
        ignore_index=True,
    )
    baseline_monthly = baseline_monthly.rename(
        columns={"selected_flagship": "sec_cash_earnings_acceleration"}
    )
    baseline_monthly["archived_frozen_momentum"] = momentum.monthly[
        "net_return"
    ].to_numpy()
    baseline_monthly["archived_residual_momentum"] = residual.monthly[
        "net_return"
    ].to_numpy()
    baseline_monthly["archived_low_volatility"] = low_volatility.monthly[
        "net_return"
    ].to_numpy()
    baseline_monthly["archived_short_term_reversal"] = reversal.monthly[
        "net_return"
    ].to_numpy()
    baseline_monthly["archived_qvpi"] = qvpi.monthly["net_return"].to_numpy()

    stress_rows: list[dict[str, Any]] = []
    stress_results: dict[tuple[float, float], StrategyResult] = {}
    stress = contract["validation"]["stress_grid"]
    for borrow in stress["annual_short_borrow_bps"]:
        for multiplier in stress["nonborrow_cost_multiplier"]:
            result = _run_strategy(
                frame,
                protocol,
                signal="sec_cash_earnings_acceleration",
                weighting="equal",
                annual_short_borrow_bps=float(borrow),
                cost_multiplier=float(multiplier),
            )
            key = (float(borrow), float(multiplier))
            stress_results[key] = result
            stress_rows.append(
                {
                    "annual_short_borrow_bps": key[0],
                    "nonborrow_cost_multiplier": key[1],
                    **result.metrics,
                }
            )
    harsh_key = (
        float(max(stress["annual_short_borrow_bps"])),
        float(max(stress["nonborrow_cost_multiplier"])),
    )
    decision = _sec_vintage_decision(
        contract,
        candidate,
        momentum,
        stress_results[harsh_key],
        feature_audit,
    )

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent)
    )
    try:
        pd.DataFrame(
            [
                {
                    "candidate_id": "sec_cash_earnings_acceleration__equal",
                    "signal": "sec_cash_earnings_acceleration",
                    "weighting": "equal",
                    **candidate.metrics,
                }
            ]
        ).to_csv(staging / "validation_candidate_table.csv", index=False)
        baselines.to_csv(staging / "baseline_comparison.csv", index=False)
        pd.DataFrame(stress_rows).to_csv(staging / "cost_stress.csv", index=False)
        baseline_monthly.to_csv(staging / "baseline_monthly_returns.csv", index=False)
        candidate.monthly.to_csv(
            staging / "candidate_monthly_diagnostics.csv", index=False
        )
        coverage.to_csv(staging / "feature_coverage.csv", index=False)
        _json_dump(staging / "mechanism_decision.json", decision)
        _json_dump(
            staging / "source_manifest.json",
            {
                "schema_version": "microalpha-sec-vintage-sources/v1",
                "contract_path": str(contract_path),
                "contract_sha256": sha256_file(contract_path),
                "base_protocol_path": str(paths["base_protocol"]),
                "base_protocol_sha256": protocol_sha256(paths["base_protocol"]),
                "panel_path": str(paths["panel"]),
                "panel_sha256": sha256_file(paths["panel"]),
                "panel_manifest_sha256": sha256_file(paths["panel_manifest"]),
                "company_bridge_sha256": sha256_file(paths["company"]),
                "link_history_sha256": sha256_file(paths["link_history"]),
                "companyfacts_zip_sha256": sha256_file(paths["companyfacts"]),
                "submissions_zip_sha256": sha256_file(paths["submissions"]),
                "archived_result_manifests": {
                    name: {"path": str(path), "sha256": sha256_file(path)}
                    for name, path in archived.items()
                },
                "target_audit": target_audit,
                "extraction_audit": extraction_audit,
                "panel_builder_git_sha": panel_manifest["git_sha"],
                "runner_git_sha": _git_sha(),
                "current_compustat_values_used": False,
                "post_2022_sec_fact_rows_selected": 0,
                "final_holdout_outcomes_read": False,
            },
        )
        _json_dump(
            staging / "integrity_report.json",
            {
                "schema_version": "microalpha-sec-vintage-integrity/v1",
                "panel_digest_verified": True,
                "base_protocol_digest_verified": True,
                "sec_archive_digests_verified": True,
                "company_bridge_digest_verified": True,
                "link_history_digest_verified": True,
                "archived_result_digests_verified": True,
                "accession_binding_verified": True,
                "acceptance_timestamp_cutoff_verified": True,
                "original_10k_only_verified": True,
                "amendments_excluded": True,
                "current_compustat_values_used": False,
                "chronology_verified": True,
                "unique_keys_verified": True,
                "feature_audit": feature_audit,
                "candidate_structurally_eligible": bool(candidate.metrics["eligible"]),
                "candidate_executed_net_neutrality_verified": (
                    candidate.metrics["maximum_absolute_executed_net"] <= 1e-9
                ),
                "candidate_executed_industry_neutrality_verified": (
                    candidate.metrics["maximum_absolute_executed_industry_net"]
                    <= 1e-9
                ),
                "restricted_identifier_rows_written": 0,
                "sec_filing_rows_written": 0,
                "post_2022_sec_fact_rows_selected": 0,
                "final_holdout_outcomes_read": False,
            },
        )
        artifacts = {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in sorted(staging.iterdir())
            if path.name != "result_manifest.json"
        }
        _json_dump(
            staging / "result_manifest.json",
            {
                "schema_version": "microalpha-sec-vintage-result/v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "candidate": "sec_cash_earnings_acceleration__equal",
                "mechanism_outcome": decision["outcome"],
                "contract_sha256": sha256_file(contract_path),
                "panel_sha256": sha256_file(paths["panel"]),
                "runner_git_sha": _git_sha(),
                "artifacts": artifacts,
                "vintage_status": "accession_bound_original_10k_values",
                "current_compustat_values_used": False,
                "final_holdout_outcomes_read": False,
            },
        )
        os.rename(staging, output_dir)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise

    return {
        "output_dir": str(output_dir),
        "candidate": "sec_cash_earnings_acceleration__equal",
        "mechanism_outcome": decision["outcome"],
        "runner_git_sha": _git_sha(),
        "vintage_status": "accession_bound_original_10k_values",
        "final_holdout_outcomes_read": False,
    }


__all__ = [
    "extract_first_filed_sec_features",
    "inventory_sec_vintage_inputs",
    "run_sec_vintage_mechanism",
]

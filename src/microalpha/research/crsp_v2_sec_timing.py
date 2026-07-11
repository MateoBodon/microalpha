"""Point-in-time SEC annual reporting-timeliness research primitives."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
import yaml

from .crsp_v2 import (
    CRSPV2Error,
    audit_source_protocol,
    protocol_sha256,
    sha256_file,
)
from .crsp_v2_fundamental import _centered_percentile_rank
from .crsp_v2_low_volatility import _internal_baseline_row
from .crsp_v2_sec_vintage import (
    _archived_strategy_result,
    _first_filed_10ks,
    _load_company_cik_map,
    _normalize_cik,
    _target_ciks,
)
from .crsp_v2_selection import (
    StrategyResult,
    _baseline_table,
    _git_sha,
    _load_signal_frame,
    _run_strategy,
    _sql_literal,
    _validate_selection_inputs,
)

TIMING_FEATURE_COLUMNS = ["reporting_timeliness_level", "reporting_timeliness_change"]
AGGREGATE_COVERAGE_COLUMNS = [
    "formation_date",
    "base_eligible_names",
    "complete_names",
    "ambiguous_ccm_rows",
    "complete_industries",
]
TARGET_AUDIT_RECEIPT_KEYS = (
    "company_rows",
    "unique_company_ciks",
    "duplicate_company_ciks",
    "duplicate_company_gvkeys",
    "eligible_permno_gvkey_pairs",
    "pairs_with_cik",
    "pairs_without_cik",
    "target_ciks",
    "panel_return_column_projected",
)
EXTRACTION_AUDIT_RECEIPT_KEYS = (
    "submissions_archive_member_count",
    "requested_ciks",
    "missing_submission_ciks",
    "supplemental_members_opened",
    "original_xbrl_10k_rows_before_cutoff",
    "first_filed_10k_rows",
    "duplicate_original_accessions_removed",
    "report_dates_with_multiple_original_10ks",
    "valid_delay_rows",
    "consecutive_timing_pairs",
    "ciks_with_timing_pairs",
    "minimum_selected_delay_days",
    "maximum_selected_delay_days",
    "maximum_selected_acceptance_timestamp",
    "post_cutoff_filing_rows_selected",
    "return_columns_projected",
)
FRAME_AUDIT_RECEIPT_KEYS = (
    "company_rows",
    "unique_company_ciks",
    "duplicate_company_ciks",
    "duplicate_company_gvkeys",
    "feature_rows_with_company_bridge",
    "frame_rows",
    "scored_rows",
    "minimum_complete_names",
    "median_complete_names",
    "maximum_complete_names",
    "minimum_complete_industries",
    "ambiguous_ccm_rows",
    "coverage_formation_months",
    "minimum_formation_date",
    "maximum_formation_date",
    "maximum_scored_acceptance_timestamp",
    "selected_rows_available_after_formation",
    "selected_rows_expired_before_formation",
    "panel_columns_projected",
    "return_columns_projected",
    "validation_outcomes_read",
    "final_holdout_outcomes_read",
)


def extract_first_filed_sec_timing(
    submissions_zip: str | Path,
    ciks: Iterable[str],
    *,
    minimum_report_date: str | pd.Timestamp,
    maximum_acceptance_timestamp: str | pd.Timestamp,
    minimum_delay_days: int = 1,
    maximum_delay_days: int = 200,
    minimum_report_gap_days: int = 300,
    maximum_report_gap_days: int = 430,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Extract reporting-delay level and change from consecutive original 10-Ks."""

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
    filings, source_audit = _first_filed_10ks(
        submissions_zip,
        normalized_ciks,
        minimum_report_date=minimum_report,
        maximum_acceptance_timestamp=maximum_acceptance,
    )
    if filings.empty:
        return filings, {
            **source_audit,
            "valid_delay_rows": 0,
            "consecutive_timing_pairs": 0,
            "post_cutoff_filing_rows_selected": 0,
            "return_columns_projected": False,
        }

    filings = filings.sort_values(
        ["cik", "report_date", "acceptance_timestamp", "accession"]
    ).copy()
    acceptance_day = (
        filings["acceptance_timestamp"].dt.tz_convert("UTC").dt.tz_localize(None)
    ).dt.normalize()
    filings["reporting_delay_days"] = (acceptance_day - filings["report_date"]).dt.days
    filings["prior_report_date"] = filings.groupby("cik", sort=False)[
        "report_date"
    ].shift(1)
    filings["prior_acceptance_timestamp"] = filings.groupby("cik", sort=False)[
        "acceptance_timestamp"
    ].shift(1)
    filings["prior_reporting_delay_days"] = filings.groupby("cik", sort=False)[
        "reporting_delay_days"
    ].shift(1)
    filings["report_gap_days"] = (
        filings["report_date"] - filings["prior_report_date"]
    ).dt.days
    valid_delay = filings["reporting_delay_days"].between(
        minimum_delay_days, maximum_delay_days, inclusive="both"
    )
    valid_pair = (
        valid_delay
        & filings["prior_reporting_delay_days"].between(
            minimum_delay_days, maximum_delay_days, inclusive="both"
        )
        & filings["report_gap_days"].between(
            minimum_report_gap_days, maximum_report_gap_days, inclusive="both"
        )
        & filings["prior_acceptance_timestamp"].lt(filings["acceptance_timestamp"])
    )
    features = filings.loc[valid_pair].copy()
    features["reporting_timeliness_level"] = -features["reporting_delay_days"].astype(
        float
    )
    features["reporting_timeliness_change"] = (
        features["prior_reporting_delay_days"] - features["reporting_delay_days"]
    ).astype(float)
    features["availability_date"] = acceptance_day.loc[features.index]
    features["expiry_date"] = features["availability_date"] + pd.DateOffset(months=18)
    finite = np.isfinite(features[TIMING_FEATURE_COLUMNS]).all(axis=1)
    features = features.loc[finite].reset_index(drop=True)
    keep = [
        "cik",
        "accession",
        "report_date",
        "filing_date",
        "acceptance_timestamp",
        "availability_date",
        "expiry_date",
        "reporting_delay_days",
        "prior_report_date",
        "prior_acceptance_timestamp",
        "prior_reporting_delay_days",
        "report_gap_days",
        *TIMING_FEATURE_COLUMNS,
        "original_10k_count",
    ]
    features = features[keep]
    audit = {
        **source_audit,
        "valid_delay_rows": int(valid_delay.sum()),
        "consecutive_timing_pairs": int(len(features)),
        "ciks_with_timing_pairs": int(features["cik"].nunique()),
        "minimum_selected_delay_days": (
            int(features["reporting_delay_days"].min()) if not features.empty else None
        ),
        "maximum_selected_delay_days": (
            int(features["reporting_delay_days"].max()) if not features.empty else None
        ),
        "maximum_selected_acceptance_timestamp": (
            features["acceptance_timestamp"].max().isoformat()
            if not features.empty
            else None
        ),
        "post_cutoff_filing_rows_selected": 0,
        "return_columns_projected": False,
    }
    return features, audit


def build_sec_timing_scores(
    timing_features: pd.DataFrame,
    company_path: str | Path,
    link_path: str | Path,
    panel_path: str | Path,
    protocol: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Join filing timing to formation metadata without projecting outcomes."""

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise CRSPV2Error("DuckDB is required for SEC-timing research") from exc
    company_path = Path(company_path).expanduser().resolve()
    link_path = Path(link_path).expanduser().resolve()
    panel_path = Path(panel_path).expanduser().resolve()
    company, company_audit = _load_company_cik_map(company_path)
    features = timing_features.merge(
        company, on="cik", how="inner", validate="many_to_one"
    )
    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    first_formation = validation_start - pd.offsets.MonthEnd(1)
    last_formation = validation_end - pd.offsets.MonthEnd(1)
    connection = duckdb.connect()
    try:
        connection.register("timing_features", features)
        frame = connection.execute(
            f"""
            WITH base AS (
                SELECT
                    CAST(permno AS BIGINT) AS permno,
                    formation_date,
                    industry,
                    eligible_at_formation
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
                    timing_features.cik,
                    timing_features.gvkey,
                    timing_features.accession,
                    timing_features.report_date,
                    timing_features.acceptance_timestamp,
                    timing_features.availability_date,
                    timing_features.expiry_date,
                    timing_features.reporting_delay_days,
                    timing_features.prior_reporting_delay_days,
                    timing_features.reporting_timeliness_level,
                    timing_features.reporting_timeliness_change,
                    count(DISTINCT timing_features.gvkey) OVER (
                        PARTITION BY base.permno, base.formation_date
                    ) AS matched_gvkeys,
                    row_number() OVER (
                        PARTITION BY base.permno, base.formation_date
                        ORDER BY timing_features.acceptance_timestamp DESC,
                                 timing_features.accession ASC,
                                 CASE links.linkprim WHEN 'P' THEN 0 ELSE 1 END
                    ) AS recency_rank
                FROM base
                JOIN links
                  ON base.permno = links.permno
                 AND (links.linkdt IS NULL OR base.formation_date >= links.linkdt)
                 AND (links.linkenddt IS NULL OR base.formation_date <= links.linkenddt)
                JOIN timing_features USING (gvkey)
                WHERE timing_features.availability_date <= base.formation_date
                  AND timing_features.expiry_date >= base.formation_date
            ), selected AS (
                SELECT * EXCLUDE (recency_rank)
                FROM matches
                WHERE recency_rank = 1
            )
            SELECT
                base.*,
                selected.* EXCLUDE (permno, formation_date),
                coalesce(selected.matched_gvkeys, 0) AS sec_timing_match_count
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
        raise CRSPV2Error("SEC-timing frame formation-date/PERMNO keys are not unique")
    frame["matched_gvkeys"] = (
        pd.to_numeric(frame["matched_gvkeys"], errors="coerce").fillna(0).astype(int)
    )
    chronology = frame["availability_date"].le(frame["formation_date"]) & frame[
        "expiry_date"
    ].ge(frame["formation_date"])
    complete = (
        frame["eligible_at_formation"].fillna(False).astype(bool)
        & frame["matched_gvkeys"].eq(1)
        & chronology.fillna(False)
        & frame[TIMING_FEATURE_COLUMNS].notna().all(axis=1)
    )
    for column in TIMING_FEATURE_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame.loc[~np.isfinite(frame[column]), column] = np.nan
        frame.loc[~complete, column] = np.nan
    group = frame.groupby(["formation_date", "industry"], sort=True, dropna=False)
    for column in TIMING_FEATURE_COLUMNS:
        frame[f"{column}_rank"] = group[column].transform(_centered_percentile_rank)
    frame["sec_reporting_timeliness_quality"] = frame[
        [f"{column}_rank" for column in TIMING_FEATURE_COLUMNS]
    ].mean(axis=1, skipna=False)
    frame.loc[~complete, "sec_reporting_timeliness_quality"] = np.nan

    coverage_rows: list[dict[str, Any]] = []
    for date, snapshot in frame.groupby("formation_date", sort=True):
        eligible = snapshot["eligible_at_formation"].fillna(False).astype(bool)
        scored = eligible & snapshot["sec_reporting_timeliness_quality"].notna()
        coverage_rows.append(
            {
                "formation_date": date,
                "base_eligible_names": int(eligible.sum()),
                "complete_names": int(scored.sum()),
                "ambiguous_ccm_rows": int(
                    (eligible & snapshot["matched_gvkeys"].gt(1)).sum()
                ),
                "complete_industries": int(snapshot.loc[scored, "industry"].nunique()),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    expected_formation_dates = pd.DatetimeIndex(
        pd.date_range(first_formation, last_formation, freq="ME")
    ).normalize()
    observed_formation_dates = pd.DatetimeIndex(
        pd.to_datetime(coverage["formation_date"], errors="raise")
    ).normalize()
    if not observed_formation_dates.equals(expected_formation_dates):
        raise CRSPV2Error(
            "SEC-timing metadata coverage formation months differ from the "
            "frozen 72-month chronology"
        )
    if int(coverage["ambiguous_ccm_rows"].sum()) != 0:
        raise CRSPV2Error("Ambiguous CCM mapping reached SEC-timing formation rows")
    scored = frame["sec_reporting_timeliness_quality"].notna()
    selected_metadata = frame["accession"].notna()
    available_after_formation = selected_metadata & frame["availability_date"].gt(
        frame["formation_date"]
    )
    expired_before_formation = selected_metadata & frame["expiry_date"].lt(
        frame["formation_date"]
    )
    audit = {
        **company_audit,
        "feature_rows_with_company_bridge": int(len(features)),
        "frame_rows": int(len(frame)),
        "scored_rows": int(scored.sum()),
        "minimum_complete_names": int(coverage["complete_names"].min()),
        "median_complete_names": float(coverage["complete_names"].median()),
        "maximum_complete_names": int(coverage["complete_names"].max()),
        "minimum_complete_industries": int(coverage["complete_industries"].min()),
        "ambiguous_ccm_rows": int(coverage["ambiguous_ccm_rows"].sum()),
        "coverage_formation_months": int(len(coverage)),
        "minimum_formation_date": frame["formation_date"].min().date().isoformat(),
        "maximum_formation_date": frame["formation_date"].max().date().isoformat(),
        "maximum_scored_acceptance_timestamp": (
            pd.to_datetime(frame.loc[scored, "acceptance_timestamp"], utc=True)
            .max()
            .isoformat()
            if scored.any()
            else None
        ),
        "selected_rows_available_after_formation": int(available_after_formation.sum()),
        "selected_rows_expired_before_formation": int(expired_before_formation.sum()),
        "panel_columns_projected": [
            "permno",
            "formation_date",
            "industry",
            "eligible_at_formation",
        ],
        "return_columns_projected": False,
        "validation_outcomes_read": False,
        "final_holdout_outcomes_read": False,
    }
    return frame, coverage, audit


def _load_sec_timing_validation_frame(
    score_frame: pd.DataFrame,
    panel_path: str | Path,
    protocol: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Project the frozen validation outcomes and attach the predeclared score."""

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise CRSPV2Error("DuckDB is required for SEC-timing validation") from exc
    panel_path = Path(panel_path).expanduser().resolve()
    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    first_formation = validation_start - pd.offsets.MonthEnd(1)
    scores = score_frame[
        ["permno", "formation_date", "sec_reporting_timeliness_quality"]
    ].copy()
    if scores.duplicated(["formation_date", "permno"]).any():
        raise CRSPV2Error("SEC-timing validation score keys are not unique")
    connection = duckdb.connect()
    try:
        connection.register("timing_scores", scores)
        frame = connection.execute(
            f"""
            SELECT
                CAST(panel.permno AS BIGINT) AS permno,
                panel.formation_date,
                panel.industry,
                panel.eligible_at_formation,
                panel.price,
                panel.market_cap_usd,
                panel.adv_60_usd,
                panel.volatility_126d,
                panel.full_spread_bps,
                panel.monthly_total_return,
                panel.delisting_pseudo_days,
                timing_scores.sec_reporting_timeliness_quality
            FROM read_parquet({_sql_literal(panel_path)}) AS panel
            LEFT JOIN timing_scores
              ON CAST(panel.permno AS BIGINT) = timing_scores.permno
             AND panel.formation_date = timing_scores.formation_date
            WHERE panel.formation_date BETWEEN
                  DATE {_sql_literal(first_formation.date())}
              AND DATE {_sql_literal(validation_end.date())}
            ORDER BY panel.formation_date, panel.permno
            """
        ).df()
    finally:
        connection.close()
    frame["formation_date"] = pd.to_datetime(frame["formation_date"]).dt.normalize()
    if frame.duplicated(["formation_date", "permno"]).any():
        raise CRSPV2Error("SEC-timing validation frame keys are not unique")
    expected_dates = pd.DatetimeIndex(
        pd.date_range(first_formation, validation_end, freq="ME")
    ).normalize()
    observed_dates = pd.DatetimeIndex(
        sorted(frame["formation_date"].drop_duplicates())
    ).normalize()
    if not observed_dates.equals(expected_dates):
        raise CRSPV2Error("SEC-timing validation frame is not the frozen 73 months")
    if frame["formation_date"].max() > validation_end:
        raise CRSPV2Error("SEC-timing validation opened a post-2022 outcome row")
    return frame, {
        "frame_rows": int(len(frame)),
        "formation_months_including_final_realization": int(len(observed_dates)),
        "minimum_formation_date": observed_dates.min().date().isoformat(),
        "maximum_formation_date": observed_dates.max().date().isoformat(),
        "scored_formation_rows": int(
            frame["sec_reporting_timeliness_quality"].notna().sum()
        ),
        "validation_return_columns_projected": True,
        "final_holdout_outcomes_read": False,
    }


def load_sec_timing_contract(path: str | Path) -> dict[str, Any]:
    contract_path = Path(path).expanduser().resolve()
    payload = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CRSPV2Error("SEC-timing contract must be a YAML mapping")
    if payload.get("schema_version") != "microalpha-sec-timing-protocol/v1":
        raise CRSPV2Error("Unsupported SEC-timing contract schema")
    if payload.get("status") != "predeclared_not_executed":
        raise CRSPV2Error("SEC-timing contract is not preregistered and unexecuted")
    mechanism = payload.get("frozen_mechanism", {})
    if mechanism.get("candidate_id") != "sec_reporting_timeliness_quality__equal":
        raise CRSPV2Error("SEC-timing candidate changed")
    if mechanism.get("signal") != "sec_reporting_timeliness_quality":
        raise CRSPV2Error("SEC-timing signal changed")
    if mechanism.get("weighting") != "equal":
        raise CRSPV2Error("SEC-timing weighting changed")
    expected_features = {
        "reporting_timeliness_level": (
            "negative of current acceptance UTC date minus current reportDate in "
            "calendar days"
        ),
        "reporting_timeliness_change": (
            "prior reporting-delay days minus current reporting-delay days"
        ),
    }
    if mechanism.get("raw_features") != expected_features:
        raise CRSPV2Error("SEC-timing feature definitions or directions changed")
    if list(mechanism.get("feature_rank_order", [])) != TIMING_FEATURE_COLUMNS:
        raise CRSPV2Error("SEC-timing feature order changed")
    filing = mechanism.get("filing_contract", {})
    if filing.get("selection") != "earliest acceptanceDateTime per CIK/reportDate":
        raise CRSPV2Error("SEC-timing first-filing rule changed")
    if list(filing.get("valid_delay_days_inclusive", [])) != [1, 200]:
        raise CRSPV2Error("SEC-timing delay validity bounds changed")
    if list(filing.get("consecutive_report_gap_days_inclusive", [])) != [300, 430]:
        raise CRSPV2Error("SEC-timing annual spacing changed")
    if filing.get("expiry") != "acceptance date plus eighteen calendar months":
        raise CRSPV2Error("SEC-timing expiry changed")
    filing_exact = {
        "form": "10-K",
        "is_xbrl": True,
        "original_only_exclude_amendments": True,
        "latest_available_record_only": True,
    }
    if any(filing.get(key) != value for key, value in filing_exact.items()):
        raise CRSPV2Error("SEC-timing original-XBRL filing contract changed")
    ranking = mechanism.get("ranking", {})
    if (
        ranking.get("direction")
        != "faster absolute filing and improved year-over-year timeliness rank higher"
    ):
        raise CRSPV2Error("SEC-timing ranking direction changed")
    ranking_exact = {
        "group": "formation_date and point-in-time FF12 industry",
        "transform": "average-tie percentile rank centered to [-1, 1]",
        "composite": "equal arithmetic mean of both complete feature ranks",
        "tie_break": "ascending PERMNO",
    }
    if any(ranking.get(key) != value for key, value in ranking_exact.items()):
        raise CRSPV2Error("SEC-timing ranking contract changed")
    if mechanism.get("missing_value_imputation") != "forbidden":
        raise CRSPV2Error("SEC-timing missing-value rule changed")
    ccm = mechanism.get("ccm_contract", {})
    if (
        list(ccm.get("linktype", [])) != ["LC", "LU"]
        or list(ccm.get("linkprim", [])) != ["P", "C"]
        or ccm.get("interval_must_cover_formation_date") is not True
        or ccm.get("ambiguous_permno_formation_gvkey_count") != "reject"
    ):
        raise CRSPV2Error("SEC-timing CCM contract changed")
    permitted_panel_columns = (
        payload.get("frozen_inputs", {})
        .get("selection_panel", {})
        .get("columns_permitted_before_empirical_readmission", [])
    )
    if list(permitted_panel_columns) != [
        "permno",
        "formation_date",
        "industry",
        "eligible_at_formation",
    ]:
        raise CRSPV2Error("SEC-timing return-free panel projection changed")
    coverage_gate = payload.get("future_return_free_coverage_gate", {})
    expected_coverage_gate = {
        "required_before_validation_readmission": True,
        "exact_source_digests_must_match": True,
        "expected_formation_months": 72,
        "minimum_complete_names_each_formation_month": 500,
        "minimum_complete_industries_each_formation_month": 10,
        "maximum_ambiguous_ccm_rows": 0,
        "write_only_aggregate_coverage": True,
        "raw_identifier_rows_under_git": "forbidden",
    }
    if coverage_gate != expected_coverage_gate:
        raise CRSPV2Error("SEC-timing return-free coverage gate changed")
    execution = payload.get("execution_contract", {})
    if execution.get("validation_run_permitted") is not False:
        raise CRSPV2Error("SEC-timing validation must remain disabled")
    access = payload.get("access_contract", {})
    if access.get("validation_outcomes_read") is not False:
        raise CRSPV2Error("SEC-timing validation outcomes must remain unread")
    if access.get("final_holdout_outcomes_read") is not False:
        raise CRSPV2Error("SEC-timing final holdout must remain sealed")
    access_exact = {
        "maximum_sec_acceptance_timestamp": "2022-11-30T23:59:59Z",
        "minimum_sec_report_date": "2013-01-01",
        "current_compustat_values_used": False,
        "companyfacts_values_used": False,
        "analyst_estimate_or_revision_values_used": False,
        "post_cutoff_filing_rows_selected": 0,
        "panel_return_columns_projected": False,
        "restricted_identifier_rows_written_under_git": 0,
    }
    if any(access.get(key) != value for key, value in access_exact.items()):
        raise CRSPV2Error("SEC-timing return-free access contract changed")
    return payload


def verify_sec_timing_sources(contract_path: str | Path) -> dict[str, Any]:
    """Verify frozen source bytes without building coverage or reading outcomes."""

    contract_path = Path(contract_path).expanduser().resolve()
    contract = load_sec_timing_contract(contract_path)
    frozen = contract["frozen_inputs"]
    base_protocol = contract_path.parents[2] / frozen["base_protocol_path"]
    base_protocol = base_protocol.resolve()
    if protocol_sha256(base_protocol) != str(frozen["base_protocol_sha256"]):
        raise CRSPV2Error("SEC-timing base protocol digest changed")
    panel = Path(str(frozen["selection_panel"]["path"])).resolve()
    panel_manifest = panel.with_suffix(panel.suffix + ".manifest.json")
    _validate_selection_inputs(base_protocol, panel, panel_manifest)
    checks: dict[str, Any] = {
        "base_protocol_sha256": protocol_sha256(base_protocol),
        "selection_panel_sha256": sha256_file(panel),
        "selection_panel_manifest_sha256": sha256_file(panel_manifest),
    }
    for key in ("company_cik_bridge", "ccm_link_history", "submissions_zip"):
        spec = frozen[key]
        path = Path(str(spec["path"])).resolve()
        if path.stat().st_size != int(spec["size_bytes"]):
            raise CRSPV2Error(f"SEC-timing source size changed: {key}")
        observed = sha256_file(path)
        if observed != str(spec["sha256"]):
            raise CRSPV2Error(f"SEC-timing source digest changed: {key}")
        checks[f"{key}_sha256"] = observed
    expected = {
        "selection_panel_sha256": frozen["selection_panel"]["sha256"],
        "selection_panel_manifest_sha256": frozen["selection_panel"]["manifest_sha256"],
    }
    for key, value in expected.items():
        if checks[key] != value:
            raise CRSPV2Error(f"SEC-timing frozen input changed: {key}")
    return {
        "schema_version": "microalpha-sec-timing-source-audit/v1",
        "contract_path": str(contract_path),
        "contract_sha256": sha256_file(contract_path),
        "checks": checks,
        "panel_columns_projected": [],
        "return_columns_projected": False,
        "validation_outcomes_read": False,
        "final_holdout_outcomes_read": False,
    }


def evaluate_sec_timing_coverage_gate(
    coverage: pd.DataFrame,
    contract: Mapping[str, Any],
    protocol: Mapping[str, Any],
    *,
    source_digests_verified: bool,
) -> dict[str, Any]:
    """Reduce aggregate metadata coverage against the frozen gate."""

    if list(coverage.columns) != AGGREGATE_COVERAGE_COLUMNS:
        raise CRSPV2Error(
            "SEC-timing coverage columns must appear exactly once in frozen order"
        )
    ordered = coverage[AGGREGATE_COVERAGE_COLUMNS].copy()
    ordered["formation_date"] = pd.to_datetime(
        ordered["formation_date"], errors="raise"
    ).dt.normalize()
    count_columns = AGGREGATE_COVERAGE_COLUMNS[1:]
    for column in count_columns:
        if pd.api.types.is_bool_dtype(ordered[column]):
            raise CRSPV2Error(
                f"SEC-timing aggregate count must be an integer, not boolean: {column}"
            )
        values = pd.to_numeric(ordered[column], errors="raise").to_numpy(dtype=float)
        if (
            not np.isfinite(values).all()
            or (values < 0).any()
            or not np.equal(values, np.floor(values)).all()
        ):
            raise CRSPV2Error(
                f"SEC-timing aggregate count is not a finite nonnegative integer: {column}"
            )
        ordered[column] = values.astype("int64")
    if (
        ordered["complete_names"].gt(ordered["base_eligible_names"]).any()
        or ordered["ambiguous_ccm_rows"].gt(ordered["base_eligible_names"]).any()
        or ordered["complete_names"]
        .add(ordered["ambiguous_ccm_rows"])
        .gt(ordered["base_eligible_names"])
        .any()
        or ordered["complete_industries"].gt(ordered["complete_names"]).any()
    ):
        raise CRSPV2Error("SEC-timing aggregate coverage counts are internally invalid")
    ordered = ordered.sort_values("formation_date", kind="mergesort").reset_index(
        drop=True
    )
    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    expected_dates = pd.DatetimeIndex(
        pd.date_range(
            validation_start - pd.offsets.MonthEnd(1),
            validation_end - pd.offsets.MonthEnd(1),
            freq="ME",
        )
    ).normalize()
    observed_dates = pd.DatetimeIndex(ordered["formation_date"])
    gate = contract["future_return_free_coverage_gate"]
    observed = {
        "formation_months": int(len(ordered)),
        "formation_dates_exact": bool(observed_dates.equals(expected_dates)),
        "minimum_complete_names_each_formation_month": (
            int(ordered["complete_names"].min()) if not ordered.empty else 0
        ),
        "median_complete_names": (
            float(ordered["complete_names"].median()) if not ordered.empty else 0.0
        ),
        "maximum_complete_names": (
            int(ordered["complete_names"].max()) if not ordered.empty else 0
        ),
        "minimum_complete_industries_each_formation_month": (
            int(ordered["complete_industries"].min()) if not ordered.empty else 0
        ),
        "ambiguous_ccm_rows": int(ordered["ambiguous_ccm_rows"].sum()),
        "maximum_ambiguous_ccm_rows_in_one_month": (
            int(ordered["ambiguous_ccm_rows"].max()) if not ordered.empty else 0
        ),
    }
    checks = {
        "exact_source_digests_match": (
            bool(source_digests_verified)
            if gate["exact_source_digests_must_match"]
            else True
        ),
        "expected_formation_months": (
            observed["formation_months"] == int(gate["expected_formation_months"])
            and observed["formation_dates_exact"]
        ),
        "minimum_complete_names_each_formation_month": (
            observed["minimum_complete_names_each_formation_month"]
            >= int(gate["minimum_complete_names_each_formation_month"])
        ),
        "minimum_complete_industries_each_formation_month": (
            observed["minimum_complete_industries_each_formation_month"]
            >= int(gate["minimum_complete_industries_each_formation_month"])
        ),
        "maximum_ambiguous_ccm_rows": (
            observed["ambiguous_ccm_rows"] <= int(gate["maximum_ambiguous_ccm_rows"])
        ),
        "aggregate_only_receipt": True,
    }
    failures = [name for name, passed in checks.items() if not passed]
    return {
        "schema_version": "microalpha-sec-timing-coverage-gate/v1",
        "candidate_id": contract["frozen_mechanism"]["candidate_id"],
        "expected": {
            key: gate[key]
            for key in (
                "exact_source_digests_must_match",
                "expected_formation_months",
                "minimum_complete_names_each_formation_month",
                "minimum_complete_industries_each_formation_month",
                "maximum_ambiguous_ccm_rows",
            )
        },
        "observed": observed,
        "checks": checks,
        "failures": failures,
        "gate_passed": not failures,
        "validation_run_permitted": False,
        "return_columns_projected": False,
        "final_holdout_outcomes_read": False,
    }


def _json_dump(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(dict(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _resolved_timing_paths(
    contract_path: Path, contract: Mapping[str, Any]
) -> dict[str, Path]:
    frozen = contract["frozen_inputs"]
    base_protocol = Path(str(frozen["base_protocol_path"])).expanduser()
    if not base_protocol.is_absolute():
        base_protocol = contract_path.parents[2] / base_protocol
    panel = Path(str(frozen["selection_panel"]["path"])).expanduser().resolve()
    return {
        "base_protocol": base_protocol.resolve(),
        "selection_panel": panel,
        "selection_panel_manifest": panel.with_suffix(panel.suffix + ".manifest.json"),
        "company_cik_bridge": Path(str(frozen["company_cik_bridge"]["path"]))
        .expanduser()
        .resolve(),
        "ccm_link_history": Path(str(frozen["ccm_link_history"]["path"]))
        .expanduser()
        .resolve(),
        "submissions_zip": Path(str(frozen["submissions_zip"]["path"]))
        .expanduser()
        .resolve(),
    }


def _aggregate_audit_view(
    audit: Mapping[str, Any],
    keys: Iterable[str],
    *,
    label: str,
) -> dict[str, Any]:
    """Whitelist scalar aggregate audit fields before persistence."""

    receipt: dict[str, Any] = {}
    for key in keys:
        if key not in audit:
            continue
        value = audit[key]
        if key == "panel_columns_projected":
            if not isinstance(value, (list, tuple)) or not all(
                isinstance(item, str) for item in value
            ):
                raise CRSPV2Error(f"{label} panel projection receipt is invalid")
            receipt[key] = list(value)
            continue
        if isinstance(value, (Mapping, list, tuple, set, pd.Series, pd.DataFrame)):
            raise CRSPV2Error(f"{label} audit field is not aggregate scalar: {key}")
        if isinstance(value, np.generic):
            value = value.item()
        if isinstance(value, pd.Timestamp):
            value = value.isoformat()
        receipt[key] = value
    return receipt


def _chronology_receipt(
    contract: Mapping[str, Any],
    target_audit: Mapping[str, Any],
    extraction_audit: Mapping[str, Any],
    frame_audit: Mapping[str, Any],
) -> dict[str, Any]:
    target_receipt = _aggregate_audit_view(
        target_audit, TARGET_AUDIT_RECEIPT_KEYS, label="SEC-timing target"
    )
    extraction_receipt = _aggregate_audit_view(
        extraction_audit,
        EXTRACTION_AUDIT_RECEIPT_KEYS,
        label="SEC-timing extraction",
    )
    frame_receipt = _aggregate_audit_view(
        frame_audit, FRAME_AUDIT_RECEIPT_KEYS, label="SEC-timing frame"
    )
    cutoff = pd.Timestamp(
        contract["access_contract"]["maximum_sec_acceptance_timestamp"]
    )
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    else:
        cutoff = cutoff.tz_convert("UTC")
    selected_maximum = extraction_audit.get("maximum_selected_acceptance_timestamp")
    selected_maximum_timestamp = (
        pd.Timestamp(selected_maximum) if selected_maximum is not None else None
    )
    if selected_maximum_timestamp is not None:
        if selected_maximum_timestamp.tzinfo is None:
            selected_maximum_timestamp = selected_maximum_timestamp.tz_localize("UTC")
        else:
            selected_maximum_timestamp = selected_maximum_timestamp.tz_convert("UTC")
    scored_maximum = frame_audit.get("maximum_scored_acceptance_timestamp")
    scored_maximum_timestamp = (
        pd.Timestamp(scored_maximum) if scored_maximum is not None else None
    )
    if scored_maximum_timestamp is not None:
        if scored_maximum_timestamp.tzinfo is None:
            scored_maximum_timestamp = scored_maximum_timestamp.tz_localize("UTC")
        else:
            scored_maximum_timestamp = scored_maximum_timestamp.tz_convert("UTC")
    permitted_columns = contract["frozen_inputs"]["selection_panel"][
        "columns_permitted_before_empirical_readmission"
    ]
    inherited_source = contract["inventory"]["inherited_source_receipt"]
    submissions_spec = contract["frozen_inputs"]["submissions_zip"]
    checks = {
        "target_cik_count_exact": (
            int(target_audit.get("target_ciks", -1))
            == int(inherited_source["target_ciks"])
            and int(extraction_audit.get("requested_ciks", -1))
            == int(inherited_source["target_ciks"])
        ),
        "submissions_member_count_exact": (
            int(extraction_audit.get("submissions_archive_member_count", -1))
            == int(submissions_spec["member_count"])
        ),
        "first_original_10k_count_exact": (
            int(extraction_audit.get("first_filed_10k_rows", -1))
            == int(inherited_source["first_original_xbrl_10k_rows_before_2022_12_01"])
        ),
        "supplemental_member_count_exact": (
            int(extraction_audit.get("supplemental_members_opened", -1))
            == int(inherited_source["supplemental_submission_members_opened"])
        ),
        "multiple_original_report_dates_exact": (
            int(extraction_audit.get("report_dates_with_multiple_original_10ks", -1))
            == int(inherited_source["report_dates_with_multiple_original_10ks"])
        ),
        "target_resolution_return_free": (
            target_audit.get("panel_return_column_projected") is False
        ),
        "filing_extraction_return_free": (
            extraction_audit.get("return_columns_projected") is False
        ),
        "formation_projection_return_free": (
            frame_audit.get("return_columns_projected") is False
        ),
        "validation_outcomes_unread": (
            frame_audit.get("validation_outcomes_read") is False
        ),
        "final_holdout_outcomes_unread": (
            frame_audit.get("final_holdout_outcomes_read") is False
        ),
        "panel_projection_exact": (
            list(frame_audit.get("panel_columns_projected", []))
            == list(permitted_columns)
        ),
        "no_post_cutoff_filing_selected": (
            int(extraction_audit.get("post_cutoff_filing_rows_selected", -1)) == 0
        ),
        "selected_acceptance_not_after_cutoff": (
            selected_maximum_timestamp is None or selected_maximum_timestamp <= cutoff
        ),
        "scored_acceptance_not_after_cutoff": (
            scored_maximum_timestamp is None or scored_maximum_timestamp <= cutoff
        ),
        "availability_not_after_formation": (
            int(frame_audit.get("selected_rows_available_after_formation", -1)) == 0
        ),
        "expiry_not_before_formation": (
            int(frame_audit.get("selected_rows_expired_before_formation", -1)) == 0
        ),
    }
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise CRSPV2Error(
            "SEC-timing return-free chronology failed closed: " + ", ".join(failures)
        )
    return {
        "schema_version": "microalpha-sec-timing-chronology/v1",
        "maximum_sec_acceptance_timestamp": cutoff.isoformat(),
        "minimum_sec_report_date": contract["access_contract"][
            "minimum_sec_report_date"
        ],
        "checks": checks,
        "target_audit": target_receipt,
        "extraction_audit": extraction_receipt,
        "frame_audit": frame_receipt,
        "failures": [],
        "return_columns_projected": False,
        "validation_outcomes_read": False,
        "final_holdout_outcomes_read": False,
        "restricted_identifier_rows_written": 0,
    }


def run_sec_timing_return_free_coverage(
    contract_path: str | Path,
    output_dir: str | Path,
    *,
    memory_lane_admitted: bool = False,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Run full metadata coverage and publish only aggregate receipts.

    The function never loads a return column and never writes a CIK, GVKEY,
    PERMNO, accession, filing row, feature row, or scored row.  Callers must
    separately schedule the potentially memory-heavy 3,106-CIK extraction.
    """

    if not memory_lane_admitted:
        raise CRSPV2Error(
            "Full SEC-timing coverage is locked until separate memory-lane admission"
        )
    contract_path = Path(contract_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise CRSPV2Error(
            f"Refusing to overwrite SEC-timing coverage output: {output_dir}"
        )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    contract = load_sec_timing_contract(contract_path)
    source_audit = verify_sec_timing_sources(contract_path)
    paths = _resolved_timing_paths(contract_path, contract)
    protocol = yaml.safe_load(paths["base_protocol"].read_text(encoding="utf-8"))
    if not isinstance(protocol, dict):
        raise CRSPV2Error("SEC-timing base protocol must be a YAML mapping")
    ciks, target_audit = _target_ciks(
        paths["company_cik_bridge"],
        paths["ccm_link_history"],
        paths["selection_panel"],
        protocol,
    )
    expected_target_ciks = int(
        contract["inventory"]["inherited_source_receipt"]["target_ciks"]
    )
    if (
        len(ciks) != expected_target_ciks
        or int(target_audit.get("target_ciks", -1)) != expected_target_ciks
    ):
        raise CRSPV2Error("SEC-timing target CIK population changed")
    filing = contract["frozen_mechanism"]["filing_contract"]
    timing_features, extraction_audit = extract_first_filed_sec_timing(
        paths["submissions_zip"],
        ciks,
        minimum_report_date=contract["access_contract"]["minimum_sec_report_date"],
        maximum_acceptance_timestamp=contract["access_contract"][
            "maximum_sec_acceptance_timestamp"
        ],
        minimum_delay_days=int(filing["valid_delay_days_inclusive"][0]),
        maximum_delay_days=int(filing["valid_delay_days_inclusive"][1]),
        minimum_report_gap_days=int(filing["consecutive_report_gap_days_inclusive"][0]),
        maximum_report_gap_days=int(filing["consecutive_report_gap_days_inclusive"][1]),
    )
    frame, coverage, frame_audit = build_sec_timing_scores(
        timing_features,
        paths["company_cik_bridge"],
        paths["ccm_link_history"],
        paths["selection_panel"],
        protocol,
    )
    chronology = _chronology_receipt(
        contract, target_audit, extraction_audit, frame_audit
    )
    coverage_gate = evaluate_sec_timing_coverage_gate(
        coverage, contract, protocol, source_digests_verified=True
    )
    aggregate_coverage = coverage[AGGREGATE_COVERAGE_COLUMNS].copy()
    aggregate_coverage["formation_date"] = pd.to_datetime(
        aggregate_coverage["formation_date"], errors="raise"
    ).dt.strftime("%Y-%m-%d")
    aggregate_coverage = aggregate_coverage.sort_values(
        "formation_date", kind="mergesort"
    ).reset_index(drop=True)

    source_files = {}
    source_check_names = {
        "base_protocol": "base_protocol_sha256",
        "selection_panel": "selection_panel_sha256",
        "selection_panel_manifest": "selection_panel_manifest_sha256",
        "company_cik_bridge": "company_cik_bridge_sha256",
        "ccm_link_history": "ccm_link_history_sha256",
        "submissions_zip": "submissions_zip_sha256",
    }
    for name, check_name in source_check_names.items():
        path = paths[name]
        source_files[name] = {
            "path": str(path),
            "sha256": source_audit["checks"][check_name],
            "size_bytes": path.stat().st_size,
        }
    source_manifest = {
        "schema_version": "microalpha-sec-timing-sources/v1",
        "contract_path": str(contract_path),
        "contract_sha256": sha256_file(contract_path),
        "source_files": source_files,
        "target_audit": chronology["target_audit"],
        "target_ciks": expected_target_ciks,
        "panel_columns_projected": list(
            contract["frozen_inputs"]["selection_panel"][
                "columns_permitted_before_empirical_readmission"
            ]
        ),
        "archived_return_manifests_opened": False,
        "return_columns_projected": False,
        "validation_outcomes_read": False,
        "final_holdout_outcomes_read": False,
    }
    del frame, timing_features, ciks
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent)
    )
    try:
        aggregate_coverage.to_csv(staging / "aggregate_coverage.csv", index=False)
        _json_dump(staging / "source_manifest.json", source_manifest)
        _json_dump(staging / "chronology_audit.json", chronology)
        _json_dump(staging / "coverage_gate.json", coverage_gate)
        artifacts = {
            path.name: {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in sorted(staging.iterdir())
        }
        result_manifest = {
            "schema_version": "microalpha-sec-timing-coverage-result/v1",
            "created_at_utc": generated_at_utc
            or datetime.now(timezone.utc).isoformat(),
            "candidate_id": contract["frozen_mechanism"]["candidate_id"],
            "contract_sha256": sha256_file(contract_path),
            "runner_git_sha": _git_sha(),
            "coverage_gate_passed": bool(coverage_gate["gate_passed"]),
            "validation_readmission_granted": False,
            "artifacts": artifacts,
            "written_artifact_classes": [
                "aggregate_monthly_coverage",
                "source_hash_receipt",
                "chronology_receipt",
                "coverage_gate_receipt",
            ],
            "raw_identifier_rows_written": 0,
            "return_columns_projected": False,
            "validation_outcomes_read": False,
            "final_holdout_outcomes_read": False,
        }
        _json_dump(staging / "result_manifest.json", result_manifest)
        os.rename(staging, output_dir)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return {
        "output_dir": str(output_dir),
        "candidate_id": contract["frozen_mechanism"]["candidate_id"],
        "coverage_gate_passed": bool(coverage_gate["gate_passed"]),
        "validation_readmission_granted": False,
        "runner_git_sha": _git_sha(),
        "raw_identifier_rows_written": 0,
        "return_columns_projected": False,
        "validation_outcomes_read": False,
        "final_holdout_outcomes_read": False,
    }


def _sec_timing_validation_decision(
    contract: Mapping[str, Any],
    candidate: StrategyResult,
    archived_momentum: StrategyResult,
    harsh_stress: StrategyResult,
    *,
    coverage_gate_passed: bool,
) -> dict[str, Any]:
    gates = contract["future_validation_gates"]
    performance = gates["performance"]
    checks = {
        "return_free_coverage_gate_passed": bool(coverage_gate_passed),
        "expected_validation_months": (
            int(candidate.metrics["validation_months"])
            == int(gates["expected_months"])
        ),
        "structurally_eligible": bool(candidate.metrics["eligible"]),
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
        "minimum_cagr": (
            candidate.metrics["cagr"] >= float(performance["minimum_cagr"])
        ),
        "maximum_drawdown": (
            candidate.metrics["max_drawdown"]
            <= float(performance["maximum_drawdown"])
        ),
        "harsh_stress_minimum_net_sharpe_hac": (
            harsh_stress.metrics["net_sharpe_hac"]
            >= float(performance["harsh_stress_minimum_net_sharpe_hac"])
        ),
        "harsh_stress_minimum_cagr": (
            harsh_stress.metrics["cagr"]
            >= float(performance["harsh_stress_minimum_cagr"])
        ),
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
        "validation_outcomes_read": True,
        "final_holdout_outcomes_read": False,
    }


def run_sec_timing_frozen_validation(
    contract_path: str | Path,
    output_dir: str | Path,
    *,
    validation_lane_admitted: bool = False,
) -> dict[str, Any]:
    """Execute the frozen 2017-2022 mechanism once through the existing evaluator."""

    if not validation_lane_admitted:
        raise CRSPV2Error(
            "SEC-timing validation is locked until a separate lifecycle admits it"
        )
    contract_path = Path(contract_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise CRSPV2Error(
            f"Refusing to overwrite SEC-timing validation output: {output_dir}"
        )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    contract = load_sec_timing_contract(contract_path)
    source_audit = verify_sec_timing_sources(contract_path)
    paths = _resolved_timing_paths(contract_path, contract)
    protocol = yaml.safe_load(paths["base_protocol"].read_text(encoding="utf-8"))
    if not isinstance(protocol, dict):
        raise CRSPV2Error("SEC-timing base protocol must be a YAML mapping")

    archived: dict[str, Path] = {}
    for name, spec in contract["frozen_inputs"][
        "archived_baseline_manifests"
    ].items():
        path = Path(str(spec["path"])).expanduser().resolve()
        if sha256_file(path) != str(spec["sha256"]):
            raise CRSPV2Error(f"SEC-timing archived baseline changed: {name}")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("final_holdout_outcomes_read") is not False:
            raise CRSPV2Error(f"SEC-timing archived baseline opens holdout: {name}")
        archived[str(name)] = path

    ciks, target_audit = _target_ciks(
        paths["company_cik_bridge"],
        paths["ccm_link_history"],
        paths["selection_panel"],
        protocol,
    )
    expected_target_ciks = int(
        contract["inventory"]["inherited_source_receipt"]["target_ciks"]
    )
    if len(ciks) != expected_target_ciks:
        raise CRSPV2Error("SEC-timing validation target CIK population changed")
    filing = contract["frozen_mechanism"]["filing_contract"]
    timing_features, extraction_audit = extract_first_filed_sec_timing(
        paths["submissions_zip"],
        ciks,
        minimum_report_date=contract["access_contract"]["minimum_sec_report_date"],
        maximum_acceptance_timestamp=contract["access_contract"][
            "maximum_sec_acceptance_timestamp"
        ],
        minimum_delay_days=int(filing["valid_delay_days_inclusive"][0]),
        maximum_delay_days=int(filing["valid_delay_days_inclusive"][1]),
        minimum_report_gap_days=int(filing["consecutive_report_gap_days_inclusive"][0]),
        maximum_report_gap_days=int(filing["consecutive_report_gap_days_inclusive"][1]),
    )
    score_frame, coverage, frame_audit = build_sec_timing_scores(
        timing_features,
        paths["company_cik_bridge"],
        paths["ccm_link_history"],
        paths["selection_panel"],
        protocol,
    )
    chronology = _chronology_receipt(
        contract, target_audit, extraction_audit, frame_audit
    )
    coverage_gate = evaluate_sec_timing_coverage_gate(
        coverage, contract, protocol, source_digests_verified=True
    )
    if not coverage_gate["gate_passed"]:
        raise CRSPV2Error("SEC-timing validation coverage gate no longer passes")
    frame, validation_audit = _load_sec_timing_validation_frame(
        score_frame, paths["selection_panel"], protocol
    )
    frame["sec_cash_earnings_acceleration"] = frame[
        "sec_reporting_timeliness_quality"
    ]
    del score_frame, timing_features, ciks

    candidate = _run_strategy(
        frame,
        protocol,
        signal="sec_cash_earnings_acceleration",
        weighting="equal",
    )
    standard_frame = _load_signal_frame(paths["selection_panel"], protocol)
    classic = _run_strategy(
        standard_frame,
        protocol,
        signal="mom_12_2",
        weighting="equal",
        classic=True,
    )
    momentum = _run_strategy(
        standard_frame,
        protocol,
        signal="blend_12_2_6_2",
        weighting="inverse_vol_126d",
    )
    first_filed_cash_earnings = _archived_strategy_result(
        archived["first_filed_cash_earnings"]
    )
    audit = audit_source_protocol(paths["base_protocol"])
    baselines, baseline_monthly = _baseline_table(
        protocol, audit, candidate, classic, paths["base_protocol"]
    )
    baseline_id_map = {
        "selected_flagship": "sec_reporting_timeliness_quality",
        "identical_universe_classic_mom_12_2": (
            "identical_universe_classic_momentum"
        ),
        "crsp_vw_market": "crsp_value_weighted_market",
        "crsp_ew_market": "crsp_equal_weighted_market",
    }
    baselines["baseline_id"] = baselines["baseline_id"].replace(baseline_id_map)
    baselines = pd.concat(
        [
            baselines,
            pd.DataFrame(
                [
                    _internal_baseline_row(
                        "archived_frozen_momentum",
                        momentum,
                        archived["frozen_momentum"],
                    ),
                    _internal_baseline_row(
                        "archived_first_filed_cash_earnings",
                        first_filed_cash_earnings,
                        archived["first_filed_cash_earnings"],
                    ),
                ]
            ),
        ],
        ignore_index=True,
    )
    expected_baselines = list(contract["future_validation_gates"]["baselines"])
    ordered_baseline_ids = [
        "sec_reporting_timeliness_quality",
        *expected_baselines,
    ]
    baselines = baselines.loc[
        baselines["baseline_id"].isin(ordered_baseline_ids)
    ].copy()
    if set(baselines["baseline_id"]) != set(ordered_baseline_ids):
        raise CRSPV2Error("SEC-timing frozen baseline set is incomplete")
    baselines["baseline_id"] = pd.Categorical(
        baselines["baseline_id"], categories=ordered_baseline_ids, ordered=True
    )
    baselines = baselines.sort_values("baseline_id").reset_index(drop=True)
    baselines["baseline_id"] = baselines["baseline_id"].astype(str)

    baseline_monthly = baseline_monthly.rename(columns=baseline_id_map)
    baseline_monthly["archived_frozen_momentum"] = momentum.monthly[
        "net_return"
    ].to_numpy()
    baseline_monthly["archived_first_filed_cash_earnings"] = (
        first_filed_cash_earnings.monthly["net_return"].to_numpy()
    )
    baseline_monthly = baseline_monthly[
        ["month", *ordered_baseline_ids]
    ].copy()

    stress_rows: list[dict[str, Any]] = []
    stress_results: dict[tuple[float, float], StrategyResult] = {}
    stress = contract["future_validation_gates"]["stress_grid"]
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
    decision = _sec_timing_validation_decision(
        contract,
        candidate,
        momentum,
        stress_results[harsh_key],
        coverage_gate_passed=True,
    )
    del frame, standard_frame

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent)
    )
    try:
        pd.DataFrame(
            [
                {
                    "candidate_id": contract["frozen_mechanism"]["candidate_id"],
                    "signal": contract["frozen_mechanism"]["signal"],
                    "weighting": contract["frozen_mechanism"]["weighting"],
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
                "schema_version": "microalpha-sec-timing-validation-sources/v1",
                "contract_path": str(contract_path),
                "contract_sha256": sha256_file(contract_path),
                "source_audit": source_audit,
                "archived_baseline_manifests": {
                    name: {"path": str(path), "sha256": sha256_file(path)}
                    for name, path in archived.items()
                },
                "chronology": chronology,
                "coverage_gate": coverage_gate,
                "validation_frame_audit": validation_audit,
                "runner_git_sha": _git_sha(),
                "restricted_identifier_rows_written": 0,
                "validation_outcomes_read": True,
                "final_holdout_outcomes_read": False,
            },
        )
        _json_dump(
            staging / "integrity_report.json",
            {
                "schema_version": "microalpha-sec-timing-validation-integrity/v1",
                "published_frozen_contract_verified": True,
                "source_digests_verified": True,
                "coverage_gate_verified": True,
                "chronology_verified": not chronology["failures"],
                "frozen_baseline_set_verified": True,
                "frozen_stress_grid_verified": True,
                "candidate_structurally_eligible": bool(candidate.metrics["eligible"]),
                "candidate_executed_net_neutrality_verified": (
                    candidate.metrics["maximum_absolute_executed_net"] <= 1e-9
                ),
                "candidate_executed_industry_neutrality_verified": (
                    candidate.metrics["maximum_absolute_executed_industry_net"]
                    <= 1e-9
                ),
                "restricted_identifier_rows_written": 0,
                "validation_outcomes_read": True,
                "final_holdout_outcomes_read": False,
            },
        )
        artifacts = {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in sorted(staging.iterdir())
        }
        _json_dump(
            staging / "result_manifest.json",
            {
                "schema_version": "microalpha-sec-timing-validation-result/v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "candidate": contract["frozen_mechanism"]["candidate_id"],
                "mechanism_outcome": decision["outcome"],
                "contract_sha256": sha256_file(contract_path),
                "runner_git_sha": _git_sha(),
                "artifacts": artifacts,
                "restricted_identifier_rows_written": 0,
                "validation_outcomes_read": True,
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
        "candidate": contract["frozen_mechanism"]["candidate_id"],
        "mechanism_outcome": decision["outcome"],
        "all_decision_gates_pass": decision["all_decision_gates_pass"],
        "net_sharpe_hac": candidate.metrics["net_sharpe_hac"],
        "cagr": candidate.metrics["cagr"],
        "max_drawdown": candidate.metrics["max_drawdown"],
        "runner_git_sha": _git_sha(),
        "validation_outcomes_read": True,
        "final_holdout_outcomes_read": False,
    }


__all__ = [
    "AGGREGATE_COVERAGE_COLUMNS",
    "build_sec_timing_scores",
    "evaluate_sec_timing_coverage_gate",
    "extract_first_filed_sec_timing",
    "load_sec_timing_contract",
    "run_sec_timing_frozen_validation",
    "run_sec_timing_return_free_coverage",
    "verify_sec_timing_sources",
]

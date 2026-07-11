"""Point-in-time SEC annual reporting-timeliness research primitives.

This module deliberately contains no return loader or validation runner.  It
prepares a separately preregistered filing-metadata signal while the empirical
lane is unavailable.  A later goal must explicitly add outcome execution after
rechecking the frozen contract and full return-free coverage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
import yaml

from .crsp_v2 import CRSPV2Error, protocol_sha256, sha256_file
from .crsp_v2_fundamental import _centered_percentile_rank
from .crsp_v2_sec_vintage import (
    _first_filed_10ks,
    _load_company_cik_map,
    _normalize_cik,
)
from .crsp_v2_selection import _sql_literal, _validate_selection_inputs

TIMING_FEATURE_COLUMNS = ["reporting_timeliness_level", "reporting_timeliness_change"]


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
    filings["reporting_delay_days"] = (
        acceptance_day - filings["report_date"]
    ).dt.days
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
        & filings["prior_acceptance_timestamp"].lt(
            filings["acceptance_timestamp"]
        )
    )
    features = filings.loc[valid_pair].copy()
    features["reporting_timeliness_level"] = -features["reporting_delay_days"].astype(
        float
    )
    features["reporting_timeliness_change"] = (
        features["prior_reporting_delay_days"] - features["reporting_delay_days"]
    ).astype(float)
    features["availability_date"] = acceptance_day.loc[features.index]
    features["expiry_date"] = features["availability_date"] + pd.DateOffset(
        months=18
    )
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
        & frame[TIMING_FEATURE_COLUMNS].notna().all(axis=1)
    )
    for column in TIMING_FEATURE_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame.loc[~np.isfinite(frame[column]), column] = np.nan
        frame.loc[~complete, column] = np.nan
    group = frame.groupby(["formation_date", "industry"], sort=True, dropna=False)
    for column in TIMING_FEATURE_COLUMNS:
        frame[f"{column}_rank"] = group[column].transform(
            _centered_percentile_rank
        )
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
                "complete_industries": int(
                    snapshot.loc[scored, "industry"].nunique()
                ),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    if len(coverage) != 72:
        raise CRSPV2Error("SEC-timing metadata coverage must contain 72 months")
    if int(coverage["ambiguous_ccm_rows"].sum()) != 0:
        raise CRSPV2Error("Ambiguous CCM mapping reached SEC-timing formation rows")
    scored = frame["sec_reporting_timeliness_quality"].notna()
    audit = {
        **company_audit,
        "feature_rows_with_company_bridge": int(len(features)),
        "frame_rows": int(len(frame)),
        "scored_rows": int(scored.sum()),
        "minimum_complete_names": int(coverage["complete_names"].min()),
        "median_complete_names": float(coverage["complete_names"].median()),
        "maximum_complete_names": int(coverage["complete_names"].max()),
        "ambiguous_ccm_rows": int(coverage["ambiguous_ccm_rows"].sum()),
        "maximum_formation_date": frame["formation_date"].max().date().isoformat(),
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
    ranking = mechanism.get("ranking", {})
    if (
        ranking.get("direction")
        != "faster absolute filing and improved year-over-year timeliness rank higher"
    ):
        raise CRSPV2Error("SEC-timing ranking direction changed")
    if mechanism.get("missing_value_imputation") != "forbidden":
        raise CRSPV2Error("SEC-timing missing-value rule changed")
    execution = payload.get("execution_contract", {})
    if execution.get("validation_run_permitted") is not False:
        raise CRSPV2Error("SEC-timing validation must remain disabled")
    access = payload.get("access_contract", {})
    if access.get("validation_outcomes_read") is not False:
        raise CRSPV2Error("SEC-timing validation outcomes must remain unread")
    if access.get("final_holdout_outcomes_read") is not False:
        raise CRSPV2Error("SEC-timing final holdout must remain sealed")
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
        "selection_panel_manifest_sha256": frozen["selection_panel"][
            "manifest_sha256"
        ],
    }
    for key, value in expected.items():
        if checks[key] != value:
            raise CRSPV2Error(f"SEC-timing frozen input changed: {key}")
    return {
        "schema_version": "microalpha-sec-timing-source-audit/v1",
        "checks": checks,
        "panel_columns_projected": [],
        "return_columns_projected": False,
        "validation_outcomes_read": False,
        "final_holdout_outcomes_read": False,
    }


__all__ = [
    "build_sec_timing_scores",
    "extract_first_filed_sec_timing",
    "load_sec_timing_contract",
    "verify_sec_timing_sources",
]

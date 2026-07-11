"""Preregistered annual quality/value/profitability/investment research runner."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

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

REQUIRED_ANNUAL_COLUMNS = {
    "gvkey",
    "datadate",
    "at",
    "lt",
    "ceq",
    "txditc",
    "pstk",
    "pstkl",
    "pstkrv",
    "sale",
    "cogs",
    "xsga",
    "xint",
    "che",
    "dltt",
    "dlc",
    "dp",
}
RAW_FEATURE_COLUMNS = [
    "book_to_market",
    "gross_profitability",
    "operating_profitability",
    "conservative_investment",
    "accrual_quality",
]


def _load_contract(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CRSPV2Error("Fundamental-composite contract must be a YAML mapping")
    return payload


def _resolve_repo_path(contract_path: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = contract_path.parents[2] / path
    return path.resolve()


def _sha256_bytes(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _verify_annual_inputs(
    contract: Mapping[str, Any],
) -> list[Path]:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover - research environment contract
        raise CRSPV2Error("PyArrow is required for annual input verification") from exc

    spec = contract["frozen_inputs"]["compustat_annual"]
    opened_years = [int(year) for year in spec["opened_years"]]
    if opened_years != list(range(2005, 2023)):
        raise CRSPV2Error("Annual input years must be exactly 2005-2022")
    if [int(year) for year in spec["forbidden_before_final_holdout_execution"]] != [
        2023,
        2024,
        2025,
    ]:
        raise CRSPV2Error("Final-holdout annual partitions are not sealed")

    root = Path(str(spec["root"])).expanduser().resolve()
    items = list(spec["files"])
    if len(items) != int(spec["expected_file_count"]) or len(items) != 18:
        raise CRSPV2Error("Annual input file count differs from preregistration")

    paths: list[Path] = []
    manifest_lines: list[str] = []
    total_rows = 0
    for expected_year, item in zip(opened_years, items):
        year = int(item["year"])
        if year != expected_year or year >= 2023:
            raise CRSPV2Error("Annual input ordering or holdout boundary changed")
        path = (root / str(item["file_name"])).resolve()
        if path.parent != root or path.name != f"funda_{year}.parquet":
            raise CRSPV2Error("Annual input path differs from frozen partition naming")
        if not path.is_file():
            raise CRSPV2Error(f"Annual input is missing: {path}")
        if path.stat().st_size != int(item["size_bytes"]):
            raise CRSPV2Error(f"Annual input size changed: {path.name}")
        if sha256_file(path) != str(item["sha256"]):
            raise CRSPV2Error(f"Annual input digest changed: {path.name}")
        parquet = pq.ParquetFile(path)
        row_count = int(parquet.metadata.num_rows)
        if row_count != int(item["row_count"]):
            raise CRSPV2Error(f"Annual input row count changed: {path.name}")
        missing = REQUIRED_ANNUAL_COLUMNS.difference(parquet.schema_arrow.names)
        if missing:
            raise CRSPV2Error(
                f"Annual input schema is missing {sorted(missing)}: {path.name}"
            )
        total_rows += row_count
        paths.append(path)
        manifest_lines.append(
            f"{year}|{path.name}|{path.stat().st_size}|{row_count}|{item['sha256']}"
        )

    if total_rows != int(spec["expected_total_rows"]):
        raise CRSPV2Error("Annual aggregate row count changed")
    digest = _sha256_bytes("\n".join(manifest_lines) + "\n")
    if digest != str(spec["aggregate_manifest_sha256"]):
        raise CRSPV2Error("Annual aggregate manifest digest changed")
    return paths


def _validate_contract_semantics(contract: Mapping[str, Any]) -> None:
    if contract.get("status") != "predeclared_not_executed":
        raise CRSPV2Error("Fundamental contract is not in preregistered state")
    mechanism = contract.get("frozen_mechanism", {})
    if mechanism.get("candidate_id") != "qvpi_annual_composite__equal":
        raise CRSPV2Error("Fundamental candidate differs from preregistration")
    if mechanism.get("signal") != "qvpi_annual_composite":
        raise CRSPV2Error("Fundamental signal differs from preregistration")
    if mechanism.get("weighting") != "equal":
        raise CRSPV2Error("Fundamental weighting differs from preregistration")
    annual = mechanism.get("annual_record_contract", {})
    if annual.get("availability_date") != "datadate plus six calendar months":
        raise CRSPV2Error("Accounting availability lag differs from preregistration")
    if annual.get("expiry_date") != "datadate plus eighteen calendar months":
        raise CRSPV2Error("Accounting expiry differs from preregistration")
    if list(annual.get("prior_record_spacing_months_inclusive", [])) != [9, 15]:
        raise CRSPV2Error("Annual prior-record spacing differs from preregistration")
    links = mechanism.get("ccm_contract", {})
    if set(links.get("linktype", [])) != {"LC", "LU"}:
        raise CRSPV2Error("CCM linktype filter differs from preregistration")
    if set(links.get("linkprim", [])) != {"P", "C"}:
        raise CRSPV2Error("CCM linkprim filter differs from preregistration")
    access = contract.get("access_contract", {})
    if access.get("final_holdout_outcomes_read") is not False:
        raise CRSPV2Error("Final holdout must remain sealed")
    if access.get("compustat_2023_2025_partitions_opened") is not False:
        raise CRSPV2Error("Final-holdout Compustat partitions must remain sealed")


def _validate_inputs(
    contract_path: Path,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Path],
    dict[str, Path],
    list[Path],
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

    link_spec = frozen["ccm_link_history"]
    link_path = Path(str(link_spec["path"])).expanduser().resolve()
    if sha256_file(link_path) != str(link_spec["sha256"]):
        raise CRSPV2Error("CCM link-history digest differs from preregistration")
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover
        raise CRSPV2Error("PyArrow is required for link verification") from exc
    if pq.ParquetFile(link_path).metadata.num_rows != int(link_spec["row_count"]):
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

    annual_paths = _verify_annual_inputs(contract)
    paths = {
        "base_protocol": base_protocol_path,
        "panel": panel_path,
        "panel_manifest": panel_manifest_path,
        "link_history": link_path,
    }
    return contract, protocol, panel_manifest, paths, archived, annual_paths


def _sql_path_list(paths: list[Path]) -> str:
    return "[" + ",".join(_sql_literal(path) for path in paths) + "]"


def _centered_percentile_rank(values: pd.Series) -> pd.Series:
    count = int(values.notna().sum())
    result = pd.Series(np.nan, index=values.index, dtype=float)
    if count == 0:
        return result
    ranks = values.rank(method="average", na_option="keep")
    result.loc[ranks.notna()] = 2.0 * (ranks.loc[ranks.notna()] - 0.5) / count - 1.0
    return result


def _load_fundamental_frame(
    annual_paths: list[Path],
    link_path: Path,
    panel_path: Path,
    protocol: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Join conservatively available annual accounting records to formation rows."""

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover
        raise CRSPV2Error("DuckDB is required for fundamental research") from exc
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:  # pragma: no cover
        raise CRSPV2Error("PyArrow is required for fundamental research") from exc

    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    first_formation = validation_start - pd.offsets.MonthEnd(1)
    annual_sql = _sql_path_list(annual_paths)
    connection = duckdb.connect()
    try:
        frame = connection.execute(f"""
            WITH annual_history AS (
                SELECT
                    gvkey,
                    datadate,
                    "at" AS assets,
                    lt,
                    ceq,
                    txditc,
                    pstk,
                    pstkl,
                    pstkrv,
                    sale,
                    cogs,
                    xsga,
                    xint,
                    che,
                    dltt,
                    dlc,
                    dp,
                    lag(datadate) OVER (
                        PARTITION BY gvkey ORDER BY datadate
                    ) AS lag_datadate,
                    lag("at") OVER (
                        PARTITION BY gvkey ORDER BY datadate
                    ) AS lag_assets,
                    lag(lt) OVER (
                        PARTITION BY gvkey ORDER BY datadate
                    ) AS lag_lt,
                    lag(che) OVER (
                        PARTITION BY gvkey ORDER BY datadate
                    ) AS lag_che,
                    lag(dltt) OVER (
                        PARTITION BY gvkey ORDER BY datadate
                    ) AS lag_dltt,
                    lag(dlc) OVER (
                        PARTITION BY gvkey ORDER BY datadate
                    ) AS lag_dlc
                FROM read_parquet({annual_sql})
            ), annual_features AS (
                SELECT
                    *,
                    date_diff('month', lag_datadate, datadate) AS fiscal_gap_months,
                    datadate + INTERVAL 6 MONTH AS availability_date,
                    datadate + INTERVAL 18 MONTH AS expiry_date,
                    ceq + coalesce(txditc, 0.0)
                        - coalesce(pstkrv, pstkl, pstk, 0.0) AS book_equity,
                    (sale - cogs) / nullif(lag_assets, 0.0)
                        AS gross_profitability,
                    (sale - cogs - xsga - xint)
                        / nullif(
                            ceq + coalesce(txditc, 0.0)
                                - coalesce(pstkrv, pstkl, pstk, 0.0),
                            0.0
                        ) AS operating_profitability,
                    -(assets / nullif(lag_assets, 0.0) - 1.0)
                        AS conservative_investment,
                    -(
                        ((assets - che) - (lag_assets - lag_che))
                        - ((lt - dlc - dltt) - (lag_lt - lag_dlc - lag_dltt))
                        - dp
                    ) / nullif((assets + lag_assets) / 2.0, 0.0)
                        AS accrual_quality
                FROM annual_history
                WHERE lag_datadate IS NOT NULL
                  AND date_diff('month', lag_datadate, datadate) BETWEEN 9 AND 15
            ), base AS (
                SELECT
                    permno,
                    formation_date,
                    industry,
                    eligible_at_formation,
                    price,
                    market_cap_usd,
                    adv_60_usd,
                    volatility_126d,
                    full_spread_bps,
                    monthly_total_return,
                    delisting_pseudo_days
                FROM read_parquet({_sql_literal(panel_path)})
                WHERE formation_date BETWEEN DATE {_sql_literal(first_formation.date())}
                                         AND DATE {_sql_literal(validation_end.date())}
            ), links AS (
                SELECT
                    gvkey,
                    CAST(lpermno AS BIGINT) AS permno,
                    linkdt,
                    linkenddt,
                    linktype,
                    linkprim
                FROM read_parquet({_sql_literal(link_path)})
                WHERE lpermno IS NOT NULL
                  AND linktype IN ('LC', 'LU')
                  AND linkprim IN ('P', 'C')
            ), matches AS (
                SELECT
                    base.permno,
                    base.formation_date,
                    annual_features.gvkey,
                    annual_features.datadate AS accounting_datadate,
                    annual_features.availability_date AS accounting_availability_date,
                    annual_features.expiry_date AS accounting_expiry_date,
                    annual_features.fiscal_gap_months,
                    annual_features.assets AS accounting_assets,
                    annual_features.lag_assets AS accounting_lag_assets,
                    annual_features.book_equity,
                    annual_features.book_equity * 1000000.0
                        / nullif(base.market_cap_usd, 0.0) AS book_to_market,
                    annual_features.gross_profitability,
                    annual_features.operating_profitability,
                    annual_features.conservative_investment,
                    annual_features.accrual_quality,
                    count(DISTINCT annual_features.gvkey) OVER (
                        PARTITION BY base.permno, base.formation_date
                    ) AS matched_gvkeys,
                    row_number() OVER (
                        PARTITION BY base.permno, base.formation_date
                        ORDER BY
                            annual_features.datadate DESC,
                            annual_features.gvkey ASC,
                            CASE links.linkprim WHEN 'P' THEN 0 ELSE 1 END
                    ) AS recency_rank
                FROM base
                JOIN links
                  ON base.permno = links.permno
                 AND (links.linkdt IS NULL OR base.formation_date >= links.linkdt)
                 AND (
                        links.linkenddt IS NULL
                        OR base.formation_date <= links.linkenddt
                     )
                JOIN annual_features
                  ON links.gvkey = annual_features.gvkey
                 AND annual_features.availability_date <= base.formation_date
                 AND annual_features.expiry_date >= base.formation_date
            ), selected AS (
                SELECT * EXCLUDE (recency_rank)
                FROM matches
                WHERE recency_rank = 1
            )
            SELECT
                base.*,
                selected.* EXCLUDE (permno, formation_date),
                coalesce(selected.matched_gvkeys, 0) AS accounting_match_count
            FROM base
            LEFT JOIN selected USING (permno, formation_date)
            ORDER BY base.formation_date, base.permno
            """).df()
    finally:
        connection.close()

    frame["formation_date"] = pd.to_datetime(frame["formation_date"])
    for column in (
        "accounting_datadate",
        "accounting_availability_date",
        "accounting_expiry_date",
    ):
        frame[column] = pd.to_datetime(frame[column])
    if frame.duplicated(["formation_date", "permno"]).any():
        raise CRSPV2Error("Fundamental frame formation-date/PERMNO keys are not unique")

    frame["matched_gvkeys"] = pd.to_numeric(
        frame["matched_gvkeys"], errors="coerce"
    ).fillna(0).astype(int)
    numeric = RAW_FEATURE_COLUMNS + [
        "book_equity",
        "accounting_assets",
        "accounting_lag_assets",
    ]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame.loc[~np.isfinite(frame[column]), column] = np.nan

    chronology = (
        frame["accounting_availability_date"].le(frame["formation_date"])
        & frame["accounting_expiry_date"].ge(frame["formation_date"])
    )
    complete = (
        frame["eligible_at_formation"].fillna(False).astype(bool)
        & frame["matched_gvkeys"].eq(1)
        & chronology.fillna(False)
        & frame["book_equity"].gt(0.0)
        & frame["book_to_market"].gt(0.0)
        & frame["accounting_assets"].gt(0.0)
        & frame["accounting_lag_assets"].gt(0.0)
        & frame[RAW_FEATURE_COLUMNS].notna().all(axis=1)
    )
    for column in RAW_FEATURE_COLUMNS:
        frame.loc[~complete, column] = np.nan

    group = frame.groupby(["formation_date", "industry"], sort=True, dropna=False)
    for column in RAW_FEATURE_COLUMNS:
        rank_name = f"{column}_rank"
        frame[rank_name] = group[column].transform(_centered_percentile_rank)
    frame["profitability_family_rank"] = frame[
        ["gross_profitability_rank", "operating_profitability_rank"]
    ].mean(axis=1, skipna=False)
    frame["qvpi_annual_composite"] = frame[
        [
            "book_to_market_rank",
            "profitability_family_rank",
            "conservative_investment_rank",
            "accrual_quality_rank",
        ]
    ].mean(axis=1, skipna=False)
    frame.loc[~complete, "qvpi_annual_composite"] = np.nan

    scored = frame["qvpi_annual_composite"].notna()
    if (
        frame.loc[scored, "accounting_availability_date"]
        > frame.loc[scored, "formation_date"]
    ).any():
        raise CRSPV2Error("Fundamental score uses an unavailable accounting record")
    if (
        frame.loc[scored, "accounting_expiry_date"]
        < frame.loc[scored, "formation_date"]
    ).any():
        raise CRSPV2Error("Fundamental score uses an expired accounting record")

    last_formation = validation_end - pd.offsets.MonthEnd(1)
    formation_months = pd.date_range(first_formation, last_formation, freq="ME")
    formation = frame.loc[frame["formation_date"].isin(formation_months)].copy()
    coverage_rows: list[dict[str, Any]] = []
    for date, snapshot in formation.groupby("formation_date", sort=True):
        base_eligible = snapshot["eligible_at_formation"].fillna(False).astype(bool)
        complete_snapshot = base_eligible & snapshot["qvpi_annual_composite"].notna()
        coverage_rows.append(
            {
                "formation_date": date,
                "base_eligible_names": int(base_eligible.sum()),
                "uniquely_linked_names": int(
                    (base_eligible & snapshot["matched_gvkeys"].eq(1)).sum()
                ),
                "complete_names": int(complete_snapshot.sum()),
                "ambiguous_ccm_rows": int(
                    (base_eligible & snapshot["matched_gvkeys"].gt(1)).sum()
                ),
                "complete_industries": int(
                    snapshot.loc[complete_snapshot, "industry"].nunique()
                ),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    if len(coverage) != 72:
        raise CRSPV2Error("Fundamental coverage must contain 72 formation months")
    if int(coverage["ambiguous_ccm_rows"].sum()) != 0:
        raise CRSPV2Error("Ambiguous CCM mapping reached the eligible formation set")

    audit = {
        "source_fundamental_rows": int(
            sum(pq.ParquetFile(path).metadata.num_rows for path in annual_paths)
        ),
        "frame_rows": int(len(frame)),
        "scored_rows": int(scored.sum()),
        "minimum_complete_names": int(coverage["complete_names"].min()),
        "median_complete_names": float(coverage["complete_names"].median()),
        "maximum_complete_names": int(coverage["complete_names"].max()),
        "ambiguous_ccm_rows": int(coverage["ambiguous_ccm_rows"].sum()),
        "maximum_scored_datadate": (
            frame.loc[scored, "accounting_datadate"].max().date().isoformat()
            if scored.any()
            else None
        ),
        "maximum_formation_date": frame["formation_date"].max().date().isoformat(),
        "compustat_2023_2025_partitions_opened": False,
        "final_holdout_outcomes_read": False,
    }
    return frame, coverage, audit


def _fundamental_decision(
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
        "positive_cagr": (
            candidate.metrics["cagr"] > float(performance["minimum_cagr"])
        ),
        "maximum_drawdown": (
            candidate.metrics["max_drawdown"]
            <= float(performance["maximum_drawdown"])
        ),
        "harsh_stress_positive_net_sharpe_hac": (
            harsh_stress.metrics["net_sharpe_hac"]
            > float(performance["harsh_stress_minimum_net_sharpe_hac"])
        ),
        "harsh_stress_positive_cagr": (
            harsh_stress.metrics["cagr"]
            > float(performance["harsh_stress_minimum_cagr"])
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
        "snapshot_revision_risk": "present_not_true_vintage_evidence",
        "final_holdout_outcomes_read": False,
    }


def run_fundamental_composite(
    contract_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Execute the preregistered annual composite and publish aggregate artifacts."""

    contract_path = Path(contract_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise CRSPV2Error(f"Refusing to overwrite fundamental output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    contract, protocol, panel_manifest, paths, archived, annual_paths = (
        _validate_inputs(contract_path)
    )
    audit = audit_source_protocol(paths["base_protocol"])
    fundamental_frame, feature_coverage, feature_audit = _load_fundamental_frame(
        annual_paths,
        paths["link_history"],
        paths["panel"],
        protocol,
    )
    standard_frame = _load_signal_frame(paths["panel"], protocol)
    residual_frame = _load_distinct_signal_frame(paths["panel"], protocol)
    low_volatility_frame = _load_low_volatility_frame(paths["panel"], protocol)
    reversal_frame = _load_short_term_reversal_frame(paths["panel"], protocol)

    candidate = _run_strategy(
        fundamental_frame,
        protocol,
        signal="qvpi_annual_composite",
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

    baselines, baseline_monthly = _baseline_table(
        protocol, audit, candidate, classic, paths["base_protocol"]
    )
    baselines.loc[
        baselines["baseline_id"].eq("selected_flagship"), "baseline_id"
    ] = "qvpi_annual_composite"
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
                ]
            ),
        ],
        ignore_index=True,
    )
    baseline_monthly = baseline_monthly.rename(
        columns={"selected_flagship": "qvpi_annual_composite"}
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

    stress_rows: list[dict[str, Any]] = []
    stress_results: dict[tuple[float, float], StrategyResult] = {}
    stress = contract["validation"]["stress_grid"]
    for borrow in stress["annual_short_borrow_bps"]:
        for multiplier in stress["nonborrow_cost_multiplier"]:
            result = _run_strategy(
                fundamental_frame,
                protocol,
                signal="qvpi_annual_composite",
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
    decision = _fundamental_decision(
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
                    "candidate_id": "qvpi_annual_composite__equal",
                    "signal": "qvpi_annual_composite",
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
        feature_coverage.to_csv(staging / "feature_coverage.csv", index=False)
        _json_dump(staging / "mechanism_decision.json", decision)
        _json_dump(
            staging / "source_manifest.json",
            {
                "schema_version": "microalpha-qvpi-sources/v1",
                "contract_path": str(contract_path),
                "contract_sha256": sha256_file(contract_path),
                "base_protocol_path": str(paths["base_protocol"]),
                "base_protocol_sha256": protocol_sha256(paths["base_protocol"]),
                "panel_path": str(paths["panel"]),
                "panel_sha256": sha256_file(paths["panel"]),
                "panel_manifest_sha256": sha256_file(paths["panel_manifest"]),
                "link_history_path": str(paths["link_history"]),
                "link_history_sha256": sha256_file(paths["link_history"]),
                "annual_inputs": [
                    {
                        "file_name": path.name,
                        "sha256": sha256_file(path),
                        "size_bytes": path.stat().st_size,
                    }
                    for path in annual_paths
                ],
                "archived_result_manifests": {
                    name: {"path": str(path), "sha256": sha256_file(path)}
                    for name, path in archived.items()
                },
                "panel_builder_git_sha": panel_manifest["git_sha"],
                "runner_git_sha": _git_sha(),
                "compustat_2023_2025_partitions_opened": False,
                "final_holdout_outcomes_read": False,
            },
        )
        _json_dump(
            staging / "integrity_report.json",
            {
                "schema_version": "microalpha-qvpi-integrity/v1",
                "panel_digest_verified": True,
                "base_protocol_digest_verified": True,
                "annual_input_digests_verified": True,
                "link_history_digest_verified": True,
                "archived_result_digests_verified": True,
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
                "snapshot_revision_risk": "present_not_true_vintage_evidence",
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
                "schema_version": "microalpha-qvpi-result/v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "candidate": "qvpi_annual_composite__equal",
                "mechanism_outcome": decision["outcome"],
                "contract_sha256": sha256_file(contract_path),
                "panel_sha256": sha256_file(paths["panel"]),
                "runner_git_sha": _git_sha(),
                "artifacts": artifacts,
                "snapshot_revision_risk": "present_not_true_vintage_evidence",
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
        "candidate": "qvpi_annual_composite__equal",
        "mechanism_outcome": decision["outcome"],
        "runner_git_sha": _git_sha(),
        "snapshot_revision_risk": "present_not_true_vintage_evidence",
        "final_holdout_outcomes_read": False,
    }


__all__ = ["run_fundamental_composite"]

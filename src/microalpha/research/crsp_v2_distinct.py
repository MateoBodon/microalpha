"""Predeclared CRSP-v2 residual-momentum family research runner."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
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
from .crsp_v2_selection import (
    SIGNAL_DEFINITIONS,
    StrategyResult,
    _baseline_table,
    _load_signal_frame,
    _run_strategy,
    _sql_literal,
    _validate_selection_inputs,
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # pragma: no cover - non-Git execution
        return "unknown"


def _json_dump(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False),
        encoding="utf-8",
    )


def _load_contract(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CRSPV2Error("Distinct-family contract must be a YAML mapping")
    return payload


def _validate_inputs(
    contract_path: Path,
    base_protocol_path: Path,
    panel_path: Path,
    previous_selection_manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = _load_contract(contract_path)
    base_protocol = load_protocol(base_protocol_path)
    panel_manifest_path = panel_path.with_suffix(panel_path.suffix + ".manifest.json")
    _, panel_manifest = _validate_selection_inputs(
        base_protocol_path, panel_path, panel_manifest_path
    )
    expected = contract.get("frozen_inputs", {})
    checks = {
        "base_protocol_sha256": protocol_sha256(base_protocol_path),
        "panel_sha256": sha256_file(panel_path),
        "panel_manifest_sha256": sha256_file(panel_manifest_path),
        "previous_selection_manifest_sha256": sha256_file(
            previous_selection_manifest_path
        ),
    }
    for key, observed in checks.items():
        if str(expected.get(key, "")) != observed:
            raise CRSPV2Error(f"Distinct-family frozen input mismatch: {key}")
    previous = json.loads(previous_selection_manifest_path.read_text(encoding="utf-8"))
    if previous.get("final_holdout_outcomes_read") is not False:
        raise CRSPV2Error("Previous selection receipt does not keep holdout sealed")
    if previous.get("selected_candidate") != expected.get("previous_selected_candidate"):
        raise CRSPV2Error("Previous selected candidate differs from preregistration")
    if contract.get("access_contract", {}).get("final_holdout_outcomes_read") is not False:
        raise CRSPV2Error("Distinct-family contract must seal final holdout outcomes")
    candidates = contract.get("family", {}).get("candidates", [])
    ids = [str(item.get("signal")) for item in candidates]
    if len(ids) != 3 or len(set(ids)) != 3:
        raise CRSPV2Error("Distinct family must contain exactly three unique candidates")
    if any(signal not in SIGNAL_DEFINITIONS for signal in ids):
        raise CRSPV2Error("Distinct family contains an unknown signal")
    if any(str(item.get("weighting")) != "equal" for item in candidates):
        raise CRSPV2Error("Distinct-family weighting was frozen to equal")
    return contract, base_protocol, panel_manifest


def _load_distinct_signal_frame(
    panel_path: Path, protocol: Mapping[str, Any]
) -> pd.DataFrame:
    """Build robust FF12-residual signals with explicit formation-time chronology."""

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise CRSPV2Error("DuckDB is required for CRSP-v2 distinct-family research") from exc

    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    first_formation = validation_start - pd.offsets.MonthEnd(1)
    connection = duckdb.connect()
    try:
        frame = connection.execute(f"""
            WITH industry_centered AS (
                SELECT
                    *,
                    monthly_total_return
                    - median(monthly_total_return) OVER (
                        PARTITION BY formation_date, industry
                    ) AS industry_residual_return
                FROM read_parquet({_sql_literal(panel_path)})
            ), history AS (
                SELECT
                    *,
                    count(industry_residual_return) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 11 PRECEDING AND 1 PRECEDING
                    ) AS residual12_count,
                    min(formation_date) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 11 PRECEDING AND 1 PRECEDING
                    ) AS residual12_start,
                    sum(industry_residual_return) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 11 PRECEDING AND 1 PRECEDING
                    ) AS residual12_sum,
                    count(industry_residual_return) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                    ) AS residual6_count,
                    min(formation_date) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                    ) AS residual6_start,
                    sum(industry_residual_return) OVER (
                        PARTITION BY permno ORDER BY formation_date
                        ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                    ) AS residual6_sum
                FROM industry_centered
            )
            SELECT
                permno,
                formation_date,
                industry,
                eligible_at_formation,
                price,
                adv_60_usd,
                volatility_126d,
                full_spread_bps,
                monthly_total_return,
                delisting_pseudo_days,
                industry_residual_return,
                CASE
                    WHEN residual12_count = 11
                     AND date_diff('month', residual12_start, formation_date) = 11
                    THEN residual12_sum
                END AS residual_mom_12_2,
                CASE
                    WHEN residual6_count = 5
                     AND date_diff('month', residual6_start, formation_date) = 5
                    THEN residual6_sum
                END AS residual_mom_6_2,
                CASE
                    WHEN residual12_count = 11
                     AND date_diff('month', residual12_start, formation_date) = 11
                     AND industry_residual_return IS NOT NULL
                    THEN residual12_sum - industry_residual_return
                END AS residual_mom_12_2_minus_reversal_1_1
            FROM history
            WHERE formation_date BETWEEN DATE {_sql_literal(first_formation.date())}
                                     AND DATE {_sql_literal(validation_end.date())}
            ORDER BY formation_date, permno
            """).df()
    finally:
        connection.close()
    frame["formation_date"] = pd.to_datetime(frame["formation_date"])
    if frame.duplicated(["formation_date", "permno"]).any():
        raise CRSPV2Error("Distinct signal frame keys are not unique")
    return frame


def _candidate_row(
    candidate_id: str, signal: str, weighting: str, result: StrategyResult
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "signal": signal,
        "weighting": weighting,
        **result.metrics,
    }


def _rank_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    ranked = frame.sort_values(
        [
            "eligible",
            "net_sharpe_hac",
            "worst_calendar_year_net_return",
            "total_one_way_turnover",
            "candidate_id",
        ],
        ascending=[False, False, False, True, True],
        kind="mergesort",
    ).reset_index(drop=True)
    ranked.insert(0, "selection_rank", np.arange(1, len(ranked) + 1))
    return ranked


def _family_decision(
    contract: Mapping[str, Any],
    selected: StrategyResult,
    previous: StrategyResult,
    classic: StrategyResult,
    harsh_stress: StrategyResult,
) -> dict[str, Any]:
    gates = contract["family_gate"]
    checks = {
        "structurally_eligible": bool(selected.metrics["eligible"]),
        "beats_previous_selected_by_minimum_sharpe_delta": (
            selected.metrics["net_sharpe_hac"]
            >= previous.metrics["net_sharpe_hac"]
            + float(gates["minimum_sharpe_improvement_over_previous"])
        ),
        "beats_identical_universe_classic_sharpe": (
            selected.metrics["net_sharpe_hac"] >= classic.metrics["net_sharpe_hac"]
        ),
        "positive_cagr": selected.metrics["cagr"] > 0.0,
        "max_drawdown_within_limit": (
            selected.metrics["max_drawdown"] <= float(gates["maximum_drawdown"])
        ),
        "harsh_stress_positive_sharpe": harsh_stress.metrics["net_sharpe_hac"] > 0.0,
        "harsh_stress_positive_cagr": harsh_stress.metrics["cagr"] > 0.0,
    }
    passed = all(checks.values())
    return {
        "outcome": (
            "freeze_candidate_keep_final_holdout_sealed"
            if passed
            else "archive_family_as_validation_negative"
        ),
        "all_family_gates_pass": passed,
        "checks": checks,
        "selected_net_sharpe_hac": selected.metrics["net_sharpe_hac"],
        "previous_selected_net_sharpe_hac": previous.metrics["net_sharpe_hac"],
        "identical_universe_classic_net_sharpe_hac": classic.metrics[
            "net_sharpe_hac"
        ],
        "harsh_stress_net_sharpe_hac": harsh_stress.metrics["net_sharpe_hac"],
        "final_holdout_outcomes_read": False,
    }


def run_distinct_family(
    contract_path: str | Path,
    base_protocol_path: str | Path,
    panel_path: str | Path,
    previous_selection_manifest_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Execute the three-candidate preregistered family and publish atomically."""

    contract_path = Path(contract_path).expanduser().resolve()
    base_protocol_path = Path(base_protocol_path).expanduser().resolve()
    panel_path = Path(panel_path).expanduser().resolve()
    previous_selection_manifest_path = (
        Path(previous_selection_manifest_path).expanduser().resolve()
    )
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise CRSPV2Error(f"Refusing to overwrite distinct-family output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    contract, protocol, panel_manifest = _validate_inputs(
        contract_path,
        base_protocol_path,
        panel_path,
        previous_selection_manifest_path,
    )
    audit = audit_source_protocol(base_protocol_path)
    frame = _load_distinct_signal_frame(panel_path, protocol)
    standard_frame = _load_signal_frame(panel_path, protocol)

    results: dict[str, StrategyResult] = {}
    rows: list[dict[str, Any]] = []
    for spec in contract["family"]["candidates"]:
        candidate_id = str(spec["id"])
        signal = str(spec["signal"])
        weighting = str(spec["weighting"])
        result = _run_strategy(
            frame, protocol, signal=signal, weighting=weighting
        )
        results[candidate_id] = result
        rows.append(_candidate_row(candidate_id, signal, weighting, result))
    candidates = _rank_candidates(pd.DataFrame(rows))
    eligible = candidates.loc[candidates["eligible"].astype(bool)]
    if eligible.empty:
        raise CRSPV2Error("No distinct-family candidate passes structural gates")
    selected_row = eligible.iloc[0]
    selected_id = str(selected_row["candidate_id"])
    selected = results[selected_id]

    previous_id = str(contract["frozen_inputs"]["previous_selected_candidate"])
    previous_signal, previous_weighting = previous_id.split("__", 1)
    previous = _run_strategy(
        standard_frame,
        protocol,
        signal=previous_signal,
        weighting=previous_weighting,
    )
    classic = _run_strategy(
        standard_frame,
        protocol,
        signal="mom_12_2",
        weighting="equal",
        classic=True,
    )
    baselines, baseline_monthly = _baseline_table(
        protocol, audit, selected, classic, base_protocol_path
    )
    baselines.loc[
        baselines["baseline_id"].eq("selected_flagship"), "baseline_id"
    ] = "distinct_family_best"
    previous_row = {
        "baseline_id": "previous_frozen_momentum",
        **{
            key: value
            for key, value in previous.metrics.items()
            if key
            in {
                "net_sharpe_hac",
                "net_sharpe_hac_se",
                "net_sharpe_hac_tstat",
                "cagr",
                "max_drawdown",
                "cumulative_return",
                "total_one_way_turnover",
            }
        },
        "months": int(previous.metrics["validation_months"]),
        "classification": "investable_net_frozen_validation_baseline",
        "source_path": str(previous_selection_manifest_path),
        "source_sha256": sha256_file(previous_selection_manifest_path),
    }
    baselines = pd.concat([baselines, pd.DataFrame([previous_row])], ignore_index=True)
    baseline_monthly = baseline_monthly.rename(
        columns={"selected_flagship": "distinct_family_best"}
    )
    baseline_monthly["previous_frozen_momentum"] = previous.monthly[
        "net_return"
    ].to_numpy()

    stress_rows: list[dict[str, Any]] = []
    stress_results: dict[tuple[float, float], StrategyResult] = {}
    selected_spec = next(
        item for item in contract["family"]["candidates"] if item["id"] == selected_id
    )
    for borrow in protocol["costs"]["stress"]["annual_short_borrow_bps"]:
        for multiplier in protocol["costs"]["stress"]["cost_multiplier"]:
            result = _run_strategy(
                frame,
                protocol,
                signal=str(selected_spec["signal"]),
                weighting=str(selected_spec["weighting"]),
                cost_multiplier=float(multiplier),
                annual_short_borrow_bps=float(borrow),
            )
            stress_results[(float(borrow), float(multiplier))] = result
            stress_rows.append(
                {
                    "annual_short_borrow_bps": float(borrow),
                    "nonborrow_cost_multiplier": float(multiplier),
                    **result.metrics,
                }
            )
    harsh_key = (
        float(max(protocol["costs"]["stress"]["annual_short_borrow_bps"])),
        float(max(protocol["costs"]["stress"]["cost_multiplier"])),
    )
    decision = _family_decision(
        contract, selected, previous, classic, stress_results[harsh_key]
    )
    decision["best_validation_candidate"] = selected_id

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent)
    )
    try:
        candidates.to_csv(staging / "validation_candidate_table.csv", index=False)
        baselines.to_csv(staging / "baseline_comparison.csv", index=False)
        pd.DataFrame(stress_rows).to_csv(staging / "cost_stress.csv", index=False)
        monthly = pd.DataFrame(
            {
                "month": selected.monthly["realization_date"],
                **{
                    candidate_id: result.monthly["net_return"].to_numpy()
                    for candidate_id, result in sorted(results.items())
                },
            }
        )
        monthly.to_csv(staging / "candidate_monthly_returns.csv", index=False)
        baseline_monthly.to_csv(staging / "baseline_monthly_returns.csv", index=False)
        selected.monthly.to_csv(staging / "selected_monthly_diagnostics.csv", index=False)
        _json_dump(staging / "family_decision.json", decision)
        _json_dump(
            staging / "source_manifest.json",
            {
                "schema_version": "microalpha-crsp-v2-distinct-sources/v1",
                "contract_path": str(contract_path),
                "contract_sha256": sha256_file(contract_path),
                "base_protocol_path": str(base_protocol_path),
                "base_protocol_sha256": protocol_sha256(base_protocol_path),
                "panel_path": str(panel_path),
                "panel_sha256": sha256_file(panel_path),
                "panel_manifest_sha256": sha256_file(
                    panel_path.with_suffix(panel_path.suffix + ".manifest.json")
                ),
                "previous_selection_manifest_path": str(
                    previous_selection_manifest_path
                ),
                "previous_selection_manifest_sha256": sha256_file(
                    previous_selection_manifest_path
                ),
                "panel_builder_git_sha": panel_manifest["git_sha"],
                "runner_git_sha": _git_sha(),
                "final_holdout_outcomes_read": False,
            },
        )
        _json_dump(
            staging / "integrity_report.json",
            {
                "schema_version": "microalpha-crsp-v2-distinct-integrity/v1",
                "candidate_count": len(candidates),
                "eligible_candidate_count": int(candidates["eligible"].sum()),
                "validation_months_per_candidate": {
                    candidate_id: int(result.metrics["validation_months"])
                    for candidate_id, result in sorted(results.items())
                },
                "panel_digest_verified": True,
                "base_protocol_digest_verified": True,
                "previous_selection_digest_verified": True,
                "chronology_verified": True,
                "unique_keys_verified": True,
                "selected_structurally_eligible": bool(selected.metrics["eligible"]),
                "selected_executed_net_neutrality_verified": (
                    selected.metrics["maximum_absolute_executed_net"] <= 1e-9
                ),
                "selected_executed_industry_neutrality_verified": (
                    selected.metrics["maximum_absolute_executed_industry_net"] <= 1e-9
                ),
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
                "schema_version": "microalpha-crsp-v2-distinct-result/v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "best_validation_candidate": selected_id,
                "family_outcome": decision["outcome"],
                "contract_sha256": sha256_file(contract_path),
                "panel_sha256": sha256_file(panel_path),
                "artifacts": artifacts,
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
        "best_validation_candidate": selected_id,
        "family_outcome": decision["outcome"],
        "candidate_count": len(candidates),
        "eligible_candidate_count": int(candidates["eligible"].sum()),
        "final_holdout_outcomes_read": False,
    }


__all__ = ["run_distinct_family"]

"""Single-candidate CRSP-v2 low-volatility mechanism runner."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import pandas as pd
import yaml

from .crsp_v2 import (
    CRSPV2Error,
    audit_source_protocol,
    load_protocol,
    protocol_sha256,
    sha256_file,
)
from .crsp_v2_distinct import (
    _git_sha,
    _json_dump,
    _load_distinct_signal_frame,
)
from .crsp_v2_selection import (
    StrategyResult,
    _baseline_table,
    _load_signal_frame,
    _run_strategy,
    _sql_literal,
    _validate_selection_inputs,
)


def _load_contract(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CRSPV2Error("Low-volatility contract must be a YAML mapping")
    return payload


def _validate_inputs(
    contract_path: Path,
    base_protocol_path: Path,
    panel_path: Path,
    momentum_result_manifest_path: Path,
    residual_result_manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = _load_contract(contract_path)
    protocol = load_protocol(base_protocol_path)
    panel_manifest_path = panel_path.with_suffix(panel_path.suffix + ".manifest.json")
    _, panel_manifest = _validate_selection_inputs(
        base_protocol_path, panel_path, panel_manifest_path
    )
    expected = contract.get("frozen_inputs", {})
    checks = {
        "base_protocol_sha256": protocol_sha256(base_protocol_path),
        "panel_sha256": sha256_file(panel_path),
        "panel_manifest_sha256": sha256_file(panel_manifest_path),
        "momentum_result_manifest_sha256": sha256_file(
            momentum_result_manifest_path
        ),
        "residual_result_manifest_sha256": sha256_file(
            residual_result_manifest_path
        ),
    }
    for key, observed in checks.items():
        if str(expected.get(key, "")) != observed:
            raise CRSPV2Error(f"Low-volatility frozen input mismatch: {key}")
    for path in (momentum_result_manifest_path, residual_result_manifest_path):
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("final_holdout_outcomes_read") is not False:
            raise CRSPV2Error("Archived result receipt does not keep holdout sealed")
    access = contract.get("access_contract", {})
    if access.get("final_holdout_outcomes_read") is not False:
        raise CRSPV2Error("Low-volatility contract must seal final holdout outcomes")
    mechanism = contract.get("mechanism", {})
    if mechanism.get("signal") != "low_volatility_126d":
        raise CRSPV2Error("Low-volatility signal differs from preregistration")
    if mechanism.get("weighting") != "equal":
        raise CRSPV2Error("Low-volatility weighting was frozen to equal")
    return contract, protocol, panel_manifest


def _load_low_volatility_frame(
    panel_path: Path, protocol: Mapping[str, Any]
) -> pd.DataFrame:
    """Expose the precomputed point-in-time volatility as a descending score."""

    try:
        import duckdb
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise CRSPV2Error("DuckDB is required for CRSP-v2 low-volatility research") from exc

    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    first_formation = validation_start - pd.offsets.MonthEnd(1)
    connection = duckdb.connect()
    try:
        frame = connection.execute(f"""
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
                CASE
                    WHEN volatility_126d > 0.0 THEN -volatility_126d
                END AS low_volatility_126d
            FROM read_parquet({_sql_literal(panel_path)})
            WHERE formation_date BETWEEN DATE {_sql_literal(first_formation.date())}
                                     AND DATE {_sql_literal(validation_end.date())}
            ORDER BY formation_date, permno
            """).df()
    finally:
        connection.close()
    frame["formation_date"] = pd.to_datetime(frame["formation_date"])
    if frame.duplicated(["formation_date", "permno"]).any():
        raise CRSPV2Error("Low-volatility frame keys are not unique")
    return frame


def _internal_baseline_row(
    baseline_id: str,
    result: StrategyResult,
    source_path: Path,
) -> dict[str, Any]:
    keys = {
        "net_sharpe_hac",
        "net_sharpe_hac_se",
        "net_sharpe_hac_tstat",
        "cagr",
        "max_drawdown",
        "cumulative_return",
        "total_one_way_turnover",
    }
    return {
        "baseline_id": baseline_id,
        **{key: value for key, value in result.metrics.items() if key in keys},
        "months": int(result.metrics["validation_months"]),
        "classification": "investable_net_archived_validation_baseline",
        "source_path": str(source_path),
        "source_sha256": sha256_file(source_path),
    }


def _mechanism_decision(
    contract: Mapping[str, Any],
    candidate: StrategyResult,
    strongest_archived: StrategyResult,
    harsh_stress: StrategyResult,
) -> dict[str, Any]:
    gate = contract["mechanism_gate"]
    checks = {
        "structurally_eligible": bool(candidate.metrics["eligible"]),
        "minimum_net_sharpe_hac": (
            candidate.metrics["net_sharpe_hac"]
            >= float(gate["minimum_net_sharpe_hac"])
        ),
        "minimum_hac_tstat": (
            candidate.metrics["net_sharpe_hac_tstat"]
            >= float(gate["minimum_hac_tstat"])
        ),
        "beats_strongest_archived_by_minimum_sharpe_delta": (
            candidate.metrics["net_sharpe_hac"]
            >= strongest_archived.metrics["net_sharpe_hac"]
            + float(gate["minimum_sharpe_improvement_over_strongest_archived"])
        ),
        "positive_cagr": candidate.metrics["cagr"] > 0.0,
        "max_drawdown_within_limit": (
            candidate.metrics["max_drawdown"] <= float(gate["maximum_drawdown"])
        ),
        "harsh_stress_positive_sharpe": harsh_stress.metrics["net_sharpe_hac"] > 0.0,
        "harsh_stress_positive_cagr": harsh_stress.metrics["cagr"] > 0.0,
    }
    passed = all(checks.values())
    return {
        "outcome": (
            "freeze_mechanism_keep_final_holdout_sealed"
            if passed
            else "archive_mechanism_as_validation_negative"
        ),
        "all_mechanism_gates_pass": passed,
        "checks": checks,
        "candidate_net_sharpe_hac": candidate.metrics["net_sharpe_hac"],
        "candidate_hac_tstat": candidate.metrics["net_sharpe_hac_tstat"],
        "strongest_archived_net_sharpe_hac": strongest_archived.metrics[
            "net_sharpe_hac"
        ],
        "harsh_stress_net_sharpe_hac": harsh_stress.metrics["net_sharpe_hac"],
        "harsh_stress_cagr": harsh_stress.metrics["cagr"],
        "final_holdout_outcomes_read": False,
    }


def run_low_volatility(
    contract_path: str | Path,
    base_protocol_path: str | Path,
    panel_path: str | Path,
    momentum_result_manifest_path: str | Path,
    residual_result_manifest_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Execute the preregistered single low-volatility candidate atomically."""

    contract_path = Path(contract_path).expanduser().resolve()
    base_protocol_path = Path(base_protocol_path).expanduser().resolve()
    panel_path = Path(panel_path).expanduser().resolve()
    momentum_result_manifest_path = (
        Path(momentum_result_manifest_path).expanduser().resolve()
    )
    residual_result_manifest_path = (
        Path(residual_result_manifest_path).expanduser().resolve()
    )
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise CRSPV2Error(f"Refusing to overwrite low-volatility output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    contract, protocol, panel_manifest = _validate_inputs(
        contract_path,
        base_protocol_path,
        panel_path,
        momentum_result_manifest_path,
        residual_result_manifest_path,
    )
    audit = audit_source_protocol(base_protocol_path)
    low_vol_frame = _load_low_volatility_frame(panel_path, protocol)
    standard_frame = _load_signal_frame(panel_path, protocol)
    residual_frame = _load_distinct_signal_frame(panel_path, protocol)

    candidate = _run_strategy(
        low_vol_frame,
        protocol,
        signal="low_volatility_126d",
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
    classic = _run_strategy(
        standard_frame,
        protocol,
        signal="mom_12_2",
        weighting="equal",
        classic=True,
    )
    baselines, baseline_monthly = _baseline_table(
        protocol, audit, candidate, classic, base_protocol_path
    )
    baselines.loc[
        baselines["baseline_id"].eq("selected_flagship"), "baseline_id"
    ] = "low_volatility_126d"
    baselines = pd.concat(
        [
            baselines,
            pd.DataFrame(
                [
                    _internal_baseline_row(
                        "archived_frozen_momentum",
                        momentum,
                        momentum_result_manifest_path,
                    ),
                    _internal_baseline_row(
                        "archived_residual_momentum",
                        residual,
                        residual_result_manifest_path,
                    ),
                ]
            ),
        ],
        ignore_index=True,
    )
    baseline_monthly = baseline_monthly.rename(
        columns={"selected_flagship": "low_volatility_126d"}
    )
    baseline_monthly["archived_frozen_momentum"] = momentum.monthly[
        "net_return"
    ].to_numpy()
    baseline_monthly["archived_residual_momentum"] = residual.monthly[
        "net_return"
    ].to_numpy()

    stress_rows: list[dict[str, Any]] = []
    stress_results: dict[tuple[float, float], StrategyResult] = {}
    for borrow in protocol["costs"]["stress"]["annual_short_borrow_bps"]:
        for multiplier in protocol["costs"]["stress"]["cost_multiplier"]:
            result = _run_strategy(
                low_vol_frame,
                protocol,
                signal="low_volatility_126d",
                weighting="equal",
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
    decision = _mechanism_decision(
        contract, candidate, residual, stress_results[harsh_key]
    )

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent)
    )
    try:
        pd.DataFrame(
            [
                {
                    "candidate_id": "low_volatility_126d__equal",
                    "signal": "low_volatility_126d",
                    "weighting": "equal",
                    **candidate.metrics,
                }
            ]
        ).to_csv(staging / "validation_candidate_table.csv", index=False)
        baselines.to_csv(staging / "baseline_comparison.csv", index=False)
        pd.DataFrame(stress_rows).to_csv(staging / "cost_stress.csv", index=False)
        baseline_monthly.to_csv(staging / "baseline_monthly_returns.csv", index=False)
        candidate.monthly.to_csv(staging / "candidate_monthly_diagnostics.csv", index=False)
        _json_dump(staging / "mechanism_decision.json", decision)
        _json_dump(
            staging / "source_manifest.json",
            {
                "schema_version": "microalpha-crsp-v2-low-volatility-sources/v1",
                "contract_path": str(contract_path),
                "contract_sha256": sha256_file(contract_path),
                "base_protocol_path": str(base_protocol_path),
                "base_protocol_sha256": protocol_sha256(base_protocol_path),
                "panel_path": str(panel_path),
                "panel_sha256": sha256_file(panel_path),
                "panel_manifest_sha256": sha256_file(
                    panel_path.with_suffix(panel_path.suffix + ".manifest.json")
                ),
                "momentum_result_manifest_path": str(
                    momentum_result_manifest_path
                ),
                "momentum_result_manifest_sha256": sha256_file(
                    momentum_result_manifest_path
                ),
                "residual_result_manifest_path": str(
                    residual_result_manifest_path
                ),
                "residual_result_manifest_sha256": sha256_file(
                    residual_result_manifest_path
                ),
                "panel_builder_git_sha": panel_manifest["git_sha"],
                "runner_git_sha": _git_sha(),
                "final_holdout_outcomes_read": False,
            },
        )
        _json_dump(
            staging / "integrity_report.json",
            {
                "schema_version": "microalpha-crsp-v2-low-volatility-integrity/v1",
                "candidate_count": 1,
                "validation_months": int(candidate.metrics["validation_months"]),
                "panel_digest_verified": True,
                "base_protocol_digest_verified": True,
                "archived_result_digests_verified": True,
                "chronology_verified": True,
                "unique_keys_verified": True,
                "candidate_structurally_eligible": bool(candidate.metrics["eligible"]),
                "candidate_executed_net_neutrality_verified": (
                    candidate.metrics["maximum_absolute_executed_net"] <= 1e-9
                ),
                "candidate_executed_industry_neutrality_verified": (
                    candidate.metrics["maximum_absolute_executed_industry_net"]
                    <= 1e-9
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
                "schema_version": "microalpha-crsp-v2-low-volatility-result/v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "candidate": "low_volatility_126d__equal",
                "mechanism_outcome": decision["outcome"],
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
        "candidate": "low_volatility_126d__equal",
        "mechanism_outcome": decision["outcome"],
        "final_holdout_outcomes_read": False,
    }


__all__ = ["run_low_volatility"]

"""Single-candidate CRSP-v2 short-term industry-residual reversal runner."""

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
from .crsp_v2_low_volatility import (
    _internal_baseline_row,
    _load_low_volatility_frame,
    _mechanism_decision,
)
from .crsp_v2_selection import (
    StrategyResult,
    _baseline_table,
    _load_signal_frame,
    _run_strategy,
    _validate_selection_inputs,
)


def _load_contract(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CRSPV2Error("Short-term reversal contract must be a YAML mapping")
    return payload


def _validate_inputs(
    contract_path: Path,
    base_protocol_path: Path,
    panel_path: Path,
    momentum_result_manifest_path: Path,
    residual_result_manifest_path: Path,
    low_volatility_result_manifest_path: Path,
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
        "low_volatility_result_manifest_sha256": sha256_file(
            low_volatility_result_manifest_path
        ),
    }
    for key, observed in checks.items():
        if str(expected.get(key, "")) != observed:
            raise CRSPV2Error(f"Short-term reversal frozen input mismatch: {key}")
    for path in (
        momentum_result_manifest_path,
        residual_result_manifest_path,
        low_volatility_result_manifest_path,
    ):
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("final_holdout_outcomes_read") is not False:
            raise CRSPV2Error("Archived result receipt does not keep holdout sealed")
    if contract.get("access_contract", {}).get("final_holdout_outcomes_read") is not False:
        raise CRSPV2Error("Short-term reversal contract must seal final holdout outcomes")
    mechanism = contract.get("mechanism", {})
    if mechanism.get("signal") != "short_term_reversal_1_1":
        raise CRSPV2Error("Short-term reversal signal differs from preregistration")
    if mechanism.get("weighting") != "equal":
        raise CRSPV2Error("Short-term reversal weighting was frozen to equal")
    return contract, protocol, panel_manifest


def _load_short_term_reversal_frame(
    panel_path: Path, protocol: Mapping[str, Any]
) -> pd.DataFrame:
    """Use the negative formation-month industry residual as the fixed score."""

    frame = _load_distinct_signal_frame(panel_path, protocol)
    frame["short_term_reversal_1_1"] = -pd.to_numeric(
        frame["industry_residual_return"], errors="coerce"
    )
    return frame


def run_short_term_reversal(
    contract_path: str | Path,
    base_protocol_path: str | Path,
    panel_path: str | Path,
    momentum_result_manifest_path: str | Path,
    residual_result_manifest_path: str | Path,
    low_volatility_result_manifest_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Execute the preregistered pure reversal mechanism atomically."""

    contract_path = Path(contract_path).expanduser().resolve()
    base_protocol_path = Path(base_protocol_path).expanduser().resolve()
    panel_path = Path(panel_path).expanduser().resolve()
    momentum_result_manifest_path = (
        Path(momentum_result_manifest_path).expanduser().resolve()
    )
    residual_result_manifest_path = (
        Path(residual_result_manifest_path).expanduser().resolve()
    )
    low_volatility_result_manifest_path = (
        Path(low_volatility_result_manifest_path).expanduser().resolve()
    )
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise CRSPV2Error(f"Refusing to overwrite short-term reversal output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    contract, protocol, panel_manifest = _validate_inputs(
        contract_path,
        base_protocol_path,
        panel_path,
        momentum_result_manifest_path,
        residual_result_manifest_path,
        low_volatility_result_manifest_path,
    )
    audit = audit_source_protocol(base_protocol_path)
    reversal_frame = _load_short_term_reversal_frame(panel_path, protocol)
    standard_frame = _load_signal_frame(panel_path, protocol)
    residual_frame = _load_distinct_signal_frame(panel_path, protocol)
    low_volatility_frame = _load_low_volatility_frame(panel_path, protocol)

    candidate = _run_strategy(
        reversal_frame,
        protocol,
        signal="short_term_reversal_1_1",
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
    ] = "short_term_reversal_1_1"
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
                    _internal_baseline_row(
                        "archived_low_volatility",
                        low_volatility,
                        low_volatility_result_manifest_path,
                    ),
                ]
            ),
        ],
        ignore_index=True,
    )
    baseline_monthly = baseline_monthly.rename(
        columns={"selected_flagship": "short_term_reversal_1_1"}
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

    stress_rows: list[dict[str, Any]] = []
    stress_results: dict[tuple[float, float], StrategyResult] = {}
    for borrow in protocol["costs"]["stress"]["annual_short_borrow_bps"]:
        for multiplier in protocol["costs"]["stress"]["cost_multiplier"]:
            result = _run_strategy(
                reversal_frame,
                protocol,
                signal="short_term_reversal_1_1",
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
                    "candidate_id": "short_term_reversal_1_1__equal",
                    "signal": "short_term_reversal_1_1",
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
                "schema_version": "microalpha-crsp-v2-short-term-reversal-sources/v1",
                "contract_path": str(contract_path),
                "contract_sha256": sha256_file(contract_path),
                "base_protocol_path": str(base_protocol_path),
                "base_protocol_sha256": protocol_sha256(base_protocol_path),
                "panel_path": str(panel_path),
                "panel_sha256": sha256_file(panel_path),
                "panel_manifest_sha256": sha256_file(
                    panel_path.with_suffix(panel_path.suffix + ".manifest.json")
                ),
                "archived_result_manifests": {
                    "momentum": {
                        "path": str(momentum_result_manifest_path),
                        "sha256": sha256_file(momentum_result_manifest_path),
                    },
                    "residual_momentum": {
                        "path": str(residual_result_manifest_path),
                        "sha256": sha256_file(residual_result_manifest_path),
                    },
                    "low_volatility": {
                        "path": str(low_volatility_result_manifest_path),
                        "sha256": sha256_file(low_volatility_result_manifest_path),
                    },
                },
                "panel_builder_git_sha": panel_manifest["git_sha"],
                "runner_git_sha": _git_sha(),
                "final_holdout_outcomes_read": False,
            },
        )
        _json_dump(
            staging / "integrity_report.json",
            {
                "schema_version": "microalpha-crsp-v2-short-term-reversal-integrity/v1",
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
                "schema_version": "microalpha-crsp-v2-short-term-reversal-result/v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "candidate": "short_term_reversal_1_1__equal",
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
        "candidate": "short_term_reversal_1_1__equal",
        "mechanism_outcome": decision["outcome"],
        "final_holdout_outcomes_read": False,
    }


__all__ = ["run_short_term_reversal"]

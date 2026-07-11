"""Frozen first-filed SEC cash-earnings and classic-momentum rank ensemble."""

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

from .crsp_v2 import CRSPV2Error, audit_source_protocol, sha256_file
from .crsp_v2_fundamental import _centered_percentile_rank
from .crsp_v2_low_volatility import _internal_baseline_row
from .crsp_v2_sec_vintage import (
    _archived_strategy_result,
    _build_sec_vintage_frame,
    _target_ciks,
    _validate_inputs,
    extract_first_filed_sec_features,
)
from .crsp_v2_selection import (
    StrategyResult,
    _baseline_table,
    _git_sha,
    _json_dump,
    _load_signal_frame,
    _run_strategy,
)


def _load_ensemble_contract(path: Path) -> dict[str, Any]:
    contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise CRSPV2Error("SEC-cash/momentum ensemble contract must be a mapping")
    if (
        contract.get("schema_version")
        != "microalpha-sec-cash-classic-momentum-ensemble/v1"
        or contract.get("status") != "predeclared_not_executed"
    ):
        raise CRSPV2Error("SEC-cash/momentum ensemble contract is not frozen")
    mechanism = contract["frozen_mechanism"]
    if mechanism["weighting"] != "equal" or mechanism["weight_grid"] != "forbidden":
        raise CRSPV2Error("SEC-cash/momentum ensemble portfolio weighting changed")
    ranking = mechanism["ranking"]
    if ranking["component_weights"] != {
        "first_filed_sec_cash_earnings_acceleration": 0.5,
        "classic_momentum": 0.5,
    }:
        raise CRSPV2Error("SEC-cash/momentum ensemble component weights changed")
    components = mechanism["components"]
    expected = {
        "first_filed_sec_cash_earnings_acceleration": (
            "sec_cash_earnings_acceleration"
        ),
        "classic_momentum": "mom_12_2",
    }
    if {
        name: item["source_signal"] for name, item in components.items()
    } != expected or any(item["sign"] != "positive" for item in components.values()):
        raise CRSPV2Error("SEC-cash/momentum ensemble signal or sign changed")
    if contract["access_contract"]["final_holdout_outcomes_read"] is not False:
        raise CRSPV2Error("SEC-cash/momentum ensemble final holdout must be sealed")
    return contract


def _ensemble_decision(
    contract: Mapping[str, Any],
    candidate: StrategyResult,
    first_filed_sec: StrategyResult,
    classic_momentum: StrategyResult,
    harsh_stress: StrategyResult,
    coverage: Mapping[str, Any],
) -> dict[str, Any]:
    structural = contract["promotion_gates"]["structural"]
    performance = contract["promotion_gates"]["performance"]
    strongest_component_sharpe = max(
        float(first_filed_sec.metrics["net_sharpe_hac"]),
        float(classic_momentum.metrics["net_sharpe_hac"]),
    )
    checks = {
        "expected_development_months": (
            int(candidate.metrics["validation_months"])
            == int(contract["development"]["expected_months"])
        ),
        "structurally_eligible": bool(candidate.metrics["eligible"]),
        "minimum_complete_names_each_formation_month": (
            int(coverage["minimum_complete_names"])
            >= int(structural["minimum_complete_names_each_formation_month"])
        ),
        "minimum_median_names_per_sleeve": (
            float(candidate.metrics["median_names_per_sleeve"])
            >= float(structural["minimum_median_names_per_sleeve"])
        ),
        "maximum_ambiguous_ccm_rows": (
            int(coverage["ambiguous_ccm_rows"])
            <= int(structural["maximum_ambiguous_ccm_rows"])
        ),
        "all_six_development_years_nondegenerate": (
            int(candidate.metrics["nondegenerate_validation_years"]) == 6
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
        "minimum_sharpe_improvement_over_strongest_component": (
            candidate.metrics["net_sharpe_hac"]
            >= strongest_component_sharpe
            + float(
                performance[
                    "minimum_sharpe_improvement_over_strongest_component"
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
            "promote_stop_development_begin_final_holdout"
            if passed
            else "archive_ensemble_change_information_source"
        ),
        "all_promotion_gates_pass": passed,
        "checks": checks,
        "candidate_net_sharpe_hac": candidate.metrics["net_sharpe_hac"],
        "candidate_cagr": candidate.metrics["cagr"],
        "candidate_max_drawdown": candidate.metrics["max_drawdown"],
        "first_filed_sec_net_sharpe_hac": first_filed_sec.metrics["net_sharpe_hac"],
        "classic_momentum_net_sharpe_hac": classic_momentum.metrics[
            "net_sharpe_hac"
        ],
        "strongest_component_net_sharpe_hac": strongest_component_sharpe,
        "required_net_sharpe_hac_to_beat_strongest_component": (
            strongest_component_sharpe
            + float(
                performance[
                    "minimum_sharpe_improvement_over_strongest_component"
                ]
            )
        ),
        "harsh_stress_net_sharpe_hac": harsh_stress.metrics["net_sharpe_hac"],
        "harsh_stress_cagr": harsh_stress.metrics["cagr"],
        "development_outcomes_read": True,
        "final_holdout_outcomes_read": False,
    }


def run_sec_cash_classic_momentum_ensemble(
    contract_path: str | Path,
    output_dir: str | Path,
    *,
    development_lane_admitted: bool = False,
) -> dict[str, Any]:
    """Run the exact 50/50 rank ensemble once on the frozen development window."""

    if not development_lane_admitted:
        raise CRSPV2Error("SEC-cash/momentum ensemble development is locked")
    contract_path = Path(contract_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    if output_dir.exists():
        raise CRSPV2Error(f"Refusing to overwrite ensemble output: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    contract = _load_ensemble_contract(contract_path)
    sec_spec = contract["frozen_inputs"]["sec_vintage_contract"]
    sec_contract_path = Path(str(sec_spec["path"])).expanduser()
    if not sec_contract_path.is_absolute():
        sec_contract_path = contract_path.parents[2] / sec_contract_path
    sec_contract_path = sec_contract_path.resolve()
    if sha256_file(sec_contract_path) != str(sec_spec["sha256"]):
        raise CRSPV2Error("Frozen SEC-vintage contract changed")
    sec_contract, protocol, panel_manifest, paths, archived = _validate_inputs(
        sec_contract_path
    )
    for name in ("first_filed_sec_result", "frozen_momentum_result"):
        spec = contract["frozen_inputs"][name]
        path = Path(str(spec["path"])).expanduser().resolve()
        if sha256_file(path) != str(spec["sha256"]):
            raise CRSPV2Error(f"Frozen ensemble input changed: {name}")
        if json.loads(path.read_text(encoding="utf-8")).get(
            "final_holdout_outcomes_read"
        ) is not False:
            raise CRSPV2Error(f"Frozen ensemble input opens holdout: {name}")
    first_filed_manifest = Path(
        str(contract["frozen_inputs"]["first_filed_sec_result"]["path"])
    ).expanduser().resolve()
    momentum_manifest = Path(
        str(contract["frozen_inputs"]["frozen_momentum_result"]["path"])
    ).expanduser().resolve()
    if momentum_manifest != archived["momentum"]:
        raise CRSPV2Error("Frozen momentum manifest differs from SEC contract")

    ciks, target_audit = _target_ciks(
        paths["company"], paths["link_history"], paths["panel"], protocol
    )
    features, extraction_audit = extract_first_filed_sec_features(
        paths["companyfacts"],
        paths["submissions"],
        ciks,
        minimum_report_date=sec_contract["access_contract"]["minimum_sec_report_date"],
        maximum_acceptance_timestamp=sec_contract["access_contract"][
            "maximum_sec_acceptance_timestamp"
        ],
    )
    expected_inventory = sec_contract["inventory"][
        "observed_without_return_projection"
    ]
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
        raise CRSPV2Error("Ensemble SEC inventory differs from preregistration")
    frame, _, feature_audit = _build_sec_vintage_frame(
        features,
        paths["company"],
        paths["link_history"],
        paths["panel"],
        protocol,
        include_outcomes=True,
    )
    standard_frame = _load_signal_frame(paths["panel"], protocol)
    momentum_scores = standard_frame[
        ["permno", "formation_date", "mom_12_2"]
    ].copy()
    frame = frame.merge(
        momentum_scores,
        on=["permno", "formation_date"],
        how="left",
        validate="one_to_one",
    )
    complete = (
        frame["eligible_at_formation"].fillna(False).astype(bool)
        & frame["sec_cash_earnings_acceleration"].notna()
        & frame["mom_12_2"].notna()
    )
    frame["sec_component"] = frame["sec_cash_earnings_acceleration"].where(complete)
    frame["momentum_component"] = frame["mom_12_2"].where(complete)
    group = frame.groupby(["formation_date", "industry"], sort=True, dropna=False)
    frame["sec_component_rank"] = group["sec_component"].transform(
        _centered_percentile_rank
    )
    frame["momentum_component_rank"] = group["momentum_component"].transform(
        _centered_percentile_rank
    )
    frame["sec_cash_classic_momentum_rank_ensemble"] = frame[
        ["sec_component_rank", "momentum_component_rank"]
    ].mean(axis=1, skipna=False)
    frame.loc[
        ~complete, "sec_cash_classic_momentum_rank_ensemble"
    ] = pd.NA
    validation_start = pd.Timestamp(protocol["windows"]["validation"]["start"])
    validation_end = pd.Timestamp(protocol["windows"]["validation"]["end"])
    first_formation = validation_start - pd.offsets.MonthEnd(1)
    last_formation = validation_end - pd.offsets.MonthEnd(1)
    formation = frame.loc[
        frame["formation_date"].between(first_formation, last_formation)
    ].copy()
    coverage_rows = []
    for date, snapshot in formation.groupby("formation_date", sort=True):
        scored = snapshot["sec_cash_classic_momentum_rank_ensemble"].notna()
        coverage_rows.append(
            {
                "formation_date": date,
                "complete_names": int(scored.sum()),
                "complete_industries": int(
                    snapshot.loc[scored, "industry"].nunique()
                ),
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    if len(coverage) != 72:
        raise CRSPV2Error("Ensemble coverage must contain 72 formation months")
    coverage_audit = {
        "formation_months": int(len(coverage)),
        "minimum_complete_names": int(coverage["complete_names"].min()),
        "median_complete_names": float(coverage["complete_names"].median()),
        "maximum_complete_names": int(coverage["complete_names"].max()),
        "minimum_complete_industries": int(
            coverage["complete_industries"].min()
        ),
        "ambiguous_ccm_rows": int(feature_audit["ambiguous_ccm_rows"]),
    }

    frame["sec_cash_earnings_acceleration"] = frame[
        "sec_cash_classic_momentum_rank_ensemble"
    ]
    candidate = _run_strategy(
        frame,
        protocol,
        signal="sec_cash_earnings_acceleration",
        weighting="equal",
    )
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
    first_filed_sec = _archived_strategy_result(first_filed_manifest)
    audit = audit_source_protocol(paths["base_protocol"])
    baselines, baseline_monthly = _baseline_table(
        protocol, audit, candidate, classic, paths["base_protocol"]
    )
    baseline_id_map = {
        "selected_flagship": "sec_cash_classic_momentum_rank_ensemble",
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
                        "archived_first_filed_cash_earnings",
                        first_filed_sec,
                        first_filed_manifest,
                    ),
                    _internal_baseline_row(
                        "archived_frozen_momentum", momentum, momentum_manifest
                    ),
                ]
            ),
        ],
        ignore_index=True,
    )
    expected_baselines = list(contract["development"]["baselines"])
    ordered_ids = [
        "sec_cash_classic_momentum_rank_ensemble",
        *expected_baselines,
    ]
    baselines = baselines.loc[baselines["baseline_id"].isin(ordered_ids)].copy()
    if set(baselines["baseline_id"]) != set(ordered_ids):
        raise CRSPV2Error("Ensemble frozen baseline set is incomplete")
    baselines["baseline_id"] = pd.Categorical(
        baselines["baseline_id"], categories=ordered_ids, ordered=True
    )
    baselines = baselines.sort_values("baseline_id").reset_index(drop=True)
    baselines["baseline_id"] = baselines["baseline_id"].astype(str)
    baseline_monthly = baseline_monthly.rename(columns=baseline_id_map)
    baseline_monthly["archived_first_filed_cash_earnings"] = (
        first_filed_sec.monthly["net_return"].to_numpy()
    )
    baseline_monthly["archived_frozen_momentum"] = momentum.monthly[
        "net_return"
    ].to_numpy()
    baseline_monthly = baseline_monthly[["month", *ordered_ids]].copy()

    stress_rows: list[dict[str, Any]] = []
    stress_results: dict[tuple[float, float], StrategyResult] = {}
    stress = contract["development"]["stress_grid"]
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
    decision = _ensemble_decision(
        contract,
        candidate,
        first_filed_sec,
        classic,
        stress_results[harsh_key],
        coverage_audit,
    )
    del frame, standard_frame, features, ciks

    staging = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.staging-", dir=output_dir.parent)
    )
    try:
        pd.DataFrame(
            [
                {
                    "candidate_id": contract["objective"]["candidate_id"],
                    "signal": contract["objective"]["signal"],
                    "weighting": "equal",
                    **candidate.metrics,
                }
            ]
        ).to_csv(staging / "development_candidate_table.csv", index=False)
        baselines.to_csv(staging / "baseline_comparison.csv", index=False)
        pd.DataFrame(stress_rows).to_csv(staging / "cost_stress.csv", index=False)
        baseline_monthly.to_csv(staging / "baseline_monthly_returns.csv", index=False)
        candidate.monthly.to_csv(
            staging / "candidate_monthly_diagnostics.csv", index=False
        )
        coverage.to_csv(staging / "feature_coverage.csv", index=False)
        _json_dump(staging / "promotion_decision.json", decision)
        _json_dump(
            staging / "source_manifest.json",
            {
                "schema_version": "microalpha-sec-cash-momentum-ensemble-sources/v1",
                "contract_path": str(contract_path),
                "contract_sha256": sha256_file(contract_path),
                "sec_vintage_contract_path": str(sec_contract_path),
                "sec_vintage_contract_sha256": sha256_file(sec_contract_path),
                "panel_sha256": sha256_file(paths["panel"]),
                "panel_manifest_sha256": sha256_file(paths["panel_manifest"]),
                "first_filed_sec_result_sha256": sha256_file(first_filed_manifest),
                "frozen_momentum_result_sha256": sha256_file(momentum_manifest),
                "target_audit": target_audit,
                "extraction_audit": extraction_audit,
                "feature_audit": feature_audit,
                "coverage_audit": coverage_audit,
                "panel_builder_git_sha": panel_manifest["git_sha"],
                "runner_git_sha": _git_sha(),
                "restricted_identifier_rows_written": 0,
                "development_outcomes_read": True,
                "final_holdout_outcomes_read": False,
            },
        )
        _json_dump(
            staging / "integrity_report.json",
            {
                "schema_version": "microalpha-sec-cash-momentum-ensemble-integrity/v1",
                "source_digests_verified": True,
                "component_signs_verified": True,
                "equal_component_weights_verified": True,
                "weight_grid_executed": False,
                "frozen_universe_portfolio_costs_verified": True,
                "frozen_baseline_set_verified": True,
                "frozen_stress_grid_verified": True,
                "candidate_executed_net_neutrality_verified": (
                    candidate.metrics["maximum_absolute_executed_net"] <= 1e-9
                ),
                "candidate_executed_industry_neutrality_verified": (
                    candidate.metrics["maximum_absolute_executed_industry_net"]
                    <= 1e-9
                ),
                "restricted_identifier_rows_written": 0,
                "development_run_count": 1,
                "development_outcomes_read": True,
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
                "schema_version": "microalpha-sec-cash-momentum-ensemble-result/v1",
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "candidate": contract["objective"]["candidate_id"],
                "mechanism_outcome": decision["outcome"],
                "contract_sha256": sha256_file(contract_path),
                "runner_git_sha": _git_sha(),
                "artifacts": artifacts,
                "restricted_identifier_rows_written": 0,
                "development_run_count": 1,
                "development_outcomes_read": True,
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
        "candidate": contract["objective"]["candidate_id"],
        "mechanism_outcome": decision["outcome"],
        "all_promotion_gates_pass": decision["all_promotion_gates_pass"],
        "net_sharpe_hac": candidate.metrics["net_sharpe_hac"],
        "cagr": candidate.metrics["cagr"],
        "max_drawdown": candidate.metrics["max_drawdown"],
        "runner_git_sha": _git_sha(),
        "development_run_count": 1,
        "final_holdout_outcomes_read": False,
    }


__all__ = ["run_sec_cash_classic_momentum_ensemble"]

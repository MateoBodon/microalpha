"""Deterministic synthetic correctness fixture for the public showcase.

The fixture intentionally creates invalid positive results and a labeled planted
control. It demonstrates audit behavior; it is not market evidence or alpha.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Mapping, cast

import numpy as np

from .multiple_testing import centered_max_statistic_test
from .point_in_time import PointInTimeViolation, require_point_in_time

SCHEMA_VERSION = "microalpha.audit-lab.v1"
GENERATOR_VERSION = "0.2.0"
DEFAULT_SEED = 20260715
PERIODS_PER_YEAR = 252


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sharpe(returns: np.ndarray) -> float:
    values = np.asarray(returns, dtype=float)
    std = float(values.std(ddof=0))
    if values.size < 2 or std == 0.0:
        return 0.0
    return float(np.sqrt(PERIODS_PER_YEAR) * values.mean() / std)


def _round(value: float) -> float:
    return round(float(value), 4)


def _array_digest(arrays: Mapping[str, np.ndarray]) -> str:
    digest = hashlib.sha256()
    for name in sorted(arrays):
        value = np.ascontiguousarray(arrays[name], dtype="<f8")
        digest.update(name.encode("utf-8"))
        digest.update(str(value.shape).encode("ascii"))
        digest.update(value.tobytes())
    return digest.hexdigest()


def _generator_source_hashes() -> dict[str, str]:
    """Bind the receipt to the source modules that generate its evidence."""
    module_dir = Path(__file__).resolve().parent
    return {
        name: _sha256((module_dir / name).read_bytes())
        for name in ("audit_lab.py", "multiple_testing.py", "point_in_time.py")
    }


def _comparison_csv(rows: list[dict[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=["audit", "unsafe_or_naive", "safe_or_corrected", "unit", "verdict"],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _bar(
    *, x: float, y: float, width: float, value: float, scale: float, color: str
) -> str:
    normalized = min(abs(value) / scale, 1.0)
    bar_width = max(2.0, width * normalized)
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="18" '
        f'rx="9" fill="{color}"/>'
    )


def _comparison_svg(results: dict[str, object]) -> bytes:
    leakage = results["leakage"]
    execution = results["execution"]
    costs = results["costs"]
    selection = results["selection"]
    assert isinstance(leakage, dict)
    assert isinstance(execution, dict)
    assert isinstance(costs, dict)
    assert isinstance(selection, dict)

    cards = [
        (
            "1  POINT-IN-TIME DATA",
            "Leaky revised value",
            float(leakage["leaky_sharpe"]),
            "PIT-safe value",
            float(leakage["pit_safe_sharpe"]),
            f'{leakage["unavailable_rows_blocked"]} unavailable rows blocked',
        ),
        (
            "2  EVENT-TIME EXECUTION",
            "Same-tick oracle",
            float(execution["same_tick_sharpe"]),
            "Queued t+1",
            float(execution["t_plus_1_sharpe"]),
            "State changes only when the fill event arrives",
        ),
        (
            "3  COST RECONCILIATION",
            "Gross planted control",
            float(costs["gross_sharpe"]),
            "Commission + spread + impact + borrow",
            float(costs["net_sharpe"]),
            f'Exact P&amp;L residual {float(costs["reconciliation_error"]):.1e}',
        ),
        (
            "4  SELECTION CONTROL",
            "Best of 128 noise models",
            float(selection["naive_in_sample_sharpe"]),
            "Walk-forward OOS",
            float(selection["walk_forward_oos_sharpe"]),
            f'Max-stat p={float(selection["noise_family_p_value"]):.3f}; planted control p={float(selection["planted_control_p_value"]):.3f}',
        ),
    ]

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760" role="img" aria-labelledby="title desc">',
        '<title id="title">Microalpha Audit Lab correctness results</title>',
        '<desc id="desc">Four comparisons show inflation from data leakage, same-tick execution, omitted costs, and naive model selection.</desc>',
        '<rect width="1200" height="760" rx="28" fill="#07111f"/>',
        '<text x="64" y="72" fill="#f8fafc" font-family="Inter,Arial,sans-serif" font-size="38" font-weight="700">Four ways a backtest lies</text>',
        '<text x="64" y="110" fill="#94a3b8" font-family="Inter,Arial,sans-serif" font-size="19">Known-ground-truth synthetic fixture · correctness test, not alpha</text>',
    ]
    for index, (
        heading,
        bad_label,
        bad_value,
        good_label,
        good_value,
        note,
    ) in enumerate(cards):
        row = index // 2
        col = index % 2
        x = 64 + col * 548
        y = 150 + row * 276
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="516" height="238" rx="18" fill="#0f1d2f" stroke="#20324a"/>',
                f'<text x="{x + 28}" y="{y + 40}" fill="#7dd3fc" font-family="Inter,Arial,sans-serif" font-size="15" font-weight="700" letter-spacing="1.2">{heading}</text>',
                f'<text x="{x + 28}" y="{y + 78}" fill="#cbd5e1" font-family="Inter,Arial,sans-serif" font-size="16">{bad_label}</text>',
                f'<text x="{x + 462}" y="{y + 78}" text-anchor="end" fill="#fb7185" font-family="ui-monospace,SFMono-Regular,monospace" font-size="20" font-weight="700">{bad_value:+.2f}</text>',
                _bar(
                    x=x + 28,
                    y=y + 92,
                    width=434,
                    value=bad_value,
                    scale=20.0,
                    color="#e11d48",
                ),
                f'<text x="{x + 28}" y="{y + 142}" fill="#cbd5e1" font-family="Inter,Arial,sans-serif" font-size="16">{good_label}</text>',
                f'<text x="{x + 462}" y="{y + 142}" text-anchor="end" fill="#4ade80" font-family="ui-monospace,SFMono-Regular,monospace" font-size="20" font-weight="700">{good_value:+.2f}</text>',
                _bar(
                    x=x + 28,
                    y=y + 156,
                    width=434,
                    value=good_value,
                    scale=20.0,
                    color="#22c55e",
                ),
                f'<text x="{x + 28}" y="{y + 208}" fill="#94a3b8" font-family="Inter,Arial,sans-serif" font-size="14">{note}</text>',
            ]
        )
    parts.extend(
        [
            '<text x="64" y="728" fill="#64748b" font-family="Inter,Arial,sans-serif" font-size="14">Generated by microalpha audit-demo · all values are receipt-bound</text>',
            "</svg>",
        ]
    )
    return ("\n".join(parts) + "\n").encode("utf-8")


def _lineage_svg() -> bytes:
    nodes = [
        (55, 116, 190, 78, "Synthetic oracle", "seed + schema"),
        (302, 116, 190, 78, "Availability gate", "available_at ≤ decision_at"),
        (549, 116, 190, 78, "Event queue", "fill only at market time"),
        (796, 116, 190, 78, "Cost ledger", "gross − 4 components"),
        (1043, 116, 102, 78, "Receipt", "SHA-256"),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360" role="img" aria-labelledby="title desc">',
        '<title id="title">Microalpha audit data lineage</title>',
        '<desc id="desc">A safe pipeline moves a synthetic oracle through availability, event scheduling, cost reconciliation, and an artifact receipt.</desc>',
        '<rect width="1200" height="360" rx="24" fill="#f8fafc"/>',
        '<text x="55" y="58" fill="#0f172a" font-family="Inter,Arial,sans-serif" font-size="30" font-weight="700">Audit lineage: every claim has a clock and a hash</text>',
    ]
    for idx, (x, y, width, height, title, subtitle) in enumerate(nodes):
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="14" fill="#ffffff" stroke="#0ea5e9" stroke-width="2"/>',
                f'<text x="{x + width / 2}" y="{y + 32}" text-anchor="middle" fill="#0f172a" font-family="Inter,Arial,sans-serif" font-size="16" font-weight="700">{title}</text>',
                f'<text x="{x + width / 2}" y="{y + 57}" text-anchor="middle" fill="#475569" font-family="Inter,Arial,sans-serif" font-size="12">{subtitle}</text>',
            ]
        )
        if idx < len(nodes) - 1:
            next_x = nodes[idx + 1][0]
            parts.append(
                f'<path d="M {x + width + 10} {y + height / 2} H {next_x - 14}" stroke="#38bdf8" stroke-width="3" marker-end="url(#arrow)"/>'
            )
    parts.extend(
        [
            '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#38bdf8"/></marker></defs>',
            '<path d="M 302 238 H 739" stroke="#e11d48" stroke-width="2" stroke-dasharray="8 6"/>',
            '<text x="520" y="270" text-anchor="middle" fill="#be123c" font-family="Inter,Arial,sans-serif" font-size="15" font-weight="700">Fail closed: unavailable rows or early fills never enter state</text>',
            '<text x="55" y="326" fill="#64748b" font-family="Inter,Arial,sans-serif" font-size="13">Synthetic fixture only · no provider, licensed dataset, holdout, or network access</text>',
            "</svg>",
        ]
    )
    return ("\n".join(parts) + "\n").encode("utf-8")


def _build_results(seed: int) -> tuple[dict[str, object], dict[str, np.ndarray]]:
    rng = np.random.default_rng(seed)
    n_days = 756

    # A: a revised value contains the contemporaneous return but is not available
    # until two sessions later. The safe feature is independent at decision time.
    market_returns = rng.normal(0.0, 0.01, size=n_days)
    initial_feature = rng.normal(0.0, 1.0, size=n_days)
    revised_feature = market_returns.copy()
    decision_day: np.ndarray = np.arange(n_days, dtype=float)
    revised_available_day = decision_day + 2.0
    row_ids = [f"fixture_row_{index:03d}" for index in range(n_days)]
    try:
        require_point_in_time(decision_day, revised_available_day, row_ids=row_ids)
    except PointInTimeViolation as exc:
        unavailable_count = exc.count
    else:  # pragma: no cover - fixture deliberately violates availability
        raise AssertionError("leaky fixture unexpectedly passed point-in-time gate")
    require_point_in_time(decision_day, decision_day, row_ids=row_ids)
    leaky_returns = np.sign(revised_feature) * market_returns
    pit_positions = np.sign(initial_feature)
    pit_returns = np.roll(pit_positions, 1) * market_returns
    pit_returns[0] = 0.0

    # B: a same-close oracle sees the return it is meant to trade. The queued
    # t+1 version uses the same signal only after the next event arrives.
    execution_returns = rng.normal(0.0, 0.009, size=n_days)
    same_tick = np.sign(execution_returns) * execution_returns
    queued_positions = np.roll(np.sign(execution_returns), 1)
    queued_positions[0] = 0.0
    queued_t1 = queued_positions * execution_returns

    # C: a small planted software-control edge is consumed by explicit costs.
    cost_positions = rng.choice(np.array([-1.0, 1.0]), size=n_days)
    gross_cost_fixture = 0.00045 + rng.normal(0.0, 0.006, size=n_days)
    turnover = np.abs(np.diff(np.r_[0.0, cost_positions]))
    commission = turnover * 0.00010
    half_spread = turnover * 0.00020
    impact = turnover * 0.00015
    borrow = (cost_positions < 0.0).astype(float) * 0.00002
    total_cost = commission + half_spread + impact + borrow
    net_cost_fixture = gross_cost_fixture - total_cost
    reconciliation = gross_cost_fixture - total_cost - net_cost_fixture

    # D: full-sample selection finds a winner in noise. Walk-forward selection
    # uses only the first two thirds and is evaluated on untouched final data.
    selection_rng = np.random.default_rng(seed + 1)
    base_noise_returns = selection_rng.normal(0.0, 0.01, size=n_days)
    noise_signals = selection_rng.choice(np.array([-1.0, 1.0]), size=(n_days, 128))
    noise_candidates = noise_signals * base_noise_returns[:, None]
    split = 504
    in_sample_sharpes = np.array(
        [_sharpe(noise_candidates[:split, idx]) for idx in range(128)]
    )
    selected_index = int(np.argmax(in_sample_sharpes))
    naive_full_sharpes = np.array(
        [_sharpe(noise_candidates[:, idx]) for idx in range(128)]
    )
    naive_index = int(np.argmax(naive_full_sharpes))
    walk_forward_oos = noise_candidates[split:, selected_index]

    noise_test = centered_max_statistic_test(
        noise_candidates,
        benchmark_returns=np.zeros(n_days),
        candidate_names=[f"noise_{idx:03d}" for idx in range(128)],
        seed=seed + 101,
        num_bootstrap=999,
        block_length=8,
    )
    planted = noise_candidates[:, :31].copy()
    planted_control = selection_rng.normal(0.0025, 0.01, size=n_days)
    planted = np.column_stack([planted_control, planted])
    planted_test = centered_max_statistic_test(
        planted,
        benchmark_returns=np.zeros(n_days),
        candidate_names=["planted_control", *[f"noise_{idx:03d}" for idx in range(31)]],
        seed=seed + 102,
        num_bootstrap=999,
        block_length=8,
    )

    results: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "fixture": "deterministic_synthetic_known_ground_truth",
        "claim_boundary": "software correctness demonstration; not alpha or market evidence",
        "seed": seed,
        "observations": n_days,
        "leakage": {
            "leaky_sharpe": _round(_sharpe(leaky_returns)),
            "pit_safe_sharpe": _round(_sharpe(pit_returns)),
            "inflation_removed": _round(_sharpe(leaky_returns) - _sharpe(pit_returns)),
            "unavailable_rows_blocked": unavailable_count,
            "availability_rule": "available_at <= decision_at",
        },
        "execution": {
            "same_tick_sharpe": _round(_sharpe(same_tick)),
            "t_plus_1_sharpe": _round(_sharpe(queued_t1)),
            "inflation_removed": _round(_sharpe(same_tick) - _sharpe(queued_t1)),
            "state_rule": "no fill mutation before scheduled market event",
        },
        "costs": {
            "gross_sharpe": _round(_sharpe(gross_cost_fixture)),
            "net_sharpe": _round(_sharpe(net_cost_fixture)),
            "commission_total": _round(commission.sum()),
            "half_spread_total": _round(half_spread.sum()),
            "impact_total": _round(impact.sum()),
            "borrow_total": _round(borrow.sum()),
            "reconciliation_error": float(np.max(np.abs(reconciliation))),
        },
        "selection": {
            "candidate_count": 128,
            "naive_full_sample_winner": f"noise_{naive_index:03d}",
            "naive_in_sample_sharpe": _round(naive_full_sharpes[naive_index]),
            "walk_forward_selected": f"noise_{selected_index:03d}",
            "walk_forward_oos_sharpe": _round(_sharpe(walk_forward_oos)),
            "noise_family_p_value": _round(float(cast(float, noise_test["p_value"]))),
            "planted_control_p_value": _round(
                float(cast(float, planted_test["p_value"]))
            ),
            "test": "centered synchronous max statistic vs zero-return benchmark",
        },
    }
    arrays = {
        "market_returns": market_returns,
        "initial_feature": initial_feature,
        "revised_feature": revised_feature,
        "execution_returns": execution_returns,
        "gross_cost_fixture": gross_cost_fixture,
        "cost_positions": cost_positions,
        "noise_candidates": noise_candidates,
        "planted_control": planted_control,
    }
    return results, arrays


def run_audit_lab(
    output_dir: str | Path, *, seed: int = DEFAULT_SEED
) -> dict[str, object]:
    """Generate the canonical Audit Lab evidence set and SHA-256 receipt."""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    results, arrays = _build_results(seed)
    rows = [
        {
            "audit": "point_in_time_data",
            "unsafe_or_naive": results["leakage"]["leaky_sharpe"],  # type: ignore[index]
            "safe_or_corrected": results["leakage"]["pit_safe_sharpe"],  # type: ignore[index]
            "unit": "annualized_sharpe",
            "verdict": "unavailable_rows_blocked",
        },
        {
            "audit": "event_time_execution",
            "unsafe_or_naive": results["execution"]["same_tick_sharpe"],  # type: ignore[index]
            "safe_or_corrected": results["execution"]["t_plus_1_sharpe"],  # type: ignore[index]
            "unit": "annualized_sharpe",
            "verdict": "future_fill_queued",
        },
        {
            "audit": "cost_reconciliation",
            "unsafe_or_naive": results["costs"]["gross_sharpe"],  # type: ignore[index]
            "safe_or_corrected": results["costs"]["net_sharpe"],  # type: ignore[index]
            "unit": "annualized_sharpe",
            "verdict": "all_cost_components_reconciled",
        },
        {
            "audit": "selection_control",
            "unsafe_or_naive": results["selection"]["naive_in_sample_sharpe"],  # type: ignore[index]
            "safe_or_corrected": results["selection"]["walk_forward_oos_sharpe"],  # type: ignore[index]
            "unit": "annualized_sharpe",
            "verdict": "noise_family_not_promoted",
        },
    ]
    files = {
        "audit_results.json": _json_bytes(results),
        "comparison.csv": _comparison_csv(rows),
        "audit_lab.svg": _comparison_svg(results),
        "data_lineage.svg": _lineage_svg(),
    }
    for name, content in files.items():
        (out / name).write_bytes(content)

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "generator": {
            "version": GENERATOR_VERSION,
            "source_sha256": _generator_source_hashes(),
        },
        "fixture": "deterministic_synthetic_known_ground_truth",
        "claim_boundary": "software correctness demonstration; not alpha or market evidence",
        "seed": seed,
        "input_sha256": _array_digest(arrays),
        "artifacts": {
            name: _sha256(content) for name, content in sorted(files.items())
        },
    }
    receipt_bytes = _json_bytes(receipt)
    (out / "receipt.json").write_bytes(receipt_bytes)
    return {
        "artifact_dir": str(out),
        "receipt_sha256": _sha256(receipt_bytes),
        "results": results,
    }

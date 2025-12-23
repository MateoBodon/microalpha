"""Hansen SPA test utilities for Microalpha parameter grids."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass
class SpaSummary:
    status: str
    reason: str | None
    best_model: str | None
    p_value: float | None
    observed_stat: float | None
    num_bootstrap: int
    avg_block: int
    candidate_stats: list[dict[str, float | str]]
    n_obs: int
    n_strategies: int
    diagnostics: list[str]


_MIN_OBS = 5
_VAR_EPS = 1e-12


def _degenerate_summary(
    reason: str,
    *,
    n_obs: int,
    n_strategies: int,
    avg_block: int,
    num_bootstrap: int,
    diagnostics: list[str] | None = None,
) -> SpaSummary:
    return SpaSummary(
        status="degenerate",
        reason=reason,
        best_model=None,
        p_value=None,
        observed_stat=None,
        num_bootstrap=num_bootstrap,
        avg_block=avg_block,
        candidate_stats=[],
        n_obs=n_obs,
        n_strategies=n_strategies,
        diagnostics=diagnostics or [],
    )


def _coerce_numeric_frame(frame: pd.DataFrame) -> pd.DataFrame:
    numeric = frame.apply(pd.to_numeric, errors="coerce")
    return numeric.replace([np.inf, -np.inf], np.nan)


def load_grid_returns(grid_path: Path) -> pd.DataFrame:
    if not grid_path.exists():
        raise FileNotFoundError(f"Grid returns file not found: {grid_path}")
    if grid_path.suffix.lower() == ".json":
        payload = json.loads(grid_path.read_text(encoding="utf-8"))
        rows: list[dict[str, float | str | int]] = []
        for entry in payload:
            model = entry.get("model") or entry.get("name")
            returns = entry.get("returns") or []
            timestamps = entry.get("timestamps") or []
            if not model:
                continue
            if not timestamps or len(timestamps) != len(returns):
                timestamps = list(range(len(returns)))
            for ts, value in zip(timestamps, returns):
                rows.append(
                    {
                        "panel_id": entry.get("panel_id") or f"{model}:{ts}",
                        "model": model,
                        "value": float(value),
                        "timestamp": ts,
                    }
                )
        frame = pd.DataFrame(rows)
    else:
        frame = pd.read_csv(grid_path)
    if "model" not in frame.columns or "value" not in frame.columns:
        raise ValueError("Grid returns data must include 'model' and 'value' columns")
    if "panel_id" not in frame.columns:
        if {"fold", "timestamp"}.issubset(frame.columns):
            frame["panel_id"] = frame["fold"].astype(str) + ":" + frame["timestamp"].astype(str)
        else:
            frame["panel_id"] = frame.index.astype(str)
    frame["_order"] = np.arange(len(frame))
    pivot = (
        frame.pivot_table(index="panel_id", columns="model", values="value", aggfunc="first")
        .dropna()
    )
    order = frame.groupby("panel_id")["_order"].min().sort_values()
    pivot = pivot.loc[order.index]
    return pivot


def _stationary_bootstrap_indices(n: int, avg_block: int, rng: np.random.Generator) -> np.ndarray:
    p = 1.0 / max(1, avg_block)
    indices = np.empty(n, dtype=int)
    current = int(rng.integers(0, n))
    for t in range(n):
        indices[t] = current
        if rng.random() < p:
            current = int(rng.integers(0, n))
        else:
            current = (current + 1) % n
    return indices


def _spa_stat(diff_matrix: np.ndarray) -> tuple[float, list[float]]:
    if diff_matrix.size == 0:
        return 0.0, []
    T, k = diff_matrix.shape
    stats: list[float] = []
    for j in range(k):
        series = diff_matrix[:, j]
        mean = float(np.mean(series))
        std = float(np.std(series, ddof=1))
        if std <= 0.0:
            stats.append(0.0)
            continue
        t_val = np.sqrt(T) * max(0.0, mean) / std
        stats.append(float(t_val))
    return float(max(stats)) if stats else 0.0, stats


def compute_spa(
    pivot: pd.DataFrame,
    *,
    avg_block: int = 63,
    num_bootstrap: int = 2000,
    seed: int = 0,
) -> SpaSummary:
    diagnostics: list[str] = []
    if not isinstance(pivot, pd.DataFrame):
        return _degenerate_summary(
            "pivot is not a DataFrame",
            n_obs=0,
            n_strategies=0,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
        )

    if avg_block <= 0:
        diagnostics.append("avg_block <= 0; clamped to 1")
        avg_block = 1
    if num_bootstrap <= 0:
        return _degenerate_summary(
            "num_bootstrap must be positive",
            n_obs=0,
            n_strategies=pivot.shape[1],
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
        )

    cleaned = _coerce_numeric_frame(pivot)
    dropped_cols = [col for col in cleaned.columns if cleaned[col].isna().all()]
    if dropped_cols:
        diagnostics.append(f"dropped {len(dropped_cols)} all-NaN strategy columns")
        cleaned = cleaned.drop(columns=dropped_cols)
    n_strategies = int(cleaned.shape[1])
    if n_strategies < 2:
        return _degenerate_summary(
            "need at least two strategies after cleaning",
            n_obs=0,
            n_strategies=n_strategies,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
            diagnostics=diagnostics,
        )

    pre_rows = int(cleaned.shape[0])
    cleaned = cleaned.dropna(axis=0, how="any")
    dropped_rows = pre_rows - int(cleaned.shape[0])
    if dropped_rows:
        diagnostics.append(f"dropped {dropped_rows} rows with NaN/inf values")
    n_obs = int(cleaned.shape[0])
    if n_obs < _MIN_OBS:
        return _degenerate_summary(
            f"insufficient observations (n_obs={n_obs}, min_required={_MIN_OBS})",
            n_obs=n_obs,
            n_strategies=n_strategies,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
            diagnostics=diagnostics,
        )

    variances = cleaned.var(axis=0, ddof=0)
    if np.all(np.abs(variances.to_numpy(dtype=float)) <= _VAR_EPS):
        return _degenerate_summary(
            "all strategies have zero variance",
            n_obs=n_obs,
            n_strategies=n_strategies,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
            diagnostics=diagnostics,
        )

    matrix = cleaned.to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        return _degenerate_summary(
            "non-finite values remain after cleaning",
            n_obs=n_obs,
            n_strategies=n_strategies,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
            diagnostics=diagnostics,
        )

    means = matrix.mean(axis=0)
    if not np.isfinite(means).all():
        return _degenerate_summary(
            "non-finite mean returns",
            n_obs=n_obs,
            n_strategies=n_strategies,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
            diagnostics=diagnostics,
        )

    model_names = list(cleaned.columns)
    best_idx = int(np.argmax(means))
    best_model = str(model_names[best_idx])
    diff_matrix = matrix[:, [best_idx]] - matrix
    diff_matrix = np.delete(diff_matrix, best_idx, axis=1)
    comparator_names = [name for i, name in enumerate(model_names) if i != best_idx]
    observed_stat, component_stats = _spa_stat(diff_matrix)

    if not math.isfinite(observed_stat):
        return _degenerate_summary(
            "non-finite observed SPA statistic",
            n_obs=n_obs,
            n_strategies=n_strategies,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
            diagnostics=diagnostics,
        )
    if any(not math.isfinite(stat) for stat in component_stats):
        return _degenerate_summary(
            "non-finite comparator t-stats",
            n_obs=n_obs,
            n_strategies=n_strategies,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
            diagnostics=diagnostics,
        )

    rng = np.random.default_rng(seed)
    boot_stats = np.zeros(num_bootstrap, dtype=float)
    centered = diff_matrix - diff_matrix.mean(axis=0)
    for b in range(num_bootstrap):
        indices = _stationary_bootstrap_indices(len(matrix), avg_block, rng)
        boot_slice = centered[indices, :]
        boot_stats[b], _ = _spa_stat(boot_slice)
    finite_boot = boot_stats[np.isfinite(boot_stats)]
    if finite_boot.size == 0:
        return _degenerate_summary(
            "bootstrap statistics are all NaN/inf",
            n_obs=n_obs,
            n_strategies=n_strategies,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
            diagnostics=diagnostics,
        )
    if finite_boot.size != boot_stats.size:
        diagnostics.append("dropped non-finite bootstrap statistics")
    p_value = float(np.mean(finite_boot >= observed_stat))
    if not math.isfinite(p_value):
        return _degenerate_summary(
            "non-finite SPA p-value",
            n_obs=n_obs,
            n_strategies=n_strategies,
            avg_block=avg_block,
            num_bootstrap=num_bootstrap,
            diagnostics=diagnostics,
        )
    p_value = min(max(p_value, 0.0), 1.0)

    candidate_stats: list[dict[str, float | str]] = []
    for name, stat, series in zip(
        comparator_names,
        component_stats,
        diff_matrix.T,
    ):
        candidate_stats.append(
            {
                "model": str(name),
                "mean_diff": float(np.mean(series)),
                "t_stat": float(stat),
            }
        )
    return SpaSummary(
        status="ok",
        reason=None,
        best_model=best_model,
        p_value=p_value,
        observed_stat=observed_stat,
        num_bootstrap=num_bootstrap,
        avg_block=avg_block,
        candidate_stats=candidate_stats,
        n_obs=n_obs,
        n_strategies=n_strategies,
        diagnostics=diagnostics,
    )


def write_outputs(summary: SpaSummary, json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": summary.status,
        "reason": summary.reason,
        "best_model": summary.best_model,
        "p_value": summary.p_value,
        "observed_stat": summary.observed_stat,
        "num_bootstrap": summary.num_bootstrap,
        "avg_block": summary.avg_block,
        "candidate_stats": summary.candidate_stats,
        "n_obs": summary.n_obs,
        "n_strategies": summary.n_strategies,
        "diagnostics": summary.diagnostics,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# Hansen SPA Summary", ""]
    if summary.status != "ok":
        lines.append(f"- **Status:** {summary.status}")
        lines.append(f"- **Reason:** {summary.reason or 'invalid inputs'}")
        lines.append(f"- **Observations:** {summary.n_obs}")
        lines.append(f"- **Strategies:** {summary.n_strategies}")
        if summary.diagnostics:
            lines.append(f"- **Diagnostics:** {', '.join(summary.diagnostics)}")
    else:
        lines.append(f"- **Best model:** {summary.best_model}")
        lines.append(f"- **Observed max t-stat:** {summary.observed_stat:.3f}")
        lines.append(f"- **p-value:** {summary.p_value:.3f}")
        lines.append(
            f"- **Bootstrap draws:** {summary.num_bootstrap} (avg block {summary.avg_block})"
        )
        lines.append("")
        if summary.candidate_stats:
            lines.append("| Comparator | Mean Diff | t-stat |")
            lines.append("| --- | ---:| ---:|")
            for row in summary.candidate_stats:
                lines.append(
                    f"| {row['model']} | {row['mean_diff']:.4f} | {row['t_stat']:.2f} |"
                )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--grid",
        type=Path,
        required=True,
        help="CSV/JSON file with parameter grid returns (e.g. artifacts/.../grid_returns.csv)",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("artifacts/analytics/spa.json"),
        help="Path to write SPA JSON summary",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("artifacts/analytics/spa.md"),
        help="Path to write SPA markdown summary",
    )
    parser.add_argument("--bootstrap", type=int, default=2000, help="Number of stationary bootstrap draws")
    parser.add_argument("--avg-block", type=int, default=63, help="Average block length for stationary bootstrap")
    parser.add_argument("--seed", type=int, default=0, help="Seed for reproducibility")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        pivot = load_grid_returns(args.grid)
        summary = compute_spa(
            pivot,
            avg_block=args.avg_block,
            num_bootstrap=args.bootstrap,
            seed=args.seed,
        )
    except Exception as exc:  # pragma: no cover - CLI fallback
        summary = _degenerate_summary(
            f"{type(exc).__name__}: {exc}",
            n_obs=0,
            n_strategies=0,
            avg_block=args.avg_block,
            num_bootstrap=args.bootstrap,
        )
    write_outputs(summary, args.output_json, args.output_md)


if __name__ == "__main__":
    main()

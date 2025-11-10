"""Hansen SPA test utilities for Microalpha parameter grids."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd


@dataclass
class SpaSummary:
    best_model: str
    p_value: float
    observed_stat: float
    num_bootstrap: int
    avg_block: int
    candidate_stats: list[dict[str, float | str]]


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
    if pivot.shape[1] < 2:
        raise ValueError("SPA test requires at least two candidate models")
    model_names = list(pivot.columns)
    matrix = pivot.to_numpy(dtype=float)
    means = matrix.mean(axis=0)
    best_idx = int(np.argmax(means))
    best_model = model_names[best_idx]
    diff_matrix = matrix[:, [best_idx]] - matrix
    diff_matrix = np.delete(diff_matrix, best_idx, axis=1)
    comparator_names = [name for i, name in enumerate(model_names) if i != best_idx]
    observed_stat, component_stats = _spa_stat(diff_matrix)

    rng = np.random.default_rng(seed)
    boot_stats = np.zeros(num_bootstrap)
    for b in range(num_bootstrap):
        indices = _stationary_bootstrap_indices(len(matrix), avg_block, rng)
        boot_slice = diff_matrix[indices, :]
        boot_stats[b], _ = _spa_stat(boot_slice)
    p_value = float(np.mean(boot_stats >= observed_stat))
    candidate_stats = []
    for name, stat, series in zip(
        comparator_names,
        component_stats,
        diff_matrix.T,
    ):
        candidate_stats.append(
            {
                "model": name,
                "mean_diff": float(np.mean(series)),
                "t_stat": float(stat),
            }
        )
    return SpaSummary(
        best_model=best_model,
        p_value=p_value,
        observed_stat=observed_stat,
        num_bootstrap=num_bootstrap,
        avg_block=avg_block,
        candidate_stats=candidate_stats,
    )


def write_outputs(summary: SpaSummary, json_path: Path, markdown_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "best_model": summary.best_model,
        "p_value": summary.p_value,
        "observed_stat": summary.observed_stat,
        "num_bootstrap": summary.num_bootstrap,
        "avg_block": summary.avg_block,
        "candidate_stats": summary.candidate_stats,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# Hansen SPA Summary", "", f"- **Best model:** {summary.best_model}"]
    lines.append(f"- **Observed max t-stat:** {summary.observed_stat:.3f}")
    lines.append(f"- **p-value:** {summary.p_value:.3f}")
    lines.append(f"- **Bootstrap draws:** {summary.num_bootstrap} (avg block {summary.avg_block})")
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
    pivot = load_grid_returns(args.grid)
    summary = compute_spa(
        pivot,
        avg_block=args.avg_block,
        num_bootstrap=args.bootstrap,
        seed=args.seed,
    )
    write_outputs(summary, args.output_json, args.output_md)


if __name__ == "__main__":
    main()

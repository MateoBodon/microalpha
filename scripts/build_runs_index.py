#!/usr/bin/env python3
"""Build a deterministic runs index from artifact manifests."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from microalpha.manifest import ManifestLoadError, load_manifest_path

DEFAULT_ARTIFACTS_ROOT = Path("artifacts")
DEFAULT_OUTPUT = Path("reports/summaries/runs_index.csv")

RUNS_INDEX_COLUMNS = [
    "experiment",
    "run_id",
    "artifact_dir",
    "manifest_path",
    "git_sha",
    "microalpha_version",
    "python",
    "platform",
    "seed",
    "config_path",
    "config_sha256",
    "dataset_id",
    "unsafe_execution",
    "unsafe_reasons",
    "run_invalid",
    "integrity_path",
    "selection_window_start",
    "selection_window_end",
    "holdout_start",
    "holdout_end",
    "selected_model",
    "holdout_metrics_path",
    "holdout_manifest_path",
    "headline_sharpe_ratio",
    "headline_cagr",
    "headline_max_drawdown",
    "headline_ann_vol",
    "headline_total_turnover",
    "headline_traded_days",
    "headline_num_trades",
    "headline_final_equity",
]

HEADLINE_METRIC_KEYS = (
    "sharpe_ratio",
    "cagr",
    "max_drawdown",
    "ann_vol",
    "total_turnover",
    "traded_days",
    "num_trades",
    "final_equity",
)


def _format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:.6f}"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def _normalize_path(value: Any, repo_root: Path) -> str:
    if not value:
        return ""
    text = str(value)
    path = Path(text)
    if not path.is_absolute():
        return path.as_posix()
    try:
        resolved = path.expanduser().resolve(strict=False)
        root = repo_root.resolve()
        if resolved == root or root in resolved.parents:
            return resolved.relative_to(root).as_posix()
    except Exception:
        return path.as_posix()
    return path.as_posix()


def _relative_to(path: Path, root: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path


def _load_optional_json(path_value: Any, repo_root: Path) -> dict[str, Any]:
    if not path_value:
        return {}
    path = Path(str(path_value))
    if not path.is_absolute():
        path = repo_root / path
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"warning: invalid JSON in metrics file {path}: {exc}", file=sys.stderr)
        return {}
    except OSError as exc:
        print(f"warning: unable to read metrics file {path}: {exc}", file=sys.stderr)
        return {}
    return payload if isinstance(payload, dict) else {}


def _collect_manifests(artifacts_root: Path) -> list[Path]:
    if not artifacts_root.exists():
        return []
    candidates: list[Path] = []
    candidates.extend(artifacts_root.glob("*/manifest.json"))
    candidates.extend(artifacts_root.glob("*/*/manifest.json"))
    unique: dict[str, Path] = {}
    for path in candidates:
        key = path.resolve().as_posix()
        unique[key] = path
    return sorted(unique.values(), key=lambda p: _relative_to(p, artifacts_root).as_posix())


def _extract_walkforward(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    wf = payload.get("walkforward")
    return wf if isinstance(wf, Mapping) else {}


def _build_row(
    manifest_path: Path, artifacts_root: Path, repo_root: Path
) -> dict[str, str]:
    payload = load_manifest_path(manifest_path)
    rel_manifest = _relative_to(manifest_path, artifacts_root)
    run_dir_rel = rel_manifest.parent
    run_parts = run_dir_rel.parts
    experiment = run_parts[0] if len(run_parts) > 1 else ""
    run_dir = run_dir_rel.name

    wf_payload = _extract_walkforward(payload)
    holdout_metrics_path = wf_payload.get("holdout_metrics_path")
    metrics_payload = _load_optional_json(holdout_metrics_path, repo_root)

    row: dict[str, Any] = {
        "experiment": experiment,
        "run_id": payload.get("run_id") or run_dir,
        "artifact_dir": _normalize_path(artifacts_root / run_dir_rel, repo_root),
        "manifest_path": _normalize_path(manifest_path, repo_root),
        "git_sha": payload.get("git_sha"),
        "microalpha_version": payload.get("microalpha_version"),
        "python": payload.get("python"),
        "platform": payload.get("platform"),
        "seed": payload.get("seed"),
        "config_path": _normalize_path(payload.get("config_path"), repo_root),
        "config_sha256": payload.get("config_sha256"),
        "dataset_id": payload.get("dataset_id"),
        "unsafe_execution": payload.get("unsafe_execution"),
        "unsafe_reasons": payload.get("unsafe_reasons"),
        "run_invalid": payload.get("run_invalid"),
        "integrity_path": _normalize_path(payload.get("integrity_path"), repo_root),
        "selection_window_start": wf_payload.get("selection_window_start"),
        "selection_window_end": wf_payload.get("selection_window_end"),
        "holdout_start": wf_payload.get("holdout_start"),
        "holdout_end": wf_payload.get("holdout_end"),
        "selected_model": wf_payload.get("selected_model"),
        "holdout_metrics_path": _normalize_path(holdout_metrics_path, repo_root),
        "holdout_manifest_path": _normalize_path(
            wf_payload.get("holdout_manifest_path"), repo_root
        ),
    }

    for key in HEADLINE_METRIC_KEYS:
        row[f"headline_{key}"] = metrics_payload.get(key)

    return {col: _format_value(row.get(col)) for col in RUNS_INDEX_COLUMNS}


def build_runs_index(artifacts_root: Path, repo_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for manifest_path in _collect_manifests(artifacts_root):
        rows.append(_build_row(manifest_path, artifacts_root, repo_root))
    rows.sort(key=lambda row: (row["experiment"], row["run_id"], row["artifact_dir"]))
    return rows


def write_csv(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUNS_INDEX_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifacts-root",
        type=Path,
        default=DEFAULT_ARTIFACTS_ROOT,
        help="Root directory containing artifact subfolders (default: artifacts).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="CSV output path (default: reports/summaries/runs_index.csv).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifacts_root = args.artifacts_root
    output_path = args.output

    if not artifacts_root.exists():
        print(f"warning: artifacts root not found: {artifacts_root}", file=sys.stderr)
        write_csv([], output_path)
        return 0

    try:
        rows = build_runs_index(artifacts_root, REPO_ROOT)
    except ManifestLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    write_csv(rows, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

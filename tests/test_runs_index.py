from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_runs_index.py"

EXPECTED_COLUMNS = [
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


def _write_manifest(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_runs_index_deterministic(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"

    _write_manifest(
        artifacts / "root-run" / "manifest.json",
        {"run_id": "root-run"},
    )

    holdout_metrics = artifacts / "exp_alpha" / "run-b" / "holdout_metrics.json"
    holdout_metrics.parent.mkdir(parents=True, exist_ok=True)
    holdout_metrics.write_text(
        json.dumps(
            {
                "sharpe_ratio": 1.23456789,
                "cagr": 0.1,
                "max_drawdown": 0.2,
                "ann_vol": 0.3,
                "total_turnover": 100.0,
                "traded_days": 10,
                "num_trades": 5,
                "final_equity": 1000.0,
            }
        ),
        encoding="utf-8",
    )

    _write_manifest(
        artifacts / "exp_alpha" / "run-b" / "manifest.json",
        {
            "run_id": "run-b",
            "git_sha": "abc",
            "walkforward": {
                "selection_window_start": "2020-01-01",
                "selection_window_end": "2020-12-31",
                "holdout_start": "2021-01-01",
                "holdout_end": "2021-06-30",
                "selected_model": "model-x",
                "holdout_metrics_path": str(holdout_metrics),
            },
        },
    )

    _write_manifest(
        artifacts / "exp_alpha" / "run-a" / "manifest.json",
        {"run_id": "run-a", "git_sha": "def"},
    )

    output_path = tmp_path / "runs_index.csv"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--artifacts-root",
            str(artifacts),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    with output_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == EXPECTED_COLUMNS
    assert [row["run_id"] for row in rows] == ["root-run", "run-a", "run-b"]

    metrics_row = next(row for row in rows if row["run_id"] == "run-b")
    assert metrics_row["headline_sharpe_ratio"] == "1.234568"
    assert metrics_row["headline_cagr"] == "0.100000"


def test_runs_index_invalid_json(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    bad_manifest = artifacts / "bad" / "manifest.json"
    bad_manifest.parent.mkdir(parents=True, exist_ok=True)
    bad_manifest.write_text("{", encoding="utf-8")

    output_path = tmp_path / "runs_index.csv"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--artifacts-root",
            str(artifacts),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "invalid json" in result.stderr.lower()

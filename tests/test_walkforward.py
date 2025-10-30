from __future__ import annotations

import json
from pathlib import Path

from microalpha.walkforward import run_walk_forward


def test_sample_walkforward_produces_folds(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    result = run_walk_forward(
        "configs/wfv_flagship_sample.yaml",
        override_artifacts_dir=str(artifacts_dir),
    )

    folds = result["folds"]
    assert folds, "Expected walk-forward folds to be generated"

    for fold in folds:
        assert fold["best_params"] is not None
        assert fold["test_metrics"] is not None
        assert fold.get("reality_check") is not None
        if fold.get("reality_check_pvalue") is not None:
            assert 0.0 <= float(fold["reality_check_pvalue"]) <= 1.0
        if fold.get("exposures_path"):
            assert Path(fold["exposures_path"]).exists()

    folds_path = Path(result["folds_path"])
    assert folds_path.exists()
    persisted = json.loads(folds_path.read_text())
    assert len(persisted) == len(folds)

    bootstrap_path = Path(result["bootstrap_path"])
    assert bootstrap_path.exists()
    bootstrap_payload = json.loads(bootstrap_path.read_text())
    assert isinstance(bootstrap_payload, list)
    if bootstrap_payload:
        assert all(isinstance(entry, (int, float)) for entry in bootstrap_payload)

    metrics = result["metrics"]
    if metrics.get("reality_check_p_value") is not None:
        assert 0.0 <= float(metrics["reality_check_p_value"]) <= 1.0

    exposures_path = result.get("exposures_path")
    if exposures_path:
        assert Path(exposures_path).exists()


def test_walkforward_manifest_paths_are_relative(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    result = run_walk_forward(
        "configs/wfv_flagship_sample.yaml",
        override_artifacts_dir=str(artifacts_dir),
    )

    assert Path(result["folds_path"]).exists()
    assert Path(result["bootstrap_path"]).exists()
    if result.get("exposures_path"):
        assert Path(result["exposures_path"]).exists()

from __future__ import annotations

import json
from pathlib import Path

from microalpha.runner import run_from_config


def test_runner_executes_flagship_strategy(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    result = run_from_config(
        "configs/flagship_sample.yaml",
        override_artifacts_dir=str(artifact_dir),
    )

    metrics_info = result["metrics"]
    metrics_path = Path(metrics_info["metrics_path"])
    assert metrics_path.exists()
    metrics = json.loads(metrics_path.read_text())
    assert "sharpe_ratio" in metrics
    assert "sharpe_ratio_se" in metrics

    bootstrap_path = Path(result["bootstrap_path"])
    assert bootstrap_path.exists()
    bootstrap_samples = json.loads(bootstrap_path.read_text())
    assert isinstance(bootstrap_samples, list)
    assert len(bootstrap_samples) >= 1024
    assert all(isinstance(x, (int, float)) for x in bootstrap_samples)
    assert metrics_info.get("bootstrap_samples", 0) >= 1024
    assert 0.0 <= float(metrics_info.get("bootstrap_p_value", 0.5)) <= 1.0

    exposures_path = Path(result["exposures_path"])
    assert exposures_path.exists()
    exposures = exposures_path.read_text().strip().splitlines()
    assert exposures and exposures[0].startswith("symbol")

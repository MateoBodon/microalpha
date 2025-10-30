from __future__ import annotations

from pathlib import Path
import json

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
    bootstrap = json.loads(bootstrap_path.read_text())
    assert len(bootstrap.get("distribution", [])) >= 1024
    assert 0.0 <= float(bootstrap.get("p_value", 0.5)) <= 1.0

    exposures_path = Path(result["exposures_path"])
    assert exposures_path.exists()
    exposures = exposures_path.read_text().strip().splitlines()
    assert exposures and exposures[0].startswith("symbol")

from __future__ import annotations

import json
from pathlib import Path

from microalpha.runner import run_from_config


def test_bootstrap_distribution_persisted(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    manifest = run_from_config(
        "configs/flagship_sample.yaml",
        override_artifacts_dir=str(artifact_dir),
    )

    bootstrap_path = Path(manifest["bootstrap_path"])
    assert bootstrap_path.exists()
    samples = json.loads(bootstrap_path.read_text())
    assert isinstance(samples, list)
    assert len(samples) >= 1024
    assert all(isinstance(x, (int, float)) for x in samples)

    metrics = manifest["metrics"]
    assert metrics.get("bootstrap_samples", 0) >= 1024
    p_value = float(metrics.get("bootstrap_p_value", 0.5))
    assert 0.0 <= p_value <= 1.0

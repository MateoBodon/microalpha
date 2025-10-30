from __future__ import annotations

import json
from pathlib import Path


def _latest_artifact(root: Path) -> Path:
    assert root.exists(), f"Expected artifact root {root}"  # noqa: S101
    candidates = [p for p in root.iterdir() if p.is_dir()]
    assert candidates, f"No artifact runs under {root}"  # noqa: S101
    return max(candidates, key=lambda p: p.stat().st_mtime)


def test_sample_flagship_artifact_schema() -> None:
    artifact = _latest_artifact(Path("artifacts/sample_flagship"))

    metrics_path = artifact / "metrics.json"
    assert metrics_path.exists()
    metrics = json.loads(metrics_path.read_text())
    for key in ("sharpe_ratio", "cagr", "max_drawdown", "total_turnover"):
        assert key in metrics
    assert metrics.get("bootstrap_samples", 0) >= 1
    assert "bootstrap_p_value" in metrics

    bootstrap_path = artifact / "bootstrap.json"
    assert bootstrap_path.exists()
    samples = json.loads(bootstrap_path.read_text())
    assert isinstance(samples, list)
    assert all(isinstance(x, (int, float)) for x in samples)

    assert (artifact / "equity_curve.png").exists()
    assert (artifact / "bootstrap_hist.png").exists()


def test_sample_wfv_artifact_schema() -> None:
    artifact = _latest_artifact(Path("artifacts/sample_wfv"))

    metrics_path = artifact / "metrics.json"
    assert metrics_path.exists()
    metrics = json.loads(metrics_path.read_text())
    for key in ("sharpe_ratio", "calmar_ratio", "max_drawdown", "total_turnover"):
        assert key in metrics
    if metrics.get("reality_check_p_value") is not None:
        assert 0.0 <= float(metrics["reality_check_p_value"]) <= 1.0

    bootstrap_path = artifact / "bootstrap.json"
    assert bootstrap_path.exists()
    samples = json.loads(bootstrap_path.read_text())
    assert isinstance(samples, list)
    if samples:
        assert all(isinstance(x, (int, float)) for x in samples)

    for fname in ("equity_curve.png", "bootstrap_hist.png"):
        assert (artifact / fname).exists()

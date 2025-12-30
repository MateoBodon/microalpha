from __future__ import annotations

from pathlib import Path

from microalpha.reporting.factors import compute_factor_regression


def test_factor_regression_computes_betas() -> None:
    artifact_root = Path("artifacts/sample_wfv")
    artifact = max(artifact_root.iterdir(), key=lambda p: p.name)
    output = compute_factor_regression(
        artifact / "equity_curve.csv",
        Path("data/factors/ff3_sample.csv"),
        hac_lags=3,
        allow_resample=True,
    )
    assert output.results, "Expected factor regression to produce results"
    names = [row.name for row in output.results]
    assert names[0] == "Alpha"

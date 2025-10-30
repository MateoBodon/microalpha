from __future__ import annotations

from microalpha.metrics import compute_metrics


def test_compute_metrics_includes_hac_fields(monkeypatch) -> None:
    equity_records = [
        {"timestamp": i, "equity": 100.0 + i, "exposure": 0.5}
        for i in range(40)
    ]
    monkeypatch.setenv("METRICS_HAC_LAGS", "5")
    metrics = compute_metrics(equity_records, turnover=123.0, rf=0.02)
    assert metrics["sharpe_ratio_se"] >= 0.0
    assert metrics["sharpe_ratio_ci_low"] <= metrics["sharpe_ratio_ci_high"]
    assert metrics["sharpe_ratio_tstat"] == metrics["sharpe_ratio"] / metrics["sharpe_ratio_se"]
    assert metrics["sharpe_hac_lags"] == 5.0
    monkeypatch.delenv("METRICS_HAC_LAGS")

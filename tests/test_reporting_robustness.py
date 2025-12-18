from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from microalpha.reporting.robustness import (
    compute_cost_sensitivity,
    compute_metadata_coverage,
    write_robustness_artifacts,
)
from microalpha.reporting.summary import generate_summary


def _write_equity(tmp_path: Path) -> Path:
    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    equity = pd.Series([1_000_000, 1_010_000, 1_005_000, 1_020_000, 1_025_000], index=dates)
    df = pd.DataFrame(
        {
            "timestamp": dates.view("int64"),
            "equity": equity,
            "exposure": 0.5,
            "returns": equity.pct_change().fillna(0.0),
        }
    )
    path = tmp_path / "equity_curve.csv"
    df.to_csv(path, index=False)
    return path


def test_cost_sensitivity_generates_grid(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    _write_equity(artifact_dir)

    trades = [
        {"timestamp": pd.Timestamp("2025-01-02").value, "symbol": "AAA", "qty": 100, "price": 10.0, "commission": 5.0, "slippage": 0.02},
        {"timestamp": pd.Timestamp("2025-01-03").value, "symbol": "AAA", "qty": -50, "price": 11.0, "commission": 2.5, "slippage": 0.01},
    ]
    trades_path = artifact_dir / "trades.jsonl"
    trades_path.write_text("\n".join(json.dumps(t) for t in trades), encoding="utf-8")

    result = compute_cost_sensitivity(artifact_dir, multipliers=(0.5, 1.0, 2.0))
    assert result["method"] == "ex_post_cost_scaling"
    grid = {row["multiplier"]: row for row in result["grid"]}
    assert 1.0 in grid
    assert abs(grid[1.0]["cost_drag_bps_per_year"]) < 1e-6
    assert 2.0 in grid and grid[2.0]["sharpe_ratio"] <= grid[0.5]["sharpe_ratio"]


def test_metadata_coverage_uses_meta_csv(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    _write_equity(artifact_dir)

    meta_path = tmp_path / "meta.csv"
    pd.DataFrame(
        {
            "symbol": ["AAA"],
            "adv": [1_000_000],
            "spread_bps": [12.0],
            "borrow_fee_annual_bps": [150.0],
        }
    ).to_csv(meta_path, index=False)

    config = {
        "data_path": "ignored",
        "symbol": "AAA",
        "meta_path": str(meta_path),
        "exec": {"slippage": {"default_adv": 2_000_000.0, "default_spread_bps": 10.0}},
        "strategy": {"name": "MeanReversionStrategy", "params": {}},
    }
    cfg_path = artifact_dir / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    trades = [
        {"timestamp": pd.Timestamp("2025-01-02").value, "symbol": "AAA", "qty": 100, "price": 10.0, "commission": 0.0, "slippage": 0.0},
        {"timestamp": pd.Timestamp("2025-01-03").value, "symbol": "BBB", "qty": -50, "price": 11.0, "commission": 0.0, "slippage": 0.0},
    ]
    (artifact_dir / "trades.jsonl").write_text("\n".join(json.dumps(t) for t in trades), encoding="utf-8")

    coverage = compute_metadata_coverage(artifact_dir)
    assert coverage["meta_source"].endswith("meta.csv")
    cov = coverage["coverage"]
    assert 0.6 <= cov["pct_notional_with_adv"] <= 0.7  # majority of notional has metadata
    assert cov["pct_short_notional_with_borrow_fee"] == 0.0  # BBB missing borrow meta
    assert coverage["defaults"]["default_adv"] == 2_000_000.0


def test_summary_includes_robustness_section(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    _write_equity(artifact_dir)
    (artifact_dir / "trades.jsonl").write_text("", encoding="utf-8")
    (artifact_dir / "metrics.json").write_text(json.dumps({"sharpe_ratio": 1.0, "max_drawdown": 0.1, "total_turnover": 0.0}), encoding="utf-8")
    (artifact_dir / "bootstrap.json").write_text("[]", encoding="utf-8")

    write_robustness_artifacts(artifact_dir)
    summary_path = tmp_path / "summary.md"
    generate_summary(artifact_dir, output_path=summary_path, factor_csv=None)
    text = summary_path.read_text(encoding="utf-8")
    assert "Cost & Metadata Robustness" in text
    assert "Cost sensitivity" in text
    assert "Metadata coverage" in text

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from microalpha.reporting.spa import compute_spa, load_grid_returns, write_outputs


def test_load_grid_returns_pivots_panel(tmp_path) -> None:
    path = tmp_path / "grid_returns.csv"
    rows = []
    for fold in range(2):
        for t in range(3):
            panel_id = f"{fold}:{t}"
            rows.append({"fold": fold, "timestamp": t, "model": "A", "value": 0.01 * (t + fold), "panel_id": panel_id})
            rows.append({"fold": fold, "timestamp": t, "model": "B", "value": 0.008 * (t + fold), "panel_id": panel_id})
    pd.DataFrame(rows).to_csv(path, index=False)
    pivot = load_grid_returns(path)
    assert list(pivot.columns) == ["A", "B"]
    assert pivot.shape[0] == 6


def test_compute_spa_identifies_best_model(tmp_path) -> None:
    rng = np.random.default_rng(42)
    length = 120
    obs = pd.DataFrame(
        {
            "A": rng.normal(0.001, 0.0005, size=length),
            "B": rng.normal(0.004, 0.0005, size=length),
            "C": rng.normal(-0.002, 0.0005, size=length),
        }
    )
    summary = compute_spa(obs, avg_block=5, num_bootstrap=200, seed=42)
    assert summary.status == "ok"
    assert summary.best_model == "B"
    assert summary.p_value is not None
    assert 0.0 <= summary.p_value <= 1.0
    json_path = tmp_path / "spa.json"
    md_path = tmp_path / "spa.md"
    write_outputs(summary, json_path, md_path)
    assert json_path.exists()
    assert md_path.exists()


def test_compute_spa_null_case_identical_strategies() -> None:
    rng = np.random.default_rng(123)
    series = rng.normal(0.0, 0.01, size=200)
    obs = pd.DataFrame({"A": series, "B": series})
    summary = compute_spa(obs, avg_block=5, num_bootstrap=200, seed=1)
    assert summary.status == "ok"
    assert summary.p_value is not None
    assert summary.p_value >= 0.8


def test_compute_spa_dominant_strategy() -> None:
    rng = np.random.default_rng(456)
    length = 200
    obs = pd.DataFrame(
        {
            "A": rng.normal(0.01, 0.005, size=length),
            "B": rng.normal(-0.01, 0.005, size=length),
            "C": rng.normal(0.0, 0.005, size=length),
        }
    )
    summary = compute_spa(obs, avg_block=5, num_bootstrap=200, seed=7)
    assert summary.status == "ok"
    assert summary.best_model == "A"
    assert summary.p_value is not None
    assert summary.p_value < 0.2


def test_compute_spa_degenerate_constant_returns(tmp_path) -> None:
    obs = pd.DataFrame({"A": np.full(10, 0.001), "B": np.full(10, 0.001)})
    summary = compute_spa(obs, avg_block=5, num_bootstrap=50, seed=0)
    assert summary.status == "degenerate"
    assert summary.reason
    json_path = tmp_path / "spa.json"
    md_path = tmp_path / "spa.md"
    write_outputs(summary, json_path, md_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["status"] == "degenerate"
    assert md_path.exists()

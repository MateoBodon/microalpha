from __future__ import annotations

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
    length = 120
    obs = pd.DataFrame(
        {
            "A": np.full(length, 0.001, dtype=float),
            "B": np.full(length, 0.004, dtype=float),
            "C": np.full(length, -0.002, dtype=float),
        }
    )
    summary = compute_spa(obs, avg_block=5, num_bootstrap=200, seed=42)
    assert summary.best_model == "B"
    assert 0.0 <= summary.p_value <= 1.0
    json_path = tmp_path / "spa.json"
    md_path = tmp_path / "spa.md"
    write_outputs(summary, json_path, md_path)
    assert json_path.exists()
    assert md_path.exists()

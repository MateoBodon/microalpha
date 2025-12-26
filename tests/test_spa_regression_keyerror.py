import json

import pandas as pd

from microalpha.reporting.spa import compute_spa, load_grid_returns, write_outputs


def test_spa_grid_returns_missing_panel_id_does_not_keyerror(tmp_path):
    grid_path = tmp_path / "grid_returns.csv"
    df = pd.DataFrame(
        [
            {
                "fold": 1,
                "phase": "test",
                "model": "model_a",
                "timestamp": "2020-01-01",
                "panel_id": "1:2020-01-01",
                "value": 0.01,
            },
            {
                "fold": 1,
                "phase": "test",
                "model": "model_b",
                "timestamp": "2020-01-01",
                "panel_id": "1:2020-01-01",
                "value": 0.02,
            },
            {
                "fold": 1,
                "phase": "test",
                "model": "model_a",
                "timestamp": "2020-01-02",
                "panel_id": "1:2020-01-02",
                "value": -0.01,
            },
        ]
    )
    df.to_csv(grid_path, index=False)

    pivot = load_grid_returns(grid_path)
    summary = compute_spa(pivot, avg_block=2, num_bootstrap=50, seed=1)

    json_path = tmp_path / "spa.json"
    md_path = tmp_path / "spa.md"
    write_outputs(summary, json_path, md_path)

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert "spa_status" in payload
    if payload["spa_status"] == "ok":
        assert 0.0 <= payload["p_value"] <= 1.0

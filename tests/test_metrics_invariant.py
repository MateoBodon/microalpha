from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from microalpha.runner import run_from_config


def _make_config(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dates = pd.date_range("2025-02-01", periods=6, freq="D")
    prices = [100, 101, 102, 103, 104, 105]
    df = pd.DataFrame({"close": prices}, index=dates)
    df.to_csv(data_dir / "SPY.csv")

    config = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 50000.0,
        "seed": 99,
        "exec": {"type": "instant", "commission": 0.0},
        "strategy": {
            "name": "MeanReversionStrategy",
            "params": {"lookback": 2, "z_threshold": 0.5},
        },
        "artifacts_dir": str(tmp_path / "artifacts"),
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(config))
    return cfg_path


def test_metrics_are_invariant_and_path_free(tmp_path: Path) -> None:
    cfg_path = _make_config(tmp_path)

    first = run_from_config(str(cfg_path))
    second = run_from_config(str(cfg_path))

    first_metrics = Path(first["artifacts_dir"]) / "metrics.json"
    second_metrics = Path(second["artifacts_dir"]) / "metrics.json"

    assert first_metrics.read_bytes() == second_metrics.read_bytes()

    payload = json.loads(first_metrics.read_text())
    forbidden = {"run_id", "timestamp", "artifacts_dir", "config_path"}
    assert forbidden.isdisjoint(payload)
    assert payload, "metrics payload should not be empty"
    for key, value in payload.items():
        # equity_df is not serialized; remaining metrics should be numeric or None
        assert isinstance(value, (int, float)), f"metric {key} should be numeric"

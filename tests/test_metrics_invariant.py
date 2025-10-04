from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from microalpha.runner import run_from_config


def _make_config(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dates = pd.date_range("2025-01-01", periods=6, freq="D")
    df = pd.DataFrame({"close": [100, 101, 99, 102, 98, 103]}, index=dates)
    df.to_csv(data_dir / "SPY.csv")

    config = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 100_000.0,
        "seed": 13,
        "exec": {"type": "twap", "slices": 2},
        "strategy": {
            "name": "MeanReversionStrategy",
            "params": {"lookback": 2, "z_threshold": 0.5},
        },
        "artifacts_dir": str(tmp_path / "artifacts"),
    }

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(config))
    return cfg_path


def test_metrics_are_run_invariant(tmp_path: Path) -> None:
    cfg_path = _make_config(tmp_path)

    first = run_from_config(str(cfg_path))
    second = run_from_config(str(cfg_path))

    first_metrics = Path(first["artifacts_dir"]) / "metrics.json"
    second_metrics = Path(second["artifacts_dir"]) / "metrics.json"

    assert first_metrics.read_bytes() == second_metrics.read_bytes()

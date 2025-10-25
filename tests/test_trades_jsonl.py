import json
from pathlib import Path

import pandas as pd
import yaml

from microalpha.runner import run_from_config


def _config_path(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    prices = [100, 102, 99, 103, 101]
    df = pd.DataFrame({"close": prices}, index=dates)
    df.to_csv(data_dir / "SPY.csv")

    config = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 50000.0,
        "seed": 21,
        "exec": {"type": "twap", "slices": 2, "commission": 0.0},
        "strategy": {
            "name": "MeanReversionStrategy",
            "params": {"lookback": 2, "z_threshold": 0.5},
        },
        "artifacts_dir": str(tmp_path / "artifacts"),
    }

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(config))
    return cfg_path


def test_trades_jsonl_contains_inventory_and_is_monotonic(tmp_path: Path):
    cfg_path = _config_path(tmp_path)
    result = run_from_config(str(cfg_path))

    trades_path = Path(result["trades_path"])
    assert trades_path.exists()

    with trades_path.open("r", encoding="utf-8") as handle:
        trades = [json.loads(line) for line in handle if line.strip()]

    assert trades, "expected at least one trade in the JSONL log"

    timestamps = [trade["timestamp"] for trade in trades]
    assert timestamps == sorted(timestamps), "trade timestamps must be non-decreasing"

    running_inventory = 0.0
    for trade in trades:
        running_inventory += float(trade["qty"])
        assert abs(running_inventory - float(trade["inventory"])) < 1e-9

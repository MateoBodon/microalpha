from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from microalpha.runner import run_from_config


def test_run_supports_capital_policy_and_volume_slippage(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    idx = pd.date_range("2025-02-01", periods=6, freq="D")
    df = pd.DataFrame(
        {
            "close": [100, 102, 101, 103, 104, 105],
            "volume": [1_000, 1_200, 1_100, 1_300, 1_250, 1_400],
        },
        index=idx,
    )
    df.to_csv(data_dir / "SPY.csv")

    cfg = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 100_000.0,
        "seed": 42,
        "exec": {
            "type": "vwap",
            "slices": 2,
            "commission": 0.0,
            "slippage": {"type": "volume", "impact": 0.0005},
        },
        "strategy": {
            "name": "MeanReversionStrategy",
            "params": {"lookback": 2, "z_threshold": 0.5},
        },
        "capital_policy": {
            "type": "volatility_scaled",
            "lookback": 3,
            "target_dollar_vol": 2_500.0,
            "min_qty": 1,
        },
        "artifacts_dir": str(tmp_path / "artifacts"),
    }

    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))

    result = run_from_config(str(cfg_path))
    trades_path = Path(result["trades_path"])
    assert trades_path.exists()

    metrics_path = Path(result["metrics"]["metrics_path"])
    assert metrics_path.exists()

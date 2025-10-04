from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from microalpha.config import BacktestCfg, ExecModelCfg, StrategyCfg
from microalpha.config_wfv import WalkForwardWindow, WFVCfg
from microalpha.runner import run_from_config
from microalpha.walkforward import run_walk_forward


def _write_price_series(directory: Path, periods: int = 10) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    dates = pd.date_range("2025-01-01", periods=periods, freq="D")
    df = pd.DataFrame({"close": [100 + i for i in range(periods)]}, index=dates)
    df.to_csv(directory / "SPY.csv")


def _backtest_config(tmp_path: Path) -> Path:
    data_dir = tmp_path / "run_data"
    _write_price_series(data_dir, periods=8)

    config = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 50_000.0,
        "seed": 21,
        "exec": {"type": "instant"},
        "strategy": {
            "name": "MeanReversionStrategy",
            "params": {"lookback": 2, "z_threshold": 0.5},
        },
        "artifacts_dir": str(tmp_path / "run_artifacts"),
    }

    cfg_path = tmp_path / "run_config.yaml"
    cfg_path.write_text(yaml.safe_dump(config))
    return cfg_path


def _walkforward_config(tmp_path: Path) -> Path:
    data_dir = tmp_path / "wfv_data"
    _write_price_series(data_dir, periods=16)

    config = WFVCfg(
        template=BacktestCfg(
            data_path=str(data_dir),
            symbol="SPY",
            cash=75_000.0,
            seed=11,
            exec=ExecModelCfg(type="instant"),
            strategy=StrategyCfg(
                name="MeanReversionStrategy",
                params={"lookback": 2, "z": 0.5},
            ),
        ),
        walkforward=WalkForwardWindow(
            start="2025-01-01",
            end="2025-01-16",
            training_days=6,
            testing_days=3,
        ),
        grid={"lookback": [2, 3], "z": [0.5, 1.0]},
        artifacts_dir=str(tmp_path / "wfv_artifacts"),
    )

    cfg_path = tmp_path / "wfv_config.yaml"
    cfg_path.write_text(yaml.safe_dump(config.model_dump(mode="json")))
    return cfg_path


def test_run_and_walkforward_emit_manifests_and_metrics(tmp_path: Path) -> None:
    run_cfg = _backtest_config(tmp_path)
    run_result = run_from_config(str(run_cfg))
    run_dir = Path(run_result["artifacts_dir"])

    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "metrics.json").is_file()
    assert (run_dir / "equity_curve.csv").is_file()

    wfv_cfg = _walkforward_config(tmp_path)
    wfv_result = run_walk_forward(str(wfv_cfg))
    wfv_dir = Path(wfv_result["artifacts_dir"])

    assert (wfv_dir / "manifest.json").is_file()
    assert (wfv_dir / "metrics.json").is_file()
    assert (wfv_dir / "equity_curve.csv").is_file()

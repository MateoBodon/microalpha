from pathlib import Path

import pandas as pd
import yaml

from microalpha.config import BacktestCfg, ExecModelCfg, StrategyCfg
from microalpha.config_wfv import WalkForwardWindow, WFVCfg
from microalpha.walkforward import run_walk_forward


def build_config(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dates = pd.date_range("2025-01-01", periods=12, freq="D")
    df = pd.DataFrame({"date": dates, "close": range(100, 112)})
    df.to_csv(data_dir / "SPY.csv", index=False)

    config = WFVCfg(
        template=BacktestCfg(
            data_path=str(data_dir),
            symbol="SPY",
            cash=100000.0,
            seed=7,
            exec=ExecModelCfg(type="instant"),
            strategy=StrategyCfg(
                name="MeanReversionStrategy",
                params={"lookback": 2, "z": 0.5},
            ),
        ),
        walkforward=WalkForwardWindow(
            start="2025-01-01",
            end="2025-01-12",
            training_days=4,
            testing_days=2,
        ),
        grid={"lookback": [2, 3], "z": [0.5, 1.0]},
        artifacts_dir=str(tmp_path / "artifacts"),
    )

    cfg_path = tmp_path / "wf_config.yaml"
    cfg_path.write_text(yaml.safe_dump(config.model_dump(mode="json")))
    return cfg_path


def test_fold_boundaries_and_metrics(tmp_path):
    cfg_path = build_config(tmp_path)
    result = run_walk_forward(str(cfg_path))

    folds = result["folds"]
    assert folds, "Expected at least one fold"

    for fold in folds:
        assert fold["best_params"] is not None
        train_end = pd.to_datetime(fold["train_metrics"]["period_end"]).date()
        test_start = pd.to_datetime(fold["test_metrics"]["period_start"]).date()
        assert train_end < test_start
        assert fold["test_metrics"]["observations"] > 0
        if fold["spa_pvalue"] is not None:
            assert 0.0 <= fold["spa_pvalue"] <= 1.0

    # ensure manifest style fields present
    assert Path(result["folds_path"]).exists()

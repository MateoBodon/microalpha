from itertools import product
from pathlib import Path

import yaml

from microalpha.config import BacktestCfg, ExecModelCfg, StrategyCfg
from microalpha.config_wfv import WalkForwardWindow, WFVCfg
from microalpha.walkforward import _strategy_params, load_wfv_cfg


def _enumerate_params(cfg: WFVCfg):
    base = _strategy_params(cfg.template.strategy)
    keys = sorted(cfg.grid)
    combinations = []
    for values in product(*(cfg.grid[key] for key in keys)):
        params = dict(base)
        params.update(dict(zip(keys, values)))
        combinations.append(params)
    return combinations


def test_legacy_and_new_configs_align(tmp_path: Path):
    legacy_path = Path("configs/wfv_meanrev.yaml").resolve()
    legacy_cfg = load_wfv_cfg(str(legacy_path))

    new_cfg = WFVCfg(
        template=BacktestCfg(
            data_path="data",
            symbol="SPY",
            cash=100000.0,
            seed=7,
            exec=ExecModelCfg(type="twap", aln=0.5, slices=2),
            strategy=StrategyCfg(
                name="MeanReversionStrategy",
                params={"lookback": 3, "z_threshold": 0.5},
            ),
        ),
        walkforward=WalkForwardWindow(
            start="2025-01-02",
            end="2025-01-10",
            training_days=4,
            testing_days=2,
        ),
        grid={"lookback": [3, 5], "z_threshold": [0.5, 1.0]},
        artifacts_dir="artifacts",
    )

    new_cfg_path = tmp_path / "wfv_new.yaml"
    new_cfg_path.write_text(yaml.safe_dump(new_cfg.model_dump(mode="json")))
    loaded_new = load_wfv_cfg(str(new_cfg_path))

    assert loaded_new.template == new_cfg.template
    assert loaded_new.walkforward == new_cfg.walkforward
    assert loaded_new.grid == new_cfg.grid
    assert loaded_new.artifacts_dir == new_cfg.artifacts_dir

    assert legacy_cfg.walkforward == loaded_new.walkforward
    assert legacy_cfg.grid == loaded_new.grid
    assert _strategy_params(legacy_cfg.template.strategy) == _strategy_params(
        loaded_new.template.strategy
    )

    assert _enumerate_params(legacy_cfg) == _enumerate_params(loaded_new)

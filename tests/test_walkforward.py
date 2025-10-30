import json
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
            exec=ExecModelCfg(type="instant", commission=0.0),
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
        assert "reality_check_pvalue" in fold
        if fold["reality_check_pvalue"] is not None:
            assert 0.0 <= fold["reality_check_pvalue"] <= 1.0
        assert fold["spa_pvalue"] is None
    folds_path = Path(result["folds_path"])
    assert folds_path.exists()
    persisted = json.loads(folds_path.read_text())
    assert all("reality_check_pvalue" in fold for fold in persisted)


def test_multi_asset_walkforward_maintains_data_frames(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    idx = pd.date_range("2025-01-01", periods=40, freq="D")
    for symbol, slope in {"AAA": 0.5, "BBB": 0.3, "CCC": -0.1}.items():
        prices = 100 + slope * (idx - idx[0]).days
        pd.DataFrame({"close": prices}, index=idx).to_csv(data_dir / f"{symbol}.csv")

    cfg = WFVCfg(
        template=BacktestCfg(
            data_path=str(data_dir),
            symbol="SPY",
            cash=100_000.0,
            seed=11,
            exec=ExecModelCfg(type="instant", commission=0.0),
            strategy=StrategyCfg(
                name="CrossSectionalMomentum",
                params={
                    "symbols": ["AAA", "BBB", "CCC"],
                    "lookback_months": 1,
                    "skip_months": 0,
                    "top_frac": 0.34,
                },
            ),
        ),
        walkforward=WalkForwardWindow(
            start="2025-01-01",
            end="2025-02-09",
            training_days=15,
            testing_days=5,
        ),
        grid={"lookback_months": [1], "skip_months": [0]},
        artifacts_dir=str(tmp_path / "artifacts"),
    )

    cfg_path = tmp_path / "multi_wfv.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg.model_dump(mode="json")))

    result = run_walk_forward(str(cfg_path))
    folds = result["folds"]

    assert folds, "expected folds to be generated"
    for fold in folds:
        assert fold["test_metrics"] is not None
        assert fold["best_params"] is not None


def _write_panel(data_dir: Path, symbol: str, prices: list[float]) -> None:
    idx = pd.date_range("2024-01-01", periods=len(prices), freq="D")
    pd.DataFrame({"close": prices, "volume": [1_000_000] * len(prices)}, index=idx).to_csv(
        data_dir / f"{symbol}.csv"
    )


def test_flagship_walkforward_small_panel(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_panel(data_dir, "AAA", [50 + 0.2 * i for i in range(30)])
    _write_panel(data_dir, "BBB", [40 - 0.1 * i for i in range(30)])
    _write_panel(data_dir, "SPY", [100 + 0.05 * i for i in range(30)])

    universe = tmp_path / "universe.csv"
    pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "date": "2024-01-31",
                "sector": "TECH",
                "adv_20": 5_000_000.0,
                "adv_63": 5_000_000.0,
                "adv_126": 5_000_000.0,
                "market_cap_proxy": 1_000_000_000.0,
                "close": 55.0,
            },
            {
                "symbol": "BBB",
                "date": "2024-01-31",
                "sector": "HEALTH",
                "adv_20": 5_000_000.0,
                "adv_63": 5_000_000.0,
                "adv_126": 5_000_000.0,
                "market_cap_proxy": 1_000_000_000.0,
                "close": 42.0,
            },
        ]
    ).to_csv(universe, index=False)

    cfg = WFVCfg(
        template=BacktestCfg(
            data_path=str(data_dir),
            symbol="SPY",
            cash=200_000.0,
            seed=5,
            exec=ExecModelCfg(type="instant", commission=0.0),
            strategy=StrategyCfg(
                name="FlagshipMomentumStrategy",
                params={
                    "universe_path": str(universe),
                    "lookback_months": 1,
                    "skip_months": 0,
                    "top_frac": 0.5,
                    "bottom_frac": 0.5,
                    "max_positions_per_sector": 1,
                    "min_adv": 0.0,
                    "min_price": 0.0,
                    "turnover_target_pct_adv": 0.1,
                },
            ),
            max_positions_per_sector=2,
        ),
        walkforward=WalkForwardWindow(
            start="2024-01-01",
            end="2024-02-20",
            training_days=12,
            testing_days=5,
        ),
        grid={"top_frac": [0.4, 0.5]},
        artifacts_dir=str(tmp_path / "artifacts"),
    )

    cfg_path = tmp_path / "flagship_wfv.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg.model_dump(mode="json")))

    result = run_walk_forward(str(cfg_path))
    assert result["folds"], "walk-forward should produce folds"
    for fold in result["folds"]:
        assert "reality_check_pvalue" in fold
        assert fold["spa_pvalue"] is None

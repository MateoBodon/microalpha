from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from microalpha.events import SignalEvent
from microalpha.walkforward import run_walk_forward
import microalpha.walkforward as walkforward


def test_sample_walkforward_produces_folds(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    result = run_walk_forward(
        "configs/wfv_flagship_sample.yaml",
        override_artifacts_dir=str(artifacts_dir),
    )

    folds = result["folds"]
    assert folds, "Expected walk-forward folds to be generated"

    for fold in folds:
        assert fold["best_params"] is not None
        assert fold["test_metrics"] is not None
        assert fold.get("reality_check") is not None
        if fold.get("reality_check_pvalue") is not None:
            assert 0.0 <= float(fold["reality_check_pvalue"]) <= 1.0
        if fold.get("exposures_path"):
            assert Path(fold["exposures_path"]).exists()

    folds_path = Path(result["folds_path"])
    assert folds_path.exists()
    persisted = json.loads(folds_path.read_text())
    assert len(persisted) == len(folds)

    bootstrap_path = Path(result["bootstrap_path"])
    assert bootstrap_path.exists()
    bootstrap_payload = json.loads(bootstrap_path.read_text())
    assert isinstance(bootstrap_payload, list)
    if bootstrap_payload:
        assert all(isinstance(entry, (int, float)) for entry in bootstrap_payload)

    metrics = result["metrics"]
    if metrics.get("reality_check_p_value") is not None:
        assert 0.0 <= float(metrics["reality_check_p_value"]) <= 1.0

    exposures_path = result.get("exposures_path")
    if exposures_path:
        assert Path(exposures_path).exists()


def test_walkforward_manifest_paths_are_relative(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    result = run_walk_forward(
        "configs/wfv_flagship_sample.yaml",
        override_artifacts_dir=str(artifacts_dir),
    )

    assert Path(result["folds_path"]).exists()
    assert Path(result["bootstrap_path"]).exists()
    if result.get("exposures_path"):
        assert Path(result["exposures_path"]).exists()


class HoldoutDirectionalStrategy:
    def __init__(
        self,
        symbol: str,
        direction: str = "long",
        warmup_prices=None,
        **_ignored,
    ):
        self.symbol = symbol
        self.direction = direction
        self.invested = False

    def on_market(self, event) -> list[SignalEvent]:
        if event.symbol != self.symbol or self.invested:
            return []
        self.invested = True
        side = "LONG" if self.direction == "long" else "SHORT"
        return [SignalEvent(event.timestamp, self.symbol, side)]


def _write_holdout_fixture(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    prices = [100 + i for i in range(10)] + [110 - 3 * i for i in range(10)]
    dates = pd.date_range("2020-01-01", periods=len(prices), freq="D")
    df = pd.DataFrame({"close": prices, "volume": 1_000}, index=dates)
    df.to_csv(data_dir / "TEST.csv")

    config = {
        "template": {
            "data_path": str(data_dir),
            "symbol": "TEST",
            "cash": 100000.0,
            "seed": 7,
            "exec": {"type": "instant", "commission": 0.0},
            "strategy": {
                "name": "HoldoutDirectionalStrategy",
                "params": {"direction": "long"},
            },
        },
        "walkforward": {
            "start": "2020-01-01",
            "end": "2020-01-10",
            "training_days": 3,
            "testing_days": 2,
        },
        "holdout": {"start": "2020-01-11", "end": "2020-01-20"},
        "grid": {"direction": ["long", "short"]},
    }
    cfg_path = tmp_path / "holdout_cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return cfg_path


def test_holdout_selection_excludes_holdout_data(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(
        walkforward.STRATEGY_MAPPING,
        "HoldoutDirectionalStrategy",
        HoldoutDirectionalStrategy,
    )
    cfg_path = _write_holdout_fixture(tmp_path)

    artifacts_dir = tmp_path / "artifacts"
    result = run_walk_forward(
        str(cfg_path), override_artifacts_dir=str(artifacts_dir)
    )

    holdout_manifest = Path(result["holdout_manifest_path"])
    assert holdout_manifest.exists()
    payload = json.loads(holdout_manifest.read_text())
    assert payload["selected_params"] == {"direction": "long"}
    assert payload["selected_model"] == "direction=long"
    assert Path(payload["holdout_metrics_path"]).exists()


def test_holdout_window_does_not_overlap_selection(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(
        walkforward.STRATEGY_MAPPING,
        "HoldoutDirectionalStrategy",
        HoldoutDirectionalStrategy,
    )
    cfg_path = _write_holdout_fixture(tmp_path)

    artifacts_dir = tmp_path / "artifacts"
    result = run_walk_forward(
        str(cfg_path), override_artifacts_dir=str(artifacts_dir)
    )

    holdout_start = pd.Timestamp(result["walkforward"]["holdout_start"])
    for fold in result["folds"]:
        test_end = pd.Timestamp(fold["test_end"])
        assert test_end < holdout_start

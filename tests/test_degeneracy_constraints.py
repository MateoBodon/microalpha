from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

import microalpha.walkforward as walkforward
from microalpha.events import SignalEvent
from microalpha.walkforward import run_walk_forward


class NoTradeStrategy:
    def __init__(self, symbol: str, **_ignored):
        self.symbol = symbol

    def on_market(self, event) -> list[SignalEvent]:
        return []


def _write_prices(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    dates = pd.date_range("2020-01-01", periods=12, freq="D")
    df = pd.DataFrame({"close": 100.0, "volume": 1_000}, index=dates)
    df.to_csv(data_dir / "TEST.csv")
    return data_dir


def test_non_degenerate_rejects_zero_trade_selection(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setitem(walkforward.STRATEGY_MAPPING, "NoTradeStrategy", NoTradeStrategy)
    data_dir = _write_prices(tmp_path)

    config = {
        "template": {
            "data_path": str(data_dir),
            "symbol": "TEST",
            "cash": 100000.0,
            "run_mode": "dev",
            "seed": 7,
            "exec": {"type": "instant", "commission": 0.0},
            "strategy": {"name": "NoTradeStrategy", "params": {}},
        },
        "walkforward": {
            "start": "2020-01-01",
            "end": "2020-01-12",
            "training_days": 3,
            "testing_days": 2,
        },
        "grid": {"dummy": [0]},
        "non_degenerate": {"min_trades": 1},
    }
    cfg_path = tmp_path / "wfv_no_trade.yaml"
    cfg_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(ValueError, match="Non-degenerate constraints rejected all candidates"):
        run_walk_forward(str(cfg_path), override_artifacts_dir=str(tmp_path / "artifacts"))

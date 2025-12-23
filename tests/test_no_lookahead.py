# tests/test_no_lookahead.py
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from microalpha.engine import Engine
from microalpha.events import LookaheadError, MarketEvent, SignalEvent
from microalpha.portfolio import Portfolio
from microalpha.runner import run_from_config


def test_portfolio_raises_lookahead_error_on_stale_signal():
    """
    Tests that the portfolio raises an error if it receives a SignalEvent
    with a timestamp that is earlier than its current known time.
    """

    # 1. Arrange
    # A mock data handler is needed for the Portfolio's constructor
    class MockDataHandler:
        def get_latest_price(self, symbol, timestamp):
            return 100.0

    portfolio = Portfolio(data_handler=MockDataHandler(), initial_cash=100000.0)

    # Set the portfolio's "current time" to a specific point
    portfolio.current_time = 2

    # Create a signal event with a timestamp from the PAST
    stale_signal = SignalEvent(timestamp=1, symbol="SPY", side="LONG")

    # 2. Act & 3. Assert
    # We expect a LookaheadError to be raised when processing the stale event.
    # pytest.raises acts as a context manager to catch the expected error.
    with pytest.raises(LookaheadError):
        list(portfolio.on_signal(stale_signal))


class _StubData:
    def __init__(self, events):
        self._events = list(events)

    def stream(self):
        for event in self._events:
            yield event


class _FutureSignalStrategy:
    def on_market(self, event):
        return [SignalEvent(event.timestamp + 1, event.symbol, "LONG")]


class _NoOpPortfolio:
    def on_market(self, event):
        return None

    def on_signal(self, signal):
        return []

    def on_fill(self, fill):
        return None

    def refresh_equity_after_fills(self, timestamp):
        return None


class _NoOpBroker:
    def execute(self, order, market_timestamp):
        return None


def test_engine_rejects_future_signal_timestamp():
    events = [MarketEvent(1, "SPY", 100.0, 1.0)]
    engine = Engine(
        _StubData(events),
        _FutureSignalStrategy(),
        _NoOpPortfolio(),
        _NoOpBroker(),
    )

    with pytest.raises(LookaheadError):
        engine.run()


def _make_lob_config(tmp_path: Path, *, allow_unsafe: bool | None) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    dates = pd.date_range("2025-01-01", periods=6, freq="D")
    df = pd.DataFrame({"close": [100, 101, 99, 102, 98, 103]}, index=dates)
    df.to_csv(data_dir / "SPY.csv")

    config = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 100000.0,
        "seed": 7,
        "exec": {"type": "lob", "commission": 0.0, "lob_tplus1": False},
        "strategy": {
            "name": "MeanReversionStrategy",
            "params": {"lookback": 2, "z_threshold": 0.5},
        },
        "artifacts_dir": str(tmp_path / "artifacts"),
    }
    if allow_unsafe is not None:
        config["allow_unsafe_execution"] = allow_unsafe

    cfg_path = tmp_path / "lob_same_bar.yaml"
    cfg_path.write_text(yaml.safe_dump(config))
    return cfg_path


def test_unsafe_execution_requires_opt_in_and_manifest_label(tmp_path: Path):
    cfg_path = _make_lob_config(tmp_path, allow_unsafe=None)
    with pytest.raises(ValueError, match="allow_unsafe_execution"):
        run_from_config(str(cfg_path))

    allowed_cfg = _make_lob_config(tmp_path, allow_unsafe=True)
    result = run_from_config(str(allowed_cfg))
    manifest_path = Path(result["artifacts_dir"]) / "manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["unsafe_execution"] is True
    assert "same_bar_fills_enabled" in (payload.get("unsafe_reasons") or [])
    alignment = payload.get("execution_alignment") or {}
    assert alignment.get("lob_tplus1") is False

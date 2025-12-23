import pytest

from microalpha.events import FillEvent, MarketEvent
from microalpha.integrity import evaluate_portfolio_integrity
from microalpha.portfolio import Portfolio


class _DummyDataHandler:
    def get_latest_price(self, symbol, timestamp):
        return 100.0

    def get_future_timestamps(self, start_timestamp, n):
        return []


def test_equity_updates_after_same_day_fill():
    portfolio = Portfolio(data_handler=_DummyDataHandler(), initial_cash=1000.0)
    portfolio.on_market(MarketEvent(1, "SPY", 100.0, 0.0))
    portfolio.on_market(MarketEvent(2, "SPY", 100.0, 0.0))
    portfolio.on_fill(
        FillEvent(
            timestamp=2,
            symbol="SPY",
            qty=10,
            price=100.0,
            commission=1.0,
            slippage=0.0,
        )
    )
    portfolio.refresh_equity_after_fills(2)

    assert portfolio.equity_curve[-1]["equity"] == pytest.approx(999.0)

    integrity = evaluate_portfolio_integrity(
        portfolio, equity_records=portfolio.equity_curve, slippage_total=0.0
    )
    assert integrity.ok


def test_integrity_flags_constant_equity_with_trades():
    portfolio = Portfolio(data_handler=_DummyDataHandler(), initial_cash=1000.0)
    portfolio.on_market(MarketEvent(1, "SPY", 100.0, 0.0))
    portfolio.on_fill(
        FillEvent(
            timestamp=1,
            symbol="SPY",
            qty=10,
            price=100.0,
            commission=1.0,
            slippage=0.0,
        )
    )

    integrity = evaluate_portfolio_integrity(
        portfolio, equity_records=portfolio.equity_curve, slippage_total=0.0
    )
    assert not integrity.ok
    assert any("equity curve is constant" in reason for reason in integrity.reasons)

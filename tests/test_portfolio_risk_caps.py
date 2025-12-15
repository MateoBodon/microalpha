from __future__ import annotations

from microalpha.events import SignalEvent
from microalpha.portfolio import Portfolio, PortfolioPosition


class _StubDataHandler:
    def __init__(self, price: float = 100.0) -> None:
        self.price = price

    def get_latest_price(self, symbol: str, timestamp: int):  # pragma: no cover - trivial
        return self.price


def test_portfolio_heat_cap_blocks_signal() -> None:
    dh = _StubDataHandler(price=100.0)
    portfolio = Portfolio(dh, initial_cash=100_000, max_portfolio_heat=1.0)
    portfolio.last_equity = 100_000
    portfolio.current_time = 0
    portfolio.positions["AAA"] = PortfolioPosition(qty=500)  # $50k current heat

    signal = SignalEvent(timestamp=0, symbol="BBB", side="LONG", meta={"weight": 1.0})
    qty = portfolio._sized_quantity(signal)

    assert qty == 0


def test_turnover_cap_blocks_orders() -> None:
    dh = _StubDataHandler(price=100.0)
    portfolio = Portfolio(dh, initial_cash=100_000, turnover_cap=1_000.0)
    portfolio.last_equity = 100_000
    portfolio.current_time = 0
    portfolio.total_turnover = 950.0

    signal = SignalEvent(timestamp=0, symbol="CCC", side="LONG")
    orders = portfolio.on_signal(signal)

    assert orders == []

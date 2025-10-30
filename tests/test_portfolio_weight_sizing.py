from __future__ import annotations

from microalpha.events import MarketEvent, SignalEvent
from microalpha.portfolio import Portfolio


class _StubData:
    def __init__(self, price: float = 50.0):
        self.price = price

    def get_latest_price(self, symbol: str, timestamp: int) -> float:
        return self.price

    def get_future_timestamps(self, start_timestamp: int, n: int):
        return [start_timestamp + i for i in range(1, n + 1)]


def test_portfolio_uses_signal_weight_for_sizing():
    portfolio = Portfolio(data_handler=_StubData(), initial_cash=1000.0)
    portfolio.on_market(MarketEvent(1, "AAA", 50.0, 1_000))

    long_signal = SignalEvent(
        1, "AAA", "LONG", meta={"weight": 0.2, "reason": "test"}
    )
    orders = list(portfolio.on_signal(long_signal))
    assert orders and orders[0].qty == 4  # 0.2 * 1000 / 50
    assert orders[0].side == "BUY"

    short_signal = SignalEvent(
        2, "AAA", "SHORT", meta={"weight": -0.1, "reason": "test"}
    )
    portfolio.on_market(MarketEvent(2, "AAA", 50.0, 1_000))
    short_orders = list(portfolio.on_signal(short_signal))
    assert short_orders and short_orders[0].qty == 2
    assert short_orders[0].side == "SELL"

from microalpha.events import FillEvent, SignalEvent
from microalpha.portfolio import Portfolio


class _StubDataHandler:
    def get_latest_price(self, symbol, timestamp):
        return 100.0


def test_turnover_cap_blocks_second_trade():
    portfolio = Portfolio(
        data_handler=_StubDataHandler(),
        turnover_cap=10_000.0,
        default_order_qty=100,
    )

    first_orders = portfolio.on_signal(SignalEvent(0, "SPY", "LONG"))
    assert len(first_orders) == 1

    fill = FillEvent(0, "SPY", qty=first_orders[0].qty, price=100.0, commission=0.0, slippage=0.0)
    portfolio.on_fill(fill)

    second_orders = portfolio.on_signal(SignalEvent(1, "SPY", "LONG"))
    assert second_orders == []

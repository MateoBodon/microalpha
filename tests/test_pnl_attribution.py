from __future__ import annotations

from microalpha.events import FillEvent
from microalpha.portfolio import Portfolio


class _DH:
    def get_latest_price(self, symbol, timestamp):
        return 100.0

    def get_future_timestamps(self, start_timestamp, n):
        return [start_timestamp + 1]


def test_realized_pnl_average_cost():
    p = Portfolio(data_handler=_DH(), initial_cash=0.0)
    # Buy 10 @ 100
    p.on_fill(
        FillEvent(
            timestamp=1, symbol="SPY", qty=10, price=100.0, commission=0.0, slippage=0.0
        )
    )
    # Sell 5 @ 110 => realized +50
    p.on_fill(
        FillEvent(
            timestamp=2, symbol="SPY", qty=-5, price=110.0, commission=0.0, slippage=0.0
        )
    )
    # Sell remaining 5 @ 90 => realized -50; cum 0
    p.on_fill(
        FillEvent(
            timestamp=3, symbol="SPY", qty=-5, price=90.0, commission=0.0, slippage=0.0
        )
    )

    assert abs(p.cum_realized_pnl - 0.0) < 1e-9
    assert p.trades, "expected trade records"
    assert any(abs(tr["realized_pnl"]) > 0 for tr in p.trades)

from __future__ import annotations

from microalpha.events import MarketEvent, SignalEvent
from microalpha.portfolio import Portfolio


class _DH:
    def __init__(self, price=100.0):
        self.price = price

    def get_latest_price(self, symbol, timestamp):
        return self.price

    def get_future_timestamps(self, start_timestamp, n):
        return [start_timestamp + 1]


def _init_portfolio(**kwargs) -> Portfolio:
    p = Portfolio(data_handler=_DH(), initial_cash=100000.0, **kwargs)
    p.on_market(MarketEvent(timestamp=1, symbol="SPY", price=100.0, volume=1.0))
    return p


def test_vol_target_scales_down_size_when_vol_high():
    p = _init_portfolio(vol_target_annualized=0.05, vol_lookback=5)
    # Make equity volatile
    for i, eq in enumerate([100000, 90000, 110000, 95000, 105000], start=2):
        p.equity_curve.append({"timestamp": i, "equity": eq, "exposure": 0.0})
    s = SignalEvent(timestamp=6, symbol="SPY", side="LONG")
    orders = list(p.on_signal(s))
    assert orders == [] or orders[0].qty <= p.default_order_qty


def test_portfolio_heat_blocks_trade_exceeding_cap():
    p = _init_portfolio(max_portfolio_heat=0.01)
    p.positions["SPY"] = type("_P", (), {"qty": 1000})()
    s = SignalEvent(timestamp=2, symbol="SPY", side="LONG", meta={"qty": 1000})
    orders = list(p.on_signal(s))
    assert orders == []


def test_sector_cap_blocks_when_too_many_positions():
    sectors = {"A": "TECH", "B": "TECH", "C": "FIN"}
    p = _init_portfolio(sectors=sectors, max_positions_per_sector=1)
    p.positions["A"] = type("_P", (), {"qty": 10})()
    s = SignalEvent(timestamp=2, symbol="B", side="LONG", meta={"qty": 10})
    orders = list(p.on_signal(s))
    assert orders == []


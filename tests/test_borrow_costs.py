from __future__ import annotations

import math

import pandas as pd

from microalpha.events import FillEvent, MarketEvent
from microalpha.market_metadata import SymbolMeta
from microalpha.portfolio import Portfolio


class _StubDataHandler:
    def __init__(self, price: float = 10.0):
        self.price = price

    def get_latest_price(self, symbol: str, timestamp: int) -> float:
        return self.price

    def get_future_timestamps(self, start_timestamp: int, n: int):
        return [start_timestamp + i + 1 for i in range(n)]


def test_borrow_cost_accrues_daily_for_shorts():
    symbol = "XYZ"
    meta = {symbol: SymbolMeta(borrow_fee_annual_bps=3_650.0, adv=1_000_000.0)}
    portfolio = Portfolio(data_handler=_StubDataHandler(10.0), symbol_meta=meta)

    day0 = pd.Timestamp("2020-01-02").value
    day1 = pd.Timestamp("2020-01-03").value
    day2 = pd.Timestamp("2020-01-06").value  # includes weekend gap

    portfolio.on_market(MarketEvent(day0, symbol, 10.0, 0.0))
    portfolio.on_fill(
        FillEvent(day0, symbol, qty=-100, price=10.0, commission=0.0, slippage=0.0)
    )
    portfolio.on_market(MarketEvent(day1, symbol, 10.0, 0.0))

    expected_daily_cost = 100 * 10.0 * (3_650.0 / 10_000.0) / 252.0
    assert math.isclose(portfolio.borrow_cost_total, expected_daily_cost, rel_tol=1e-9)
    assert math.isclose(portfolio.cum_realized_pnl, -expected_daily_cost, rel_tol=1e-9)

    portfolio.on_fill(
        FillEvent(day1 + 1, symbol, qty=100, price=10.0, commission=0.0, slippage=0.0)
    )
    portfolio.on_market(MarketEvent(day2, symbol, 10.0, 0.0))

    assert math.isclose(portfolio.borrow_cost_total, expected_daily_cost, rel_tol=1e-9)
    assert math.isclose(portfolio.cum_realized_pnl, -expected_daily_cost, rel_tol=1e-9)

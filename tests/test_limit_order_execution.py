from __future__ import annotations

from microalpha.events import OrderEvent
from microalpha.execution import Executor
from microalpha.market_metadata import SymbolMeta


class _StubDataHandler:
    def __init__(self, price: float = 100.0):
        self.price = price

    def get_future_timestamps(self, start_timestamp: int, n: int):
        return [start_timestamp + i for i in range(1, n + 1)]

    def get_latest_price(self, symbol: str, timestamp: int) -> float:
        return self.price

    def get_recent_prices(self, symbol: str, end_timestamp: int, lookback: int):
        return [self.price] * lookback

    def get_volume_at(self, symbol: str, timestamp: int):
        return None


def _executor(limit_mode: str, **kwargs) -> Executor:
    meta = {"XYZ": SymbolMeta(adv=2_000_000.0, spread_bps=12.0, volatility_bps=40.0)}
    return Executor(
        data_handler=_StubDataHandler(100.0),
        limit_mode=limit_mode,
        queue_coefficient=0.01,
        queue_randomize=False,
        symbol_meta=meta,
        **kwargs,
    )


def test_limit_ioc_fill_fraction_deterministic():
    executor = _executor("IOC")
    order = OrderEvent(
        timestamp=1,
        symbol="XYZ",
        qty=20_000,
        side="BUY",
        order_type="LIMIT",
        price=101.0,
    )
    fill = executor.execute(order, current_ts=1)
    assert fill is not None
    assert fill.qty == 6_000  # floor(20_000 * 0.3)
    assert fill.price <= order.price

    executor_2 = _executor("IOC")
    fill_2 = executor_2.execute(order, current_ts=1)
    assert fill_2 is not None
    assert fill_2.qty == fill.qty


def test_post_only_mode_is_more_conservative():
    ioc_executor = _executor("IOC")
    po_executor = _executor("PO", queue_passive_multiplier=0.4)

    order = OrderEvent(
        timestamp=1,
        symbol="XYZ",
        qty=20_000,
        side="BUY",
        order_type="LIMIT",
        price=101.0,
    )
    fill_ioc = ioc_executor.execute(order, current_ts=1)
    fill_po = po_executor.execute(order, current_ts=1)

    assert fill_ioc and fill_po
    assert fill_po.qty < fill_ioc.qty


def test_limit_order_rejects_unreachable_price():
    executor = _executor("IOC")
    order = OrderEvent(
        timestamp=1,
        symbol="XYZ",
        qty=10_000,
        side="BUY",
        order_type="LIMIT",
        price=99.0,
    )
    fill = executor.execute(order, current_ts=1)
    assert fill is None

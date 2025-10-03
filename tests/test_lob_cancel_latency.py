import numpy as np

from microalpha.events import OrderEvent
from microalpha.lob import LatencyModel, LimitOrderBook


def _base_latency_model(**kwargs) -> LatencyModel:
    return LatencyModel(
        ack_fixed=kwargs.get("ack_fixed", 0.1),
        ack_jitter=0.0,
        fill_fixed=kwargs.get("fill_fixed", 0.2),
        fill_jitter=0.0,
        rng=np.random.default_rng(123),
    )


def test_cancel_removes_order_before_fills():
    book = LimitOrderBook(latency_model=_base_latency_model())

    limit = OrderEvent(
        timestamp=1,
        symbol="SPY",
        qty=5,
        side="BUY",
        order_type="LIMIT",
        price=100.0,
        order_id="C1",
    )
    book.submit(limit)

    cancel = OrderEvent(
        timestamp=2,
        symbol="SPY",
        qty=0,
        side="BUY",
        order_type="CANCEL",
        order_id="C1",
    )
    assert not book.submit(cancel)
    assert "C1" not in book._lookup

    market = OrderEvent(timestamp=3, symbol="SPY", qty=5, side="SELL")
    assert not book.submit(market)


def test_latency_enforces_monotonic_fill_times():
    latency = _base_latency_model(ack_fixed=0.5, fill_fixed=1.5)
    book = LimitOrderBook(latency_model=latency)
    book.seed_book(mid_price=100.0, tick=1.0, levels=1, size=10)

    market = OrderEvent(timestamp=10, symbol="SPY", qty=4, side="SELL")
    fills = book.submit(market)
    assert fills
    fill = fills[0]

    assert fill.latency_ack >= latency.ack_fixed
    assert fill.latency_fill >= latency.fill_fixed

    effective_fill_time = fill.timestamp + fill.latency_fill
    assert effective_fill_time >= market.timestamp + latency.fill_fixed

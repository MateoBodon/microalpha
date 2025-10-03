import numpy as np

from microalpha.events import OrderEvent
from microalpha.lob import LatencyModel, LimitOrderBook


def _make_book():
    latency = LatencyModel(
        ack_fixed=0.0,
        ack_jitter=0.0,
        fill_fixed=0.0,
        fill_jitter=0.0,
        rng=np.random.default_rng(0),
    )
    return LimitOrderBook(latency_model=latency)


def test_fifo_queue_respected_across_partial_fills():
    book = _make_book()

    order_a = OrderEvent(
        timestamp=1,
        symbol="SPY",
        qty=10,
        side="BUY",
        order_type="LIMIT",
        price=100.0,
        order_id="A",
    )
    order_b = OrderEvent(
        timestamp=2,
        symbol="SPY",
        qty=10,
        side="BUY",
        order_type="LIMIT",
        price=100.0,
        order_id="B",
    )

    assert not book.submit(order_a)
    assert not book.submit(order_b)

    partial_sell = OrderEvent(timestamp=3, symbol="SPY", qty=8, side="SELL")
    fills_first = book.submit(partial_sell)
    assert len(fills_first) == 1
    assert fills_first[0].qty == -8

    bids_side, price_a = book._lookup["A"]
    remaining_a = next(o.qty for o in bids_side.levels[price_a] if o.order_id == "A")
    remaining_b = next(o.qty for o in bids_side.levels[price_a] if o.order_id == "B")
    assert remaining_a == 2
    assert remaining_b == 10

    second_sell = OrderEvent(timestamp=4, symbol="SPY", qty=12, side="SELL")
    fills_second = book.submit(second_sell)
    assert len(fills_second) == 1
    assert fills_second[0].qty == -12

    assert "A" not in book._lookup
    assert "B" not in book._lookup

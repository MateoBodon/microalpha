import math

from microalpha.events import OrderEvent
from microalpha.lob import LatencyModel, LimitOrderBook


def test_fifo_matching_and_price_levels():
    book = LimitOrderBook(latency_model=LatencyModel(seed=1))
    book.seed_book(mid_price=100.0, tick=1.0, levels=2, size=50)

    # Add additional liquidity at best bid
    order1 = OrderEvent(
        timestamp=1, symbol="SYN", qty=100, side="BUY", order_type="LIMIT", price=99.0
    )
    order2 = OrderEvent(
        timestamp=2, symbol="SYN", qty=100, side="BUY", order_type="LIMIT", price=99.0
    )
    book.submit(order1)
    book.submit(order2)

    # Market sell should match order1 before order2
    market_sell = OrderEvent(
        timestamp=3, symbol="SYN", qty=80, side="SELL", order_type="MARKET"
    )
    fills = book.submit(market_sell)
    assert fills, "Expected fills"
    assert math.isclose(fills[0].price, 99.0)
    assert fills[0].qty == -80

    level = book.bids.levels.get(99.0)
    assert level is not None
    head = level[0]
    assert head.qty == 70  # initial seed liquidity consumed before order1
    assert head.timestamp == order1.timestamp

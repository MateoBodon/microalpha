from __future__ import annotations

from microalpha.events import OrderEvent
from microalpha.execution import LOBExecution
from microalpha.lob import LatencyModel, LimitOrderBook


class _StubData:
    def __init__(self, timestamps):
        self.timestamps = sorted(timestamps)

    def get_future_timestamps(self, start_timestamp, n):
        fut = [ts for ts in self.timestamps if ts > start_timestamp]
        return fut[:n]

    def get_latest_price(self, symbol, timestamp):
        return 100.0


def test_lob_tplus1_shifts_fill_timestamp():
    data = _StubData([1, 2, 3])
    book = LimitOrderBook(latency_model=LatencyModel())
    book.seed_book(mid_price=100.0, tick=1.0, levels=1, size=10)
    exec_t1 = LOBExecution(data_handler=data, book=book, lob_tplus1=True)

    order = OrderEvent(timestamp=1, symbol="SPY", qty=5, side="BUY")
    fill = exec_t1.execute(order, 1)
    assert fill is not None
    assert fill.timestamp >= 2


def test_lob_same_tick_does_not_shift_timestamp():
    data = _StubData([1, 2, 3])
    book = LimitOrderBook(latency_model=LatencyModel())
    book.seed_book(mid_price=100.0, tick=1.0, levels=1, size=10)
    exec_t0 = LOBExecution(data_handler=data, book=book, lob_tplus1=False)

    order = OrderEvent(timestamp=1, symbol="SPY", qty=5, side="BUY")
    fill = exec_t0.execute(order, 1)
    assert fill is not None
    assert fill.timestamp == 1

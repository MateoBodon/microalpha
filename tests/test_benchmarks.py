import numpy as np

from microalpha.engine import Engine
from microalpha.events import MarketEvent
from microalpha.execution import Executor
from microalpha.portfolio import Portfolio


class SyntheticData:
    def __init__(self, events):
        self.events = events

    def stream(self):
        return iter(self.events)

    def get_future_timestamps(self, start_timestamp, n):
        return [start_timestamp + i + 1 for i in range(n)]

    def get_latest_price(self, symbol, timestamp):
        return 100.0


class NullStrategy:
    def on_market(self, event):
        return []


class NullExecutor(Executor):
    def _slippage(self, qty: int) -> float:
        return 0.0

    def _commission(self, qty: int) -> float:
        return 0.0


def test_engine_benchmark_smoke():
    events = [MarketEvent(i, "SYN", 100.0, 1.0) for i in range(1000)]
    data = SyntheticData(events)
    strategy = NullStrategy()
    executor = NullExecutor(data)
    broker = executor
    portfolio = Portfolio(data_handler=data)

    engine = Engine(data, strategy, portfolio, broker, rng=np.random.default_rng(7))
    engine.run()

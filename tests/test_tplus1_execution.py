from microalpha.broker import SimulatedBroker
from microalpha.engine import Engine
import numpy as np

from microalpha.broker import SimulatedBroker
from microalpha.engine import Engine
from microalpha.events import MarketEvent, SignalEvent
from microalpha.execution import Executor
from microalpha.portfolio import Portfolio


class StubData:
    def __init__(self, events):
        self.events = sorted(events, key=lambda e: e.timestamp)
        self._by_time = {event.timestamp: event for event in self.events}

    def stream(self):
        for event in self.events:
            yield event

    def get_future_timestamps(self, start_timestamp, n):
        futures = [ts for ts in self._by_time if ts > start_timestamp]
        return sorted(futures)[:n]

    def get_latest_price(self, symbol, timestamp):
        event = self._by_time.get(timestamp)
        return None if event is None else event.price


class SingleTradeStrategy:
    def __init__(self):
        self.triggered = False

    def on_market(self, event):
        if not self.triggered:
            self.triggered = True
            return [SignalEvent(event.timestamp, event.symbol, "LONG")]
        return []


class LoggingPortfolio(Portfolio):
    def __init__(self, data_handler, initial_cash):
        super().__init__(data_handler, initial_cash)
        self.fill_timestamps = []

    def on_fill(self, fill):
        self.fill_timestamps.append(fill.timestamp)
        super().on_fill(fill)


def test_orders_fill_no_earlier_than_next_tick():
    events = [
        MarketEvent(1, "SPY", 100.0, 1.0),
        MarketEvent(2, "SPY", 101.0, 1.0),
    ]
    data = StubData(events)
    strategy = SingleTradeStrategy()
    portfolio = LoggingPortfolio(data, 100000.0)
    executor = Executor(data)
    broker = SimulatedBroker(executor)

    engine = Engine(data, strategy, portfolio, broker, rng=np.random.default_rng(11))
    engine.run()

    assert portfolio.fill_timestamps
    assert all(ts >= 2 for ts in portfolio.fill_timestamps)

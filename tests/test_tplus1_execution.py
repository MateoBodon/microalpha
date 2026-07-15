import numpy as np

from microalpha.broker import SimulatedBroker
from microalpha.engine import Engine
from microalpha.events import MarketEvent, OrderEvent, SignalEvent
from microalpha.execution import (
    TWAP,
    VWAP,
    Executor,
    ImplementationShortfall,
    LOBExecution,
)
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


class SymbolAwareStubData(StubData):
    def get_future_timestamps(self, start_timestamp, n, symbol=None):
        futures = [
            event.timestamp
            for event in self.events
            if event.timestamp > start_timestamp
            and (symbol is None or event.symbol == symbol)
        ]
        return sorted(futures)[:n]


class ClockGuardedData(StubData):
    """Fails if an executor reads a price before its event is streamed."""

    def __init__(self, events):
        super().__init__(events)
        self.current_timestamp = None
        self.price_reads = []

    def stream(self):
        for event in self.events:
            self.current_timestamp = event.timestamp
            yield event

    def get_latest_price(self, symbol, timestamp):
        self.price_reads.append((self.current_timestamp, timestamp))
        if self.current_timestamp is None or timestamp > self.current_timestamp:
            raise AssertionError("future market price was read before its event")
        return super().get_latest_price(symbol, timestamp)


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


def test_future_fill_is_materialized_only_when_engine_reaches_timestamp():
    events = [
        MarketEvent(1, "SPY", 100.0, 1.0),
        MarketEvent(2, "SPY", 101.0, 1.0),
        MarketEvent(3, "SPY", 102.0, 1.0),
    ]
    data = ClockGuardedData(events)
    portfolio = LoggingPortfolio(data, 100000.0)

    class StateObservingStrategy(SingleTradeStrategy):
        def __init__(self):
            super().__init__()
            self.observed = []

        def on_market(self, event):
            position = portfolio.positions.get("SPY")
            self.observed.append(
                {
                    "timestamp": event.timestamp,
                    "qty": 0 if position is None else position.qty,
                    "cash": portfolio.cash,
                }
            )
            return super().on_market(event)

    strategy = StateObservingStrategy()
    engine = Engine(
        data,
        strategy,
        portfolio,
        SimulatedBroker(Executor(data)),
        rng=np.random.default_rng(11),
    )
    engine.run()

    assert strategy.observed[0] == {"timestamp": 1, "qty": 0, "cash": 100000.0}
    assert strategy.observed[1]["timestamp"] == 2
    assert strategy.observed[1]["qty"] > 0
    assert strategy.observed[1]["cash"] < 100000.0
    assert portfolio.fill_timestamps == [2]
    assert all(read_ts <= engine_ts for engine_ts, read_ts in data.price_reads)


def test_all_safe_planners_fail_closed_without_a_future_tick():
    data = StubData([MarketEvent(1, "SPY", 100.0, 1.0)])
    order = OrderEvent(1, "SPY", 10, "BUY")
    planners = [
        Executor(data),
        TWAP(data, slices=2),
        VWAP(data, slices=2),
        ImplementationShortfall(data, slices=2),
    ]
    for planner in planners:
        assert planner.plan(order, 1) == []
        assert planner.last_reject_reason == "no_future_market_event"
        assert planner.execute(order, 1) is None
        assert planner.last_reject_reason == "no_future_market_event"

    class BookThatMustNotBeTouched:
        def submit(self, _order):
            raise AssertionError("terminal t+1 order reached the book")

    lob = LOBExecution(data, book=BookThatMustNotBeTouched(), lob_tplus1=True)
    assert lob.plan(order, 1) == []
    assert lob.last_reject_reason == "no_future_market_event"


def test_async_multiasset_order_uses_next_event_for_same_symbol():
    events = [
        MarketEvent(1, "AAA", 100.0, 1.0),
        MarketEvent(2, "BBB", 50.0, 1.0),
        MarketEvent(3, "AAA", 101.0, 1.0),
    ]
    data = SymbolAwareStubData(events)
    strategy = SingleTradeStrategy()
    portfolio = LoggingPortfolio(data, 100000.0)
    engine = Engine(
        data,
        strategy,
        portfolio,
        SimulatedBroker(Executor(data)),
        rng=np.random.default_rng(11),
    )
    engine.run()
    assert portfolio.fill_timestamps == [3]

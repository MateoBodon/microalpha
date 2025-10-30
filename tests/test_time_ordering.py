import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from microalpha.engine import Engine
from microalpha.events import LookaheadError, MarketEvent


class ListData:
    def __init__(self, events):
        self.events = events

    def stream(self):
        for event in self.events:
            yield event


class NullStrategy:
    def on_market(self, event):
        return []


class NullPortfolio:
    def on_market(self, event):
        return None

    def on_signal(self, signal):
        return []

    def on_fill(self, fill):
        return None


class NullBroker:
    def execute(self, order, market_timestamp):
        return None


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st.lists(st.integers(min_value=0, max_value=10), min_size=10, unique=True))
def test_market_events_must_be_sorted(ts):
    events = [MarketEvent(t, "SPY", 100.0, 1.0) for t in sorted(ts, reverse=True)]
    engine = Engine(
        ListData(events),
        NullStrategy(),
        NullPortfolio(),
        NullBroker(),
        rng=np.random.default_rng(5),
    )

    with pytest.raises(LookaheadError):
        engine.run()

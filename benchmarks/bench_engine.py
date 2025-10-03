"""Microalpha engine benchmark harness."""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from microalpha.engine import Engine
from microalpha.events import MarketEvent
from microalpha.execution import Executor
from microalpha.portfolio import Portfolio


@dataclass
class SyntheticData:
    events: list[MarketEvent]

    def stream(self):
        for event in self.events:
            yield event

    def get_future_timestamps(self, start_timestamp: int, n: int):
        return [start_timestamp + i + 1 for i in range(n)]

    def get_latest_price(self, symbol: str, timestamp: int):
        return 100.0


@dataclass
class NoOpStrategy:
    symbol: str

    def on_market(self, event):
        return []


class NullExecutor(Executor):
    def _slippage(self, qty: int) -> float:
        return 0.0

    def _commission(self, qty: int) -> float:
        return 0.0


def run_bench(num_events: int = 1_000_000) -> dict[str, float]:
    timestamps = np.arange(num_events, dtype=np.int64)
    events = [MarketEvent(int(ts), "SYN", 100.0, 1.0) for ts in timestamps]

    data = SyntheticData(events)
    strategy = NoOpStrategy(symbol="SYN")
    executor = NullExecutor(data_handler=data)
    broker = executor  # executor conforms to broker interface via executor
    portfolio = Portfolio(data_handler=data, initial_cash=1_000_000.0)

    engine = Engine(data, strategy, portfolio, broker, seed=123)

    t0 = time.perf_counter()
    engine.run()
    dt = time.perf_counter() - t0

    evps = int(num_events / dt) if dt else 0
    results = {"events": num_events, "sec": round(dt, 3), "evps": evps}
    print(results)
    return results


if __name__ == "__main__":
    run_bench()

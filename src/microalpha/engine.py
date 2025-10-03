"""Event-driven backtest engine enforcing strict time ordering."""

from __future__ import annotations

from typing import Iterable

import os
import cProfile
import random
from pathlib import Path

import numpy as np

from .events import FillEvent, LookaheadError, MarketEvent, OrderEvent, SignalEvent


class Engine:
    def __init__(self, data, strategy, portfolio, broker, seed: int = 42):
        self.clock: int | None = None
        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio
        self.broker = broker
        np.random.seed(seed)
        random.seed(seed)

    def run(self) -> None:
        profiler = None
        if os.getenv("MICROALPHA_PROFILE"):
            profiler = cProfile.Profile()
            profiler.enable()

        for market_event in self.data.stream():
            self._on_market(market_event)

        if profiler:
            profiler.disable()
            output_dir = Path("artifacts")
            output_dir.mkdir(parents=True, exist_ok=True)
            profiler.dump_stats(str(output_dir / "profile.pstats"))

    def _on_market(self, market_event: MarketEvent) -> None:
        if self.clock is not None and market_event.timestamp < self.clock:
            raise LookaheadError("out-of-order market event")

        self.clock = market_event.timestamp
        self.portfolio.on_market(market_event)

        signals: Iterable[SignalEvent] = self.strategy.on_market(market_event)
        for signal in signals:
            if signal.timestamp < self.clock:
                raise LookaheadError("signal time < current clock")

            orders: Iterable[OrderEvent] = self.portfolio.on_signal(signal)
            for order in orders:
                fill: FillEvent | None = self.broker.execute(order, market_event.timestamp)
                if fill is None:
                    continue
                if fill.timestamp < market_event.timestamp:
                    raise LookaheadError("fill before current market event")
                self.portfolio.on_fill(fill)

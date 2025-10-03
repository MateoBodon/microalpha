"""Event-driven backtest engine enforcing strict time ordering."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import random

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
        for market_event in self.data.stream():
            self._on_market(market_event)

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

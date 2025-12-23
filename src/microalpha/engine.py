"""Event-driven backtest engine enforcing strict time ordering."""

from __future__ import annotations

import cProfile
import os
from pathlib import Path
from typing import Iterable

import numpy as np

from .events import FillEvent, LookaheadError, MarketEvent, OrderEvent, SignalEvent


class Engine:
    def __init__(
        self, data, strategy, portfolio, broker, rng: np.random.Generator | None = None
    ):
        self.clock: int | None = None
        self.data = data
        self.strategy = strategy
        self.portfolio = portfolio
        self.broker = broker
        self.rng = rng or np.random.default_rng()
        self._pending_equity_refresh_ts: int | None = None

    def run(self) -> None:
        profiler = None
        if os.getenv("MICROALPHA_PROFILE"):
            profiler = cProfile.Profile()
            profiler.enable()

        for market_event in self.data.stream():
            self._on_market(market_event)

        if self._pending_equity_refresh_ts is not None:
            self.portfolio.refresh_equity_after_fills(self._pending_equity_refresh_ts)
            self._pending_equity_refresh_ts = None

        if profiler:
            profiler.disable()
            # Prefer explicit artifacts dir from environment, fallback to top-level 'artifacts/'
            outdir_env = os.getenv("MICROALPHA_ARTIFACTS_DIR", "artifacts")
            output_dir = Path(outdir_env)
            output_dir.mkdir(parents=True, exist_ok=True)
            profiler.dump_stats(str(output_dir / "profile.pstats"))

    def _on_market(self, market_event: MarketEvent) -> None:
        if self.clock is not None and market_event.timestamp < self.clock:
            raise LookaheadError("out-of-order market event")

        if (
            self._pending_equity_refresh_ts is not None
            and market_event.timestamp != self._pending_equity_refresh_ts
        ):
            self.portfolio.refresh_equity_after_fills(self._pending_equity_refresh_ts)
            self._pending_equity_refresh_ts = None

        self.clock = market_event.timestamp
        self.portfolio.on_market(market_event)

        signals: Iterable[SignalEvent] = self.strategy.on_market(market_event)
        same_day_fill = False
        for signal in signals:
            if signal.timestamp < self.clock:
                raise LookaheadError("signal time < current clock")

            orders: Iterable[OrderEvent] = self.portfolio.on_signal(signal)
            for order in orders:
                fill: FillEvent | None = self.broker.execute(
                    order, market_event.timestamp
                )
                if fill is None:
                    continue
                if fill.timestamp < market_event.timestamp:
                    raise LookaheadError("fill before current market event")
                if fill.timestamp == market_event.timestamp:
                    same_day_fill = True
                self.portfolio.on_fill(fill)
        if same_day_fill:
            self._pending_equity_refresh_ts = market_event.timestamp

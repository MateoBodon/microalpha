"""Event-driven backtest engine enforcing strict time ordering."""

from __future__ import annotations

import cProfile
import os
from pathlib import Path
from typing import Iterable

import numpy as np

from .events import FillEvent, LookaheadError, MarketEvent, OrderEvent, SignalEvent
from .execution import ExecutionPlan


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
        self._pending_executions: list[ExecutionPlan] = []

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
        self._materialize_due(market_event)

        signals_iter: Iterable[SignalEvent] = self.strategy.on_market(market_event)
        signals = list(signals_iter)
        order_flow = getattr(self.portfolio, "order_flow", None)
        if order_flow and signals:
            try:
                order_flow.begin_rebalance(signals, market_event.timestamp)
            except (
                Exception
            ) as exc:  # pragma: no cover - diagnostics should not fail run
                order_flow.record_error(
                    f"begin_rebalance_error: {type(exc).__name__}: {exc}"
                )
        same_day_fill = False
        for signal in signals:
            if signal.timestamp < self.clock:
                raise LookaheadError("signal time < current clock")
            if signal.timestamp > self.clock:
                raise LookaheadError("signal time > current clock")

            orders: Iterable[OrderEvent] = self.portfolio.on_signal(signal)
            for order in orders:
                plans = self._plan_execution(order, market_event.timestamp)
                if not plans:
                    if order_flow:
                        reason = getattr(
                            getattr(self.broker, "executor", None),
                            "last_reject_reason",
                            None,
                        )
                        order_flow.record_broker_reject(order, reason)
                    continue
                if order_flow:
                    order_flow.record_broker_accept(order)
                for plan in plans:
                    if plan.timestamp < market_event.timestamp:
                        raise LookaheadError("planned fill before current market event")
                    if plan.timestamp == market_event.timestamp:
                        fill = self._materialize(plan)
                        if fill is not None:
                            if order_flow:
                                order_flow.record_fill(fill, order=plan.order)
                            self.portfolio.on_fill(fill)
                            same_day_fill = True
                    else:
                        self._pending_executions.append(plan)
        if same_day_fill:
            self._pending_equity_refresh_ts = market_event.timestamp
        if order_flow and signals:
            try:
                order_flow.end_rebalance()
            except (
                Exception
            ) as exc:  # pragma: no cover - diagnostics should not fail run
                order_flow.record_error(
                    f"end_rebalance_error: {type(exc).__name__}: {exc}"
                )

    def _plan_execution(
        self, order: OrderEvent, market_timestamp: int
    ) -> list[ExecutionPlan]:
        planner = getattr(self.broker, "plan", None)
        if callable(planner):
            return list(planner(order, market_timestamp))

        # Compatibility for simple third-party test brokers. Built-in brokers
        # use the safe planning API above and never read a future market price
        # before the engine reaches it.
        fill = self.broker.execute(order, market_timestamp)
        if fill is None:
            return []
        return [ExecutionPlan(fill.timestamp, order, abs(fill.qty), fill)]

    def _materialize(self, plan: ExecutionPlan) -> FillEvent | None:
        materializer = getattr(self.broker, "materialize", None)
        if callable(materializer):
            return materializer(plan)
        return plan.prepared_fill

    def _materialize_due(self, market_event: MarketEvent) -> None:
        overdue = [
            plan
            for plan in self._pending_executions
            if plan.timestamp < market_event.timestamp
            and plan.order.symbol == market_event.symbol
        ]
        if overdue:
            raise LookaheadError("scheduled execution timestamp was not observed")

        due = [
            plan
            for plan in self._pending_executions
            if plan.timestamp == market_event.timestamp
            and plan.order.symbol == market_event.symbol
        ]
        if not due:
            return

        due_ids = {id(plan) for plan in due}
        self._pending_executions = [
            plan for plan in self._pending_executions if id(plan) not in due_ids
        ]
        order_flow = getattr(self.portfolio, "order_flow", None)
        applied = False
        for plan in due:
            fill = self._materialize(plan)
            if fill is None:
                continue
            if fill.timestamp != market_event.timestamp:
                raise LookaheadError(
                    "materialized fill timestamp differs from schedule"
                )
            if order_flow:
                order_flow.record_fill(fill, order=plan.order)
            self.portfolio.on_fill(fill)
            applied = True
        if applied:
            self.portfolio.refresh_equity_after_fills(market_event.timestamp)

"""Broker wrapper delegating to execution models."""

from __future__ import annotations

from typing import Optional

from .events import FillEvent, OrderEvent
from .execution import ExecutionPlan, Executor


class SimulatedBroker:
    def __init__(self, executor: Executor):
        self.executor = executor

    def execute(self, order: OrderEvent, market_timestamp: int) -> Optional[FillEvent]:
        return self.executor.execute(order, market_timestamp)

    def plan(self, order: OrderEvent, market_timestamp: int) -> list[ExecutionPlan]:
        return self.executor.plan(order, market_timestamp)

    def materialize(self, plan: ExecutionPlan) -> Optional[FillEvent]:
        return self.executor.materialize(plan)

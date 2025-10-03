"""Broker wrapper delegating to execution models."""

from __future__ import annotations

from typing import Optional

from .events import FillEvent, OrderEvent
from .execution import Executor


class SimulatedBroker:
    def __init__(self, executor: Executor):
        self.executor = executor

    def execute(self, order: OrderEvent, market_timestamp: int) -> Optional[FillEvent]:
        return self.executor.execute(order, market_timestamp)

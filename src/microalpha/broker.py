"""Execution models for simulating fills."""

from __future__ import annotations

from typing import Optional

from .events import FillEvent, OrderEvent
from .slippage import VolumeSlippageModel


class SimulatedBroker:
    def __init__(
        self,
        data_handler,
        commission: float = 1.0,
        slippage_model=None,
        mode: str = "twap",
    ):
        self.data_handler = data_handler
        self.commission = commission
        self.slippage_model = slippage_model or VolumeSlippageModel()
        self.mode = mode

    def execute(self, order: OrderEvent, market_timestamp: int) -> Optional[FillEvent]:
        if self.mode.lower() == "instant":
            candidate_times = [market_timestamp]
        else:
            candidate_times = self.data_handler.get_future_timestamps(market_timestamp, 1)
            if not candidate_times:
                candidate_times = [market_timestamp]

        fill_timestamp = candidate_times[0]
        price = self.data_handler.get_latest_price(order.symbol, fill_timestamp)
        if price is None:
            return None

        sign = 1 if order.side == "BUY" else -1
        slippage = self.slippage_model.calculate_slippage(order.qty, price)
        fill_price = price + slippage * sign
        qty_signed = sign * order.qty

        return FillEvent(
            timestamp=fill_timestamp,
            symbol=order.symbol,
            qty=qty_signed,
            price=fill_price,
            commission=self.commission,
            slippage=slippage,
        )

"""Execution models responsible for producing fills."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .events import FillEvent, OrderEvent


@dataclass
class Executor:
    data_handler: any
    price_impact: float = 0.0
    commission: float = 0.0

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        fill_ts = self._fill_timestamp(order, current_ts)
        return self._build_fill(order, fill_ts, order.qty)

    def _fill_timestamp(self, order: OrderEvent, current_ts: int) -> int:
        future = self.data_handler.get_future_timestamps(current_ts, 1)
        return future[0] if future else current_ts

    def _slippage(self, qty: int) -> float:
        return self.price_impact * abs(qty)

    def _commission(self, qty: int) -> float:
        return self.commission * abs(qty)

    def _build_fill(self, order: OrderEvent, timestamp: int, qty: int) -> Optional[FillEvent]:
        price = self.data_handler.get_latest_price(order.symbol, timestamp)
        if price is None or qty == 0:
            return None

        sign = 1 if order.side == "BUY" else -1
        slippage = self._slippage(qty)
        fill_price = price + slippage * sign
        commission = self._commission(qty)
        return FillEvent(
            timestamp=timestamp,
            symbol=order.symbol,
            qty=sign * qty,
            price=fill_price,
            commission=commission,
            slippage=slippage,
        )


class TWAP(Executor):
    def __init__(self, data_handler, price_impact: float = 0.0, commission: float = 0.0, slices: int = 4):
        super().__init__(data_handler, price_impact, commission)
        self.slices = max(1, slices)

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        future = self.data_handler.get_future_timestamps(current_ts, self.slices)
        if not future:
            future = [current_ts]

        base = order.qty // len(future)
        remainder = order.qty % len(future)

        total_signed_qty = 0
        total_trade_value = 0.0
        total_commission = 0.0
        slippages = []
        last_ts = future[-1]

        for idx, ts in enumerate(future):
            qty = base + (1 if idx < remainder else 0)
            if qty == 0:
                continue
            partial = self._build_fill(order, ts, qty)
            if partial is None:
                continue
            total_signed_qty += partial.qty
            total_trade_value += partial.price * partial.qty
            total_commission += partial.commission
            slippages.append(partial.slippage)

        if total_signed_qty == 0:
            return None

        avg_price = total_trade_value / total_signed_qty
        avg_slippage = sum(slippages) / len(slippages) if slippages else 0.0

        return FillEvent(
            timestamp=last_ts,
            symbol=order.symbol,
            qty=total_signed_qty,
            price=avg_price,
            commission=total_commission,
            slippage=avg_slippage,
        )


class SquareRootImpact(Executor):
    def _slippage(self, qty: int) -> float:
        return self.price_impact * (abs(qty) ** 0.5)


class KyleLambda(Executor):
    def __init__(self, data_handler, lam: float = 0.0, **kw):
        super().__init__(data_handler, **kw)
        self.lam = lam

    def _slippage(self, qty: int) -> float:
        return self.lam * qty

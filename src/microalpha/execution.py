"""Execution models responsible for producing fills."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol, Sequence

import numpy as np

from .events import FillEvent, OrderEvent
from .lob import LatencyModel, LimitOrderBook
from .slippage import SlippageModel


class DataHandlerProtocol(Protocol):
    def get_future_timestamps(self, start_timestamp: int, n: int) -> Sequence[int]: ...

    def get_latest_price(self, symbol: str, timestamp: int) -> float | None: ...

    def get_volume_at(self, symbol: str, timestamp: int) -> float | None: ...


@dataclass
class Executor:
    data_handler: DataHandlerProtocol
    price_impact: float = 0.0
    commission: float = 0.0
    slippage_model: SlippageModel | None = None

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        fill_ts = self._fill_timestamp(order, current_ts)
        return self._build_fill(order, fill_ts, order.qty)

    def _fill_timestamp(self, order: OrderEvent, current_ts: int) -> int:
        future = self.data_handler.get_future_timestamps(current_ts, 1)
        return future[0] if future else current_ts

    def _slippage(self, qty: int, price: float) -> float:
        if self.slippage_model is not None:
            return float(self.slippage_model.calculate_slippage(qty, price))
        return self.price_impact * abs(qty)

    def _commission(self, qty: int) -> float:
        return self.commission * abs(qty)

    def _build_fill(
        self, order: OrderEvent, timestamp: int, qty: int
    ) -> Optional[FillEvent]:
        price = self.data_handler.get_latest_price(order.symbol, timestamp)
        if price is None or qty == 0:
            return None

        sign = 1 if order.side == "BUY" else -1
        slippage = self._slippage(qty, price)
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
    def __init__(
        self,
        data_handler,
        price_impact: float = 0.0,
        commission: float = 0.0,
        slices: int = 4,
        slippage_model: SlippageModel | None = None,
    ):
        super().__init__(data_handler, price_impact, commission, slippage_model)
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


class VWAP(Executor):
    """Volume-weighted execution across future timestamps.

    Allocates order quantity proportional to available volumes at future ticks.
    If volumes are missing, falls back to equal weighting.
    """

    slices: int

    def __init__(
        self,
        data_handler,
        price_impact: float = 0.0,
        commission: float = 0.0,
        slices: int = 4,
        slippage_model: SlippageModel | None = None,
    ):
        super().__init__(data_handler, price_impact, commission, slippage_model)
        self.slices = max(1, slices)

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        future = list(self.data_handler.get_future_timestamps(current_ts, self.slices))
        if not future:
            future = [current_ts]

        vols = []
        for ts in future:
            v = None
            try:
                v = self.data_handler.get_volume_at(order.symbol, ts)
            except AttributeError:
                v = None
            vols.append(1.0 if (v is None or v <= 0) else float(v))

        total_vol = sum(vols)
        if total_vol <= 0:
            weights = [1.0 / len(future)] * len(future)
        else:
            weights = [v / total_vol for v in vols]

        # Allocate integer shares by largest remainder method
        raw = [w * order.qty for w in weights]
        base = [int(x) for x in raw]
        allocated = sum(base)
        remainder = order.qty - allocated
        remainders = [(i, raw[i] - base[i]) for i in range(len(raw))]
        remainders.sort(key=lambda x: x[1], reverse=True)
        for i in range(remainder):
            base[remainders[i % len(base)][0]] += 1

        total_signed_qty = 0
        total_trade_value = 0.0
        total_commission = 0.0
        slippages: list[float] = []
        last_ts = future[-1]
        for qty, ts in zip(base, future):
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


class ImplementationShortfall(Executor):
    """Front-loaded schedule approximating IS minimisation.

    Uses geometric weights controlled by `urgency` (0<urgency<=1),
    with higher urgency concentrating more size early.
    """

    slices: int
    urgency: float

    def __init__(
        self,
        data_handler,
        price_impact: float = 0.0,
        commission: float = 0.0,
        slices: int = 4,
        urgency: float = 0.7,
        slippage_model: SlippageModel | None = None,
    ):
        super().__init__(data_handler, price_impact, commission, slippage_model)
        self.slices = max(1, slices)
        self.urgency = max(1e-3, min(float(urgency), 1.0))

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        future = list(self.data_handler.get_future_timestamps(current_ts, self.slices))
        if not future:
            future = [current_ts]
        # Geometric weights, normalised
        weights = np.array([self.urgency**i for i in range(len(future))], dtype=float)
        s = float(weights.sum()) or 1.0
        weights = (weights / s).tolist()

        raw = [w * order.qty for w in weights]
        base = [int(x) for x in raw]
        allocated = sum(base)
        remainder = order.qty - allocated
        remainders = [(i, raw[i] - base[i]) for i in range(len(raw))]
        remainders.sort(key=lambda x: x[1], reverse=True)
        for i in range(remainder):
            base[remainders[i % len(base)][0]] += 1

        total_signed_qty = 0
        total_trade_value = 0.0
        total_commission = 0.0
        slippages: list[float] = []
        last_ts = future[-1]
        for qty, ts in zip(base, future):
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
    def _slippage(self, qty: int, price: float) -> float:
        return self.price_impact * (abs(qty) ** 0.5)


class KyleLambda(Executor):
    def __init__(
        self,
        data_handler,
        lam: float = 0.0,
        slippage_model: SlippageModel | None = None,
        **kw: Any,
    ):
        super().__init__(data_handler, slippage_model=slippage_model, **kw)
        self.lam = lam

    def _slippage(self, qty: int, price: float) -> float:
        return self.lam * qty


class LOBExecution(Executor):
    """Execution wrapper backed by the internal limit order book."""

    def __init__(
        self,
        data_handler,
        price_impact: float = 0.0,
        commission: float = 0.0,
        book: LimitOrderBook | None = None,
        lob_tplus1: bool = True,
        slippage_model: SlippageModel | None = None,
    ):
        super().__init__(data_handler, price_impact, commission, slippage_model)
        self.book = book or LimitOrderBook(LatencyModel())
        self.lob_tplus1 = lob_tplus1

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        fills = self.book.submit(order)
        if not fills:
            return None
        if len(fills) == 1:
            fill = fills[0]
            # Enforce t+1 semantics by moving fill timestamp to next tick if requested
            if self.lob_tplus1:
                next_ts = self.data_handler.get_future_timestamps(order.timestamp, 1)
                if next_ts:
                    fill = FillEvent(
                        timestamp=next_ts[0],
                        symbol=fill.symbol,
                        qty=fill.qty,
                        price=fill.price,
                        commission=fill.commission,
                        slippage=fill.slippage,
                        latency_ack=fill.latency_ack,
                        latency_fill=fill.latency_fill,
                    )
            return fill

        total_qty = sum(f.qty for f in fills)
        if total_qty == 0:
            return None
        gross_notional = sum(abs(f.qty) * f.price for f in fills)
        avg_price = gross_notional / sum(abs(f.qty) for f in fills)
        latency_ack = max(f.latency_ack for f in fills)
        latency_fill = max(f.latency_fill for f in fills)

        ts = fills[-1].timestamp
        if self.lob_tplus1:
            future = self.data_handler.get_future_timestamps(order.timestamp, 1)
            if future:
                ts = future[0]
        return FillEvent(
            timestamp=ts,
            symbol=fills[0].symbol,
            qty=total_qty,
            price=avg_price,
            commission=sum(f.commission for f in fills),
            slippage=0.0,
            latency_ack=latency_ack,
            latency_fill=latency_fill,
        )

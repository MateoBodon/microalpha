"""Execution models responsible for producing fills."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Mapping, Optional, Protocol, Sequence

import numpy as np

from .events import FillEvent, OrderEvent
from .lob import LatencyModel, LimitOrderBook
from .market_metadata import SymbolMeta
from .slippage import SlippageModel


class DataHandlerProtocol(Protocol):
    def get_future_timestamps(self, start_timestamp: int, n: int) -> Sequence[int]: ...

    def get_latest_price(self, symbol: str, timestamp: int) -> float | None: ...

    def get_volume_at(self, symbol: str, timestamp: int) -> float | None: ...

    def get_recent_prices(
        self, symbol: str, end_timestamp: int, lookback: int
    ) -> Sequence[float]: ...


@dataclass
class Executor:
    data_handler: DataHandlerProtocol
    price_impact: float = 0.0
    commission: float = 0.0
    slippage_model: SlippageModel | None = None
    symbol_meta: Mapping[str, SymbolMeta] | None = None
    limit_mode: Literal["IOC", "PO", "ioc", "po"] | None = None
    queue_coefficient: float = 0.5
    queue_passive_multiplier: float = 0.5
    queue_seed: int | None = None
    queue_randomize: bool = True
    volatility_lookback: int = 20
    min_fill_qty: int = 1
    last_reject_reason: str | None = None
    _reject_reasons: list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._symbol_meta: Dict[str, SymbolMeta] = {}
        if self.symbol_meta:
            for symbol, meta in self.symbol_meta.items():
                self._symbol_meta[symbol.upper()] = meta

        self.limit_mode = self._normalise_mode(self.limit_mode)
        self.queue_coefficient = float(max(self.queue_coefficient, 0.0))
        self.queue_passive_multiplier = float(max(self.queue_passive_multiplier, 0.0))
        self.min_fill_qty = max(int(self.min_fill_qty), 0)

        self._queue_rng: np.random.Generator | None = None
        if self.limit_mode:
            seed = self.queue_seed if self.queue_seed is not None else 0
            self._queue_rng = np.random.default_rng(seed)

        if self.slippage_model and self._symbol_meta:
            self.slippage_model.update_metadata(self._symbol_meta)

    def _reset_reject_tracking(self) -> None:
        self.last_reject_reason = None
        self._reject_reasons = []

    def _record_reject(self, reason: str) -> None:
        self._reject_reasons.append(reason)
        self.last_reject_reason = reason

    def _summarize_reject_reasons(self) -> str:
        if not self._reject_reasons:
            return "no_fills"
        counts = Counter(self._reject_reasons)
        return counts.most_common(1)[0][0]

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        self._reset_reject_tracking()
        fill_ts = self._fill_timestamp(order, current_ts)
        fill = self._build_fill(order, fill_ts, order.qty)
        if fill is None:
            self.last_reject_reason = self._summarize_reject_reasons()
        return fill

    def _fill_timestamp(self, order: OrderEvent, current_ts: int) -> int:
        future = self.data_handler.get_future_timestamps(current_ts, 1)
        return future[0] if future else current_ts

    def _slippage(self, symbol: str, qty: int, price: float) -> float:
        if self.slippage_model is not None:
            return float(
                self.slippage_model.calculate_slippage(
                    qty,
                    price,
                    symbol=symbol,
                )
            )
        magnitude = self.price_impact * abs(qty)
        return math.copysign(magnitude, qty)

    def _commission(self, qty: int) -> float:
        return self.commission * abs(qty)

    def _build_fill(
        self, order: OrderEvent, timestamp: int, qty: int
    ) -> Optional[FillEvent]:
        market_price = self.data_handler.get_latest_price(order.symbol, timestamp)
        if market_price is None:
            self._record_reject("missing_price")
            return None
        if qty == 0:
            self._record_reject("qty_zero")
            return None

        meta = self._get_symbol_meta(order.symbol)
        limit_context = bool(self.limit_mode) or order.order_type == "LIMIT"
        limit_price = order.price if order.order_type == "LIMIT" else None

        if self.limit_mode is not None:
            spread_bps = meta.spread_bps if meta.spread_bps and meta.spread_bps > 0 else 10.0
            half_spread_px = (spread_bps / 20_000.0) * market_price
            if self.limit_mode == "IOC":
                limit_price = market_price if limit_price is None else limit_price
            elif self.limit_mode == "PO":
                if limit_price is None:
                    if order.side == "BUY":
                        limit_price = market_price - half_spread_px
                    else:
                        limit_price = market_price + half_spread_px
            else:
                limit_price = market_price if limit_price is None else limit_price

        if not self._limit_crossable(order, market_price, limit_price, limit_context):
            self._record_reject("limit_not_crossed")
            return None

        fill_qty = self._resolve_fill_quantity(
            order, market_price, timestamp, qty, limit_context, meta
        )
        if fill_qty == 0:
            self._record_reject("fill_qty_zero")
            return None

        sign = 1 if order.side == "BUY" else -1
        signed_qty = sign * fill_qty
        slippage = self._slippage(order.symbol, signed_qty, market_price)
        execution_price = self._apply_slippage(
            order, market_price, limit_price, slippage, limit_context
        )
        commission = self._commission(fill_qty)
        effective_slippage = execution_price - market_price
        return FillEvent(
            timestamp=timestamp,
            symbol=order.symbol,
            qty=signed_qty,
            price=execution_price,
            commission=commission,
            slippage=effective_slippage,
        )

    # --- Limit order helpers -------------------------------------------------
    @staticmethod
    def _normalise_mode(
        mode: Literal["IOC", "PO", "ioc", "po"] | None,
    ) -> Literal["IOC", "PO"] | None:
        if mode is None:
            return None
        mode_str = mode.upper()
        if mode_str not in {"IOC", "PO"}:
            raise ValueError(f"Unsupported limit execution mode '{mode}'")
        return mode_str

    def _limit_crossable(
        self,
        order: OrderEvent,
        market_price: float,
        limit_price: float | None,
        limit_context: bool,
    ) -> bool:
        if not limit_context:
            return True
        if self.limit_mode == "PO":  # allow passive fills via queue model
            return True
        if limit_price is None:
            return True
        if order.side == "BUY":
            return limit_price >= market_price
        return limit_price <= market_price

    def _resolve_fill_quantity(
        self,
        order: OrderEvent,
        market_price: float,
        timestamp: int,
        qty: int,
        limit_context: bool,
        meta: SymbolMeta,
    ) -> int:
        if not limit_context:
            return qty

        fraction = self._queue_fill_fraction(
            order, market_price, timestamp, qty, meta
        )
        if fraction <= 0.0:
            return 0

        filled = int(math.floor(qty * fraction))
        if filled == 0 and fraction > 0.0 and self.min_fill_qty > 0:
            filled = min(self.min_fill_qty, qty)
        return min(max(filled, 0), qty)

    def _queue_fill_fraction(
        self,
        order: OrderEvent,
        market_price: float,
        timestamp: int,
        qty: int,
        meta: SymbolMeta,
    ) -> float:
        abs_qty = max(abs(qty), 1)
        adv = meta.adv if meta.adv and meta.adv > 0 else float(abs_qty) * 20.0
        spread_bps = meta.spread_bps if meta.spread_bps and meta.spread_bps > 0 else 10.0

        vol_bps = self._resolve_volatility_bps(order.symbol, timestamp, meta)
        if vol_bps <= 0:
            return 0.0

        base = self.queue_coefficient * (spread_bps / vol_bps) * (adv / abs_qty)
        base = max(0.0, min(base, 1.0))

        if self.limit_mode == "PO":
            base *= self.queue_passive_multiplier

        if self._queue_rng is not None and self.queue_randomize:
            base *= self._queue_rng.uniform(0.8, 1.2)

        return max(0.0, min(base, 1.0))

    def _resolve_volatility_bps(
        self, symbol: str, timestamp: int, meta: SymbolMeta
    ) -> float:
        if meta.volatility_bps and meta.volatility_bps > 0:
            return float(meta.volatility_bps)
        prices = []
        try:
            prices = list(
                self.data_handler.get_recent_prices(
                    symbol, timestamp, max(self.volatility_lookback, 2)
                )
            )
        except AttributeError:
            prices = []
        if len(prices) < 2:
            spread = meta.spread_bps if meta.spread_bps else 0.0
            return max(spread, 1.0)
        prices_arr = np.asarray(prices, dtype=float)
        returns = np.diff(prices_arr) / prices_arr[:-1]
        if returns.size == 0:
            return max(meta.spread_bps or 0.0, 1.0)
        vol = float(np.std(returns, ddof=0))
        vol_bps = vol * 10_000.0
        return max(vol_bps, 1.0)

    def _apply_slippage(
        self,
        order: OrderEvent,
        market_price: float,
        limit_price: float | None,
        slippage: float,
        limit_context: bool,
    ) -> float:
        raw_price = market_price + slippage
        if not limit_context or limit_price is None:
            return raw_price
        if self.limit_mode == "PO":
            return limit_price
        if order.side == "BUY":
            return min(limit_price, raw_price)
        return max(limit_price, raw_price)

    def _get_symbol_meta(self, symbol: str) -> SymbolMeta:
        return self._symbol_meta.get(symbol.upper(), SymbolMeta())


class TWAP(Executor):
    def __init__(
        self,
        data_handler,
        price_impact: float = 0.0,
        commission: float = 0.0,
        slices: int = 4,
        slippage_model: SlippageModel | None = None,
        **kwargs: Any,
    ):
        super().__init__(
            data_handler=data_handler,
            price_impact=price_impact,
            commission=commission,
            slippage_model=slippage_model,
            **kwargs,
        )
        self.slices = max(1, slices)

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        self._reset_reject_tracking()
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
            self.last_reject_reason = self._summarize_reject_reasons()
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
        **kwargs: Any,
    ):
        super().__init__(
            data_handler=data_handler,
            price_impact=price_impact,
            commission=commission,
            slippage_model=slippage_model,
            **kwargs,
        )
        self.slices = max(1, slices)

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        self._reset_reject_tracking()
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
            self.last_reject_reason = self._summarize_reject_reasons()
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
        **kwargs: Any,
    ):
        super().__init__(
            data_handler=data_handler,
            price_impact=price_impact,
            commission=commission,
            slippage_model=slippage_model,
            **kwargs,
        )
        self.slices = max(1, slices)
        self.urgency = max(1e-3, min(float(urgency), 1.0))

    def execute(self, order: OrderEvent, current_ts: int) -> Optional[FillEvent]:
        self._reset_reject_tracking()
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
            self.last_reject_reason = self._summarize_reject_reasons()
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
    def _slippage(self, symbol: str, qty: int, price: float) -> float:
        magnitude = self.price_impact * (abs(qty) ** 0.5)
        return math.copysign(magnitude, qty)


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

    def _slippage(self, symbol: str, qty: int, price: float) -> float:
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
        self._reset_reject_tracking()
        fills = self.book.submit(order)
        if not fills:
            self._record_reject("lob_no_fills")
            self.last_reject_reason = self._summarize_reject_reasons()
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

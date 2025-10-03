"""Simplified limit order book with FIFO price levels and latency model."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

import numpy as np

from .events import FillEvent, OrderEvent


@dataclass
class LatencyModel:
    ack_fixed: float = 0.001
    ack_jitter: float = 0.0005
    fill_fixed: float = 0.01
    fill_jitter: float = 0.002
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        self._rng = np.random.default_rng(self.seed)

    def sample(self) -> tuple[float, float]:
        ack = self.ack_fixed + self._rng.uniform(0, self.ack_jitter)
        fill = self.fill_fixed + self._rng.uniform(0, self.fill_jitter)
        return ack, fill


@dataclass
class LimitOrder:
    order_id: str
    side: str
    price: float
    qty: int
    timestamp: int


class BookSide:
    def __init__(self, is_bid: bool) -> None:
        self.is_bid = is_bid
        self.levels: Dict[float, Deque[LimitOrder]] = {}
        self.prices: List[float] = []

    def _insert_price(self, price: float) -> None:
        if price in self.levels:
            return
        self.levels[price] = deque()
        self.prices.append(price)
        self.prices.sort(reverse=self.is_bid)

    def _remove_price(self, price: float) -> None:
        if price in self.levels and not self.levels[price]:
            self.prices.remove(price)
            del self.levels[price]

    def add(self, order: LimitOrder) -> None:
        self._insert_price(order.price)
        self.levels[order.price].append(order)

    def best_price(self) -> Optional[float]:
        return self.prices[0] if self.prices else None

    def pop_order(self, price: float) -> Optional[LimitOrder]:
        if price not in self.levels:
            return None
        level = self.levels[price]
        if not level:
            return None
        order = level[0]
        if order.qty == 0:
            level.popleft()
            order = level[0] if level else None
        return order

    def consume(self, price: float, qty: int) -> List[LimitOrder]:
        fills: List[LimitOrder] = []
        while qty > 0 and price in self.levels and self.levels[price]:
            head = self.levels[price][0]
            traded = min(qty, head.qty)
            head.qty -= traded
            qty -= traded
            fills.append(LimitOrder(head.order_id, head.side, price, traded, head.timestamp))
            if head.qty == 0:
                self.levels[price].popleft()
        self._remove_price(price)
        return fills

    def matchable(self, price: Optional[float], incoming_side: str) -> bool:
        best = self.best_price()
        if best is None:
            return False
        if price is None:
            return True
        if incoming_side == "BUY":
            return best <= price
        return best >= price

    def iterate_levels(self):
        for price in list(self.prices):
            yield price


class LimitOrderBook:
    def __init__(self, latency_model: Optional[LatencyModel] = None) -> None:
        self.bids = BookSide(is_bid=True)
        self.asks = BookSide(is_bid=False)
        self.latency_model = latency_model or LatencyModel()
        self._id_counter = 0
        self._lookup: Dict[str, tuple[BookSide, float]] = {}

    def _next_id(self) -> str:
        self._id_counter += 1
        return f"LOB-{self._id_counter}"

    def seed_book(
        self,
        mid_price: float,
        tick: float,
        levels: int,
        size: int,
    ) -> None:
        for i in range(1, levels + 1):
            bid_price = mid_price - i * tick
            ask_price = mid_price + i * tick
            bid_order = LimitOrder(self._next_id(), "BUY", bid_price, size, 0)
            ask_order = LimitOrder(self._next_id(), "SELL", ask_price, size, 0)
            self.bids.add(bid_order)
            self.asks.add(ask_order)
            self._lookup[bid_order.order_id] = (self.bids, bid_price)
            self._lookup[ask_order.order_id] = (self.asks, ask_price)

    def submit(self, order_event: OrderEvent) -> List[FillEvent]:
        if order_event.order_type == "CANCEL" and order_event.order_id:
            self.cancel(order_event.order_id)
            return []

        order_id = order_event.order_id or self._next_id()
        remaining_qty = abs(order_event.qty)
        fills: List[FillEvent] = []
        ack_latency, fill_latency = self.latency_model.sample()

        side = order_event.side
        aggressive_book = self.asks if side == "BUY" else self.bids
        passive_book = self.bids if side == "BUY" else self.asks

        price_limit = order_event.price if order_event.order_type == "LIMIT" else None

        # Matching phase
        while remaining_qty > 0 and aggressive_book.matchable(price_limit, side):
            best_price = aggressive_book.best_price()
            if best_price is None:
                break
            if price_limit is not None:
                if side == "BUY" and best_price > price_limit:
                    break
                if side == "SELL" and best_price < price_limit:
                    break

            matched_orders = aggressive_book.consume(best_price, remaining_qty)
            if not matched_orders:
                break
            traded = sum(order.qty for order in matched_orders)
            remaining_qty -= traded
            signed_qty = traded if side == "BUY" else -traded
            fills.append(
                FillEvent(
                    timestamp=order_event.timestamp,
                    symbol=order_event.symbol,
                    qty=signed_qty,
                    price=best_price,
                    commission=0.0,
                    slippage=0.0,
                    latency_ack=ack_latency,
                    latency_fill=fill_latency,
                )
            )

        if remaining_qty > 0 and order_event.order_type == "LIMIT":
            order = LimitOrder(order_id, side, price_limit if price_limit is not None else 0.0, remaining_qty, order_event.timestamp)
            passive_book.add(order)
            self._lookup[order_id] = (passive_book, order.price)

        return fills

    def cancel(self, order_id: str) -> None:
        if order_id not in self._lookup:
            return
        book, price = self._lookup.pop(order_id)
        if price not in book.levels:
            return
        level = book.levels[price]
        book.levels[price] = deque([order for order in level if order.order_id != order_id])
        book._remove_price(price)


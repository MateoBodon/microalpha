"""Portfolio management reacting to fills and signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .events import FillEvent, LookaheadError, MarketEvent, OrderEvent, SignalEvent


@dataclass
class PortfolioPosition:
    qty: int = 0


class Portfolio:
    def __init__(self, data_handler, initial_cash: float = 100000.0, default_order_qty: int = 400):
        self.data_handler = data_handler
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, PortfolioPosition] = {}
        self.equity_curve: List[Dict[str, float]] = []
        self.current_time: int | None = None
        self.total_turnover = 0.0
        self.default_order_qty = default_order_qty

    def on_market(self, event: MarketEvent) -> None:
        self.current_time = event.timestamp
        market_value = 0.0
        for symbol, position in self.positions.items():
            price = self.data_handler.get_latest_price(symbol, event.timestamp)
            if price is None:
                continue
            market_value += position.qty * price

        total_equity = self.cash + market_value
        exposure = market_value / total_equity if total_equity else 0.0
        self.equity_curve.append(
            {
                "timestamp": event.timestamp,
                "equity": total_equity,
                "exposure": exposure,
            }
        )

    def on_signal(self, signal: SignalEvent) -> Iterable[OrderEvent]:
        if self.current_time is not None and signal.timestamp < self.current_time:
            raise LookaheadError("Signal event timestamp is in the past.")

        qty = self._signal_quantity(signal)
        if qty == 0:
            return []

        if signal.side == "EXIT":
            position = self.positions.get(signal.symbol)
            if not position or position.qty == 0:
                return []
            side = "SELL" if position.qty > 0 else "BUY"
            return [OrderEvent(signal.timestamp, signal.symbol, abs(position.qty), side)]

        side = "BUY" if signal.side == "LONG" else "SELL"
        return [OrderEvent(signal.timestamp, signal.symbol, qty, side)]

    def on_fill(self, fill: FillEvent) -> None:
        if self.current_time is not None and fill.timestamp < self.current_time:
            raise LookaheadError("Fill event timestamp is in the past.")

        position = self.positions.setdefault(fill.symbol, PortfolioPosition())
        position.qty += fill.qty

        trade_value = fill.price * fill.qty
        self.cash -= trade_value
        self.cash -= fill.commission
        self.total_turnover += abs(trade_value)

    def _signal_quantity(self, signal: SignalEvent) -> int:
        if signal.meta and "qty" in signal.meta:
            return int(signal.meta["qty"])
        return self.default_order_qty


"""Portfolio management reacting to fills and signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, cast

from .events import FillEvent, LookaheadError, MarketEvent, OrderEvent, SignalEvent
from .logging import JsonlWriter


@dataclass
class PortfolioPosition:
    qty: int = 0


class Portfolio:
    def __init__(
        self,
        data_handler,
        initial_cash: float = 100000.0,
        default_order_qty: int = 400,
        max_exposure: float | None = None,
        max_drawdown_stop: float | None = None,
        turnover_cap: float | None = None,
        kelly_fraction: float | None = None,
        trade_logger: JsonlWriter | None = None,
    ):
        self.data_handler = data_handler
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, PortfolioPosition] = {}
        self.equity_curve: List[Dict[str, float | int]] = []
        self.current_time: int | None = None
        self.total_turnover = 0.0
        self.default_order_qty = default_order_qty
        self.max_exposure = max_exposure
        self.max_drawdown_stop = max_drawdown_stop
        self.turnover_cap = turnover_cap
        self.kelly_fraction = kelly_fraction
        self.high_water_mark = initial_cash
        self.drawdown_halted = False
        self.market_value = 0.0
        self.last_equity = initial_cash
        self.trades: List[Dict[str, float | int | str | None]] = []
        self.trade_logger = trade_logger
        self.trade_log_path = trade_logger.path if trade_logger else None

    def on_market(self, event: MarketEvent) -> None:
        self.current_time = event.timestamp
        market_value = 0.0
        per_symbol_mv: Dict[str, float] = {}
        for symbol, position in self.positions.items():
            price = self.data_handler.get_latest_price(symbol, event.timestamp)
            if price is None:
                continue
            mv = position.qty * price
            per_symbol_mv[symbol] = mv
            market_value += mv

        total_equity = self.cash + market_value
        exposure = market_value / total_equity if total_equity else 0.0
        self.market_value = market_value
        self.last_equity = total_equity
        self.high_water_mark = max(self.high_water_mark, total_equity)

        if (
            self.max_drawdown_stop is not None
            and total_equity < self.high_water_mark
            and (self.high_water_mark - total_equity) / self.high_water_mark
            >= self.max_drawdown_stop
        ):
            self.drawdown_halted = True

        # Cross-sectional stats
        abs_values = [abs(v) for v in per_symbol_mv.values() if v != 0]
        sum_abs = sum(abs_values)
        gross_exposure = sum_abs / total_equity if total_equity and sum_abs else 0.0
        num_positions = int(sum(1 for v in per_symbol_mv.values() if v != 0))
        concentration = 0.0
        if sum_abs > 0:
            weights = [v / sum_abs for v in abs_values]
            concentration = float(sum(w * w for w in weights))

        self.equity_curve.append(
            {
                "timestamp": event.timestamp,
                "equity": total_equity,
                "exposure": exposure,
                "gross_exposure": gross_exposure,
                "num_positions": num_positions,
                "concentration": concentration,
            }
        )

    def on_signal(self, signal: SignalEvent) -> Iterable[OrderEvent]:
        if self.current_time is not None and signal.timestamp < self.current_time:
            raise LookaheadError("Signal event timestamp is in the past.")

        if signal.side == "EXIT":
            position = self.positions.get(signal.symbol)
            if not position or position.qty == 0:
                return []
            side = cast(Literal["BUY", "SELL"], "SELL" if position.qty > 0 else "BUY")
            return [
                OrderEvent(signal.timestamp, signal.symbol, abs(position.qty), side)
            ]

        if self.drawdown_halted:
            return []

        qty = self._signal_quantity(signal)
        if qty == 0:
            return []

        price = self.data_handler.get_latest_price(signal.symbol, signal.timestamp)
        if price is None:
            return []

        if self.turnover_cap is not None:
            projected_turnover = self.total_turnover + price * qty
            if projected_turnover > self.turnover_cap:
                return []

        side = cast(Literal["BUY", "SELL"], "BUY" if signal.side == "LONG" else "SELL")
        anticipated_market_value = (
            self.market_value + (qty if side == "BUY" else -qty) * price
        )
        projected_equity = self.last_equity if self.last_equity else self.initial_cash
        projected_exposure = (
            abs(anticipated_market_value) / projected_equity
            if projected_equity
            else 0.0
        )

        if self.max_exposure is not None and projected_exposure > self.max_exposure:
            return []

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

        side = cast(Literal["BUY", "SELL"], "BUY" if fill.qty > 0 else "SELL")
        inventory = position.qty
        trade_record: Dict[str, float | int | str | None] = {
            "timestamp": fill.timestamp,
            "symbol": fill.symbol,
            "side": side,
            "qty": float(fill.qty),
            "price": float(fill.price),
            "commission": float(fill.commission),
            "slippage": float(fill.slippage),
            "cash": float(self.cash),
            "inventory": float(inventory),
            "latency_ack": float(getattr(fill, "latency_ack", 0.0)),
            "latency_fill": float(getattr(fill, "latency_fill", 0.0)),
        }
        self.trades.append(trade_record)

        if self.trade_logger:
            self.trade_logger.write(
                {
                    "timestamp": fill.timestamp,
                    "order_id": getattr(fill, "order_id", None),
                    "symbol": fill.symbol,
                    "side": side,
                    "qty": float(fill.qty),
                    "price": float(fill.price),
                    "commission": float(fill.commission),
                    "slippage": float(fill.slippage),
                    "inventory": float(inventory),
                    "cash": float(self.cash),
                }
            )
            self.trade_log_path = self.trade_logger.path

    def _signal_quantity(self, signal: SignalEvent) -> int:
        if signal.meta and "qty" in signal.meta:
            return int(signal.meta["qty"])
        if self.kelly_fraction and self.last_equity and self.current_time is not None:
            price = self.data_handler.get_latest_price(signal.symbol, self.current_time)
            if price:
                alloc = self.last_equity * self.kelly_fraction
                return max(int(alloc / price), 0)
        return self.default_order_qty

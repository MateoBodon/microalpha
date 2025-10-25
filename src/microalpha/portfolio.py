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
        vol_target_annualized: float | None = None,
        vol_lookback: int | None = None,
        max_portfolio_heat: float | None = None,
        sectors: Dict[str, str] | None = None,
        max_positions_per_sector: int | None = None,
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
        self.vol_target_annualized = vol_target_annualized
        self.vol_lookback = vol_lookback or 20
        self.max_portfolio_heat = max_portfolio_heat
        self.sector_of: Dict[str, str] = sectors or {}
        self.max_positions_per_sector = max_positions_per_sector

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

        qty = self._sized_quantity(signal)
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

    def _sized_quantity(self, signal: SignalEvent) -> int:
        base = self._signal_quantity(signal)
        if base == 0 or not self.last_equity:
            return base
        price = self.data_handler.get_latest_price(signal.symbol, self.current_time) if self.current_time else None
        if self.vol_target_annualized and price:
            # Approximate daily vol from equity history
            import pandas as _pd

            eq = _pd.DataFrame(self.equity_curve)
            if not eq.empty:
                eq = eq.tail(self.vol_lookback)
                ret = eq["equity"].pct_change().dropna()
                if not ret.empty:
                    ann_vol = float(ret.std(ddof=0) * (252 ** 0.5))
                    target_vol = max(self.vol_target_annualized, 1e-9)
                    scale = target_vol / max(ann_vol, 1e-9)
                    base = max(int(base * scale), 0)

        # Portfolio heat cap: sum |position| * price / equity <= max_portfolio_heat
        if self.max_portfolio_heat and price:
            projected_pos_value = abs(base) * price
            current_heat_value = 0.0
            for sym, pos in self.positions.items():
                p = self.data_handler.get_latest_price(sym, self.current_time) if self.current_time else None
                if p:
                    current_heat_value += abs(pos.qty) * p
            projected_heat = (current_heat_value + projected_pos_value) / max(self.last_equity, 1e-9)
            if projected_heat > self.max_portfolio_heat:
                return 0

        # Sector cap: limit number of open positions per sector
        if self.max_positions_per_sector and self.sector_of:
            sector = self.sector_of.get(signal.symbol)
            if sector:
                open_in_sector = 0
                for sym, pos in self.positions.items():
                    if pos.qty != 0 and self.sector_of.get(sym) == sector:
                        open_in_sector += 1
                if open_in_sector >= self.max_positions_per_sector and base > 0:
                    return 0

        return base

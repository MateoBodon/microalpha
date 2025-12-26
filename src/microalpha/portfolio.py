"""Portfolio management reacting to fills and signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Mapping, cast
from typing import TYPE_CHECKING

from .events import FillEvent, LookaheadError, MarketEvent, OrderEvent, SignalEvent
from .logging import JsonlWriter
from .market_metadata import SymbolMeta

if TYPE_CHECKING:
    from .order_flow import OrderFlowDiagnostics

NS_PER_DAY = 86_400_000_000_000
TRADING_DAYS_PER_YEAR = 252


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
        max_gross_leverage: float | None = None,
        max_single_name_weight: float | None = None,
        sectors: Dict[str, str] | None = None,
        max_positions_per_sector: int | None = None,
        capital_policy=None,
        symbol_meta: Mapping[str, SymbolMeta] | None = None,
        borrow_cfg: Mapping[str, float | None] | object | None = None,
        order_flow: "OrderFlowDiagnostics | None" = None,
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
        self.max_gross_leverage = max_gross_leverage
        self.max_single_name_weight = max_single_name_weight
        self.max_drawdown_stop = max_drawdown_stop
        self.turnover_cap = turnover_cap
        self.kelly_fraction = kelly_fraction
        self.high_water_mark = initial_cash
        self.drawdown_halted = False
        self.market_value = 0.0
        self.gross_market_value = 0.0
        self.last_equity = initial_cash
        self.trades: List[Dict[str, float | int | str | None]] = []
        self.trade_logger = trade_logger
        self.trade_log_path = trade_logger.path if trade_logger else None
        self.commission_total: float = 0.0
        self.vol_target_annualized = vol_target_annualized
        self.vol_lookback = vol_lookback or 20
        self.max_portfolio_heat = max_portfolio_heat
        self.sector_of: Dict[str, str] = sectors or {}
        self.max_positions_per_sector = max_positions_per_sector
        self.capital_policy = capital_policy
        self.avg_cost: Dict[str, float] = {}
        self.cum_realized_pnl: float = 0.0
        self._symbol_meta: Dict[str, SymbolMeta] = {}
        if symbol_meta:
            self._symbol_meta = {sym.upper(): meta for sym, meta in symbol_meta.items()}
        self.borrow_cost_total: float = 0.0
        self._last_borrow_day: Dict[str, int] = {}
        self.borrow_fee_bps: float | None = None
        self.borrow_fee_floor_bps: float | None = None
        self.borrow_fee_multiplier: float = 1.0
        self.order_flow = order_flow
        self._last_sizing_reject_reason: str | None = None
        if borrow_cfg is not None:
            if isinstance(borrow_cfg, Mapping):
                self.borrow_fee_bps = (
                    float(borrow_cfg["annual_fee_bps"])
                    if borrow_cfg.get("annual_fee_bps") is not None
                    else None
                )
                self.borrow_fee_floor_bps = (
                    float(borrow_cfg["floor_bps"])
                    if borrow_cfg.get("floor_bps") is not None
                    else None
                )
                if borrow_cfg.get("multiplier") is not None:
                    self.borrow_fee_multiplier = float(borrow_cfg.get("multiplier", 1.0))
            else:
                self.borrow_fee_bps = (
                    float(getattr(borrow_cfg, "annual_fee_bps"))
                    if getattr(borrow_cfg, "annual_fee_bps", None) is not None
                    else None
                )
                self.borrow_fee_floor_bps = (
                    float(getattr(borrow_cfg, "floor_bps"))
                    if getattr(borrow_cfg, "floor_bps", None) is not None
                    else None
                )
                if getattr(borrow_cfg, "multiplier", None) is not None:
                    self.borrow_fee_multiplier = float(getattr(borrow_cfg, "multiplier"))

    def on_market(self, event: MarketEvent) -> None:
        self._record_equity(event.timestamp, apply_borrow_costs=True, overwrite_last=True)

    def refresh_equity_after_fills(self, timestamp: int) -> None:
        """Refresh the latest equity snapshot after same-day fills."""
        self._record_equity(timestamp, apply_borrow_costs=False, overwrite_last=True)

    def _record_equity(
        self,
        timestamp: int,
        *,
        apply_borrow_costs: bool,
        overwrite_last: bool,
    ) -> None:
        self.current_time = timestamp
        market_value = 0.0
        gross_market_value = 0.0
        borrow_cost = 0.0
        for symbol, position in self.positions.items():
            price = self.data_handler.get_latest_price(symbol, timestamp)
            if price is None:
                continue
            market_value += position.qty * price
            gross_market_value += abs(position.qty * price)
            if apply_borrow_costs:
                borrow_cost += self._borrow_cost_for(
                    symbol, position.qty, price, timestamp
                )

        if apply_borrow_costs and borrow_cost > 0.0:
            self.cash -= borrow_cost
            self.cum_realized_pnl -= borrow_cost
            self.borrow_cost_total += borrow_cost

        total_equity = self.cash + market_value
        exposure = market_value / total_equity if total_equity else 0.0
        gross_exposure = gross_market_value / total_equity if total_equity else 0.0
        self.market_value = market_value
        self.gross_market_value = gross_market_value
        self.last_equity = total_equity
        self.high_water_mark = max(self.high_water_mark, total_equity)

        if (
            self.max_drawdown_stop is not None
            and total_equity < self.high_water_mark
            and (self.high_water_mark - total_equity) / self.high_water_mark
            >= self.max_drawdown_stop
        ):
            self.drawdown_halted = True

        record = {
            "timestamp": timestamp,
            "equity": total_equity,
            "exposure": exposure,
            "gross_exposure": gross_exposure,
        }
        if (
            overwrite_last
            and self.equity_curve
            and self.equity_curve[-1].get("timestamp") == timestamp
        ):
            self.equity_curve[-1] = record
        else:
            self.equity_curve.append(record)

    def valuation_snapshot(self, timestamp: int | None = None) -> tuple[float, float, float]:
        """Return (market_value, gross_market_value, unrealized_pnl) at timestamp."""
        ts = self.current_time if timestamp is None else timestamp
        if ts is None:
            return 0.0, 0.0, 0.0
        market_value = 0.0
        gross_market_value = 0.0
        unrealized_pnl = 0.0
        for symbol, position in self.positions.items():
            if position.qty == 0:
                continue
            price = self.data_handler.get_latest_price(symbol, ts)
            if price is None:
                price = self.avg_cost.get(symbol)
            if price is None:
                continue
            market_value += position.qty * price
            gross_market_value += abs(position.qty * price)
            avg_cost = self.avg_cost.get(symbol, price)
            unrealized_pnl += (price - avg_cost) * position.qty
        return market_value, gross_market_value, unrealized_pnl

    def on_signal(self, signal: SignalEvent) -> Iterable[OrderEvent]:
        if self.current_time is not None and signal.timestamp < self.current_time:
            raise LookaheadError("Signal event timestamp is in the past.")

        if signal.side == "EXIT":
            position = self.positions.get(signal.symbol)
            if not position or position.qty == 0:
                if self.order_flow:
                    self.order_flow.record_order_drop(
                        "exit_no_position", signal=signal
                    )
                return []
            side = cast(Literal["BUY", "SELL"], "SELL" if position.qty > 0 else "BUY")
            order = OrderEvent(signal.timestamp, signal.symbol, abs(position.qty), side)
            if self.order_flow:
                self.order_flow.record_order_created(order, signal=signal)
            return [order]

        if self.drawdown_halted:
            if self.order_flow:
                self.order_flow.record_order_drop(
                    "drawdown_halted", signal=signal, clipped_by_caps=True
                )
            return []

        qty = self._sized_quantity(signal)
        if qty == 0:
            if self.order_flow:
                reason = self._last_sizing_reject_reason or "qty_rounded_to_zero"
                self.order_flow.record_order_drop(reason, signal=signal)
            return []

        price = self.data_handler.get_latest_price(signal.symbol, signal.timestamp)
        if price is None:
            if self.order_flow:
                self.order_flow.record_order_drop("missing_price", signal=signal)
            return []

        if self.turnover_cap is not None:
            projected_turnover = self.total_turnover + price * qty
            if projected_turnover > self.turnover_cap:
                if self.order_flow:
                    self.order_flow.record_order_drop(
                        "turnover_cap", signal=signal, clipped_by_caps=True
                    )
                return []

        side = cast(Literal["BUY", "SELL"], "BUY" if signal.side == "LONG" else "SELL")
        projected_equity = self.last_equity if self.last_equity else self.initial_cash
        has_weight = bool(
            signal.meta and "weight" in signal.meta and "qty" not in signal.meta
        )
        anticipated_market_value = (
            self.market_value + (qty if side == "BUY" else -qty) * price
        )
        projected_exposure = (
            abs(anticipated_market_value) / projected_equity if projected_equity else 0.0
        )

        if self.max_exposure is not None and projected_exposure > self.max_exposure:
            if has_weight and projected_equity:
                max_abs_mv = float(self.max_exposure) * projected_equity
                if side == "BUY":
                    max_additional = max_abs_mv - self.market_value
                else:
                    max_additional = max_abs_mv + self.market_value
                max_qty_exposure = int(max_additional / price) if max_additional > 0 else 0
                if max_qty_exposure <= 0:
                    if self.order_flow:
                        self.order_flow.record_order_drop(
                            "max_exposure", signal=signal, clipped_by_caps=True
                        )
                    return []
                if max_qty_exposure < qty:
                    qty = max_qty_exposure
                    if self.order_flow:
                        self.order_flow.record_order_clip("max_exposure", signal=signal)
                anticipated_market_value = (
                    self.market_value + (qty if side == "BUY" else -qty) * price
                )
                projected_exposure = (
                    abs(anticipated_market_value) / projected_equity
                    if projected_equity
                    else 0.0
                )
                if projected_exposure > self.max_exposure:
                    if self.order_flow:
                        self.order_flow.record_order_drop(
                            "max_exposure", signal=signal, clipped_by_caps=True
                        )
                    return []
            else:
                if self.order_flow:
                    self.order_flow.record_order_drop(
                        "max_exposure", signal=signal, clipped_by_caps=True
                    )
                return []

        if self.max_single_name_weight is not None and projected_equity:
            prev_qty = self.positions.get(signal.symbol, PortfolioPosition()).qty
            new_qty = prev_qty + (qty if side == "BUY" else -qty)
            projected_weight = abs(new_qty * price) / projected_equity
            if projected_weight > self.max_single_name_weight:
                if has_weight:
                    max_abs_qty = int(
                        (float(self.max_single_name_weight) * projected_equity) / price
                    )
                    if max_abs_qty <= 0:
                        if self.order_flow:
                            self.order_flow.record_order_drop(
                                "max_single_name_weight",
                                signal=signal,
                                clipped_by_caps=True,
                            )
                        return []
                    desired_new_qty = max_abs_qty if side == "BUY" else -max_abs_qty
                    clipped_qty = abs(desired_new_qty - prev_qty)
                    if clipped_qty <= 0:
                        if self.order_flow:
                            self.order_flow.record_order_drop(
                                "max_single_name_weight",
                                signal=signal,
                                clipped_by_caps=True,
                            )
                        return []
                    if clipped_qty < qty:
                        qty = clipped_qty
                        if self.order_flow:
                            self.order_flow.record_order_clip(
                                "max_single_name_weight", signal=signal
                            )
                    new_qty = prev_qty + (qty if side == "BUY" else -qty)
                    projected_weight = abs(new_qty * price) / projected_equity
                    if projected_weight > self.max_single_name_weight:
                        if self.order_flow:
                            self.order_flow.record_order_drop(
                                "max_single_name_weight",
                                signal=signal,
                                clipped_by_caps=True,
                            )
                        return []
                else:
                    if self.order_flow:
                        self.order_flow.record_order_drop(
                            "max_single_name_weight",
                            signal=signal,
                            clipped_by_caps=True,
                        )
                    return []

        if self.max_gross_leverage is not None and projected_equity:
            prev_qty = self.positions.get(signal.symbol, PortfolioPosition()).qty
            prev_abs_value = abs(prev_qty * price)
            new_qty = prev_qty + (qty if side == "BUY" else -qty)
            new_abs_value = abs(new_qty * price)
            current_gross = (
                self.gross_market_value
                if self.gross_market_value > 0.0
                else self._estimate_gross_market_value()
            )
            projected_gross = max(current_gross - prev_abs_value + new_abs_value, 0.0)
            projected_gross_exposure = projected_gross / projected_equity
            if projected_gross_exposure > self.max_gross_leverage:
                if self.order_flow:
                    self.order_flow.record_order_drop(
                        "max_gross_leverage", signal=signal, clipped_by_caps=True
                    )
                return []

        order = OrderEvent(signal.timestamp, signal.symbol, qty, side)
        if self.order_flow:
            self.order_flow.record_order_created(order, signal=signal)
        return [order]

    def on_fill(self, fill: FillEvent) -> None:
        if self.current_time is not None and fill.timestamp < self.current_time:
            raise LookaheadError("Fill event timestamp is in the past.")

        position = self.positions.setdefault(fill.symbol, PortfolioPosition())
        prev_qty = position.qty
        position.qty += fill.qty

        trade_value = fill.price * fill.qty
        self.cash -= trade_value
        self.cash -= fill.commission
        self.commission_total += float(fill.commission)
        self.total_turnover += abs(trade_value)

        side = cast(Literal["BUY", "SELL"], "BUY" if fill.qty > 0 else "SELL")
        inventory = position.qty

        # Realized PnL attribution using average cost per symbol
        realized = 0.0
        avg_cost = self.avg_cost.get(fill.symbol, fill.price)
        if prev_qty > 0 and fill.qty < 0:
            # Selling out of a long
            reduced = min(abs(fill.qty), prev_qty)
            realized = (fill.price - avg_cost) * reduced
        elif prev_qty < 0 and fill.qty > 0:
            # Buying to cover a short
            reduced = min(fill.qty, abs(prev_qty))
            realized = (avg_cost - fill.price) * reduced

        self.cum_realized_pnl += realized

        # Update average cost after fill
        new_qty = position.qty
        if new_qty == 0:
            self.avg_cost.pop(fill.symbol, None)
        else:
            # If position crossed through zero, set avg cost to fill price for new side
            if (prev_qty > 0 and new_qty < 0) or (prev_qty < 0 and new_qty > 0):
                self.avg_cost[fill.symbol] = fill.price
            else:
                # If increasing exposure on same side, update weighted average
                if (prev_qty >= 0 and fill.qty > 0) or (prev_qty <= 0 and fill.qty < 0):
                    self.avg_cost[fill.symbol] = (
                        avg_cost * prev_qty + fill.price * fill.qty
                    ) / new_qty
                else:
                    # Reducing but not crossing: keep existing avg cost
                    self.avg_cost[fill.symbol] = avg_cost
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
            "realized_pnl": float(realized),
            "cum_realized_pnl": float(self.cum_realized_pnl),
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

    def _borrow_cost_for(
        self, symbol: str, qty: int, price: float, timestamp: int
    ) -> float:
        key = symbol.upper()
        if qty >= 0:
            self._last_borrow_day.pop(key, None)
            return 0.0

        meta = self._symbol_meta.get(key)
        raw_bps = meta.borrow_fee_annual_bps if meta and meta.borrow_fee_annual_bps else None
        if raw_bps is None and self.borrow_fee_bps is not None:
            raw_bps = self.borrow_fee_bps
        if raw_bps is None and self.borrow_fee_floor_bps is not None:
            raw_bps = self.borrow_fee_floor_bps
        if raw_bps is None or raw_bps <= 0:
            self._last_borrow_day.pop(key, None)
            return 0.0
        effective_bps = float(raw_bps) * self.borrow_fee_multiplier
        if self.borrow_fee_floor_bps is not None:
            effective_bps = max(effective_bps, float(self.borrow_fee_floor_bps))

        current_day = int(timestamp // NS_PER_DAY)
        prev_day = self._last_borrow_day.get(key)

        if prev_day == current_day:
            return 0.0

        if prev_day is None:
            days = 1
        else:
            days = max(current_day - prev_day, 1)

        self._last_borrow_day[key] = current_day

        annual_rate = effective_bps / 10_000.0
        daily_rate = annual_rate / TRADING_DAYS_PER_YEAR
        notional = abs(qty) * price
        return notional * daily_rate * days

    def _estimate_gross_market_value(self) -> float:
        gross_value = 0.0
        if self.current_time is None:
            return gross_value
        for sym, pos in self.positions.items():
            if pos.qty == 0:
                continue
            price = self.data_handler.get_latest_price(sym, self.current_time)
            if price is None:
                price = self.avg_cost.get(sym)
            if price is None:
                continue
            gross_value += abs(pos.qty) * price
        return gross_value

    def _signal_quantity(self, signal: SignalEvent) -> int:
        if signal.meta:
            if "qty" in signal.meta:
                return int(signal.meta["qty"])
            if "weight" in signal.meta:
                target_weight = float(signal.meta["weight"])
                equity = self.last_equity if self.last_equity is not None else self.initial_cash
                if equity and equity > 0:
                    price = self.data_handler.get_latest_price(signal.symbol, signal.timestamp)
                    if price is None and self.current_time is not None:
                        price = self.data_handler.get_latest_price(
                            signal.symbol, self.current_time
                        )
                    if price and price > 0:
                        target_dollar = target_weight * equity
                        qty = int(abs(target_dollar / price))
                        return qty
                return 0
        if self.kelly_fraction and self.last_equity and self.current_time is not None:
            price = self.data_handler.get_latest_price(signal.symbol, self.current_time)
            if price:
                alloc = self.last_equity * self.kelly_fraction
                return max(int(alloc / price), 0)
        return self.default_order_qty

    def _sized_quantity(self, signal: SignalEvent) -> int:
        self._last_sizing_reject_reason = None
        base = self._signal_quantity(signal)
        if base == 0 or not self.last_equity:
            if base == 0:
                self._last_sizing_reject_reason = "qty_rounded_to_zero"
            return base
        price = (
            self.data_handler.get_latest_price(signal.symbol, self.current_time)
            if self.current_time is not None
            else None
        )
        if self.vol_target_annualized and price:
            # Approximate daily vol from equity history
            import pandas as _pd

            eq = _pd.DataFrame(self.equity_curve)
            if not eq.empty:
                eq = eq.tail(self.vol_lookback)
                ret = eq["equity"].pct_change().dropna()
                if not ret.empty:
                    ann_vol = float(ret.std(ddof=0) * (252**0.5))
                    target_vol = max(self.vol_target_annualized, 1e-9)
                    scale = target_vol / max(ann_vol, 1e-9)
                    base = max(int(base * scale), 0)

        # Portfolio heat cap: sum |position| * price / equity <= max_portfolio_heat
        if self.max_portfolio_heat and price:
            projected_pos_value = abs(base) * price
            current_heat_value = 0.0
            for sym, pos in self.positions.items():
                p = (
                    self.data_handler.get_latest_price(sym, self.current_time)
                    if self.current_time is not None
                    else None
                )
                if p:
                    current_heat_value += abs(pos.qty) * p
            projected_heat = (current_heat_value + projected_pos_value) / max(
                self.last_equity, 1e-9
            )
            if projected_heat > self.max_portfolio_heat:
                self._last_sizing_reject_reason = "max_portfolio_heat"
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
                    self._last_sizing_reject_reason = "max_positions_per_sector"
                    return 0

        # Capital policy adjustment (e.g., vol scaling)
        if self.capital_policy and price and self.current_time is not None:
            base = int(
                self.capital_policy.size(
                    signal.symbol,
                    cast(str, signal.side),
                    float(price),
                    int(base),
                    self,
                    int(self.current_time),
                )
            )
            if base == 0:
                self._last_sizing_reject_reason = "capital_policy_zero"
        return base

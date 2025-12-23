"""Integrity checks for PnL and equity consistency."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .portfolio import Portfolio


@dataclass
class IntegrityResult:
    ok: bool
    reasons: list[str]
    details: dict[str, float | int | None]


def _equity_series(
    equity_records: Sequence[Mapping[str, float | int]] | None,
) -> np.ndarray:
    if not equity_records:
        return np.asarray([], dtype=float)
    values: list[float] = []
    for record in equity_records:
        try:
            values.append(float(record.get("equity", 0.0)))
        except (TypeError, ValueError):
            values.append(0.0)
    return np.asarray(values, dtype=float)


def _equity_is_constant(series: np.ndarray, *, tol_abs: float, tol_rel: float) -> bool:
    if series.size <= 1:
        return True
    min_val = float(series.min())
    max_val = float(series.max())
    scale = max(abs(min_val), abs(max_val), 1.0)
    return abs(max_val - min_val) <= max(tol_abs, tol_rel * scale)


def evaluate_portfolio_integrity(
    portfolio: Portfolio,
    *,
    equity_records: Sequence[Mapping[str, float | int]] | None = None,
    slippage_total: float = 0.0,
    tol_abs: float = 1e-6,
    tol_rel: float = 1e-8,
) -> IntegrityResult:
    equity_records = equity_records or portfolio.equity_curve
    equity_series = _equity_series(equity_records)

    num_trades = len(getattr(portfolio, "trades", None) or [])
    turnover = float(getattr(portfolio, "total_turnover", 0.0) or 0.0)
    commission_total = float(getattr(portfolio, "commission_total", 0.0) or 0.0)
    borrow_cost_total = float(getattr(portfolio, "borrow_cost_total", 0.0) or 0.0)

    market_value, _, unrealized_pnl = portfolio.valuation_snapshot()
    final_equity = float(portfolio.cash + market_value)
    initial_equity = float(portfolio.initial_cash)
    realized_pnl = float(getattr(portfolio, "cum_realized_pnl", 0.0) or 0.0)

    expected_equity = initial_equity + realized_pnl + unrealized_pnl - commission_total
    recon_error = float(final_equity - expected_equity)
    recon_tol = max(tol_abs, tol_rel * max(abs(final_equity), abs(expected_equity), 1.0))

    total_costs = commission_total + borrow_cost_total + float(slippage_total)
    equity_constant = _equity_is_constant(equity_series, tol_abs=tol_abs, tol_rel=tol_rel)

    reasons: list[str] = []
    if abs(recon_error) > recon_tol:
        reasons.append(
            "final_equity does not reconcile with realized/unrealized PnL and costs"
        )
    if turnover > 0 and num_trades == 0:
        reasons.append("turnover > 0 with num_trades == 0 (metrics inconsistent)")
    if (num_trades > 0 or total_costs > 0) and equity_constant:
        reasons.append("equity curve is constant despite trades/costs")

    details = {
        "initial_equity": initial_equity,
        "final_equity": final_equity,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": float(unrealized_pnl),
        "commission_total": commission_total,
        "borrow_cost_total": borrow_cost_total,
        "slippage_total": float(slippage_total),
        "turnover": turnover,
        "num_trades": int(num_trades),
        "equity_min": float(equity_series.min()) if equity_series.size else None,
        "equity_max": float(equity_series.max()) if equity_series.size else None,
        "equity_constant": float(1.0 if equity_constant else 0.0),
        "recon_error": recon_error,
        "recon_tol": recon_tol,
        "total_costs": float(total_costs),
    }

    return IntegrityResult(ok=not reasons, reasons=reasons, details=details)

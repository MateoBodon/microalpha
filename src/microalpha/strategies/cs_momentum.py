from __future__ import annotations

from typing import Dict, List, Sequence

import pandas as pd

from ..events import SignalEvent


class CrossSectionalMomentum:
    """12-1 style cross-sectional momentum with monthly rebalance.

    Emits LONG signals for top `top_frac` fraction by trailing return over
    `lookback_months` excluding the most recent `skip_months`.
    """

    symbols: Sequence[str]
    lookback_months: int = 12
    skip_months: int = 1
    top_frac: float = 0.3

    # State
    price_history: Dict[str, List[float]]
    invested: Dict[str, bool]
    last_month: int | None

    def __init__(self, symbols: Sequence[str], lookback_months: int = 12, skip_months: int = 1, top_frac: float = 0.3):
        self.symbols = list(symbols)
        self.lookback_months = lookback_months
        self.skip_months = skip_months
        self.top_frac = top_frac
        self.price_history = {s: [] for s in self.symbols}
        self.invested = {s: False for s in self.symbols}
        self.last_month = None

    def _rebalance_needed(self, ts_ns: int) -> bool:
        ts = pd.to_datetime(ts_ns)
        month_key = ts.year * 100 + ts.month
        if self.last_month is None or self.last_month != month_key:
            self.last_month = month_key
            return True
        return False

    def _momentum_score(self, prices: List[float]) -> float:
        series = pd.Series(prices)
        # Use monthly sampling by last ~21 trading days per month
        if len(series) < (self.lookback_months + self.skip_months) * 21:
            return float("nan")
        # Approximate monthly sampling using 21-day steps
        monthly = series.iloc[::21]
        if len(monthly) < self.lookback_months + self.skip_months + 1:
            return float("nan")
        # Exclude last skip months
        end = -self.skip_months if self.skip_months > 0 else None
        start = end - self.lookback_months if end is not None else -self.lookback_months
        window = monthly.iloc[start:end]
        if window.empty:
            return float("nan")
        return float(window.iloc[-1] / window.iloc[0] - 1.0)

    def on_market(self, event) -> List[SignalEvent]:
        if event.symbol not in self.symbols:
            return []
        self.price_history[event.symbol].append(event.price)
        signals: List[SignalEvent] = []

        if not self._rebalance_needed(event.timestamp):
            return []

        # Compute scores
        scores: Dict[str, float] = {}
        for sym, prices in self.price_history.items():
            scores[sym] = self._momentum_score(prices)

        # Rank and select top fraction
        valid = {k: v for k, v in scores.items() if pd.notna(v)}
        if not valid:
            return []
        k = max(1, int(len(valid) * self.top_frac))
        top = set(sorted(valid, key=valid.get, reverse=True)[:k])

        # Emit signals: LONG for selected, EXIT for previously invested but not selected
        for sym in self.symbols:
            if sym in top and not self.invested.get(sym, False):
                self.invested[sym] = True
                signals.append(SignalEvent(event.timestamp, sym, "LONG", meta={"qty": 1}))
            elif sym not in top and self.invested.get(sym, False):
                self.invested[sym] = False
                signals.append(SignalEvent(event.timestamp, sym, "EXIT"))

        return signals



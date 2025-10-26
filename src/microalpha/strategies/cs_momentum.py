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
    bottom_frac: float | None = None
    long_short: bool = True

    # State
    price_history: Dict[str, List[float]]
    invested: Dict[str, int]
    last_month: int | None

    def __init__(
        self,
        symbols: Sequence[str],
        lookback_months: int = 12,
        skip_months: int = 1,
        top_frac: float = 0.3,
        bottom_frac: float | None = None,
        long_short: bool = True,
        warmup_history: Dict[str, Sequence[float]] | None = None,
    ):
        self.symbols = list(symbols)
        self.lookback_months = lookback_months
        self.skip_months = skip_months
        self.top_frac = top_frac
        self.bottom_frac = bottom_frac if bottom_frac is not None else top_frac
        self.long_short = bool(long_short)
        self.price_history = {
            s: list(warmup_history.get(s, [])) if warmup_history else []
            for s in self.symbols
        }
        # position state: 1 long, -1 short, 0 flat
        self.invested = {s: 0 for s in self.symbols}
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

        # Rank and select top/bottom fractions
        valid = {k: v for k, v in scores.items() if pd.notna(v)}
        if not valid:
            return []
        k_top = max(1, int(len(valid) * self.top_frac))
        top = set(sorted(valid, key=lambda sym: valid[sym], reverse=True)[:k_top])
        bottom: set[str] = set()
        if self.long_short and self.bottom_frac and self.bottom_frac > 0:
            k_bot = max(1, int(len(valid) * self.bottom_frac))
            bottom = set(sorted(valid, key=lambda sym: valid[sym])[:k_bot])

        # Emit signals: LONG for top, SHORT for bottom, EXIT when leaving sets
        for sym in self.symbols:
            st = self.invested.get(sym, 0)
            if sym in top:
                if st <= 0:
                    # exit short if any
                    if st < 0:
                        signals.append(SignalEvent(event.timestamp, sym, "EXIT"))
                    self.invested[sym] = 1
                    signals.append(
                        SignalEvent(event.timestamp, sym, "LONG", meta={"qty": 1})
                    )
            elif sym in bottom and self.long_short:
                if st >= 0:
                    if st > 0:
                        signals.append(SignalEvent(event.timestamp, sym, "EXIT"))
                    self.invested[sym] = -1
                    signals.append(
                        SignalEvent(event.timestamp, sym, "SHORT", meta={"qty": 1})
                    )
            else:
                if st != 0:
                    self.invested[sym] = 0
                    signals.append(SignalEvent(event.timestamp, sym, "EXIT"))

        return signals

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd

from ..events import MarketEvent, SignalEvent


@dataclass
class CrossSectionalReversal:
    symbol_universe: Sequence[str]
    lookback_days: int = 5
    top_frac: float = 0.2
    vol_target: float = 0.10
    warmup_prices: Dict[str, List[float]] | None = None

    def __post_init__(self) -> None:
        self.prices: Dict[str, List[float]] = (
            {s: list(self.warmup_prices.get(s, [])) for s in self.symbol_universe}
            if self.warmup_prices
            else {s: [] for s in self.symbol_universe}
        )
        self.current_holds: set[str] = set()

    def on_market_batch(self, events: Sequence[MarketEvent]):
        for e in events:
            if e.symbol in self.prices:
                self.prices[e.symbol].append(e.price)

        if any(len(self.prices[s]) < (self.lookback_days + 2) for s in self.symbol_universe):
            return []

        rev: Dict[str, float] = {}
        for s in self.symbol_universe:
            p = pd.Series(self.prices[s])
            r = p.pct_change(self.lookback_days).iloc[-1]
            rev[s] = float(-r)

        n = max(1, int(len(self.symbol_universe) * self.top_frac))
        top = set(sorted(rev, key=rev.get, reverse=True)[:n])

        annual = np.sqrt(252.0)
        weights: Dict[str, float] = {}
        for s in top:
            ret = pd.Series(self.prices[s]).pct_change().dropna()
            vol = float(ret.rolling(21).std().iloc[-1]) if len(ret) >= 21 else 0.0
            target_daily = self.vol_target / annual
            w = target_daily / vol if vol > 0 else 0.0
            weights[s] = max(0.0, min(w, 1.0))

        ts = events[0].timestamp
        signals: List[SignalEvent] = []

        to_exit = self.current_holds - top
        for s in to_exit:
            signals.append(SignalEvent(ts, s, "EXIT"))

        for s in top:
            qty_hint = int(100 * weights.get(s, 0.0))
            if qty_hint <= 0:
                continue
            signals.append(SignalEvent(ts, s, "LONG", meta={"qty": qty_hint}))

        self.current_holds = top
        return signals



from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd

from ..events import MarketEvent, SignalEvent


@dataclass
class CrossSectionalMomentum:
    symbol_universe: Sequence[str]
    lookback_months: int = 12
    skip_months: int = 1
    top_frac: float = 0.2
    vol_target: float = 0.10  # annualised
    warmup_prices: Dict[str, List[float]] | None = None

    def __post_init__(self) -> None:
        self.prices: Dict[str, List[float]] = (
            {s: list(self.warmup_prices.get(s, [])) for s in self.symbol_universe}
            if self.warmup_prices
            else {s: [] for s in self.symbol_universe}
        )
        self.current_holds: set[str] = set()

    def on_market_batch(self, events: Sequence[MarketEvent]) -> List[SignalEvent]:
        # Ingest prices
        for e in events:
            if e.symbol in self.prices:
                self.prices[e.symbol].append(e.price)

        # Require enough history for LB + skip
        lb = self.lookback_months * 21
        skip = self.skip_months * 21
        min_len = lb + skip + 1
        if any(len(self.prices[s]) < min_len for s in self.symbol_universe):
            return []

        # Compute momentum (price[t-skip] / price[t-skip-lb] - 1)
        mom: Dict[str, float] = {}
        for s in self.symbol_universe:
            p = pd.Series(self.prices[s])
            p_t = p.iloc[-(skip + 1)]
            p_lb = p.iloc[-(skip + lb + 1)]
            mom[s] = float(p_t / p_lb - 1.0) if p_lb != 0 else 0.0

        # Rank and select top fraction
        n = max(1, int(len(self.symbol_universe) * self.top_frac))
        top = set(sorted(mom, key=mom.get, reverse=True)[:n])

        # Vol targeting via simple per-asset rolling vol (21-day) to reach vol_target
        annual = np.sqrt(252.0)
        weights: Dict[str, float] = {}
        for s in top:
            ret = pd.Series(self.prices[s]).pct_change().dropna()
            vol = float(ret.rolling(21).std().iloc[-1]) if len(ret) >= 21 else 0.0
            # avoid division by zero
            target_daily = self.vol_target / annual
            w = target_daily / vol if vol > 0 else 0.0
            weights[s] = max(0.0, min(w, 1.0))

        # Convert weights to integer share hints (qty) via meta, equalized to 100 shares scale
        ts = events[0].timestamp
        signals: List[SignalEvent] = []

        # Exit losers not in top
        to_exit = self.current_holds - top
        for s in to_exit:
            signals.append(SignalEvent(ts, s, "EXIT"))

        # Enter/maintain winners
        for s in top:
            qty_hint = int(100 * weights.get(s, 0.0))
            if qty_hint <= 0:
                continue
            signals.append(SignalEvent(ts, s, "LONG", meta={"qty": qty_hint}))

        self.current_holds = top
        return signals



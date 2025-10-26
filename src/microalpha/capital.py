"""Capital allocation policies for multi-asset sizing.

Policies transform a base order quantity into a risk-aware size per symbol.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


class DataHandlerLike(Protocol):
    def get_recent_prices(
        self, symbol: str, end_timestamp: int, lookback: int
    ) -> list[float]: ...


class PortfolioLike(Protocol):
    data_handler: DataHandlerLike
    last_equity: float | None


class CapitalPolicy(Protocol):
    def size(
        self,
        symbol: str,
        side: str,
        price: float,
        base_qty: int,
        portfolio: PortfolioLike,
        timestamp: int | None,
    ) -> int: ...


@dataclass
class VolatilityScaledPolicy:
    """Scale base order size inversely to recent volatility.

    - lookback: number of observations (e.g., days) to estimate volatility
    - target_dollar_vol: the target dollar volatility per new position
    - min_qty: floor on final absolute quantity when base_qty > 0
    """

    lookback: int = 20
    target_dollar_vol: float = 10_000.0
    min_qty: int = 1

    def size(
        self,
        symbol: str,
        side: str,
        price: float,
        base_qty: int,
        portfolio: PortfolioLike,
        timestamp: int | None,
    ) -> int:
        if base_qty <= 0:
            return base_qty
        if timestamp is None:
            return base_qty

        prices = portfolio.data_handler.get_recent_prices(
            symbol, timestamp, self.lookback
        )
        if len(prices) < 2 or price <= 0:
            return base_qty

        arr = np.asarray(prices, dtype=float)
        ret = np.diff(arr) / arr[:-1]
        vol = float(np.std(ret, ddof=0))
        if vol <= 0:
            return base_qty

        # Dollar vol of base trade; scale to target_dollar_vol
        dollar_vol = price * base_qty * vol
        if dollar_vol <= 0:
            return base_qty
        scale = self.target_dollar_vol / dollar_vol
        sized = int(np.floor(base_qty * scale))
        if base_qty > 0:
            sized = max(sized, self.min_qty)
        return sized

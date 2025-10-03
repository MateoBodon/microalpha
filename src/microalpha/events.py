"""Core event types exchanged between components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional


@dataclass(frozen=True)
class MarketEvent:
    timestamp: int
    symbol: str
    price: float
    volume: float


@dataclass(frozen=True)
class SignalEvent:
    timestamp: int
    symbol: str
    side: Literal["LONG", "SHORT", "EXIT"]
    meta: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class OrderEvent:
    timestamp: int
    symbol: str
    qty: int
    side: Literal["BUY", "SELL"]


@dataclass(frozen=True)
class FillEvent:
    timestamp: int
    symbol: str
    qty: int
    price: float
    commission: float
    slippage: float


class LookaheadError(Exception):
    """Raised when an operation would violate temporal ordering."""

    pass


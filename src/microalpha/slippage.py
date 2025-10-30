"""Slippage and market impact models."""

from __future__ import annotations

import math
from typing import Dict, Mapping

from .market_metadata import SymbolMeta

__all__ = [
    "SlippageModel",
    "VolumeSlippageModel",
    "LinearImpact",
    "SquareRootImpact",
    "LinearPlusSqrtImpact",
]


class SlippageModel:
    """Base class for slippage models with optional symbol metadata support."""

    def __init__(self, *, metadata: Mapping[str, SymbolMeta] | None = None) -> None:
        self._metadata: Dict[str, SymbolMeta] = {}
        if metadata:
            self.update_metadata(metadata)

    def calculate_slippage(
        self,
        quantity: int,
        price: float,
        *,
        symbol: str | None = None,
    ) -> float:
        """Return the signed price delta for the trade."""

        raise NotImplementedError

    # -- metadata helpers -------------------------------------------------
    def update_metadata(self, metadata: Mapping[str, SymbolMeta]) -> None:
        for symbol, meta in metadata.items():
            self._metadata[symbol.upper()] = meta

    def get_metadata(self, symbol: str | None) -> SymbolMeta:
        if symbol is None:
            return SymbolMeta()
        return self._metadata.get(symbol.upper(), SymbolMeta())


class VolumeSlippageModel(SlippageModel):
    """Legacy quadratic volume model retained for backward compatibility."""

    def __init__(
        self, price_impact: float = 0.0001, *, metadata: Mapping[str, SymbolMeta] | None = None
    ) -> None:
        super().__init__(metadata=metadata)
        self.price_impact = float(price_impact)

    def calculate_slippage(
        self, quantity: int, price: float, *, symbol: str | None = None
    ) -> float:
        magnitude = self.price_impact * (abs(quantity) ** 2)
        return math.copysign(magnitude, quantity)


class _ImpactBase(SlippageModel):
    def __init__(
        self,
        *,
        metadata: Mapping[str, SymbolMeta] | None = None,
        default_adv: float = 1_000_000.0,
        default_spread_bps: float = 5.0,
        spread_floor_multiplier: float = 0.5,
    ) -> None:
        super().__init__(metadata=metadata)
        self.default_adv = float(default_adv)
        self.default_spread_bps = float(max(default_spread_bps, 0.0))
        self.spread_floor_multiplier = float(max(spread_floor_multiplier, 0.0))

    def _effective_adv(self, meta: SymbolMeta) -> float:
        adv = meta.adv if meta.adv and meta.adv > 0 else None
        return adv if adv is not None else self.default_adv

    def _effective_spread_bps(self, meta: SymbolMeta) -> float:
        spread = meta.spread_bps if meta.spread_bps and meta.spread_bps > 0 else None
        return spread if spread is not None else self.default_spread_bps

    def _apply_floor(self, impact_bps: float, spread_bps: float) -> float:
        floor = self.spread_floor_multiplier * spread_bps
        return max(floor, impact_bps)

    @staticmethod
    def _bps_to_price(impact_bps: float, price: float, quantity: int) -> float:
        magnitude = (impact_bps / 10_000.0) * price
        return math.copysign(magnitude, quantity)


class LinearImpact(_ImpactBase):
    """Linear impact respecting a spread floor."""

    def __init__(
        self,
        k_lin: float = 25.0,
        *,
        metadata: Mapping[str, SymbolMeta] | None = None,
        default_adv: float = 1_000_000.0,
        default_spread_bps: float = 5.0,
        spread_floor_multiplier: float = 0.5,
    ) -> None:
        super().__init__(
            metadata=metadata,
            default_adv=default_adv,
            default_spread_bps=default_spread_bps,
            spread_floor_multiplier=spread_floor_multiplier,
        )
        self.k_lin = float(max(k_lin, 0.0))

    def calculate_slippage(
        self, quantity: int, price: float, *, symbol: str | None = None
    ) -> float:
        meta = self.get_metadata(symbol)
        adv = self._effective_adv(meta)
        spread_bps = self._effective_spread_bps(meta)
        ratio = abs(quantity) / max(adv, 1e-9)
        impact_bps = self._apply_floor(self.k_lin * ratio, spread_bps)
        return self._bps_to_price(impact_bps, price, quantity)


class SquareRootImpact(_ImpactBase):
    """Square-root impact with spread floor."""

    def __init__(
        self,
        eta: float = 100.0,
        *,
        metadata: Mapping[str, SymbolMeta] | None = None,
        default_adv: float = 1_000_000.0,
        default_spread_bps: float = 5.0,
        spread_floor_multiplier: float = 0.5,
    ) -> None:
        super().__init__(
            metadata=metadata,
            default_adv=default_adv,
            default_spread_bps=default_spread_bps,
            spread_floor_multiplier=spread_floor_multiplier,
        )
        self.eta = float(max(eta, 0.0))

    def calculate_slippage(
        self, quantity: int, price: float, *, symbol: str | None = None
    ) -> float:
        meta = self.get_metadata(symbol)
        adv = self._effective_adv(meta)
        spread_bps = self._effective_spread_bps(meta)
        ratio = abs(quantity) / max(adv, 1e-9)
        impact_bps = self._apply_floor(self.eta * math.sqrt(ratio), spread_bps)
        return self._bps_to_price(impact_bps, price, quantity)


class LinearPlusSqrtImpact(_ImpactBase):
    """Hybrid linear + square-root impact with spread floor."""

    def __init__(
        self,
        k_lin: float = 25.0,
        eta: float = 75.0,
        *,
        metadata: Mapping[str, SymbolMeta] | None = None,
        default_adv: float = 1_000_000.0,
        default_spread_bps: float = 5.0,
        spread_floor_multiplier: float = 0.5,
    ) -> None:
        super().__init__(
            metadata=metadata,
            default_adv=default_adv,
            default_spread_bps=default_spread_bps,
            spread_floor_multiplier=spread_floor_multiplier,
        )
        self.k_lin = float(max(k_lin, 0.0))
        self.eta = float(max(eta, 0.0))

    def calculate_slippage(
        self, quantity: int, price: float, *, symbol: str | None = None
    ) -> float:
        meta = self.get_metadata(symbol)
        adv = self._effective_adv(meta)
        spread_bps = self._effective_spread_bps(meta)
        ratio = abs(quantity) / max(adv, 1e-9)
        linear_bps = self.k_lin * ratio
        sqrt_bps = self.eta * math.sqrt(ratio)
        impact_bps = self._apply_floor(linear_bps + sqrt_bps, spread_bps)
        return self._bps_to_price(impact_bps, price, quantity)

"""Utility helpers for symbol-level market metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional

import pandas as pd

__all__ = ["SymbolMeta", "load_symbol_meta", "merge_symbol_meta"]


@dataclass(frozen=True)
class SymbolMeta:
    """Snapshot of per-symbol liquidity and financing characteristics."""

    adv: float | None = None
    spread_bps: float | None = None
    borrow_fee_annual_bps: float | None = None
    volatility_bps: float | None = None

    def with_overrides(
        self,
        *,
        adv: float | None = None,
        spread_bps: float | None = None,
        borrow_fee_annual_bps: float | None = None,
        volatility_bps: float | None = None,
    ) -> "SymbolMeta":
        """Return a copy of the metadata with the provided overrides."""

        return SymbolMeta(
            adv=adv if adv is not None else self.adv,
            spread_bps=spread_bps if spread_bps is not None else self.spread_bps,
            borrow_fee_annual_bps=(
                borrow_fee_annual_bps
                if borrow_fee_annual_bps is not None
                else self.borrow_fee_annual_bps
            ),
            volatility_bps=(
                volatility_bps
                if volatility_bps is not None
                else self.volatility_bps
            ),
        )


def load_symbol_meta(path: str | Path) -> Dict[str, SymbolMeta]:
    """Load symbol metadata from a CSV file.

    Expected columns::

        symbol, adv, borrow_fee_annual_bps, spread_bps [, volatility_bps]

    Additional columns are ignored. Missing columns default to ``None``.
    Symbols are upper-cased to ensure consistency with the rest of the engine.
    """

    csv_path = Path(path).expanduser().resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"Symbol metadata CSV not found: {csv_path}")

    frame = pd.read_csv(csv_path)
    if "symbol" not in frame.columns:
        raise ValueError("Symbol metadata CSV must include a 'symbol' column.")

    metadata: Dict[str, SymbolMeta] = {}
    for row in frame.itertuples(index=False):
        symbol = str(row.symbol).upper()
        adv = getattr(row, "adv", None)
        spread_bps = getattr(row, "spread_bps", None)
        borrow_fee = getattr(row, "borrow_fee_annual_bps", None)
        vol_bps = getattr(row, "volatility_bps", None)
        metadata[symbol] = SymbolMeta(
            adv=_coerce_float_or_none(adv),
            spread_bps=_coerce_float_or_none(spread_bps),
            borrow_fee_annual_bps=_coerce_float_or_none(borrow_fee),
            volatility_bps=_coerce_float_or_none(vol_bps),
        )
    return metadata


def merge_symbol_meta(
    *collections: Mapping[str, SymbolMeta] | Iterable[tuple[str, SymbolMeta]]
) -> Dict[str, SymbolMeta]:
    """Merge multiple symbol metadata mappings."""

    merged: Dict[str, SymbolMeta] = {}
    for collection in collections:
        items: Iterable[tuple[str, SymbolMeta]]
        if isinstance(collection, Mapping):
            items = collection.items()
        else:
            items = collection
        for symbol, meta in items:
            merged[symbol.upper()] = meta
    return merged


def _coerce_float_or_none(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

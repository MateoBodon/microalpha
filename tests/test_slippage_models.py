from __future__ import annotations

import math

import pytest

from microalpha.market_metadata import SymbolMeta
from microalpha.slippage import (
    LinearImpact,
    LinearPlusSqrtImpact,
    SquareRootImpact,
    VolumeSlippageModel,
)


def test_linear_impact_respects_spread_floor():
    metadata = {"XYZ": SymbolMeta(adv=1_000_000.0, spread_bps=10.0)}
    model = LinearImpact(k_lin=25.0, metadata=metadata)

    price = 20.0
    qty = 1_000
    impact = model.calculate_slippage(qty, price, symbol="XYZ")
    expected_floor = (0.5 * metadata["XYZ"].spread_bps / 10_000.0) * price
    assert math.isclose(impact, expected_floor, rel_tol=1e-9)

    sell_impact = model.calculate_slippage(-qty, price, symbol="XYZ")
    assert math.isclose(sell_impact, -expected_floor, rel_tol=1e-9)


def test_sqrt_impact_grows_with_quantity():
    metadata = {"ABC": SymbolMeta(adv=500_000.0, spread_bps=4.0)}
    model = SquareRootImpact(eta=120.0, metadata=metadata)

    price = 50.0
    qty_small = 1_000
    qty_large = 20_000

    impact_small = model.calculate_slippage(qty_small, price, symbol="ABC")
    impact_large = model.calculate_slippage(qty_large, price, symbol="ABC")

    assert impact_large > impact_small
    assert impact_small > 0


def test_linear_plus_sqrt_combines_components():
    metadata = {"MNO": SymbolMeta(adv=2_000_000.0, spread_bps=6.0)}
    model = LinearPlusSqrtImpact(k_lin=40.0, eta=80.0, metadata=metadata)

    price = 35.0
    qty = 50_000
    impact = model.calculate_slippage(qty, price, symbol="MNO")

    adv = metadata["MNO"].adv
    assert adv is not None
    spread = metadata["MNO"].spread_bps or 0.0
    ratio = qty / adv
    expected_bps = max(
        spread * 0.5,
        40.0 * ratio + 80.0 * math.sqrt(ratio),
    )
    expected_price = expected_bps / 10_000.0 * price
    assert math.isclose(impact, expected_price, rel_tol=1e-9)


@pytest.mark.parametrize("qty", [10, -10])
def test_volume_slippage_model_remains_signed(qty: int):
    model = VolumeSlippageModel(price_impact=0.002)
    impact = model.calculate_slippage(qty, price=100.0, symbol="ANY")
    assert math.copysign(1.0, impact) == math.copysign(1.0, qty)

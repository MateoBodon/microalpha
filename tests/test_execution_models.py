import math

from microalpha.execution import KyleLambda, SquareRootImpact


class _DummyDataHandler:
    def get_latest_price(self, symbol, timestamp):  # pragma: no cover - not used here
        return 100.0


def test_sqrt_impact_slippage_increases_sublinearly():
    handler = _DummyDataHandler()
    model = SquareRootImpact(handler, price_impact=0.02)
    small_qty = 100
    big_qty = 10_000

    small_slip = model._slippage(small_qty)
    big_slip = model._slippage(big_qty)

    assert big_slip > small_slip
    assert math.isclose(small_slip, 0.02 * math.sqrt(small_qty))
    assert (big_slip / small_slip) < (big_qty / small_qty)


def test_kyle_lambda_linear_slippage():
    handler = _DummyDataHandler()
    model = KyleLambda(handler, lam=1e-5)

    assert model._slippage(2_000) == 0.02
    assert model._slippage(0) == 0.0

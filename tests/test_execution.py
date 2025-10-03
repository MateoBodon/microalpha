import math

from microalpha.events import OrderEvent
from microalpha.execution import Executor, KyleLambda, SquareRootImpact, TWAP


class StubDataHandler:
    def __init__(self, prices, future_map):
        self.prices = prices
        self.future_map = future_map

    def get_future_timestamps(self, start_timestamp, n):
        futures = self.future_map.get(start_timestamp, [])
        return futures[:n]

    def get_latest_price(self, symbol, timestamp):
        return self.prices.get(timestamp)


class StubOrder(OrderEvent):
    def __init__(self, timestamp, qty, side="BUY"):
        super().__init__(timestamp=timestamp, symbol="SPY", qty=qty, side=side)


def test_linear_executor_produces_expected_slippage_and_commission():
    prices = {2: 100.0}
    futures = {1: [2]}
    data = StubDataHandler(prices, futures)
    executor = Executor(data_handler=data, price_impact=0.1, commission=0.01)

    order = StubOrder(timestamp=1, qty=10, side="BUY")
    fill = executor.execute(order, 1)

    assert math.isclose(fill.price, 101.0)
    assert math.isclose(fill.slippage, 1.0)
    assert math.isclose(fill.commission, 0.1)


def test_square_root_executor_uses_root_volume():
    prices = {2: 50.0}
    futures = {1: [2]}
    data = StubDataHandler(prices, futures)
    executor = SquareRootImpact(data_handler=data, price_impact=0.25, commission=0.0)

    order = StubOrder(timestamp=1, qty=16, side="BUY")
    fill = executor.execute(order, 1)

    assert math.isclose(fill.slippage, 0.25 * 4)
    assert math.isclose(fill.price, 50.0 + fill.slippage)


def test_kyle_lambda_executor_scales_with_qty():
    prices = {2: 80.0}
    futures = {1: [2]}
    data = StubDataHandler(prices, futures)
    executor = KyleLambda(data_handler=data, lam=0.2, commission=0.0)

    order = StubOrder(timestamp=1, qty=5, side="BUY")
    fill = executor.execute(order, 1)

    assert math.isclose(fill.slippage, 1.0)
    assert math.isclose(fill.price, 81.0)


def test_twap_executor_averages_partial_fills():
    prices = {2: 100.0, 3: 102.0}
    futures = {1: [2, 3]}
    data = StubDataHandler(prices, futures)
    executor = TWAP(data_handler=data, price_impact=0.0, commission=0.0, slices=2)

    order = StubOrder(timestamp=1, qty=4, side="BUY")
    fill = executor.execute(order, 1)

    assert fill.qty == 4
    expected_price = (100.0 * 2 + 102.0 * 2) / 4
    assert math.isclose(fill.price, expected_price)

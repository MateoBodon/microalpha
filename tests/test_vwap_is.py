from __future__ import annotations

import math

from microalpha.events import OrderEvent
from microalpha.execution import VWAP, ImplementationShortfall


class StubData:
    def __init__(self, price_map, vol_map, futures):
        self.price_map = price_map
        self.vol_map = vol_map
        self.futures = futures

    def get_future_timestamps(self, start_timestamp, n):
        return self.futures[:n]

    def get_latest_price(self, symbol, timestamp):
        return float(self.price_map[timestamp])

    def get_volume_at(self, symbol, timestamp):
        return float(self.vol_map.get(timestamp, 1.0))


def test_vwap_allocates_by_volume():
    # Volumes 1:3 => shares should allocate 1/4 and 3/4
    price_map = {2: 100.0, 3: 200.0}
    vol_map = {2: 10.0, 3: 30.0}
    data = StubData(price_map, vol_map, [2, 3])
    vwap = VWAP(data_handler=data, price_impact=0.0, commission=0.0, slices=2)
    order = OrderEvent(1, "SPY", qty=40, side="BUY")
    fill = vwap.execute(order, 1)
    assert fill.qty == 40
    # Expected weighted avg price
    expected = (100.0 * 10 + 200.0 * 30) / (10 + 30)
    assert math.isclose(fill.price, expected)


def test_is_front_loads_by_urgency():
    price_map = {2: 100.0, 3: 200.0, 4: 300.0}
    vol_map = {}
    data = StubData(price_map, vol_map, [2, 3, 4])
    is_exec = ImplementationShortfall(
        data_handler=data, price_impact=0.0, commission=0.0, slices=3, urgency=0.5
    )
    order = OrderEvent(1, "SPY", qty=9, side="BUY")
    fill = is_exec.execute(order, 1)
    assert fill.qty == 9
    # Should be closer to early prices than late
    assert fill.price < 200.0

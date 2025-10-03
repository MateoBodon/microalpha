# tests/test_data.py
from pathlib import Path

import pandas as pd

from microalpha.data import CsvDataHandler
from microalpha.events import MarketEvent


def test_csv_data_handler_streams_events(tmp_path: Path):
    """
    Tests if the CsvDataHandler correctly reads a CSV and yields MarketEvents.
    `tmp_path` is a pytest fixture that provides a temporary directory.
    """
    # 1. Arrange: Create a dummy CSV file in the temp directory
    test_csv_dir = tmp_path
    symbol = "TEST_SYMBOL"
    test_csv_path = test_csv_dir / f"{symbol}.csv"

    dates = pd.to_datetime(["2025-09-23", "2025-09-24"])
    df = pd.DataFrame(index=dates, data={"close": [100.0, 101.5], "volume": [10, 20]})
    df.to_csv(test_csv_path)

    # 2. Act: Initialize the handler and stream events
    handler = CsvDataHandler(csv_dir=test_csv_dir, symbol=symbol)
    events_generator = handler.stream()
    events_list = list(events_generator)

    # 3. Assert: Check if the generated events are correct
    assert len(events_list) == 2

    assert isinstance(events_list[0], MarketEvent)
    assert events_list[0].symbol == symbol
    assert events_list[0].price == 100.0
    assert events_list[0].timestamp == pd.Timestamp("2025-09-23").value
    assert events_list[0].volume == 10

    assert events_list[1].price == 101.5
    assert events_list[1].volume == 20

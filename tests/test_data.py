# tests/test_data.py
from pathlib import Path

import pandas as pd

from microalpha.data import CsvDataHandler, MultiCsvDataHandler
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


def test_multi_csv_data_handler_streams_batches(tmp_path: Path):
    # Arrange: create two symbols with overlapping dates
    data_dir = tmp_path
    dates = pd.to_datetime(["2025-01-01", "2025-01-02", "2025-01-03"])
    df_a = pd.DataFrame(index=dates, data={"close": [10.0, 11.0, 12.0]})
    df_b = pd.DataFrame(index=dates[[0, 2]], data={"close": [20.0, 22.0]})
    df_a.to_csv(data_dir / "AAA.csv")
    df_b.to_csv(data_dir / "BBB.csv")

    handler = MultiCsvDataHandler(csv_dir=data_dir, symbols=["AAA", "BBB"])
    batches = list(handler.stream_batches())

    # Expect batches at 3 timestamps
    assert len(batches) == 3
    # First batch has both AAA and BBB
    assert {e.symbol for e in batches[0]} == {"AAA", "BBB"}
    # Second batch only AAA (BBB missing 2025-01-02)
    assert {e.symbol for e in batches[1]} == {"AAA"}
    # Third batch both again
    assert {e.symbol for e in batches[2]} == {"AAA", "BBB"}

# microalpha/data.py
from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Optional, cast

import pandas as pd

from .events import MarketEvent


class DataHandler:
    """
    Base class for data handlers.
    """

    def stream(self) -> Iterator[MarketEvent]:
        raise NotImplementedError("stream() must be implemented")


class CsvDataHandler(DataHandler):
    def __init__(self, csv_dir: Path, symbol: str, mode: str = "exact"):
        self.csv_dir = csv_dir
        self.symbol = symbol
        self.file_path = self.csv_dir / f"{self.symbol}.csv"
        # load the full dataset here
        self.full_data = self._load_data()
        # hold the subset of data for a specific backtest period
        self.data = self.full_data
        self.mode = mode

    def _load_data(self) -> Optional[pd.DataFrame]:
        """Loads the entire CSV into a dataframe, returns it."""
        try:
            return pd.read_csv(self.file_path, index_col=0, parse_dates=True)
        except FileNotFoundError:
            print(f"Error: Data file not found at {self.file_path}")
            return None

    def set_date_range(self, start_date, end_date):
        """
        Sets the active data to a subset of the full dataset.
        This is the key method for walk-forward validation.
        """
        if self.full_data is None:
            self.data = None
        else:
            self.data = self.full_data.loc[start_date:end_date]

    def stream(self) -> Iterator[MarketEvent]:
        """Yield ``MarketEvent`` instances ordered by timestamp."""
        if self.data is None:
            return

        for row in self.data.sort_index().itertuples():
            ts_int = self._to_int_timestamp(row.Index)
            volume = float(getattr(row, "volume", 0.0))
            price = cast(float, row.close)
            yield MarketEvent(ts_int, self.symbol, price, volume)

    def get_latest_price(self, symbol: str, timestamp: int):
        """Return the price for ``symbol`` according to the configured lookup mode."""
        if symbol != self.symbol or self.data is None:
            return None

        ts = self._to_datetime(timestamp)

        if self.mode == "exact":
            try:
                close_value = cast(float, self.data.loc[ts, "close"])
                return close_value
            except KeyError:
                return None

        idx = self.data.index.searchsorted(ts, side="right") - 1
        if idx < 0:
            return None
        close_value = cast(float, self.data.iloc[idx]["close"])
        return close_value

    def get_future_timestamps(self, start_timestamp: int, n: int) -> List[int]:
        """
        Gets the next `n` timestamps from the data starting after a given timestamp.
        Used by the TWAP execution handler to schedule child orders.
        """
        if self.data is None:
            return []

        # Get the index of all future dates
        ts = self._to_datetime(start_timestamp)
        future_dates = self.data.index[self.data.index > ts]

        # Return the next n dates, or fewer if we are at the end of the data
        return [self._to_int_timestamp(idx) for idx in future_dates[:n]]

    @staticmethod
    def _to_int_timestamp(value) -> int:
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, pd.Timestamp):
            return int(value.value)
        return int(pd.Timestamp(value).value)

    @staticmethod
    def _to_datetime(value) -> pd.Timestamp:
        if isinstance(value, pd.Timestamp):
            return value
        return pd.to_datetime(value)

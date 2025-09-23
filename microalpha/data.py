# microalpha/data.py
from pathlib import Path

import pandas as pd

from .events import MarketEvent


class DataHandler:
    """
    Base class for data handlers.
    """
    def stream_events(self):
        raise NotImplementedError("stream_events() must be implemented")

class CsvDataHandler(DataHandler):
    def __init__(self, csv_dir: Path, symbol: str):
        self.csv_dir = csv_dir
        self.symbol = symbol
        self.file_path = self.csv_dir / f"{self.symbol}.csv"
        # load the full dataset here
        self.full_data = self._load_data()
        # hold the subset of data for a specific backtest period
        self.data = self.full_data

    def _load_data(self) -> pd.DataFrame | None:
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

    def stream_events(self):
        """Yields MarketEvents from the currently active dataframe."""
        if self.data is None:
            return
        for row in self.data.itertuples():
            yield MarketEvent(
                timestamp=row.Index,
                symbol=self.symbol,
                price=float(row.close)
            )

    def get_latest_price(self, symbol: str, timestamp: pd.Timestamp):
        """Returns the last known price for a symbol at or before a given timestamp."""
        if symbol != self.symbol or self.data is None:
            return None

        try:
            # Get the price from the 'close' of the bar at the given timestamp
            return self.data.loc[timestamp]['close']
        except KeyError:
            # If no exact timestamp match, you might want to forward-fill or return None
            # For simplicity, we'll just return None if no data is available.
            return None


    def get_future_timestamps(self, start_timestamp: pd.Timestamp, n: int):
        """
        Gets the next `n` timestamps from the data starting after a given timestamp.
        Used by the TWAP execution handler to schedule child orders.
        """
        if self.data is None:
            return []

        # Get the index of all future dates
        future_dates = self.data.index[self.data.index > start_timestamp]

        # Return the next n dates, or fewer if we are at the end of the data
        return future_dates[:n].tolist()

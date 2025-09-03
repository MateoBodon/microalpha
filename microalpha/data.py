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
        self._load_data()

    def _load_data(self):
        """Loads the entire CSV into a dataframe. Ok for small datasets."""
        try:
            self.data = pd.read_csv(self.file_path, index_col=0, parse_dates=True)
        except FileNotFoundError:
            self.data = None
            print(f"Error: Data file not found at {self.file_path}")

    def stream_events(self):
        """Yields MarketEvents from the pre-loaded dataframe."""
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
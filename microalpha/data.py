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
    """
    Reads CSV files and streams market data events.
    """
    def __init__(self, csv_dir: Path, symbol: str):
        self.csv_dir = csv_dir
        self.symbol = symbol
        self.file_path = self.csv_dir / f"{self.symbol}.csv"

    def stream_events(self):
        """
        Reads the CSV file row by row and yields a MarketEvent for each.
        Using a generator is memory-efficient.
        """
        try:
            df = pd.read_csv(self.file_path, index_col=0, parse_dates=True)
        except FileNotFoundError:
            print(f"Error: Data file not found at {self.file_path}")
            return

        for row in df.itertuples():
            yield MarketEvent(
                timestamp=row.Index,
                symbol=self.symbol,
                price=float(row.close) # Assuming a 'close' column
            )
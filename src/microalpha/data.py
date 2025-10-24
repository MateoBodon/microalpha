# microalpha/data.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, cast

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


class MultiCsvDataHandler(DataHandler):
    """
    Multi-asset data handler that loads multiple symbol CSVs and produces a merged
    chronological stream of MarketEvents. Provides optional batched iteration via
    ``stream_batches`` for cross-sectional strategies.

    CSV format matches ``CsvDataHandler``: first column is a datetime index, must
    contain a ``close`` column and optional ``volume``.
    """

    def __init__(
        self,
        csv_dir: Path,
        symbols: Sequence[str] | None = None,
        *,
        universe_path: Path | None = None,
        mode: str = "exact",
    ):
        self.csv_dir = csv_dir
        if symbols is None and universe_path is None:
            raise ValueError("Provide either symbols or universe_path")
        if symbols is None and universe_path is not None:
            raw = Path(universe_path).read_text(encoding="utf-8")
            symbols = [line.strip() for line in raw.splitlines() if line.strip()]
        if not symbols:
            raise ValueError("No symbols provided for MultiCsvDataHandler")

        self.symbols: List[str] = list(symbols or [])
        self.mode = mode
        self.data_by_symbol: Dict[str, Optional[pd.DataFrame]] = {}
        for sym in self.symbols:
            self.data_by_symbol[sym] = self._load_symbol(sym)

        # Build the global union index (sorted)
        indices = [df.index for df in self.data_by_symbol.values() if df is not None]
        self.union_index = (
            pd.Index(sorted(set().union(*[set(idx) for idx in indices])))
            if indices
            else pd.Index([])
        )

    def _load_symbol(self, symbol: str) -> Optional[pd.DataFrame]:
        path = self.csv_dir / f"{symbol}.csv"
        try:
            return pd.read_csv(path, index_col=0, parse_dates=True)
        except FileNotFoundError:
            print(f"Error: Data file not found for {symbol} at {path}")
            return None

    def stream(self) -> Iterator[MarketEvent]:
        """Yield MarketEvents across all symbols ordered by timestamp."""
        for ts in self.union_index:
            for sym in self.symbols:
                df = self.data_by_symbol.get(sym)
                if df is None:
                    continue
                if ts in df.index:
                    row = df.loc[ts]
                    price = cast(float, row["close"])
                    volume = float(row["volume"]) if "volume" in df.columns else 0.0
                    yield MarketEvent(self._to_int_timestamp(ts), sym, price, volume)

    def stream_batches(self) -> Iterator[List[MarketEvent]]:
        """Yield lists of MarketEvents grouped by timestamp for cross-sectional use."""
        for ts in self.union_index:
            batch: List[MarketEvent] = []
            for sym in self.symbols:
                df = self.data_by_symbol.get(sym)
                if df is None:
                    continue
                if ts in df.index:
                    row = df.loc[ts]
                    price = cast(float, row["close"])
                    volume = float(row["volume"]) if "volume" in df.columns else 0.0
                    batch.append(MarketEvent(self._to_int_timestamp(ts), sym, price, volume))
            if batch:
                yield batch

    def get_latest_price(self, symbol: str, timestamp: int) -> float | None:
        df = self.data_by_symbol.get(symbol)
        if df is None or df.empty:
            return None

        ts = self._to_datetime(timestamp)

        if self.mode == "exact":
            try:
                close_value = cast(float, df.loc[ts, "close"])
                return close_value
            except KeyError:
                return None

        idx = df.index.searchsorted(ts, side="right") - 1
        if idx < 0:
            return None
        close_value = cast(float, df.iloc[idx]["close"])
        return close_value

    def get_future_timestamps(self, start_timestamp: int, n: int) -> List[int]:
        """Return next n timestamps from the global union index strictly after start."""
        if self.union_index.empty:
            return []

        ts = self._to_datetime(start_timestamp)
        future = self.union_index[self.union_index > ts]
        return [self._to_int_timestamp(idx) for idx in future[:n]]

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

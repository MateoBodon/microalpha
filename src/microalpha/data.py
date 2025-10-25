# microalpha/data.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, cast

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
            df = pd.read_csv(self.file_path, index_col=0, parse_dates=True)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Data file not found: {self.file_path}") from exc

        if df is None or df.empty:
            return None
        if "close" not in df.columns:
            raise ValueError(f"Expected 'close' column in {self.file_path}")
        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError("CSV index must be datetimes (parsed via parse_dates=True)")
        return df

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
    """Multi-asset CSV handler that synchronises events across symbols.

    Streams `MarketEvent`s sorted by timestamp across all symbols. Each CSV is
    expected at `<csv_dir>/<symbol>.csv` with a datetime index and a `close` column.
    """

    def __init__(self, csv_dir: Path, symbols: Sequence[str], mode: str = "ffill"):
        self.csv_dir = csv_dir
        self.symbols = list(symbols)
        self.mode = mode
        self.full_frames: Dict[str, Optional[pd.DataFrame]] = {
            s: self._load_single(s) for s in self.symbols
        }
        self.frames: Dict[str, Optional[pd.DataFrame]] = dict(self.full_frames)
        # Compatibility flags with single-asset handler
        self.full_data: Optional[pd.DataFrame] = None
        self.data: Optional[pd.DataFrame] = pd.DataFrame()

    def _load_single(self, symbol: str) -> Optional[pd.DataFrame]:
        path = self.csv_dir / f"{symbol}.csv"
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Data file not found: {path}") from exc
        if df is None or df.empty:
            return None
        if "close" not in df.columns:
            raise ValueError(f"Expected 'close' column in {path}")
        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError("CSV index must be datetimes (parsed via parse_dates=True)")
        return df

    def set_date_range(self, start_date, end_date) -> None:
        for sym, df in self.full_frames.items():
            if df is None:
                self.frames[sym] = None
            else:
                self.frames[sym] = df.loc[start_date:end_date]

    def _iter_union_index(self) -> Iterator[pd.Timestamp]:
        indices = [df.index for df in self.frames.values() if df is not None]
        if not indices:
            return iter(())
        union = indices[0]
        for idx in indices[1:]:
            union = union.union(idx)
        return iter(union.sort_values())

    def stream(self) -> Iterator[MarketEvent]:
        if not self.frames:
            return
        for ts in self._iter_union_index():
            for sym, df in self.frames.items():
                if df is None:
                    continue
                price = self._lookup_price(df, ts)
                if price is None:
                    continue
                # Reuse CsvDataHandler timestamp helpers
                yield MarketEvent(CsvDataHandler._to_int_timestamp(ts), sym, float(price), 0.0)

    def get_latest_price(self, symbol: str, timestamp: int):
        df = self.frames.get(symbol)
        if df is None:
            return None
        ts = CsvDataHandler._to_datetime(timestamp)
        return self._lookup_price(df, ts)

    def get_future_timestamps(self, start_timestamp: int, n: int) -> List[int]:
        # Use the union index to determine the next times globally
        ts = CsvDataHandler._to_datetime(start_timestamp)
        union = list(self._iter_union_index())
        idx = pd.Index(union).searchsorted(ts, side="right")
        return [CsvDataHandler._to_int_timestamp(t) for t in union[idx : idx + n]]

    def _lookup_price(self, df: pd.DataFrame, ts: pd.Timestamp) -> Optional[float]:
        if self.mode == "exact":
            try:
                return cast(float, df.loc[ts, "close"])  # type: ignore[index]
            except KeyError:
                return None
        idx = df.index.searchsorted(ts, side="right") - 1
        if idx < 0:
            return None
        return cast(float, df.iloc[idx]["close"])  # type: ignore[index]

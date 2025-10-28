"""Benchmark MultiCsvDataHandler streaming throughput."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable, Iterator, List, Tuple

import numpy as np
import pandas as pd

from microalpha.data import MultiCsvDataHandler
from microalpha.events import MarketEvent


def _write_panel(csv_dir: Path, symbols: List[str], base_dates: pd.DatetimeIndex) -> None:
    rng = np.random.default_rng(2025)
    csv_dir.mkdir(parents=True, exist_ok=True)
    for symbol in symbols:
        mask = rng.random(len(base_dates)) > 0.1  # drop ~10% to create gaps
        idx = base_dates[mask]
        noise = rng.normal(0, 0.5, size=idx.size).cumsum()
        prices = 100.0 + noise
        df = pd.DataFrame({"close": prices}, index=idx)
        df.to_csv(csv_dir / f"{symbol}.csv")


def _baseline_stream(handler: MultiCsvDataHandler) -> Iterator[MarketEvent]:
    frames = {
        sym: df for sym, df in handler.frames.items() if df is not None and not df.empty
    }
    if not frames:
        return iter(())
    union = None
    for df in frames.values():
        union = df.index if union is None else union.union(df.index)
    if union is None:
        return iter(())
    union = union.sort_values()
    events: List[MarketEvent] = []
    for ts in union:
        for sym in handler.symbols:
            df = frames.get(sym)
            if df is None:
                continue
            if handler.mode == "exact":
                try:
                    value = df.loc[ts, "close"]  # type: ignore[index]
                except KeyError:
                    continue
                price = float(value.iloc[0]) if isinstance(value, pd.Series) else float(value)
            else:
                idx = df.index.searchsorted(ts, side="right") - 1
                if idx < 0:
                    continue
                price = float(df.iloc[idx]["close"])  # type: ignore[index]
            events.append(MarketEvent(int(ts.value), sym, price, 0.0))
    return iter(events)


def _collect(events: Iterable[MarketEvent]) -> List[MarketEvent]:
    return list(events)


def run_benchmark(
    num_symbols: int = 50,
    num_days: int = 50_000,
    mode: str = "ffill",
) -> Tuple[int, float, float]:
    tmp_dir = Path("benchmarks/_tmp_multi")
    if tmp_dir.exists():
        for item in tmp_dir.iterdir():
            item.unlink()
    symbols = [f"S{idx:03d}" for idx in range(num_symbols)]
    base_dates = pd.date_range("2015-01-01", periods=num_days, freq="D")
    _write_panel(tmp_dir, symbols, base_dates)

    handler_fast = MultiCsvDataHandler(tmp_dir, symbols, mode=mode)
    handler_fast.set_date_range(base_dates[0], base_dates[-1])
    handler_slow = MultiCsvDataHandler(tmp_dir, symbols, mode=mode)
    handler_slow.set_date_range(base_dates[0], base_dates[-1])

    t0 = time.perf_counter()
    fast_events = _collect(handler_fast.stream())
    dt_fast = time.perf_counter() - t0

    t1 = time.perf_counter()
    slow_events = _collect(_baseline_stream(handler_slow))
    dt_slow = time.perf_counter() - t1

    assert fast_events == slow_events

    evps_fast = int(len(fast_events) / dt_fast) if dt_fast else 0
    evps_slow = int(len(slow_events) / dt_slow) if dt_slow else 0

    results = {
        "mode": mode,
        "symbols": num_symbols,
        "rows": num_days,
        "events": len(fast_events),
        "fast_sec": round(dt_fast, 3),
        "fast_evps": evps_fast,
        "slow_sec": round(dt_slow, 3),
        "slow_evps": evps_slow,
    }
    print(results)
    return len(fast_events), dt_fast, dt_slow


if __name__ == "__main__":
    run_benchmark()

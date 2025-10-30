from __future__ import annotations

from pathlib import Path

import pandas as pd

from microalpha.data import MultiCsvDataHandler


def _write_csv(path: Path, idx: list[pd.Timestamp], closes: list[float]) -> None:
    df = pd.DataFrame(
        {
            "close": closes,
            "volume": [1_000_000 + i * 10_000 for i in range(len(closes))],
        },
        index=pd.DatetimeIndex(idx),
    )
    df.to_csv(path)


def test_multicsv_union_index_and_price_modes(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    a_idx = pd.to_datetime(["2025-01-01", "2025-01-03"])  # gap on 2025-01-02
    b_idx = pd.to_datetime(["2025-01-02"])  # only middle date
    _write_csv(data_dir / "A.csv", list(a_idx), [100.0, 101.0])
    _write_csv(data_dir / "B.csv", list(b_idx), [200.0])

    # ffill mode (default)
    dh = MultiCsvDataHandler(csv_dir=data_dir, symbols=["A", "B"], mode="ffill")
    dh.set_date_range("2025-01-01", "2025-01-03")

    # union should be 1st, 2nd, 3rd
    union_ts = list(dh._iter_union_index())
    assert union_ts == sorted(union_ts)
    assert [ts.date().isoformat() for ts in union_ts] == [
        "2025-01-01",
        "2025-01-02",
        "2025-01-03",
    ]

    # ffill lookup returns latest known
    mid = int((pd.Timestamp("2025-01-01") + pd.Timedelta(hours=12)).value)
    assert dh.get_latest_price("A", mid) == 100.0

    # exact mode returns None when not aligned
    dh_exact = MultiCsvDataHandler(csv_dir=data_dir, symbols=["A", "B"], mode="exact")
    dh_exact.set_date_range("2025-01-01", "2025-01-03")
    assert dh_exact.get_latest_price("A", mid) is None


def _baseline_events(handler: MultiCsvDataHandler) -> list[tuple[int, str, float]]:
    frames = {
        sym: df for sym, df in handler.frames.items() if df is not None and not df.empty
    }
    if not frames:
        return []
    union = None
    for df in frames.values():
        union = df.index if union is None else union.union(df.index)
    if union is None:
        return []
    union = union.sort_values()
    events: list[tuple[int, str, float]] = []
    for ts in union:
        ts_int = int(ts.value)
        for sym in handler.symbols:
            df = frames.get(sym)
            if df is None:
                continue
            if handler.mode == "exact":
                try:
                    value = df.loc[ts, "close"]  # type: ignore[index]
                except KeyError:
                    continue
                if isinstance(value, pd.Series):
                    if value.empty:
                        continue
                    price = float(value.iloc[0])
                else:
                    price = float(value)
                events.append((ts_int, sym, price))
            else:
                idx = df.index.searchsorted(ts, side="right") - 1
                if idx < 0:
                    continue
                price = float(df.iloc[idx]["close"])  # type: ignore[index]
                events.append((ts_int, sym, price))
    return events


def _collect_events(handler: MultiCsvDataHandler) -> list[tuple[int, str, float]]:
    return [
        (event.timestamp, event.symbol, float(event.price))
        for event in handler.stream()
    ]


def test_stream_matches_baseline_logic(tmp_path: Path) -> None:
    data_dir = tmp_path / "panel"
    data_dir.mkdir()

    idx = pd.date_range("2025-01-01", periods=6, freq="D")
    # Introduce gaps for each symbol
    symbol_data = {
        "AAA": ([idx[0], idx[2], idx[5]], [100.0, 101.0, 103.0]),
        "BBB": ([idx[1], idx[3]], [50.0, 55.0]),
        "CCC": ([idx[0], idx[1], idx[4]], [200.0, 201.0, 202.0]),
    }
    for sym, (dates, prices) in symbol_data.items():
        _write_csv(data_dir / f"{sym}.csv", list(dates), prices)

    for mode in ("ffill", "exact"):
        handler = MultiCsvDataHandler(csv_dir=data_dir, symbols=list(symbol_data), mode=mode)
        handler.set_date_range(idx[0], idx[-1])
        expected = _baseline_events(handler)
        observed = _collect_events(handler)
        assert observed == expected

        future = handler.get_future_timestamps(int(idx[1].value), 2)
        assert len(future) == 2
        aligned_ts = int(idx[2].value)
        bridge_ts = int((idx[2] + pd.Timedelta(hours=12)).value)
        aligned_vol = handler.get_volume_at("AAA", aligned_ts)
        assert aligned_vol is not None and aligned_vol > 0
        bridge_vol = handler.get_volume_at("AAA", bridge_ts)
        assert bridge_vol is None

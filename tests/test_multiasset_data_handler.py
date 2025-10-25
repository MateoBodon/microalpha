from __future__ import annotations

from pathlib import Path

import pandas as pd

from microalpha.data import MultiCsvDataHandler


def _write_csv(path: Path, idx: list[pd.Timestamp], closes: list[float]) -> None:
    df = pd.DataFrame({"close": closes}, index=pd.DatetimeIndex(idx))
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
    assert [ts.date().isoformat() for ts in union_ts] == ["2025-01-01", "2025-01-02", "2025-01-03"]

    # ffill lookup returns latest known
    mid = int((pd.Timestamp("2025-01-01") + pd.Timedelta(hours=12)).value)
    assert dh.get_latest_price("A", mid) == 100.0

    # exact mode returns None when not aligned
    dh_exact = MultiCsvDataHandler(csv_dir=data_dir, symbols=["A", "B"], mode="exact")
    dh_exact.set_date_range("2025-01-01", "2025-01-03")
    assert dh_exact.get_latest_price("A", mid) is None


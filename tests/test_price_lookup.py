import pandas as pd

from microalpha.data import CsvDataHandler


def _make_series(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    idx = pd.date_range("2025-01-01 09:30", periods=3, freq="min")
    df = pd.DataFrame({"close": [100.0, 101.0, 102.0]}, index=idx)
    (data_dir / "TEST.csv").write_text(df.to_csv())
    return data_dir, idx


def test_price_lookup_modes(tmp_path):
    data_dir, idx = _make_series(tmp_path)

    mid_ts = int((idx[0] + pd.Timedelta(seconds=30)).value)
    before_start = int((idx[0] - pd.Timedelta(minutes=1)).value)

    exact_handler = CsvDataHandler(csv_dir=data_dir, symbol="TEST", mode="exact")
    assert exact_handler.get_latest_price("TEST", mid_ts) is None
    assert exact_handler.get_latest_price("TEST", before_start) is None

    ffill_handler = CsvDataHandler(csv_dir=data_dir, symbol="TEST", mode="ffill")
    assert ffill_handler.get_latest_price("TEST", mid_ts) == 100.0

    just_before_second = int((idx[1] - pd.Timedelta(seconds=1)).value)
    assert ffill_handler.get_latest_price("TEST", just_before_second) == 100.0

    after_last = int((idx[-1] + pd.Timedelta(minutes=5)).value)
    assert ffill_handler.get_latest_price("TEST", after_last) == 102.0

    assert ffill_handler.get_latest_price("TEST", before_start) is None

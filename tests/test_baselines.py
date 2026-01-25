from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from microalpha.reporting.baselines import BASELINE_COLUMNS, compute_baselines


def _write_equity_curve(path: Path, dates: pd.DatetimeIndex) -> None:
    df = pd.DataFrame(
        {
            "timestamp": [int(ts.value) for ts in dates],
            "equity": [1_000_000.0] * len(dates),
            "returns": [0.0] * len(dates),
        }
    )
    df.to_csv(path, index=False)


def _write_universe(path: Path, dates: pd.DatetimeIndex, symbols: list[str]) -> None:
    rows = []
    for ts in dates:
        for sym in symbols:
            rows.append({"symbol": sym, "date": ts.strftime("%Y-%m-%d"), "sector": "X"})
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_prices(path: Path, dates: pd.DatetimeIndex, prices: list[float]) -> None:
    df = pd.DataFrame({"close": prices}, index=dates)
    df.to_csv(path)


def test_momentum_baseline_no_lookahead(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    data_dir = tmp_path / "data"
    artifact_dir.mkdir()
    data_dir.mkdir()

    dates = pd.date_range("2020-02-29", "2021-04-30", freq="ME")
    symbols = ["ALFA", "BETA"]

    universe_path = tmp_path / "universe.csv"
    _write_universe(universe_path, dates, symbols)

    config = {
        "data_path": str(data_dir),
        "strategy": {"params": {"universe_path": str(universe_path)}},
    }
    (artifact_dir / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")

    # Symbol ALFA trends up through Feb 2021, then dips in April.
    alfa_prices = list(pd.Series(range(len(dates))).astype(float) + 100.0)
    alfa_prices[-2] = 200.0  # 2021-03-31
    alfa_prices[-1] = 180.0  # 2021-04-30

    # Symbol BETA flat through Feb 2021, jumps in March (skip month), rises in April.
    beta_prices = [100.0] * len(dates)
    beta_prices[-2] = 300.0  # 2021-03-31
    beta_prices[-1] = 330.0  # 2021-04-30

    _write_prices(data_dir / "ALFA.csv", dates, alfa_prices)
    _write_prices(data_dir / "BETA.csv", dates, beta_prices)

    _write_equity_curve(artifact_dir / "equity_curve.csv", dates)

    baselines = compute_baselines(artifact_dir)
    assert list(baselines.columns) == list(BASELINE_COLUMNS)

    april_row = baselines[baselines["date"] == pd.Timestamp("2021-04-30")]
    assert not april_row.empty
    mom_return = float(april_row["mom_12_1"].iloc[0])
    assert mom_return < 0.0


def test_baselines_schema_stable(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    data_dir = tmp_path / "data"
    artifact_dir.mkdir()
    data_dir.mkdir()

    dates = pd.date_range("2021-01-31", "2021-06-30", freq="ME")
    symbols = ["ALFA"]

    universe_path = tmp_path / "universe.csv"
    _write_universe(universe_path, dates, symbols)

    config = {
        "data_path": str(data_dir),
        "strategy": {"params": {"universe_path": str(universe_path)}},
    }
    (artifact_dir / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")

    prices = [100.0 + i for i in range(len(dates))]
    _write_prices(data_dir / "ALFA.csv", dates, prices)
    _write_equity_curve(artifact_dir / "equity_curve.csv", dates)

    baselines = compute_baselines(artifact_dir)
    assert list(baselines.columns) == list(BASELINE_COLUMNS)
    assert (artifact_dir / "baselines.csv").exists()
    assert (artifact_dir / "baselines_status.json").exists()

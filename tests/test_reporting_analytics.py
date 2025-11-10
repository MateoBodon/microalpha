from __future__ import annotations

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from microalpha.reporting.analytics import (
    compute_decile_table,
    compute_ic_series,
    compute_rolling_betas,
    generate_analytics,
)


def test_compute_ic_series_matches_spearman() -> None:
    signals = pd.DataFrame(
        {
            "as_of": pd.to_datetime([
                "2024-01-01",
                "2024-01-01",
                "2024-01-01",
                "2024-01-02",
                "2024-01-02",
                "2024-01-02",
            ]),
            "symbol": ["A", "B", "C", "A", "B", "C"],
            "score": [1.0, 2.0, 3.0, 3.0, 2.0, 1.0],
            "forward_return": [0.1, 0.2, 0.3, 0.1, 0.2, 0.4],
        }
    )
    ic = compute_ic_series(signals)
    assert len(ic) == 2
    assert np.isclose(ic.iloc[0], 1.0)
    assert np.isclose(ic.iloc[1], -1.0)


def test_compute_decile_table_adds_long_short() -> None:
    dates = pd.to_datetime(["2024-01-01"] * 10)
    scores = np.linspace(-1.0, 1.0, 10)
    forwards = np.linspace(-0.05, 0.05, 10)
    signals = pd.DataFrame(
        {
            "as_of": dates,
            "symbol": [f"S{i}" for i in range(10)],
            "score": scores,
            "forward_return": forwards,
        }
    )
    table = compute_decile_table(signals, deciles=10)
    assert "P10" in table["decile"].values
    assert any(v.startswith("P10") and "P1" in v for v in table["decile"].astype(str))


def test_generate_analytics_writes_artifacts(tmp_path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    signals_rows = []
    for as_of in dates:
        for i in range(10):
            signals_rows.append(
                {
                    "as_of": as_of,
                    "symbol": f"S{i}",
                    "score": float(i) + as_of.day / 100.0,
                    "forward_return": 0.01 * (i - 5),
                }
            )
    pd.DataFrame(signals_rows).to_csv(artifact_dir / "signals.csv", index=False)

    equity = pd.DataFrame(
        {
            "timestamp": dates,
            "equity": np.linspace(1_000_000, 1_020_000, len(dates)),
            "exposure": np.linspace(0.5, 0.8, len(dates)),
            "returns": np.linspace(0.001, -0.001, len(dates)),
        }
    )
    equity.to_csv(artifact_dir / "equity_curve.csv", index=False)

    factors = pd.DataFrame(
        {
            "date": dates,
            "Mkt_RF": np.linspace(0.0, 0.002, len(dates)),
            "SMB": 0.0005,
            "HML": -0.0003,
            "RF": 0.0001,
        }
    )
    factor_path = tmp_path / "factors.csv"
    factors.to_csv(factor_path, index=False)

    result = generate_analytics(
        artifact_dir,
        factor_path=factor_path,
        plots_dir=tmp_path / "plots",
        analytics_dir=tmp_path / "analytics",
        window=3,
        deciles=5,
    )

    assert result.ic_series_path.exists()
    assert result.deciles_path.exists()
    assert result.ic_plot.exists()
    assert result.decile_plot.exists()

    deciles = pd.read_csv(result.deciles_path)
    assert any(label.endswith("-P1") for label in deciles["decile"].astype(str))


def test_compute_rolling_betas_handles_clean_window() -> None:
    returns = pd.Series(
        [0.01, 0.02, 0.015, 0.005],
        index=pd.date_range("2024-01-01", periods=4, freq="D"),
        name="returns",
    )
    factors = pd.DataFrame(
        {
            "date": returns.index,
            "Mkt_RF": [0.008, 0.01, 0.009, 0.004],
            "SMB": [0.001, 0.002, 0.0, -0.001],
            "HML": [0.0, 0.0005, -0.0002, 0.0001],
            "RF": 0.0001,
        }
    ).set_index("date")
    betas = compute_rolling_betas(returns, factors, window=3)
    assert set(betas.columns) == {"alpha", "Mkt_RF", "SMB", "HML"}

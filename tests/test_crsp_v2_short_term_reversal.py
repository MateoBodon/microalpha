from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from microalpha.research.crsp_v2 import CRSPV2Error
from microalpha.research.crsp_v2_short_term_reversal import (
    _load_short_term_reversal_frame,
    run_short_term_reversal,
)


def _protocol() -> dict:
    return {
        "windows": {
            "validation": {"start": "2017-01-01", "end": "2017-01-31"}
        }
    }


def test_reversal_uses_negative_formation_month_industry_residual(
    tmp_path: Path,
) -> None:
    dates = pd.date_range("2015-12-31", "2017-01-31", freq="ME")
    rows = []
    for date in dates:
        for permno, value in ((1, 0.03), (2, 0.01), (3, -0.01)):
            rows.append(
                {
                    "permno": permno,
                    "formation_date": date,
                    "industry": "One",
                    "eligible_at_formation": True,
                    "price": 50.0,
                    "adv_60_usd": 100_000_000.0,
                    "volatility_126d": 0.02,
                    "full_spread_bps": 10.0,
                    "monthly_total_return": value,
                    "delisting_pseudo_days": 0,
                }
            )
    panel_path = tmp_path / "panel.parquet"
    connection = duckdb.connect()
    connection.register("panel", pd.DataFrame(rows))
    connection.execute(f"COPY panel TO '{panel_path}' (FORMAT PARQUET)")
    connection.close()

    frame = _load_short_term_reversal_frame(panel_path, _protocol())
    december = frame.loc[frame["formation_date"].eq("2016-12-31")]

    scores = december.set_index("permno")["short_term_reversal_1_1"]
    assert scores.loc[1] == pytest.approx(-0.02)
    assert scores.loc[2] == pytest.approx(0.0)
    assert scores.loc[3] == pytest.approx(0.02)


def test_reversal_publication_refuses_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "preserve"
    marker.write_text("yes", encoding="utf-8")
    with pytest.raises(CRSPV2Error, match="Refusing to overwrite"):
        run_short_term_reversal(
            tmp_path / "contract.yaml",
            tmp_path / "base.yaml",
            tmp_path / "panel.parquet",
            tmp_path / "momentum.json",
            tmp_path / "residual.json",
            tmp_path / "low_volatility.json",
            output,
        )
    assert marker.read_text(encoding="utf-8") == "yes"

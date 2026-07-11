from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from microalpha.research.crsp_v2 import CRSPV2Error
from microalpha.research.crsp_v2_low_volatility import (
    _load_low_volatility_frame,
    run_low_volatility,
)


def _protocol() -> dict:
    return {
        "windows": {
            "validation": {"start": "2017-01-01", "end": "2017-01-31"}
        }
    }


def test_low_volatility_score_is_fixed_negative_point_in_time_value(
    tmp_path: Path,
) -> None:
    panel = pd.DataFrame(
        {
            "permno": [1, 2, 3],
            "formation_date": pd.to_datetime(["2016-12-31"] * 3),
            "industry": ["One"] * 3,
            "eligible_at_formation": [True] * 3,
            "price": [50.0] * 3,
            "adv_60_usd": [100_000_000.0] * 3,
            "volatility_126d": [0.01, 0.02, 0.00],
            "full_spread_bps": [10.0] * 3,
            "monthly_total_return": [0.01] * 3,
            "delisting_pseudo_days": [0] * 3,
        }
    )
    panel_path = tmp_path / "panel.parquet"
    connection = duckdb.connect()
    connection.register("panel", panel)
    connection.execute(f"COPY panel TO '{panel_path}' (FORMAT PARQUET)")
    connection.close()

    frame = _load_low_volatility_frame(panel_path, _protocol())

    assert frame.loc[frame["permno"].eq(1), "low_volatility_126d"].iloc[0] == -0.01
    assert frame.loc[frame["permno"].eq(2), "low_volatility_126d"].iloc[0] == -0.02
    assert pd.isna(
        frame.loc[frame["permno"].eq(3), "low_volatility_126d"].iloc[0]
    )


def test_low_volatility_publication_refuses_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "preserve"
    marker.write_text("yes", encoding="utf-8")
    with pytest.raises(CRSPV2Error, match="Refusing to overwrite"):
        run_low_volatility(
            tmp_path / "contract.yaml",
            tmp_path / "base.yaml",
            tmp_path / "panel.parquet",
            tmp_path / "momentum.json",
            tmp_path / "residual.json",
            output,
        )
    assert marker.read_text(encoding="utf-8") == "yes"

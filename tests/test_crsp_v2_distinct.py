from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from microalpha.research.crsp_v2 import CRSPV2Error
from microalpha.research.crsp_v2_distinct import (
    _load_distinct_signal_frame,
    _rank_candidates,
    run_distinct_family,
)


def _protocol() -> dict:
    return {
        "windows": {
            "validation": {"start": "2017-01-01", "end": "2017-01-31"}
        }
    }


def test_residual_signal_chronology_and_reversal_control(tmp_path: Path) -> None:
    dates = pd.date_range("2015-12-31", "2017-01-31", freq="ME")
    rows = []
    for date_index, date in enumerate(dates):
        for permno, spread in ((1, 0.02), (2, 0.00), (3, -0.02)):
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
                    "monthly_total_return": 0.01 + spread,
                    "delisting_pseudo_days": 0,
                }
            )
    panel = pd.DataFrame(rows)
    panel.loc[
        panel["formation_date"].eq(pd.Timestamp("2016-12-31"))
        & panel["permno"].eq(1),
        "monthly_total_return",
    ] = 5.01
    panel_path = tmp_path / "panel.parquet"
    connection = duckdb.connect()
    connection.register("panel", panel)
    connection.execute(f"COPY panel TO '{panel_path}' (FORMAT PARQUET)")
    connection.close()

    frame = _load_distinct_signal_frame(panel_path, _protocol())
    december = frame.loc[
        frame["formation_date"].eq("2016-12-31") & frame["permno"].eq(1)
    ].iloc[0]

    assert december["residual_mom_12_2"] == pytest.approx(11 * 0.02)
    assert december["residual_mom_6_2"] == pytest.approx(5 * 0.02)
    assert december["industry_residual_return"] == pytest.approx(5.0)
    assert december["residual_mom_12_2_minus_reversal_1_1"] == pytest.approx(
        11 * 0.02 - 5.0
    )


def test_distinct_reducer_prefers_primary_hac_sharpe() -> None:
    candidates = pd.DataFrame(
        [
            {
                "candidate_id": "low",
                "eligible": True,
                "net_sharpe_hac": 0.5,
                "worst_calendar_year_net_return": 0.1,
                "total_one_way_turnover": 1.0,
            },
            {
                "candidate_id": "high",
                "eligible": True,
                "net_sharpe_hac": 0.6,
                "worst_calendar_year_net_return": -0.2,
                "total_one_way_turnover": 2.0,
            },
            {
                "candidate_id": "ineligible",
                "eligible": False,
                "net_sharpe_hac": 99.0,
                "worst_calendar_year_net_return": 99.0,
                "total_one_way_turnover": 0.0,
            },
        ]
    )
    ranked = _rank_candidates(candidates)
    assert ranked["candidate_id"].tolist() == ["high", "low", "ineligible"]


def test_distinct_publication_refuses_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "preserve"
    marker.write_text("yes", encoding="utf-8")
    with pytest.raises(CRSPV2Error, match="Refusing to overwrite"):
        run_distinct_family(
            tmp_path / "contract.yaml",
            tmp_path / "base.yaml",
            tmp_path / "panel.parquet",
            tmp_path / "previous.json",
            output,
        )
    assert marker.read_text(encoding="utf-8") == "yes"

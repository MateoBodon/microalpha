from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from microalpha.research.crsp_v2 import CRSPV2Error
from microalpha.research.crsp_v2_fundamental import (
    _centered_percentile_rank,
    _load_fundamental_frame,
    run_fundamental_composite,
)


def _protocol() -> dict:
    return {
        "windows": {
            "validation": {"start": "2017-01-01", "end": "2022-12-31"}
        }
    }


def _write_fixture(tmp_path: Path, *, ambiguous: bool = False) -> tuple[Path, Path, Path]:
    dates = pd.date_range("2016-12-31", "2022-12-31", freq="ME")
    panel_rows = []
    for date in dates:
        for permno in (1, 2, 3, 4):
            panel_rows.append(
                {
                    "permno": permno,
                    "formation_date": date,
                    "industry": "One",
                    "eligible_at_formation": True,
                    "price": 50.0,
                    "market_cap_usd": float(permno * 100_000_000),
                    "adv_60_usd": 100_000_000.0,
                    "volatility_126d": 0.02,
                    "full_spread_bps": 10.0,
                    "monthly_total_return": 0.01,
                    "delisting_pseudo_days": 0,
                }
            )
    panel_path = tmp_path / "panel.parquet"
    pd.DataFrame(panel_rows).to_parquet(panel_path, index=False)

    annual_rows = []
    for permno in (1, 2, 3, 4):
        gvkey = f"{permno:06d}"
        for datadate, current in (
            (pd.Timestamp("2015-06-30"), False),
            (
                pd.Timestamp("2016-07-31")
                if permno == 4
                else pd.Timestamp("2016-06-30"),
                True,
            ),
        ):
            scale = float(permno)
            annual_rows.append(
                {
                    "gvkey": gvkey,
                    "datadate": datadate,
                    "at": 100.0,
                    "lt": 40.0,
                    "ceq": 90.0 - 10.0 * scale if current else 60.0,
                    "txditc": 0.0,
                    "pstk": 0.0,
                    "pstkl": np.nan,
                    "pstkrv": np.nan,
                    "sale": 180.0 - 20.0 * scale if current else 100.0,
                    "cogs": 40.0,
                    "xsga": 10.0,
                    "xint": 5.0,
                    "che": 10.0,
                    "dltt": 20.0,
                    "dlc": 5.0,
                    "dp": 0.0,
                }
            )
    if ambiguous:
        annual_rows.extend(
            [
                {**annual_rows[0], "gvkey": "999999"},
                {**annual_rows[1], "gvkey": "999999"},
            ]
        )
    annual_path = tmp_path / "annual.parquet"
    pd.DataFrame(annual_rows).to_parquet(annual_path, index=False)

    link_rows = [
        {
            "gvkey": f"{permno:06d}",
            "linkprim": "P",
            "linktype": "LU",
            "lpermno": permno,
            "linkdt": pd.Timestamp("2000-01-01"),
            "linkenddt": pd.NaT,
        }
        for permno in (1, 2, 3, 4)
    ]
    if ambiguous:
        link_rows.append(
            {
                "gvkey": "999999",
                "linkprim": "C",
                "linktype": "LC",
                "lpermno": 1,
                "linkdt": pd.Timestamp("2000-01-01"),
                "linkenddt": pd.NaT,
            }
        )
    link_path = tmp_path / "links.parquet"
    pd.DataFrame(link_rows).to_parquet(link_path, index=False)
    return annual_path, link_path, panel_path


def test_centered_percentile_rank_is_symmetric_and_tie_stable() -> None:
    values = pd.Series([1.0, 2.0, 2.0, 4.0, np.nan])
    ranked = _centered_percentile_rank(values)
    assert ranked.iloc[0] == pytest.approx(-0.75)
    assert ranked.iloc[1] == pytest.approx(0.0)
    assert ranked.iloc[2] == pytest.approx(0.0)
    assert ranked.iloc[3] == pytest.approx(0.75)
    assert pd.isna(ranked.iloc[4])


def test_fundamental_frame_enforces_six_month_availability_and_fixed_ranks(
    tmp_path: Path,
) -> None:
    annual, links, panel = _write_fixture(tmp_path)
    frame, coverage, audit = _load_fundamental_frame(
        [annual], links, panel, _protocol()
    )
    december = frame.loc[frame["formation_date"].eq("2016-12-31")]
    scores = december.set_index("permno")["qvpi_annual_composite"]

    assert scores.loc[1] > scores.loc[2] > scores.loc[3]
    assert pd.isna(scores.loc[4])
    january_four = frame.loc[
        frame["formation_date"].eq("2017-01-31") & frame["permno"].eq(4),
        "qvpi_annual_composite",
    ].iloc[0]
    assert pd.notna(january_four)
    scored = frame["qvpi_annual_composite"].notna()
    assert (
        frame.loc[scored, "accounting_availability_date"]
        <= frame.loc[scored, "formation_date"]
    ).all()
    assert len(coverage) == 72
    assert audit["compustat_2023_2025_partitions_opened"] is False
    assert audit["final_holdout_outcomes_read"] is False


def test_fundamental_frame_stops_on_ambiguous_primary_ccm_mapping(
    tmp_path: Path,
) -> None:
    annual, links, panel = _write_fixture(tmp_path, ambiguous=True)
    with pytest.raises(CRSPV2Error, match="Ambiguous CCM"):
        _load_fundamental_frame([annual], links, panel, _protocol())


def test_fundamental_publication_refuses_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "preserve"
    marker.write_text("yes", encoding="utf-8")
    with pytest.raises(CRSPV2Error, match="Refusing to overwrite"):
        run_fundamental_composite(tmp_path / "contract.yaml", output)
    assert marker.read_text(encoding="utf-8") == "yes"

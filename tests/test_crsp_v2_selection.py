from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import duckdb
import numpy as np
import pandas as pd
import pytest
import yaml

from microalpha.research.crsp_v2 import CRSPV2Error, protocol_sha256, sha256_file
from microalpha.research.crsp_v2_selection import (
    _load_signal_frame,
    _rank_candidates,
    _read_daily_factor_zip,
    _read_ff5_rf_zip,
    _read_momentum_deciles_zip,
    _run_strategy,
    _validate_selection_inputs,
    run_selection,
)


def _protocol(*, validation_start: str = "2017-01-01", validation_end: str = "2022-12-31") -> dict:
    return {
        "windows": {
            "validation": {"start": validation_start, "end": validation_end},
        },
        "candidate_grid": {
            "common_rules": {"long_fraction": 0.10, "short_fraction": 0.10},
        },
        "portfolio": {
            "capital_usd": 15_000_000,
            "target_gross_exposure": 1.0,
            "target_net_exposure": 0.0,
            "max_single_name_weight": 0.02,
            "max_industry_gross_weight": 0.15,
            "max_participation_of_60d_adv": 0.02,
        },
        "costs": {
            "primary": {
                "commission_bps_each_side": 5.0,
                "fallback_full_spread_bps": 10.0,
                "annual_short_borrow_bps": 300.0,
            }
        },
    }


def test_signal_windows_exclude_the_current_month(tmp_path: Path) -> None:
    dates = pd.date_range("2015-01-31", "2017-01-31", freq="ME")
    returns = np.full(len(dates), 0.01)
    returns[dates.get_loc(pd.Timestamp("2016-12-31"))] = 5.0
    panel = pd.DataFrame(
        {
            "permno": 10001,
            "formation_date": dates,
            "industry": "BusEq",
            "eligible_at_formation": True,
            "price": 50.0,
            "adv_60_usd": 100_000_000.0,
            "volatility_126d": 0.02,
            "full_spread_bps": 10.0,
            "monthly_total_return": returns,
            "delisting_pseudo_days": 0,
        }
    )
    panel_path = tmp_path / "panel.parquet"
    connection = duckdb.connect()
    connection.register("panel", panel)
    connection.execute(f"COPY panel TO '{panel_path}' (FORMAT PARQUET)")
    connection.close()

    scored = _load_signal_frame(
        panel_path,
        _protocol(validation_start="2017-01-01", validation_end="2017-01-31"),
    )
    december = scored.loc[scored["formation_date"].eq("2016-12-31")].iloc[0]

    assert december["mom_12_2"] == pytest.approx(1.01**11 - 1.0)
    assert december["mom_6_2"] == pytest.approx(1.01**5 - 1.0)
    assert december["mom_12_2"] < 1.0


def test_validation_engine_maps_formation_to_next_month_and_applies_costs() -> None:
    dates = pd.date_range("2016-12-31", "2022-12-31", freq="ME")
    rows: list[dict[str, float | int | bool | str | pd.Timestamp]] = []
    permno = 1
    securities: list[tuple[int, str, float]] = []
    for industry_index in range(8):
        industry = f"Industry-{industry_index}"
        for rank in range(40):
            securities.append((permno, industry, float(40 - rank)))
            permno += 1
    for month_index, date in enumerate(dates):
        alpha_scale = 0.0003 + 0.0001 * np.sin(month_index / 3.0)
        for security, industry, score in securities:
            if security == 3 and month_index == 1:
                continue
            placeholder = security == 2 and month_index == 2
            centered_score = score - 20.5
            delisted = security == 1 and month_index == 1
            rows.append(
                {
                    "permno": security,
                    "formation_date": date,
                    "industry": industry,
                    "eligible_at_formation": not (
                        placeholder or (security == 1 and month_index >= 1)
                    ),
                    "price": np.nan if placeholder else 50.0,
                    "adv_60_usd": 100_000_000.0,
                    "volatility_126d": 0.02 + (security % 5) * 0.001,
                    "full_spread_bps": 10.0,
                    "monthly_total_return": (
                        np.nan
                        if placeholder
                        else (-1.0 if delisted else centered_score * alpha_scale)
                    ),
                    "delisting_pseudo_days": int(delisted),
                    "mom_12_2": score,
                    "mom_6_2": score * 0.8,
                    "blend_12_2_6_2": score * 0.9,
                }
            )
    frame = pd.DataFrame(rows)

    result = _run_strategy(
        frame,
        _protocol(),
        signal="mom_12_2",
        weighting="equal",
    )

    assert len(result.monthly) == 72
    first = result.monthly.iloc[0]
    assert first["formation_date"] == pd.Timestamp("2016-12-31")
    assert first["realization_date"] == pd.Timestamp("2017-01-31")
    assert first["net_return"] < first["gross_return"]
    assert result.monthly["max_target_industry_gross"].max() <= 0.15 + 1e-12
    assert result.monthly["max_executed_industry_gross"].max() <= 0.15 + 1e-9
    assert result.monthly["max_abs_executed_industry_net"].max() <= 1e-9
    assert result.monthly["executed_net"].abs().max() <= 1e-9
    assert result.metrics["delisted_positions_liquidated"] == 1
    assert result.metrics["untradable_target_names"] >= 1
    assert result.metrics["present_no_session_rows_zero_marked"] >= 1
    assert result.metrics["median_names_per_sleeve"] >= 30
    assert result.metrics["eligible"] is True

    executable_missing_return = frame.copy()
    executable_missing_return.loc[
        executable_missing_return["permno"].eq(2)
        & executable_missing_return["formation_date"].eq(pd.Timestamp("2017-02-28")),
        "price",
    ] = 50.0
    with pytest.raises(
        CRSPV2Error,
        match="executable or delisting observation lacks its CIZ return",
    ):
        _run_strategy(
            executable_missing_return,
            _protocol(),
            signal="mom_12_2",
            weighting="equal",
        )


def test_frozen_reducer_is_lexicographic_and_deterministic() -> None:
    candidates = pd.DataFrame(
        [
            {
                "candidate_id": "z",
                "eligible": True,
                "median_calendar_year_net_sharpe_hac": 1.0,
                "worst_calendar_year_net_return": -0.10,
                "total_one_way_turnover": 2.0,
            },
            {
                "candidate_id": "b",
                "eligible": True,
                "median_calendar_year_net_sharpe_hac": 1.0,
                "worst_calendar_year_net_return": -0.05,
                "total_one_way_turnover": 3.0,
            },
            {
                "candidate_id": "a",
                "eligible": True,
                "median_calendar_year_net_sharpe_hac": 1.0,
                "worst_calendar_year_net_return": -0.05,
                "total_one_way_turnover": 3.0,
            },
            {
                "candidate_id": "ineligible",
                "eligible": False,
                "median_calendar_year_net_sharpe_hac": 99.0,
                "worst_calendar_year_net_return": 99.0,
                "total_one_way_turnover": 0.0,
            },
        ]
    )

    ranked = _rank_candidates(candidates)

    assert ranked["candidate_id"].tolist() == ["a", "b", "z", "ineligible"]
    assert ranked["selection_rank"].tolist() == [1, 2, 3, 4]


def test_public_baseline_parsers_cover_daily_and_monthly_formats(tmp_path: Path) -> None:
    mom_path = tmp_path / "mom.zip"
    with ZipFile(mom_path, "w") as archive:
        archive.writestr(
            "mom.csv",
            "header\n,Mom,\n20170103,1.00,\n20170104,2.00,\n",
        )
    ff5_path = tmp_path / "ff5.zip"
    with ZipFile(ff5_path, "w") as archive:
        archive.writestr(
            "ff5.csv",
            "header\n,Mkt-RF,SMB,HML,RMW,CMA,RF\n"
            "20170103,0,0,0,0,0,0.10\n20170104,0,0,0,0,0,0.20\n",
        )
    decile_path = tmp_path / "deciles.zip"
    with ZipFile(decile_path, "w") as archive:
        archive.writestr(
            "deciles.csv",
            "Value Weight Returns -- Monthly\n"
            ",Lo PRIOR,PRIOR 2,PRIOR 3,PRIOR 4,PRIOR 5,PRIOR 6,PRIOR 7,PRIOR 8,PRIOR 9,Hi PRIOR\n"
            "201701,1,2,3,4,5,6,7,8,9,11\n\n",
        )

    mom = _read_daily_factor_zip(mom_path, "mom")
    rf = _read_ff5_rf_zip(ff5_path)
    deciles = _read_momentum_deciles_zip(decile_path)

    assert mom.loc[pd.Period("2017-01", freq="M")] == pytest.approx(1.01 * 1.02 - 1)
    assert rf.loc[pd.Period("2017-01", freq="M")] == pytest.approx(1.001 * 1.002 - 1)
    assert deciles.loc[pd.Period("2017-01", freq="M")] == pytest.approx(0.10)


def _selection_contract_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    protocol = {
        "schema_version": "microalpha-flagship-protocol/v1",
        "protocol_id": "selection-contract-test",
        "windows": {"validation": {"start": "2017-01-01", "end": "2022-12-31"}},
    }
    protocol_path = tmp_path / "protocol.yaml"
    protocol_path.write_text(yaml.safe_dump(protocol), encoding="utf-8")
    panel_path = tmp_path / "panel.parquet"
    panel_path.write_bytes(b"panel-evidence")
    manifest_path = panel_path.with_suffix(".parquet.manifest.json")
    manifest = {
        "stage": "selection",
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": protocol_sha256(protocol_path),
        "output": {"sha256": sha256_file(panel_path), "max_date": "2022-12-31"},
        "access_contract": {
            "primary_holdout_partitions_opened_for_outcome_rows": False,
            "primary_post_validation_rows_materialized": 0,
            "post_validation_stocknames_rows_materialized": 0,
            "post_validation_delisting_rows_materialized": 0,
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return protocol_path, panel_path, manifest_path


def test_selection_contract_rejects_tamper_and_holdout_receipts(tmp_path: Path) -> None:
    protocol_path, panel_path, manifest_path = _selection_contract_fixture(tmp_path)
    _validate_selection_inputs(protocol_path, panel_path, manifest_path)

    panel_path.write_bytes(b"tampered")
    with pytest.raises(CRSPV2Error, match="Panel digest"):
        _validate_selection_inputs(protocol_path, panel_path, manifest_path)

    panel_path.write_bytes(b"panel-evidence")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["access_contract"][
        "primary_holdout_partitions_opened_for_outcome_rows"
    ] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(CRSPV2Error, match="holdout access receipt"):
        _validate_selection_inputs(protocol_path, panel_path, manifest_path)


def test_selection_publication_refuses_existing_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "existing"
    output_dir.mkdir()
    marker = output_dir / "marker.txt"
    marker.write_text("preserve", encoding="utf-8")

    with pytest.raises(CRSPV2Error, match="Refusing to overwrite"):
        run_selection(tmp_path / "missing.yaml", tmp_path / "missing.parquet", output_dir)
    assert marker.read_text(encoding="utf-8") == "preserve"

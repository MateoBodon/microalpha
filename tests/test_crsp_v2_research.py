from __future__ import annotations

import pandas as pd
import pytest

from microalpha.research.crsp_v2 import (
    CRSPV2Error,
    apply_constrained_trade_capacity,
    apply_trade_capacity,
    build_point_in_time_universe,
    estimate_rebalance_cost,
    ff12_industry,
    industry_neutral_weights,
    label_split,
    reconcile_ciz_delisting_returns,
    resolve_point_in_time_names,
)


def _protocol() -> dict:
    return {
        "windows": {
            "warmup": {"start": "2005-01-01", "end": "2006-12-31"},
            "training": {"start": "2007-01-01", "end": "2016-12-31"},
            "validation": {"start": "2017-01-01", "end": "2022-12-31"},
            "final_holdout": {"start": "2023-01-01", "end": "2025-12-31"},
        }
    }


def test_manifest_bound_split_labels() -> None:
    protocol = _protocol()
    assert label_split("2005-01-01", protocol) == "warmup"
    assert label_split("2010-06-30", protocol) == "training"
    assert label_split("2022-12-31", protocol) == "validation"
    assert label_split("2023-01-01", protocol) == "final_holdout"
    assert label_split("2026-01-01", protocol) == "outside"


def test_point_in_time_names_and_ciz_delisting_are_not_double_counted() -> None:
    daily = pd.DataFrame(
        {
            "permno": [10001, 10001],
            "dlycaldt": ["2005-01-03", "2005-01-04"],
            "dlydelflg": ["N", "Y"],
            "dlyret": [0.02, -0.40],
            "dlyretmissflg": ["NA", "NA"],
            "ticker": ["ALFA", None],
            "primaryexch": ["N", None],
            "sharetype": ["NS", None],
            "securitytype": ["EQTY", None],
            "securitysubtype": ["COM", None],
            "usincflg": ["Y", None],
            "conditionaltype": ["RW", None],
            "tradingstatusflg": ["A", None],
            "siccd": [3571, None],
        }
    )
    names = pd.DataFrame(
        {
            "permno": [10001],
            "namedt": ["2000-01-01"],
            "nameenddt": ["2005-01-03"],
            "ticker": ["ALFA"],
            "primaryexch": ["N"],
            "sharetype": ["NS"],
            "securitytype": ["EQTY"],
            "securitysubtype": ["COM"],
            "usincflg": ["Y"],
            "conditionaltype": ["RW"],
            "tradingstatusflg": ["A"],
            "siccd": [3571],
        }
    )
    resolved = resolve_point_in_time_names(daily.iloc[[0]], names)
    assert resolved.loc[0, "name_ticker"] == "ALFA"

    delists = pd.DataFrame(
        {
            "permno": [10001],
            "delistingdt": ["2005-01-03"],
            "deldlydt": ["2005-01-04"],
            "delret": [-0.40],
            "delretmisstype": ["NA"],
        }
    )
    reconciled = reconcile_ciz_delisting_returns(daily, delists)
    assert reconciled.loc[1, "total_return"] == pytest.approx(-0.40)
    assert bool(reconciled.loc[1, "delisting_return_reconciled"])

    bad_delists = delists.assign(delret=-0.25)
    with pytest.raises(CRSPV2Error, match="disagree"):
        reconcile_ciz_delisting_returns(daily, bad_delists)


def test_ff12_mapping_and_point_in_time_universe() -> None:
    assert ff12_industry(3571) == "BusEq"
    assert ff12_industry(6021) == "Money"
    assert ff12_industry(1311) == "Enrgy"
    assert ff12_industry(None) == "Other"

    frame = pd.DataFrame(
        {
            "permno": [1, 2],
            "formation_date": ["2022-12-30", "2022-12-30"],
            "sharetype": ["NS", "NS"],
            "securitytype": ["EQTY", "EQTY"],
            "securitysubtype": ["COM", "COM"],
            "usincflg": ["Y", "Y"],
            "primaryexch": ["N", "Q"],
            "conditionaltype": ["RW", "RW"],
            "tradingstatusflg": ["A", "A"],
            "price": [20.0, 3.0],
            "market_cap_usd": [1_000_000_000.0, 1_000_000_000.0],
            "adv_60_usd": [50_000_000.0, 50_000_000.0],
            "history_months": [24, 24],
            "siccd": [3571, 6021],
        }
    )
    rules = {
        "sharetype": ["NS"],
        "securitytype": ["EQTY"],
        "securitysubtype": ["COM"],
        "usincflg": ["Y"],
        "primaryexch": ["N", "A", "Q"],
        "conditionaltype": ["RW"],
        "tradingstatusflg": ["A"],
        "minimum_price": 5.0,
        "minimum_market_cap_usd": 250_000_000.0,
        "minimum_60d_median_dollar_volume_usd": 5_000_000.0,
        "minimum_return_history_months": 12,
    }
    universe = build_point_in_time_universe(frame, rules)
    assert universe["permno"].tolist() == [1]
    assert universe["industry"].tolist() == ["BusEq"]


def test_industry_neutral_weights_capacity_turnover_and_costs() -> None:
    snapshot = pd.DataFrame(
        {
            "permno": list(range(1, 9)),
            "industry": ["BusEq"] * 4 + ["Money"] * 4,
            "score": [4.0, 2.0, -2.0, -4.0, 3.0, 1.0, -1.0, -3.0],
            "volatility_126d": [0.02] * 8,
        }
    )
    target = industry_neutral_weights(
        snapshot,
        weighting="inverse_vol_126d",
        sleeve_fraction=0.25,
        target_gross=1.0,
        max_industry_gross_weight=0.50,
        max_single_name_weight=0.30,
    )
    assert target.abs().sum() == pytest.approx(1.0)
    assert target.sum() == pytest.approx(0.0)
    industry = snapshot.set_index("permno")["industry"]
    assert target.groupby(industry.reindex(target.index)).sum().abs().max() < 1e-12

    previous = pd.Series(dtype=float)
    adv = pd.Series(100_000_000.0, index=target.index)
    adv.loc[target.index[0]] = 100_000.0
    capacity = apply_trade_capacity(
        previous,
        target,
        adv,
        capital_usd=15_000_000.0,
        max_participation=0.02,
        max_single_name_weight=0.30,
    )
    assert capacity.fill_ratio < 1.0
    assert capacity.executed_turnover < capacity.requested_turnover
    assert target.index[0] in capacity.constrained_names

    spreads = pd.Series(10.0, index=capacity.executed_weights.index)
    spreads.iloc[0] = float("nan")
    costs = estimate_rebalance_cost(
        previous,
        capacity.executed_weights,
        adv,
        spreads,
        capital_usd=15_000_000.0,
        commission_bps_each_side=5.0,
        impact_bps_at_one_percent_adv=10.0,
        annual_short_borrow_bps=300.0,
        holding_days=21,
        fallback_full_spread_bps=10.0,
    )
    assert costs["total_cost_dollars"] > 0.0
    assert costs["one_way_turnover"] == pytest.approx(capacity.executed_turnover)
    assert costs["fallback_spread_count"] == 1.0


def test_inverse_volatility_name_cap_redistributes_without_losing_neutrality() -> None:
    snapshot = pd.DataFrame(
        {
            "permno": list(range(1, 9)),
            "industry": ["BusEq"] * 8,
            "score": [8.0, 7.0, 6.0, 5.0, -5.0, -6.0, -7.0, -8.0],
            "volatility_126d": [0.01, 1.0, 0.5, 0.5, 0.5, 0.5, 1.0, 0.01],
        }
    )
    weights = industry_neutral_weights(
        snapshot,
        weighting="inverse_vol_126d",
        sleeve_fraction=0.25,
        target_gross=1.0,
        max_industry_gross_weight=1.0,
        max_single_name_weight=0.30,
    )
    assert weights.abs().max() <= 0.30 + 1e-12
    assert weights.abs().sum() == pytest.approx(1.0)
    assert weights.sum() == pytest.approx(0.0)


def test_industry_gross_cap_redistributes_and_fails_when_infeasible() -> None:
    rows: list[dict[str, float | int | str]] = []
    permno = 1
    for industry, count in [("BusEq", 10)] + [
        (f"Industry-{index}", 2) for index in range(1, 8)
    ]:
        for rank in range(count):
            rows.append(
                {
                    "permno": permno,
                    "industry": industry,
                    "score": float(count - rank),
                    "volatility_126d": 0.02,
                }
            )
            permno += 1
    snapshot = pd.DataFrame(rows)

    weights = industry_neutral_weights(
        snapshot,
        weighting="equal",
        sleeve_fraction=0.50,
        target_gross=1.0,
        max_industry_gross_weight=0.15,
        max_single_name_weight=0.10,
    )
    industry = snapshot.set_index("permno")["industry"]
    industry_gross = weights.abs().groupby(industry.reindex(weights.index)).sum()
    assert industry_gross.max() <= 0.15 + 1e-12
    assert industry_gross.loc["BusEq"] == pytest.approx(0.15)
    assert weights.abs().sum() == pytest.approx(1.0)

    with pytest.raises(CRSPV2Error, match="Industry gross/name caps are infeasible"):
        industry_neutral_weights(
            snapshot.loc[snapshot["industry"].isin(["BusEq", "Industry-1"])],
            weighting="equal",
            sleeve_fraction=0.50,
            target_gross=1.0,
            max_industry_gross_weight=0.15,
            max_single_name_weight=0.10,
        )


def test_name_capacity_is_applied_before_industry_gross_is_distributed() -> None:
    rows: list[dict[str, float | int | str]] = []
    permno = 1
    industry_counts = [("Large", 100)] + [
        (f"Small-{index:02d}", 2) for index in range(50)
    ]
    for industry, count in industry_counts:
        for rank in range(count):
            rows.append(
                {
                    "permno": permno,
                    "industry": industry,
                    "score": float(count - rank),
                    "volatility_126d": 0.02,
                }
            )
            permno += 1
    snapshot = pd.DataFrame(rows)

    weights = industry_neutral_weights(
        snapshot,
        sleeve_fraction=0.10,
        target_gross=1.0,
        max_industry_gross_weight=1.0,
        max_single_name_weight=0.02,
    )

    industry = snapshot.set_index("permno")["industry"]
    gross = weights.abs().groupby(industry.reindex(weights.index)).sum()
    assert gross["Large"] == pytest.approx(0.40)
    assert sorted(gross.drop("Large")) == pytest.approx([0.012] * 50)
    assert weights.abs().max() <= 0.02 + 1e-12


def test_constrained_capacity_preserves_actual_industry_neutrality() -> None:
    target = pd.Series({1: 0.10, 2: -0.10, 3: 0.10, 4: -0.10})
    previous = pd.Series(dtype=float)
    adv = pd.Series({1: 1_000_000.0, 2: 100_000_000.0, 3: 100_000_000.0, 4: 100_000_000.0})
    industry = pd.Series({1: "A", 2: "A", 3: "B", 4: "B"})

    result = apply_constrained_trade_capacity(
        previous,
        target,
        adv,
        industry,
        capital_usd=1_000_000.0,
        max_participation=0.02,
        max_single_name_weight=0.20,
        max_industry_gross_weight=0.20,
    )

    executed = result.executed_weights
    assert executed.loc[1] == pytest.approx(0.02)
    assert executed.loc[2] == pytest.approx(-0.02)
    assert executed.groupby(industry).sum().abs().max() < 1e-9
    assert executed.abs().groupby(industry).sum().max() <= 0.20 + 1e-9
    assert result.fill_ratio < 1.0

from __future__ import annotations

import pandas as pd

from scripts.build_wrds_signals import _build_signals


def test_build_signals_filters_and_computes_scores(tmp_path) -> None:
    universe = tmp_path / "universe.csv"
    rows = [
        {"symbol": "AAA", "date": "2020-01-31", "close": 100.0, "adv_20": 5_000_000, "sector": "Tech"},
        {"symbol": "AAA", "date": "2020-02-29", "close": 110.0, "adv_20": 5_500_000, "sector": "Tech"},
        {"symbol": "AAA", "date": "2020-03-31", "close": 120.0, "adv_20": 6_000_000, "sector": "Tech"},
        {"symbol": "AAA", "date": "2020-04-30", "close": 130.0, "adv_20": 6_500_000, "sector": "Tech"},
        {"symbol": "AAA", "date": "2020-05-31", "close": 135.0, "adv_20": 6_700_000, "sector": "Tech"},
            {"symbol": "BBB", "date": "2020-01-31", "close": 50.0, "adv_20": 1_000_000, "sector": "Energy"},
            {"symbol": "BBB", "date": "2020-02-29", "close": 55.0, "adv_20": 1_200_000, "sector": "Energy"},
            {"symbol": "BBB", "date": "2020-03-31", "close": 60.0, "adv_20": 1_300_000, "sector": "Energy"},
            {"symbol": "BBB", "date": "2020-04-30", "close": 65.0, "adv_20": 1_400_000, "sector": "Energy"},
            {"symbol": "BBB", "date": "2020-05-31", "close": 70.0, "adv_20": 1_500_000, "sector": "Energy"},
        ]
    pd.DataFrame(rows).to_csv(universe, index=False)

    output = tmp_path / "signals.csv"
    _build_signals(
        universe,
        output,
        lookback_months=2,
        skip_months=1,
        min_adv=2_000_000,  # filter out BBB rows
    )

    result = pd.read_csv(output)
    # Only AAA rows should remain and score should match the ratio of shifted closes
    assert set(result["symbol"]) == {"AAA"}
    assert len(result) > 0
    first = result.iloc[0]
    expected_score = (120.0 / 100.0) - 1.0
    assert abs(first["score"] - expected_score) < 1e-9
    expected_forward = (135.0 / 130.0) - 1.0
    assert abs(first["forward_return"] - expected_forward) < 1e-9

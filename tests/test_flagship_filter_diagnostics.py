import pandas as pd

from microalpha.strategies.flagship_mom import FlagshipMomentumStrategy, TRADING_DAYS_MONTH


def test_flagship_filter_diagnostics_counts(tmp_path):
    universe_path = tmp_path / "universe.csv"
    df = pd.DataFrame(
        {
            "date": ["2020-01-15", "2020-01-15", "2020-01-15"],
            "symbol": ["AAA", "BBB", "CCC"],
            "sector": ["A", "B", "C"],
            "adv_20": [200.0, 50.0, 200.0],
            "close": [5.0, 20.0, 20.0],
        }
    )
    df.to_csv(universe_path, index=False)

    required = (1 + 0) * TRADING_DAYS_MONTH + 1
    warmup_history = {
        "AAA": [10.0] * (required - 1) + [5.0],
        "BBB": [10.0] * (required - 1) + [20.0],
        "CCC": [10.0] * (required - 1) + [20.0],
    }

    strategy = FlagshipMomentumStrategy(
        symbols=["AAA", "BBB", "CCC"],
        universe_path=str(universe_path),
        lookback_months=1,
        skip_months=0,
        top_frac=1.0,
        bottom_frac=0.0,
        min_price=10.0,
        min_adv=100.0,
        warmup_history=warmup_history,
    )

    strategy._rebalance(pd.Timestamp("2020-01-31"), event_timestamp=0)

    diagnostics = strategy.get_filter_diagnostics()
    assert diagnostics["rebalance_count"] == 1
    entry = diagnostics["per_rebalance"][0]
    assert entry["universe_total"] == 3
    assert entry["with_history"] == 3
    assert entry["min_price_pass"] == 2
    assert entry["min_adv_pass"] == 1
    assert entry["frame_count"] == 1
    assert entry["long_target"] == 1
    assert entry["long_selected"] == 1
    assert entry["short_target"] == 0
    assert entry["short_selected"] == 0

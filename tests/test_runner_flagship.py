from __future__ import annotations

from pathlib import Path

import pandas as pd

from microalpha.runner import run_from_config


def _write_symbol_csv(path: Path, prices: list[float]) -> None:
    idx = pd.date_range("2024-01-01", periods=len(prices), freq="D")
    pd.DataFrame({"close": prices, "volume": [1_000_000] * len(prices)}, index=idx).to_csv(path)


def test_runner_executes_flagship_strategy(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    _write_symbol_csv(data_dir / "AAA.csv", [50 + i * 0.3 for i in range(40)])
    _write_symbol_csv(data_dir / "BBB.csv", [40 - i * 0.2 for i in range(40)])
    # base symbol (unused but required for config schema)
    _write_symbol_csv(data_dir / "SPY.csv", [100 + i * 0.1 for i in range(40)])

    universe = tmp_path / "universe.csv"
    pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "date": "2024-01-31",
                "sector": "TECH",
                "adv_20": 5_000_000.0,
                "adv_63": 5_000_000.0,
                "adv_126": 5_000_000.0,
                "market_cap_proxy": 1_000_000_000.0,
                "close": 55.0,
            },
            {
                "symbol": "BBB",
                "date": "2024-01-31",
                "sector": "HEALTH",
                "adv_20": 5_000_000.0,
                "adv_63": 5_000_000.0,
                "adv_126": 5_000_000.0,
                "market_cap_proxy": 1_000_000_000.0,
                "close": 42.0,
            },
        ]
    ).to_csv(universe, index=False)

    cfg = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 250_000.0,
        "seed": 7,
        "exec": {"type": "instant", "commission": 0.0},
        "strategy": {
            "name": "FlagshipMomentumStrategy",
            "params": {
                "universe_path": str(universe),
                "lookback_months": 1,
                "skip_months": 0,
                "top_frac": 0.5,
                "bottom_frac": 0.5,
                "max_positions_per_sector": 1,
                "min_adv": 0.0,
                "min_price": 0.0,
            },
        },
        "artifacts_dir": str(tmp_path / "artifacts"),
    }

    import yaml

    config_path = tmp_path / "flagship.yaml"
    config_path.write_text(yaml.safe_dump(cfg))

    result = run_from_config(str(config_path))
    metrics_path = Path(result["metrics"]["metrics_path"])
    assert metrics_path.exists()
    payload = metrics_path.read_text()
    assert "sharpe_ratio" in payload
    assert "sharpe_ratio_se" in payload

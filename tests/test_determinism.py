from pathlib import Path

import pandas as pd
import yaml

from microalpha.runner import run_from_config


def _make_config(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dates = pd.date_range("2025-01-01", periods=6, freq="D")
    prices = [100, 101, 99, 102, 98, 103]
    df = pd.DataFrame({"close": prices}, index=dates)
    df.to_csv(data_dir / "SPY.csv")

    config = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 100000.0,
        "seed": 13,
        "exec": {"type": "twap", "slices": 2},
        "strategy": {
            "name": "MeanReversionStrategy",
            "params": {"lookback": 2, "z_threshold": 0.5},
        },
        "artifacts_dir": str(tmp_path / "artifacts"),
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(config))
    return cfg_path


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes() if path.exists() else b""


def test_repeated_runs_are_deterministic(tmp_path):
    cfg_path = _make_config(tmp_path)

    result_one = run_from_config(str(cfg_path))
    result_two = run_from_config(str(cfg_path))

    art_one = Path(result_one["artifacts_dir"])
    art_two = Path(result_two["artifacts_dir"])

    assert _read_bytes(art_one / "equity_curve.csv") == _read_bytes(
        art_two / "equity_curve.csv"
    )
    assert _read_bytes(art_one / "metrics.json") == _read_bytes(
        art_two / "metrics.json"
    )

    trades_one = _read_bytes(art_one / "trades.jsonl")
    trades_two = _read_bytes(art_two / "trades.jsonl")
    assert trades_one == trades_two

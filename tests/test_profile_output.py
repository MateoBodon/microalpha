from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import yaml

from microalpha.runner import run_from_config


def _make_cfg(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    dates = pd.date_range("2025-01-01", periods=5, freq="D")
    df = pd.DataFrame({"close": [100, 101, 102, 103, 104]}, index=dates)
    df.to_csv(data_dir / "SPY.csv")

    cfg = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 100000.0,
        "seed": 1,
        "exec": {"type": "instant", "commission": 0.0},
        "strategy": {"name": "MeanReversionStrategy", "params": {"lookback": 2, "z_threshold": 0.5}},
        "artifacts_dir": str(tmp_path / "artifacts"),
    }
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return path


def test_profile_written_to_run_artifacts(tmp_path: Path, monkeypatch) -> None:
    cfg_path = _make_cfg(tmp_path)
    monkeypatch.setenv("MICROALPHA_PROFILE", "1")

    result = run_from_config(str(cfg_path))
    art = Path(result["artifacts_dir"])
    prof = art / "profile.pstats"
    assert prof.exists(), "expected profile output under artifacts directory"


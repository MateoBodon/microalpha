from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from microalpha.runner import run_from_config


def _write_symbol(df: pd.DataFrame, root: Path, symbol: str) -> None:
    (root / f"{symbol}.csv").write_text(df.to_csv(index=True))


def test_cs_momentum_smoke(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    idx = pd.date_range("2020-01-01", periods=90, freq="D")
    # Three symbols: A strongest, B medium, C weakest
    a = pd.DataFrame({"close": 100 + (idx - idx[0]).days * 0.5}, index=idx)
    b = pd.DataFrame({"close": 100 + (idx - idx[0]).days * 0.2}, index=idx)
    c = pd.DataFrame({"close": 100 + (idx - idx[0]).days * 0.05}, index=idx)
    _write_symbol(a, data_dir, "A")
    _write_symbol(b, data_dir, "B")
    _write_symbol(c, data_dir, "C")

    cfg = {
        "data_path": str(data_dir),
        "symbol": "SPY",
        "cash": 100000.0,
        "seed": 11,
        "exec": {"type": "instant", "commission": 0.0},
        "strategy": {
            "name": "CrossSectionalMomentum",
            "params": {"symbols": ["A", "B", "C"], "lookback_months": 2, "skip_months": 0, "top_frac": 0.34},
        },
        "artifacts_dir": str(tmp_path / "artifacts"),
    }
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))

    result = run_from_config(str(cfg_path))
    # Expect artifacts, metrics, and a trades log path
    assert Path(result["artifacts_dir"]).exists()
    trades_path = Path(result.get("trades_path") or "")
    assert trades_path.exists()


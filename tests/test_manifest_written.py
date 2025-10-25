from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import yaml

from microalpha.config import BacktestCfg, ExecModelCfg, StrategyCfg
from microalpha.config_wfv import WalkForwardWindow, WFVCfg
from microalpha.runner import run_from_config
from microalpha.walkforward import run_walk_forward


def _make_run_config(tmp_path: Path) -> Path:
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
        "exec": {"type": "instant", "commission": 0.0},
        "strategy": {
            "name": "MeanReversionStrategy",
            "params": {"lookback": 2, "z_threshold": 0.5},
        },
        "artifacts_dir": str(tmp_path / "artifacts"),
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(config))
    return cfg_path


def _make_wfv_config(tmp_path: Path) -> Path:
    data_dir = tmp_path / "wfv_data"
    data_dir.mkdir()
    dates = pd.date_range("2025-01-01", periods=12, freq="D")
    df = pd.DataFrame({"date": dates, "close": range(100, 112)})
    df.to_csv(data_dir / "SPY.csv", index=False)

    config = WFVCfg(
        template=BacktestCfg(
            data_path=str(data_dir),
            symbol="SPY",
            cash=100000.0,
            seed=7,
            exec=ExecModelCfg(type="instant", commission=0.0),
            strategy=StrategyCfg(
                name="MeanReversionStrategy",
                params={"lookback": 2, "z": 0.5},
            ),
        ),
        walkforward=WalkForwardWindow(
            start="2025-01-01",
            end="2025-01-12",
            training_days=4,
            testing_days=2,
        ),
        grid={"lookback": [2, 3], "z": [0.5, 1.0]},
        artifacts_dir=str(tmp_path / "wfv_artifacts"),
    )

    cfg_path = tmp_path / "wfv_config.yaml"
    cfg_path.write_text(yaml.safe_dump(config.model_dump(mode="json")))
    return cfg_path


def test_run_and_wfv_emit_manifests(tmp_path: Path) -> None:
    run_cfg = _make_run_config(tmp_path)
    run_result = run_from_config(str(run_cfg))
    run_artifacts = Path(run_result["artifacts_dir"])

    run_manifest = run_artifacts / "manifest.json"
    run_metrics = run_artifacts / "metrics.json"

    assert run_manifest.exists()
    assert run_metrics.exists()

    manifest_payload = json.loads(run_manifest.read_text())
    required_fields = {
        "run_id",
        "git_sha",
        "microalpha_version",
        "python",
        "platform",
        "numpy_version",
        "pandas_version",
        "seed",
        "config_sha256",
    }
    assert required_fields.issubset(manifest_payload)
    assert manifest_payload["run_id"] == run_artifacts.name

    metrics_payload = json.loads(run_metrics.read_text())
    forbidden = {"run_id", "timestamp", "artifacts_dir", "config_path"}
    assert forbidden.isdisjoint(metrics_payload)

    wfv_cfg = _make_wfv_config(tmp_path)
    wfv_result = run_walk_forward(str(wfv_cfg))
    wfv_artifacts = Path(wfv_result["artifacts_dir"])

    wfv_manifest = wfv_artifacts / "manifest.json"
    wfv_metrics = wfv_artifacts / "metrics.json"

    assert wfv_manifest.exists()
    assert wfv_metrics.exists()

    wfv_manifest_payload = json.loads(wfv_manifest.read_text())
    assert required_fields.issubset(wfv_manifest_payload)
    assert wfv_manifest_payload["run_id"] == wfv_artifacts.name

    wfv_metrics_payload = json.loads(wfv_metrics.read_text())
    assert forbidden.isdisjoint(wfv_metrics_payload)

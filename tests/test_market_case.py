from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from microalpha.market_case import run_market_case, validate_market_case_artifacts


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.iterdir())
        if path.is_file()
    }


def test_market_case_is_byte_identical_and_schema_valid(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    result_a = run_market_case(first)
    result_b = run_market_case(second)

    assert result_a["receipt_sha256"] == result_b["receipt_sha256"]
    assert _hashes(first) == _hashes(second)
    assert validate_market_case_artifacts(first)["status"] == "pass"


def test_market_case_enforces_chronology_cost_identity_and_claim_boundary(
    tmp_path: Path,
):
    result = run_market_case(tmp_path)
    metrics = result["metrics"]
    daily = pd.read_csv(tmp_path / "daily.csv", parse_dates=["date"])

    assert (pd.to_datetime(daily["signal_available_date"]) < daily["date"]).all()
    residual = daily["gross_return"] - daily["total_cost"] - daily["strategy_net"]
    assert float(residual.abs().max()) < 5e-9
    assert metrics["fixed_specification"]["selected_on_oos_performance"] is False
    assert metrics["selection_control"]["num_candidates"] == 4
    assert metrics["selection_control"]["p_value"] >= 0.05
    assert metrics["investment_claim"] == "none"


def test_market_case_receipt_binds_source_and_every_artifact(tmp_path: Path):
    result = run_market_case(tmp_path)
    receipt = json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "data_manifest.json").read_text(encoding="utf-8"))

    assert len(result["receipt_sha256"]) == 64
    assert receipt["input"]["sha256"] == manifest["snapshot_sha256"]
    for name, expected in receipt["artifacts"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == expected

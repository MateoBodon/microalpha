from __future__ import annotations

from pathlib import Path

import pytest

from microalpha.artifact_verify import verify_artifact_dir
from microalpha.audit_lab import run_audit_lab
from microalpha.market_case import run_market_case


def test_public_verifier_accepts_audit_and_market_receipts(tmp_path: Path):
    audit = tmp_path / "audit"
    market = tmp_path / "market"
    run_audit_lab(audit)
    run_market_case(market)

    assert verify_artifact_dir(audit)["status"] == "pass"
    assert verify_artifact_dir(market)["status"] == "pass"


def test_public_verifier_rejects_tampering(tmp_path: Path):
    audit = tmp_path / "audit"
    run_audit_lab(audit)
    (audit / "comparison.csv").write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ValueError, match="hash mismatch"):
        verify_artifact_dir(audit)

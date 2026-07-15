import hashlib
import json
from pathlib import Path

from microalpha.audit_lab import run_audit_lab


def _hashes(root: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.iterdir())
        if path.is_file()
    }


def test_audit_lab_is_byte_identical_across_clean_paths(tmp_path: Path):
    first = tmp_path / "first"
    second = tmp_path / "another-location"
    result_a = run_audit_lab(first)
    result_b = run_audit_lab(second)

    assert result_a["receipt_sha256"] == result_b["receipt_sha256"]
    assert _hashes(first) == _hashes(second)


def test_audit_lab_detects_all_four_known_failure_modes(tmp_path: Path):
    result = run_audit_lab(tmp_path)
    payload = result["results"]

    assert payload["leakage"]["unavailable_rows_blocked"] == 756
    assert payload["leakage"]["inflation_removed"] > 10.0
    assert payload["execution"]["inflation_removed"] > 10.0
    assert payload["costs"]["gross_sharpe"] > payload["costs"]["net_sharpe"]
    assert payload["costs"]["reconciliation_error"] == 0.0
    assert payload["selection"]["noise_family_p_value"] >= 0.05
    assert payload["selection"]["planted_control_p_value"] <= 0.01


def test_receipt_hashes_every_canonical_artifact(tmp_path: Path):
    result = run_audit_lab(tmp_path)
    receipt = json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))

    assert len(result["receipt_sha256"]) == 64
    assert set(receipt["artifacts"]) == {
        "audit_results.json",
        "comparison.csv",
        "audit_lab.svg",
        "data_lineage.svg",
    }
    for name, expected in receipt["artifacts"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == expected
    assert receipt["generator"]["version"] == "0.2.0"
    for name, expected in receipt["generator"]["source_sha256"].items():
        source = Path("src/microalpha") / name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    serialized = (tmp_path / "receipt.json").read_text(encoding="utf-8")
    assert "/Users/" not in serialized
    assert "/Volumes/" not in serialized

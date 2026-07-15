"""Public artifact verification entry point."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, cast

from .market_case import SCHEMA_VERSION as MARKET_SCHEMA, validate_market_case_artifacts


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_artifact_dir(artifact_dir: str | Path) -> dict[str, object]:
    """Verify a receipt-bound Microalpha artifact directory.

    Market-case artifacts additionally enforce schema, chronology, and the cost
    identity.  Other receipt-bound fixtures receive the generic file-hash gate.
    """

    root = Path(artifact_dir)
    receipt_path = root / "receipt.json"
    if not receipt_path.is_file():
        raise ValueError(f"receipt.json not found in {root}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not isinstance(receipt, dict):
        raise ValueError("receipt must be a JSON object")
    schema_version = receipt.get("schema_version")
    artifacts = receipt.get("artifacts")
    if not isinstance(schema_version, str) or not isinstance(artifacts, dict):
        raise ValueError("receipt is missing schema_version or artifacts")

    if schema_version == MARKET_SCHEMA:
        result = validate_market_case_artifacts(root)
        result["receipt_sha256"] = _sha256(receipt_path.read_bytes())
        return result

    verified = 0
    for name, expected in cast(Mapping[str, str], artifacts).items():
        path = root / name
        if not path.is_file():
            raise ValueError(f"receipt artifact missing: {name}")
        if _sha256(path.read_bytes()) != expected:
            raise ValueError(f"artifact hash mismatch: {name}")
        verified += 1
    return {
        "status": "pass",
        "schema_version": schema_version,
        "artifacts": verified,
        "receipt_sha256": _sha256(receipt_path.read_bytes()),
    }

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    return env


def test_audit_demo_cli_writes_receipt_and_json_stdout(tmp_path: Path) -> None:
    output = tmp_path / "evidence"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "microalpha.cli",
            "audit-demo",
            "--out",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=_environment(),
    )
    payload = json.loads(completed.stdout)

    assert payload["receipt_sha256"]
    assert (output / "receipt.json").is_file()
    assert payload["results"]["claim_boundary"].endswith("not alpha or market evidence")


def test_cli_version_is_available() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "microalpha.cli", "--version"],
        check=True,
        capture_output=True,
        text=True,
        env=_environment(),
    )
    assert completed.stdout.startswith("cli.py ")

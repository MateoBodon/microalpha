from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_data_policy_check() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "check_data_policy.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

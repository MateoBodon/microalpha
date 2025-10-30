from __future__ import annotations

import subprocess
import sys


def test_cli_help_displays_commands() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "microalpha.cli", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )

    stdout = result.stdout.lower()
    assert "usage:" in stdout
    for command in ("run", "wfv", "report", "info"):
        assert command in stdout

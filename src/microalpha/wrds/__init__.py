"""Lightweight helpers for detecting local WRDS credentials and exports."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

WRDS_HOST: Final[str] = "wrds-pgdata.wharton.upenn.edu"
WRDS_PORT: Final[int] = 9737
WRDS_DB: Final[str] = "wrds"


def pgpass_path() -> Path:
    """Return the expected ~/.pgpass location."""

    return Path.home() / ".pgpass"


def has_pgpass_credentials(host: str = WRDS_HOST) -> bool:
    """Check whether ~/.pgpass contains a WRDS entry without leaking contents."""

    path = pgpass_path()
    if not path.exists():
        return False

    try:
        mode = path.stat().st_mode
    except OSError:
        return False
    if mode & 0o077:
        # PostgreSQL ignores entries unless perms are 600; treat as absent.
        return False

    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            fields = stripped.split(":")
            if len(fields) >= 5 and host in fields[0]:
                return True
    except OSError:
        return False
    return False


def has_wrds_credentials() -> bool:
    """True when ~/.pgpass or WRDS_USERNAME provides credentials."""

    if has_pgpass_credentials():
        return True
    return bool(os.getenv("WRDS_USERNAME"))


def get_wrds_data_root() -> Path | None:
    """Resolve WRDS data root from WRDS_DATA_ROOT without printing it."""

    raw = os.getenv("WRDS_DATA_ROOT")
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def has_wrds_data(min_entries: int = 1) -> bool:
    """Return True if WRDS_DATA_ROOT exists and looks non-empty."""

    root = get_wrds_data_root()
    if root is None or not root.exists():
        return False
    try:
        count = 0
        for _ in root.iterdir():
            count += 1
            if count >= min_entries:
                return True
    except OSError:
        return False
    return False


def wrds_status() -> dict[str, bool]:
    """Structured status for debugging/logging (no secrets)."""

    return {
        "pgpass": has_pgpass_credentials(),
        "env_username": bool(os.getenv("WRDS_USERNAME")),
        "data_root": has_wrds_data(),
    }


def is_wrds_path(path: Path) -> bool:
    """Return True if ``path`` resolves under WRDS_DATA_ROOT."""

    root = get_wrds_data_root()
    if root is None:
        return False
    try:
        resolved = path.expanduser().resolve()
    except FileNotFoundError:
        resolved = path.expanduser().resolve(strict=False)
    try:
        return root == resolved or root in resolved.parents
    except RuntimeError:
        return False


def guard_no_wrds_copy(path: Path, *, operation: str = "copy") -> None:
    """Raise if attempting to copy data directly from WRDS_DATA_ROOT."""

    if is_wrds_path(path):
        raise ValueError(
            f"Refusing to {operation} file from WRDS_DATA_ROOT: {path}"
        )


__all__ = [
    "WRDS_DB",
    "WRDS_HOST",
    "WRDS_PORT",
    "guard_no_wrds_copy",
    "get_wrds_data_root",
    "has_pgpass_credentials",
    "has_wrds_credentials",
    "has_wrds_data",
    "is_wrds_path",
    "pgpass_path",
    "wrds_status",
]

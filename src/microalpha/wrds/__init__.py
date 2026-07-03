"""Lightweight helpers for detecting local WRDS credentials and exports."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Final, Iterable, Mapping, Tuple

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


def _local_wrds_doc_path() -> Path | None:
    try:
        repo_root = Path(__file__).resolve().parents[3]
    except IndexError:
        return None
    return repo_root / "docs" / "local" / "WRDS_DATA_ROOT.md"


def _parse_wrds_root(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if stripped.startswith("export WRDS_DATA_ROOT="):
        return stripped.split("=", 1)[1].strip()
    if stripped.startswith("WRDS_DATA_ROOT="):
        return stripped.split("=", 1)[1].strip()
    if stripped.startswith("- "):
        candidate = stripped[2:].strip()
        if candidate and "/" in candidate and " " not in candidate:
            return candidate
    return None


def _load_local_wrds_data_root() -> Path | None:
    doc_path = _local_wrds_doc_path()
    if doc_path is None or not doc_path.exists():
        return None
    try:
        for line in doc_path.read_text(encoding="utf-8").splitlines():
            candidate = _parse_wrds_root(line)
            if not candidate or "$" in candidate:
                continue
            candidate = candidate.strip("'\"")
            path = Path(candidate).expanduser()
            try:
                resolved = path.resolve()
            except FileNotFoundError:
                resolved = path.resolve(strict=False)
            if resolved.exists():
                return resolved
    except OSError:
        return None
    return None


def get_wrds_data_root() -> Path | None:
    """Resolve WRDS data root from WRDS_DATA_ROOT (with local-doc fallback)."""

    raw = os.getenv("WRDS_DATA_ROOT")
    if raw:
        return Path(raw).expanduser().resolve()
    return _load_local_wrds_data_root()


def _iter_string_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_string_values(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_string_values(item)


def _config_mentions_wrds(config: Mapping[str, Any] | None) -> bool:
    if not config:
        return False
    if "wrds" in config:
        return True
    for text in _iter_string_values(config):
        if "WRDS_DATA_ROOT" in text:
            return True
        lowered = text.lower()
        if "/wrds/" in lowered or lowered.endswith("/wrds"):
            return True
    return False


def _parse_dataset_id_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    lowered = stripped.lower()
    if lowered.startswith("dataset_id"):
        _, _, remainder = stripped.partition("=")
        if not remainder:
            _, _, remainder = stripped.partition(":")
        candidate = remainder.strip()
        return candidate or None
    return stripped


def _dataset_id_from_version_file(root: Path) -> Tuple[str | None, str | None]:
    version_path = root / "WRDS_EXPORT_VERSION.txt"
    if not version_path.exists():
        return None, None
    try:
        for line in version_path.read_text(encoding="utf-8").splitlines():
            candidate = _parse_dataset_id_line(line)
            if candidate:
                return candidate, f"file:{version_path}"
    except OSError:
        return None, None
    return None, None


def resolve_wrds_dataset_id(config: Mapping[str, Any] | None = None) -> Tuple[str | None, str | None]:
    env_id = (os.getenv("WRDS_DATASET_ID") or "").strip()
    if env_id:
        return env_id, "env:WRDS_DATASET_ID"
    if config:
        wrds_cfg = config.get("wrds") if isinstance(config, Mapping) else None
        if isinstance(wrds_cfg, Mapping):
            cfg_id = str(wrds_cfg.get("dataset_id") or "").strip()
            if cfg_id:
                return cfg_id, "config:wrds.dataset_id"
    root = get_wrds_data_root()
    if root is not None:
        dataset_id, source = _dataset_id_from_version_file(root)
        if dataset_id:
            return dataset_id, source
    return None, None


def wrds_provenance(config: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    if config is not None and not _config_mentions_wrds(config):
        return None
    dataset_id, dataset_source = resolve_wrds_dataset_id(config)
    data_root = get_wrds_data_root()
    if dataset_id is None and data_root is None:
        return None
    payload: dict[str, Any] = {}
    if dataset_id:
        payload["dataset_id"] = dataset_id
    if dataset_source:
        payload["dataset_id_source"] = dataset_source
    if data_root:
        payload["data_root"] = str(data_root)
        version_path = data_root / "WRDS_EXPORT_VERSION.txt"
        if version_path.exists():
            payload["export_version_path"] = str(version_path)
    if config and isinstance(config.get("wrds"), Mapping):
        wrds_cfg = config["wrds"]
        export_manifest = wrds_cfg.get("export_manifest") or wrds_cfg.get("manifest_path")
        if export_manifest:
            payload["export_manifest"] = os.path.expandvars(str(export_manifest))
    return payload


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
    "resolve_wrds_dataset_id",
    "wrds_provenance",
    "has_pgpass_credentials",
    "has_wrds_credentials",
    "has_wrds_data",
    "is_wrds_path",
    "pgpass_path",
    "wrds_status",
]

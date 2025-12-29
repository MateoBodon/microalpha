#!/usr/bin/env python3
"""Validate docs/agent_runs run logs and META.json integrity."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


RUNS_ROOT = Path("docs/agent_runs")
TICKETS_FILE = Path("docs/CODEX_SPRINT_TICKETS.md")

REQUIRED_FILES = (
    "PROMPT.md",
    "COMMANDS.md",
    "RESULTS.md",
    "TESTS.md",
    "META.json",
)

REQUIRED_META_KEYS = (
    "run_name",
    "ticket_id",
    "started_at_utc",
    "finished_at_utc",
    "git_sha_before",
    "git_sha_after",
    "branch_name",
    "host_env_notes",
    "dataset_id",
    "config_paths",
    "config_sha256",
    "artifact_paths",
    "report_paths",
    "web_sources",
)

TICKET_RE = re.compile(r"^ticket-\d{2}$")
TICKET_HEADER_RE = re.compile(r"^##\s+(ticket-\d{2})\b", re.IGNORECASE)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load_ticket_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    tickets: set[str] = set()
    for line in path.read_text().splitlines():
        match = TICKET_HEADER_RE.match(line.strip())
        if match:
            tickets.add(match.group(1))
    return tickets


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def validate_meta(meta_path: Path, run_dir: Path, ticket_ids: set[str], errors: list[str]) -> None:
    try:
        data = json.loads(meta_path.read_text())
    except Exception as exc:  # pragma: no cover - generic parse guard
        errors.append(f"{meta_path}: JSON parse error: {exc}")
        return

    for key in REQUIRED_META_KEYS:
        if key not in data:
            errors.append(f"{meta_path}: missing required key '{key}'")

    run_name = data.get("run_name")
    require(
        run_name == run_dir.name,
        errors,
        f"{meta_path}: run_name '{run_name}' does not match directory '{run_dir.name}'",
    )

    ticket_id = data.get("ticket_id")
    require(
        isinstance(ticket_id, str) and TICKET_RE.match(ticket_id),
        errors,
        f"{meta_path}: ticket_id '{ticket_id}' is not in ticket-XX format",
    )
    if isinstance(ticket_id, str) and ticket_ids:
        require(
            ticket_id in ticket_ids,
            errors,
            f"{meta_path}: ticket_id '{ticket_id}' not found in {TICKETS_FILE}",
        )

    for key in ("git_sha_before", "git_sha_after"):
        sha_val = data.get(key)
        require(
            isinstance(sha_val, str) and SHA_RE.match(sha_val),
            errors,
            f"{meta_path}: {key} '{sha_val}' is not a 40-hex SHA",
        )

    for key in ("started_at_utc", "finished_at_utc"):
        val = data.get(key)
        require(
            isinstance(val, str),
            errors,
            f"{meta_path}: {key} must be a string",
        )

    dataset_id = data.get("dataset_id")
    require(
        isinstance(dataset_id, str),
        errors,
        f"{meta_path}: dataset_id must be a string",
    )

    type_checks = {
        "config_paths": list,
        "config_sha256": dict,
        "artifact_paths": list,
        "report_paths": list,
        "web_sources": list,
    }
    for key, expected_type in type_checks.items():
        val = data.get(key)
        require(
            isinstance(val, expected_type),
            errors,
            f"{meta_path}: {key} must be a {expected_type.__name__}",
        )


def validate_run_logs() -> int:
    errors: list[str] = []
    if not RUNS_ROOT.exists():
        errors.append(f"{RUNS_ROOT} does not exist")
        for err in errors:
            print(err)
        return 1

    ticket_ids = load_ticket_ids(TICKETS_FILE)
    if not ticket_ids:
        errors.append(f"No ticket headers found in {TICKETS_FILE}")

    for run_dir in sorted(p for p in RUNS_ROOT.iterdir() if p.is_dir()):
        for filename in REQUIRED_FILES:
            path = run_dir / filename
            if not path.exists():
                errors.append(f"{run_dir}: missing required file {filename}")

        meta_path = run_dir / "META.json"
        if meta_path.exists():
            validate_meta(meta_path, run_dir, ticket_ids, errors)

    if errors:
        for err in errors:
            print(err)
        return 1
    print("All run logs validated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(validate_run_logs())

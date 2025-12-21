#!/usr/bin/env python3
"""Create a Prompt-3 bundle for Codex audit artifacts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} must be set")
    return value


def _copy_path(src: Path, dest_root: Path, missing: list[str]) -> None:
    if not src.exists():
        missing.append(str(src))
        return
    dest = dest_root / src
    if src.is_dir():
        shutil.copytree(src, dest)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def _load_meta_shas(meta_path: Path) -> tuple[str | None, str | None]:
    if not meta_path.exists():
        return None, None
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, None
    return payload.get("git_sha_before"), payload.get("git_sha_after")


def main() -> None:
    ticket = _env("TICKET")
    run_name = _env("RUN_NAME")

    timestamp = time.strftime("%Y-%m-%dT%H-%M-%SZ", time.gmtime())
    bundle_dir = Path("docs/gpt_bundles")
    bundle_dir.mkdir(parents=True, exist_ok=True)
    stage = bundle_dir / f".staging_{timestamp}_{ticket}_{run_name}"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    required = [
        Path("AGENTS.md"),
        Path("docs/PLAN_OF_RECORD.md"),
        Path("docs/DOCS_AND_LOGGING_SYSTEM.md"),
        Path("docs/CODEX_SPRINT_TICKETS.md"),
        Path("PROGRESS.md"),
        Path("project_state/CURRENT_RESULTS.md"),
        Path("project_state/KNOWN_ISSUES.md"),
        Path("project_state/CONFIG_REFERENCE.md"),
        Path(f"docs/agent_runs/{run_name}"),
    ]

    for item in required:
        _copy_path(item, stage, missing)

    diff_path = stage / "DIFF.patch"
    last_commit_path = stage / "LAST_COMMIT.txt"

    sha_before, sha_after = _load_meta_shas(
        Path(f"docs/agent_runs/{run_name}/META.json")
    )
    diff_cmd = ["git", "diff"]
    if sha_before and sha_after:
        diff_cmd.append(f"{sha_before}..{sha_after}")
    else:
        diff_cmd.append("HEAD~1..HEAD")

    diff_text = subprocess.check_output(diff_cmd, text=True, stderr=subprocess.STDOUT)
    diff_path.write_text(diff_text, encoding="utf-8")

    last_commit = subprocess.check_output(
        ["git", "log", "-1", "--pretty=format:%H%n%an%n%ad%n%s"],
        text=True,
    )
    last_commit_path.write_text(last_commit + "\n", encoding="utf-8")

    bundle_path = bundle_dir / f"{timestamp}_{ticket}_{run_name}.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in stage.rglob("*"):
            if file.is_file():
                zf.write(file, file.relative_to(stage))

    shutil.rmtree(stage)
    print(bundle_path)
    if missing:
        print("Missing bundle items:", ", ".join(missing))


if __name__ == "__main__":
    main()

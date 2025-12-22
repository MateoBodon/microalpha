#!/usr/bin/env python3
"""Create a Prompt-3 bundle for Codex audit artifacts."""

from __future__ import annotations

import json
import os
import re
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


def _load_meta(meta_path: Path) -> dict:
    if not meta_path.exists():
        raise SystemExit(f"Missing META.json at {meta_path}")
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid META.json at {meta_path}: {exc}") from exc


def _require_ticket_defined(meta_path: Path, sprint_path: Path) -> str:
    meta = _load_meta(meta_path)
    ticket_id = meta.get("ticket_id")
    if not ticket_id:
        raise SystemExit(f"Missing ticket_id in {meta_path}")
    if not sprint_path.exists():
        raise SystemExit(f"Missing sprint ticket file at {sprint_path}")
    sprint_text = sprint_path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^##\s+{re.escape(ticket_id)}\b", re.MULTILINE)
    if not pattern.search(sprint_text):
        raise SystemExit(
            f"Ticket '{ticket_id}' not found in {sprint_path}.\n"
            f"Add a section header like '## {ticket_id} — ...' before bundling."
        )
    return ticket_id


def _resolve_ref(ref: str) -> str:
    try:
        resolved = subprocess.check_output(
            ["git", "rev-parse", ref], text=True, stderr=subprocess.STDOUT
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Failed to resolve git ref '{ref}': {exc.output}") from exc
    if not resolved:
        raise SystemExit(f"Failed to resolve git ref '{ref}'")
    return resolved


def _derive_diff_range(meta_path: Path) -> tuple[str, str, str]:
    sha_before, sha_after = _load_meta_shas(meta_path)
    if sha_before and sha_after:
        base = _resolve_ref(sha_before)
        head = _resolve_ref(sha_after)
        source = f"META.json ({sha_before}..{sha_after})"
        return base, head, source

    base = _resolve_ref("HEAD~1")
    head = _resolve_ref("HEAD")
    source = "default HEAD~1..HEAD"
    return base, head, source


def _write_commits(stage: Path, base: str, head: str, source: str) -> None:
    commits = subprocess.check_output(
        ["git", "log", "--reverse", "--pretty=format:%H %s", f"{base}..{head}"],
        text=True,
        stderr=subprocess.STDOUT,
    )
    payload = "\n".join(
        [
            f"base: {base}",
            f"head: {head}",
            f"source: {source}",
            "",
            "commits:",
            commits.strip(),
            "",
        ]
    )
    (stage / "COMMITS.txt").write_text(payload, encoding="utf-8")


def _require_clean_worktree() -> None:
    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain"], text=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Failed to read git status: {exc.output}") from exc
    if status.strip():
        raise SystemExit(
            "Refusing to bundle: git worktree is dirty.\n"
            "Commit, stash, or clean changes before running gpt-bundle.\n"
            "git status --porcelain output:\n"
            f"{status}"
        )


def _collect_check_files(stage: Path, run_name: str) -> list[Path]:
    files = [Path("PROGRESS.md")]
    run_dir = Path("docs/agent_runs") / run_name
    staged_run_dir = stage / run_dir
    if staged_run_dir.exists():
        for file in staged_run_dir.rglob("*"):
            if file.is_file():
                files.append(file.relative_to(stage))
    return files


def _hydrate_base_file(base: str, rel_path: Path, dest_root: Path) -> None:
    try:
        content = subprocess.check_output(
            ["git", "show", f"{base}:{rel_path.as_posix()}"],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        return
    target = dest_root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def _verify_patch_matches(
    diff_path: Path,
    stage: Path,
    base: str,
    head: str,
    run_name: str,
) -> None:
    check_files = _collect_check_files(stage, run_name)
    if not check_files:
        return

    scratch = stage / ".patch_check"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True, exist_ok=True)

    for rel_path in check_files:
        _hydrate_base_file(base, rel_path, scratch)

    for rel_path in check_files:
        patch_text = subprocess.check_output(
            [
                "git",
                "diff",
                f"{base}..{head}",
                "--",
                rel_path.as_posix(),
            ],
            text=True,
            stderr=subprocess.STDOUT,
        )
        if not patch_text.strip():
            continue
        patch_file = scratch / f".patch_{rel_path.as_posix().replace('/', '_')}"
        patch_file.write_text(patch_text, encoding="utf-8")
        try:
            subprocess.check_output(
                [
                    "git",
                    "apply",
                    "--unsafe-paths",
                    "--directory",
                    str(scratch),
                    str(patch_file),
                ],
                text=True,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            raise SystemExit(
                "DIFF.patch failed to apply cleanly during bundle verification:\n"
                f"{exc.output}"
            ) from exc

    mismatches: list[str] = []
    for rel_path in check_files:
        staged_file = stage / rel_path
        patched_file = scratch / rel_path
        if not staged_file.exists():
            continue
        if not patched_file.exists():
            mismatches.append(rel_path.as_posix())
            continue
        if staged_file.read_bytes() != patched_file.read_bytes():
            mismatches.append(rel_path.as_posix())

    if mismatches:
        raise SystemExit(
            "DIFF.patch does not reproduce bundled files for: "
            + ", ".join(sorted(mismatches))
        )


def main() -> None:
    ticket = _env("TICKET")
    run_name = _env("RUN_NAME")
    meta_path = Path(f"docs/agent_runs/{run_name}/META.json")
    _require_ticket_defined(meta_path, Path("docs/CODEX_SPRINT_TICKETS.md"))
    _require_clean_worktree()

    timestamp = os.environ.get("BUNDLE_TIMESTAMP") or time.strftime(
        "%Y-%m-%dT%H-%M-%SZ", time.gmtime()
    )
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

    base, head, source = _derive_diff_range(meta_path)
    _write_commits(stage, base, head, source)
    diff_cmd = ["git", "diff", f"{base}..{head}"]
    diff_text = subprocess.check_output(diff_cmd, text=True, stderr=subprocess.STDOUT)
    diff_path.write_text(diff_text, encoding="utf-8")
    _verify_patch_matches(diff_path, stage, base, head, run_name)

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
        message = "Missing bundle items: " + ", ".join(missing)
        print(message)
        raise SystemExit(message)


if __name__ == "__main__":
    main()

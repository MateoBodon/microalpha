#!/usr/bin/env python3
"""tools/agentic/project_state_refresh.py

Project-state refresher + packager.

This script is deterministic and LLM-free. It:
- (Optionally) runs a repo-specific project_state generator if present.
- Ensures a minimum `project_state/` skeleton exists.
- Captures git metadata under `project_state/_generated/`.
- Optionally emits a zip bundle for LLM context handoffs.

Default zip output path (tracking-policy compatible):
  artifacts/_local/project_state_bundles/project_state_<UTCSTAMP>.zip

Repo-specific generator (optional)
---------------------------------
If your repo has a richer project_state generator, this script will try to run it
*before* packaging. It looks for:

- tools/project_state_generate.py   (used in some repos)
- tools/project_state/generate.py

You can override with `--generator PATH` or skip with `--no-generate`.

"""  # noqa: D400

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple


def _run(cmd: list[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, cwd=str(cwd) if cwd else None, stderr=subprocess.STDOUT)
        return 0, out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output.decode("utf-8", errors="replace")


def _git_root(start: Path) -> Optional[Path]:
    code, out = _run(["git", "-C", str(start), "rev-parse", "--show-toplevel"])
    if code != 0:
        return None
    return Path(out.strip())


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _ensure_file(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if p.is_file():
            out.append(p)
    return sorted(out, key=lambda p: str(p))


TEMPLATE_INDEX = """# Project State Index

This folder holds a *curated* snapshot of how the project works.

- ARCHITECTURE.md
- RUNBOOK.md
- CURRENT_RESULTS.md
- KNOWN_ISSUES.md
- CONFIG_REFERENCE.md

Generated files live in `_generated/` and should not be hand-edited.
"""

TEMPLATE_ARCH = """# Architecture

(Describe the system at a high level: major components, data flow, boundaries.)
"""

TEMPLATE_RUNBOOK = """# Runbook

(How to run tests, build, lint, execute key scripts, and reproduce results.)
"""

TEMPLATE_RESULTS = """# Current Results

(What is the latest known-good output? Where are artifacts? How to reproduce?)
"""

TEMPLATE_ISSUES = """# Known Issues

- (Issue) — (impact) — (workaround) — (owner/ticket)
"""

TEMPLATE_CONFIG = """# Config Reference

(List important configuration knobs, env vars, and defaults.)
"""


def _write_git_metadata(repo: Path, gen_dir: Path) -> None:
    gen_dir.mkdir(parents=True, exist_ok=True)
    _, head = _run(["git", "-C", str(repo), "rev-parse", "HEAD"])
    _, branch = _run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"])
    _, status = _run(["git", "-C", str(repo), "status", "--porcelain=v1", "-b"])
    _, log = _run(["git", "-C", str(repo), "log", "-n", "50", "--oneline", "--decorate"])
    (gen_dir / "git_head.txt").write_text(head, encoding="utf-8")
    (gen_dir / "git_branch.txt").write_text(branch, encoding="utf-8")
    (gen_dir / "git_status.txt").write_text(status, encoding="utf-8")
    (gen_dir / "git_log.txt").write_text(log, encoding="utf-8")


def _find_generator(repo: Path) -> Optional[Path]:
    candidates = [
        repo / "tools" / "project_state_generate.py",
        repo / "tools" / "project_state" / "generate.py",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


def _run_generator(repo: Path, gen: Path) -> Tuple[bool, str]:
    code, out = _run([sys.executable, str(gen)], cwd=repo)
    return (code == 0), out


def _zip_selected(repo: Path, zip_path: Path) -> None:
    include_paths: list[Path] = []

    def add_if_exists(rel: str) -> None:
        p = repo / rel
        if p.exists() and p.is_file():
            include_paths.append(p)

    # Root docs
    for rel in ["AGENTS.md", "PROJECT.md", "PROGRESS.md", "TRACKING_POLICY.md"]:
        add_if_exists(rel)

    # Docs
    for rel in [
        "docs/PLAN_OF_RECORD.md",
        "docs/RUNBOOK.md",
        "docs/DECISIONS.md",
        "docs/DOCS_AND_LOGGING_SYSTEM.md",
        "docs/CODEX_SPRINT_TICKETS.md",
        "docs/NOW.md",
        "docs/TICKETS.md",
    ]:
        add_if_exists(rel)

    # project_state (all)
    ps_dir = repo / "project_state"
    if ps_dir.exists():
        include_paths.extend([p for p in _iter_files(ps_dir)])

    zip_path.parent.mkdir(parents=True, exist_ok=True)
    include_paths = sorted(set(include_paths), key=lambda p: str(p))

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        meta = (
            f"generated_at_utc: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
            f"repo_root: {repo}\n"
        )
        zf.writestr("PROJECT_STATE_META.md", meta)

        for p in include_paths:
            arc = str(p.relative_to(repo))
            zf.write(p, arc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="store_true", help="Emit a project_state zip bundle")
    ap.add_argument("--out-dir", default=None, help="Zip output directory (default: artifacts/_local/project_state_bundles)")
    ap.add_argument("--no-generate", action="store_true", help="Skip running any repo-specific generator")
    ap.add_argument("--generator", default=None, help="Explicit generator path (python script)")
    args = ap.parse_args()

    start = Path.cwd()
    repo = _git_root(start) or start

    # Optional generator
    if not args.no_generate:
        gen = Path(args.generator).resolve() if args.generator else _find_generator(repo)
        if gen:
            ok, out = _run_generator(repo, gen)
            if not ok:
                print(f"[warn] project_state generator failed: {gen}", file=sys.stderr)
                print(out, file=sys.stderr)

    ps = repo / "project_state"
    gen_dir = ps / "_generated"

    # Ensure skeleton docs exist (never overwrite).
    _ensure_file(ps / "INDEX.md", TEMPLATE_INDEX)
    _ensure_file(ps / "ARCHITECTURE.md", TEMPLATE_ARCH)
    _ensure_file(ps / "RUNBOOK.md", TEMPLATE_RUNBOOK)
    _ensure_file(ps / "CURRENT_RESULTS.md", TEMPLATE_RESULTS)
    _ensure_file(ps / "KNOWN_ISSUES.md", TEMPLATE_ISSUES)
    _ensure_file(ps / "CONFIG_REFERENCE.md", TEMPLATE_CONFIG)

    _write_git_metadata(repo, gen_dir)

    if args.zip:
        out_dir = Path(args.out_dir) if args.out_dir else (repo / "artifacts" / "_local" / "project_state_bundles")
        out_dir.mkdir(parents=True, exist_ok=True)
        zip_path = out_dir / f"project_state_{_utc_stamp()}.zip"
        _zip_selected(repo, zip_path)
        print(str(zip_path))
    else:
        print(str(ps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

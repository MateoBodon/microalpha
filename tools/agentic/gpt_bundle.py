#!/usr/bin/env python3
"""tools/agentic/gpt_bundle.py

Create a review bundle (zip) suitable for sending to an LLM reviewer.

Design goals
- Deterministic: stable file ordering; no LLM calls.
- Review-first: includes DIFF.patch (range diff) + key docs + run log.
- Dirty-tree tolerant: includes worktree/staged patches + untracked list when dirty.
- Tracking-policy compatible: default output under artifacts/_local/gpt_bundles (ignored).

Bundle contents (always)
- BUNDLE_META.md
- REPO_SNAPSHOT.md        (tracked-file inventory summary)
- DIFF.patch              (git diff --binary <base>..<head>)
- GIT_LOG.txt             (git log <base>..<head>)
- GIT_DIFF_STAT.txt
- GIT_STATUS.txt

Bundle contents (when dirty)
- WORKTREE.patch          (git diff)
- STAGED.patch            (git diff --cached)
- UNTRACKED_FILES.txt     (git ls-files --others --exclude-standard)

Bundle contents (best-effort, if present)
- Root docs: AGENTS.md, PROJECT.md, PROGRESS.md, TRACKING_POLICY.md
- docs/: PLAN_OF_RECORD.md, RUNBOOK.md, DECISIONS.md, DOCS_AND_LOGGING_SYSTEM.md, CODEX_SPRINT_TICKETS.md
- Ticket file under docs/tickets/
- Run log folder under docs/agent_runs/<RUN_NAME>/
- Selected project_state docs (ARCHITECTURE, RUNBOOK, CURRENT_RESULTS, KNOWN_ISSUES, CONFIG_REFERENCE, INDEX)

Usage
  python3 tools/agentic/gpt_bundle.py --ticket "ticket-10c_tracking-policy-wrds-local" --run-name "20260126_204606_ticket-10c_tracking-policy-wrds-local"

It prints the output zip path on success.

"""  # noqa: D400

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Tuple


# ------------------------------- helpers ------------------------------------


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


def _slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "bundle"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _safe_relpath(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except Exception:
        return str(path)


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p


# ------------------------------ git logic -----------------------------------


@dataclass(frozen=True)
class GitRange:
    base_ref: str
    base_sha: str
    head_sha: str
    branch: str
    upstream: str


def _git_head(repo: Path) -> str:
    code, out = _run(["git", "-C", str(repo), "rev-parse", "HEAD"])
    return out.strip() if code == 0 else ""


def _git_branch(repo: Path) -> str:
    code, out = _run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"])
    return out.strip() if code == 0 else ""


def _git_upstream(repo: Path) -> str:
    # Prefer the branch upstream (e.g., origin/main for a feature branch).
    code, out = _run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if code == 0 and out.strip():
        return out.strip()

    # Fallback to origin/HEAD symbolic ref (default branch).
    code, out = _run(["git", "-C", str(repo), "symbolic-ref", "refs/remotes/origin/HEAD"])
    if code == 0 and out.strip().startswith("refs/remotes/origin/"):
        return out.strip().replace("refs/remotes/origin/", "origin/")

    # Common defaults.
    for candidate in ["origin/main", "origin/master", "main", "master"]:
        code, _ = _run(["git", "-C", str(repo), "rev-parse", candidate])
        if code == 0:
            return candidate

    return ""


def _git_merge_base(repo: Path, a: str, b: str) -> str:
    code, out = _run(["git", "-C", str(repo), "merge-base", a, b])
    return out.strip() if code == 0 else ""


def _git_dirty(repo: Path) -> Tuple[bool, str]:
    code, out = _run(["git", "-C", str(repo), "status", "--porcelain=v1", "-b"])
    if code != 0:
        return False, out
    lines = out.splitlines()
    dirty = any(line and not line.startswith("##") for line in lines)
    return dirty, out


def _resolve_range(repo: Path, base_ref: Optional[str]) -> GitRange:
    head = _git_head(repo)
    branch = _git_branch(repo)

    upstream = _git_upstream(repo)
    use_ref = base_ref or upstream or ""

    base_sha = ""
    if use_ref:
        base_sha = _git_merge_base(repo, head, use_ref)

    # Final fallback: HEAD~1 if exists.
    if not base_sha:
        code, out = _run(["git", "-C", str(repo), "rev-parse", "HEAD~1"])
        if code == 0:
            base_sha = out.strip()
            use_ref = "HEAD~1"

    if not base_sha or not head:
        raise RuntimeError("Unable to resolve git range (is this a git repo with at least one commit?).")

    return GitRange(base_ref=use_ref, base_sha=base_sha, head_sha=head, branch=branch, upstream=upstream)


def _repo_snapshot_md(repo: Path, *, max_lines: int = 400) -> str:
    """Produce a compact, high-signal snapshot from tracked files."""
    code, out = _run(["git", "-C", str(repo), "ls-files"])
    files = out.splitlines() if code == 0 else []

    # Count by top-level directory.
    counts: dict[str, int] = {}
    for f in files:
        top = f.split("/", 1)[0] if "/" in f else "(root)"
        counts[top] = counts.get(top, 0) + 1

    lines = []
    lines.append(f"# Repo Snapshot\n")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
    lines.append(f"Tracked files: {len(files)}\n")
    lines.append("## Top-level counts\n")

    for k in sorted(counts.keys(), key=lambda x: (-counts[x], x)):
        lines.append(f"- {k}: {counts[k]}\n")

    lines.append("\n## Key docs (if present)\n")
    for rel in ["AGENTS.md", "PROJECT.md", "PROGRESS.md", "TRACKING_POLICY.md", "docs/RUNBOOK.md", "project_state/ARCHITECTURE.md"]:
        p = repo / rel
        if p.exists():
            lines.append(f"- {rel}\n")

    # Include a short sample of tracked paths for navigation.
    lines.append("\n## Sample tracked paths\n")
    sample = files[: max_lines]
    for f in sample:
        lines.append(f"- {f}\n")
    if len(files) > len(sample):
        lines.append(f"\n… truncated ({len(files) - len(sample)} more)\n")

    return "".join(lines)


# ----------------------------- bundling -------------------------------------


DEFAULT_INCLUDE_FILES = [
    "AGENTS.md",
    "PROJECT.md",
    "PROGRESS.md",
    "TRACKING_POLICY.md",
    "docs/PLAN_OF_RECORD.md",
    "docs/RUNBOOK.md",
    "docs/DECISIONS.md",
    "docs/DOCS_AND_LOGGING_SYSTEM.md",
    "docs/CODEX_SPRINT_TICKETS.md",
    "docs/NOW.md",
    "docs/TICKETS.md",
    # project_state (small, high-signal)
    "project_state/INDEX.md",
    "project_state/ARCHITECTURE.md",
    "project_state/RUNBOOK.md",
    "project_state/CURRENT_RESULTS.md",
    "project_state/KNOWN_ISSUES.md",
    "project_state/CONFIG_REFERENCE.md",
]


def _candidate_ticket_paths(repo: Path, ticket: str) -> list[Path]:
    if not ticket:
        return []
    tickets_dir = repo / "docs" / "tickets"
    if not tickets_dir.exists():
        return []

    # Exact match (allow user to pass full filename)
    p = tickets_dir / ticket
    if p.exists() and p.is_file():
        return [p]

    # Try common naming patterns.
    slug = _slug(ticket)
    candidates: list[Path] = []
    for child in tickets_dir.glob("*.md"):
        if slug in _slug(child.name):
            candidates.append(child)

    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[:3]


def _choose_run_dir(repo: Path, run_name: Optional[str], ticket: str) -> Optional[Path]:
    runs_root = repo / "docs" / "agent_runs"
    if not runs_root.exists():
        return None

    if run_name:
        p = runs_root / run_name
        if p.exists() and p.is_dir():
            return p

    slug = _slug(ticket) if ticket else ""
    dirs = [d for d in runs_root.iterdir() if d.is_dir()]
    if slug:
        dirs = [d for d in dirs if slug in _slug(d.name)]
    if not dirs:
        return None
    dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return dirs[0]


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_tree(src_dir: Path, dst_dir: Path, *, max_file_bytes: int, skipped: list[str]) -> None:
    for p in _iter_files(src_dir):
        rel = p.relative_to(src_dir)
        try:
            size = p.stat().st_size
        except Exception:
            skipped.append(f"{src_dir}/{rel}  (skipped: stat failed)")
            continue
        if size > max_file_bytes:
            skipped.append(f"{src_dir}/{rel}  (skipped: >{max_file_bytes} bytes)")
            continue
        out = dst_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _zip_dir(src_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    files = sorted([p for p in _iter_files(src_dir)], key=lambda p: str(p.relative_to(src_dir)))
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            arcname = str(p.relative_to(src_dir))
            zf.write(p, arcname)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticket", default="", help="Ticket id/label (used for heuristics + filename)")
    ap.add_argument("--run-name", default=None, help="Run log directory name under docs/agent_runs")
    ap.add_argument("--out-dir", default=None, help="Output directory (default: artifacts/_local/gpt_bundles)")
    ap.add_argument("--base", default=None, help="Base ref for range diff (default: branch upstream)")
    ap.add_argument("--max-file-bytes", type=int, default=1_000_000, help="Skip included files larger than this many bytes")
    ap.add_argument("--snapshot-max-lines", type=int, default=400, help="Max tracked paths to include in REPO_SNAPSHOT.md")
    args = ap.parse_args()

    start = Path.cwd()
    repo = _git_root(start) or start
    gr = _resolve_range(repo, args.base)

    dirty, status = _git_dirty(repo)

    out_dir = Path(args.out_dir) if args.out_dir else (repo / "artifacts" / "_local" / "gpt_bundles")
    _ensure_dir(out_dir)

    stamp = _utc_stamp()
    suffix = f"_ticket-{_slug(args.ticket)}" if args.ticket else ""
    zip_path = out_dir / f"gpt_bundle_{stamp}{suffix}.zip"

    skipped: list[str] = []

    with tempfile.TemporaryDirectory(prefix="gpt_bundle_") as td:
        work = Path(td)

        # Snapshot
        _write_text(work / "REPO_SNAPSHOT.md", _repo_snapshot_md(repo, max_lines=args.snapshot_max_lines))

        # Git artifacts
        _write_text(work / "GIT_STATUS.txt", status)

        _, log = _run(["git", "-C", str(repo), "log", "--oneline", "--decorate", f"{gr.base_sha}..{gr.head_sha}"])
        _write_text(work / "GIT_LOG.txt", log)

        _, stat = _run(["git", "-C", str(repo), "diff", "--stat", f"{gr.base_sha}..{gr.head_sha}"])
        _write_text(work / "GIT_DIFF_STAT.txt", stat)

        _, diff = _run(["git", "-C", str(repo), "diff", "--binary", f"{gr.base_sha}..{gr.head_sha}"])
        _write_text(work / "DIFF.patch", diff)

        if dirty:
            _, wt = _run(["git", "-C", str(repo), "diff"])
            _write_text(work / "WORKTREE.patch", wt)
            _, cached = _run(["git", "-C", str(repo), "diff", "--cached"])
            _write_text(work / "STAGED.patch", cached)
            _, untracked = _run(["git", "-C", str(repo), "ls-files", "--others", "--exclude-standard"])
            _write_text(work / "UNTRACKED_FILES.txt", untracked)

        meta_lines = [
            f"generated_at_utc: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
            f"repo_root: {repo}",
            f"branch: {gr.branch}",
            f"upstream: {gr.upstream}",
            f"base_ref: {gr.base_ref}",
            f"base_sha: {gr.base_sha}",
            f"head_sha: {gr.head_sha}",
            f"git_dirty: {'true' if dirty else 'false'}",
            f"ticket: {args.ticket or ''}",
            f"run_name: {args.run_name or ''}",
        ]
        _write_text(work / "BUNDLE_META.md", "\n".join(meta_lines) + "\n")

        # Include standard docs (best effort)
        for rel in DEFAULT_INCLUDE_FILES:
            src = repo / rel
            if not src.exists() or not src.is_file():
                continue
            try:
                size = src.stat().st_size
            except Exception:
                skipped.append(f"{rel}  (skipped: stat failed)")
                continue
            if size > args.max_file_bytes:
                skipped.append(f"{rel}  (skipped: >{args.max_file_bytes} bytes)")
                continue
            _copy_file(src, work / rel)

        # Ticket file(s)
        for tpath in _candidate_ticket_paths(repo, args.ticket):
            rel = _safe_relpath(tpath, repo)
            if tpath.stat().st_size > args.max_file_bytes:
                skipped.append(f"{rel}  (skipped: >{args.max_file_bytes} bytes)")
                continue
            _copy_file(tpath, work / rel)

        # Run log dir
        run_dir = _choose_run_dir(repo, args.run_name, args.ticket)
        if run_dir:
            _copy_tree(run_dir, work / _safe_relpath(run_dir, repo), max_file_bytes=args.max_file_bytes, skipped=skipped)

        if skipped:
            _write_text(work / "SKIPPED_FILES.txt", "\n".join(skipped) + "\n")

        _zip_dir(work, zip_path)

    print(str(zip_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

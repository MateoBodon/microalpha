#!/usr/bin/env python3
"""
gpt_bundle.py

Creates a zip bundle intended to be uploaded to GPT for review.

Outputs:
  artifacts/_local/gpt_bundles/gpt_bundle_<timestamp>[_<ticket>].zip

The bundle includes:
- docs/_generated/repo_snapshot.md (auto-generated)
- git status, log, diffs
- ticket file (if present)
- selected small changed files (best-effort)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


def run(cmd: list[str], cwd: Optional[Path] = None) -> Tuple[int, str]:
    try:
        out = subprocess.check_output(
            cmd, cwd=str(cwd) if cwd else None, stderr=subprocess.STDOUT
        )
        return 0, out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        return e.returncode, e.output.decode("utf-8", errors="replace")


def git_root(start: Path) -> Optional[Path]:
    code, out = run(["git", "-C", str(start), "rev-parse", "--show-toplevel"])
    if code != 0:
        return None
    return Path(out.strip())


def ensure_repo_snapshot(repo: Path, scratch_dir: Path) -> Optional[Path]:
    snap = repo / "docs" / "_generated" / "repo_snapshot.md"
    if snap.exists():
        return snap
    tool = repo / "tools" / "agentic" / "repo_snapshot.py"
    if tool.exists():
        scratch_dir.mkdir(parents=True, exist_ok=True)
        scratch_snap = scratch_dir / "repo_snapshot.md"
        code, out = run(
            [sys.executable, str(tool), "--out", str(scratch_snap)], cwd=repo
        )
        if code == 0:
            p = Path(out.strip().splitlines()[-1])
            if p.exists():
                return p
    return None


def git_status_porcelain(repo: Path) -> str:
    code, out = run(["git", "-C", str(repo), "status", "--porcelain"])
    if code != 0:
        raise SystemExit(f"Failed to read git status:\n{out}")
    return out


def stash_push(repo: Path, label: str) -> str:
    code, out = run(["git", "-C", str(repo), "stash", "push", "-u", "-m", label])
    if code != 0:
        raise SystemExit(f"Failed to stash worktree:\n{out}")
    code, out = run(["git", "-C", str(repo), "stash", "list", "-1"])
    if code != 0 or not out.strip():
        raise SystemExit(f"Failed to read stash list:\n{out}")
    ref = out.split(":", 1)[0].strip()
    if not ref.startswith("stash@{"):
        raise SystemExit(f"Unexpected stash ref format: {out.strip()}")
    return ref


def restore_stash(repo: Path, stash_ref: str, status_before: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo), "stash", "apply", "--index", stash_ref],
        text=True,
        capture_output=True,
    )
    status_after = git_status_porcelain(repo)
    if result.returncode != 0 or status_after != status_before:
        message = "\n".join(
            [
                "Failed to restore stashed changes cleanly after bundling.",
                f"stash ref: {stash_ref}",
                "stdout:",
                result.stdout.strip(),
                "stderr:",
                result.stderr.strip(),
                "status before:",
                status_before.strip(),
                "status after:",
                status_after.strip(),
                "",
                "Your stash has NOT been dropped. Inspect with:",
                "  git stash list",
                f"  git stash show -p {stash_ref}",
            ]
        ).strip()
        raise SystemExit(message)

    code, out = run(["git", "-C", str(repo), "stash", "drop", stash_ref])
    if code != 0:
        raise SystemExit(f"Failed to drop stash {stash_ref}:\n{out}")


def prepare_worktree(
    repo: Path, label: str, no_stash: bool
) -> tuple[str, str | None, bool]:
    status_before = git_status_porcelain(repo)
    dirty = bool(status_before.strip())
    stash_ref = None
    if dirty:
        if no_stash:
            raise SystemExit(
                "Dirty worktree detected and --no-stash specified. "
                "Commit, stash, or clean changes before running gpt-bundle."
            )
        stash_ref = stash_push(repo, label)
        status_after = git_status_porcelain(repo)
        if status_after.strip():
            raise SystemExit(
                "Expected clean worktree after stash, but changes remain:\n"
                f"{status_after}"
            )
    return status_before, stash_ref, dirty


def bundle_root(repo: Path) -> Path:
    return repo / "artifacts" / "_local" / "gpt_bundles"


def list_changed_files(repo: Path, stash_ref: Optional[str] = None) -> list[str]:
    if stash_ref:
        _, out = run(
            ["git", "-C", str(repo), "stash", "show", "--name-only", stash_ref]
        )
        return [line.strip() for line in out.splitlines() if line.strip()]
    # Prefer git diff names for working tree
    _, out = run(["git", "-C", str(repo), "diff", "--name-only"])
    changed = [line.strip() for line in out.splitlines() if line.strip()]
    # Include staged
    _, out2 = run(["git", "-C", str(repo), "diff", "--cached", "--name-only"])
    for line in out2.splitlines():
        line = line.strip()
        if line and line not in changed:
            changed.append(line)
    return changed


def collect_diffs(repo: Path, stash_ref: Optional[str]) -> tuple[str, str, str]:
    if stash_ref:
        _, diff = run(["git", "-C", str(repo), "stash", "show", "-p", stash_ref])
        _, diff_stat = run(
            ["git", "-C", str(repo), "stash", "show", "--stat", stash_ref]
        )
        return diff, "", diff_stat
    _, diff = run(["git", "-C", str(repo), "diff"])
    _, diff_cached = run(["git", "-C", str(repo), "diff", "--cached"])
    _, diff_stat = run(["git", "-C", str(repo), "diff", "--stat"])
    return diff, diff_cached, diff_stat


def add_file_if_small(
    z: zipfile.ZipFile, repo: Path, rel_path: str, max_bytes: int = 120_000
) -> None:
    p = repo / rel_path
    if not p.exists() or not p.is_file():
        return
    try:
        if p.stat().st_size > max_bytes:
            return
        z.write(p, arcname=str(p.relative_to(repo)))
    except Exception:
        return


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--zip", action="store_true", help="Create zip bundle (default behavior)."
    )
    ap.add_argument(
        "--ticket", type=str, default=None, help="Ticket id to include (optional)."
    )
    ap.add_argument("--out", type=str, default=None, help="Output zip path (optional).")
    ap.add_argument(
        "--include-files",
        action="store_true",
        help="Include small changed files in addition to diffs.",
    )
    ap.add_argument(
        "--no-stash",
        action="store_true",
        help="Disable auto-stash; fail if the worktree is dirty.",
    )
    args = ap.parse_args()

    start = Path.cwd()
    repo = git_root(start) or start

    bundle_dir = bundle_root(repo)

    status_before, stash_ref, dirty = prepare_worktree(
        repo,
        label=f"temp: gpt_bundle {args.ticket or ''}".strip(),
        no_stash=args.no_stash,
    )
    print(f"Dirty worktree detected: {'yes' if dirty else 'no'}")
    print(f"Stash used: {'yes' if stash_ref else 'no'}")

    try:
        bundle_dir.mkdir(parents=True, exist_ok=True)
        # Ensure snapshot exists
        snap = ensure_repo_snapshot(repo, bundle_dir)

        # Collect git info
        _, log = run(
            ["git", "-C", str(repo), "log", "-n", "50", "--oneline", "--decorate"]
        )
        diff, diff_cached, diff_stat = collect_diffs(repo, stash_ref)
        changed = list_changed_files(repo, stash_ref)

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        ticket = (args.ticket or "").strip()
        suffix = f"_{ticket}" if ticket else ""
        out_zip = (
            Path(args.out)
            if args.out
            else (bundle_dir / f"gpt_bundle_{ts}{suffix}.zip")
        )

        readme = f"""GPT Bundle

Generated: {ts}Z
Repo: {repo}
Ticket: {ticket or "(none)"}

Contents:
- docs/_generated/repo_snapshot.md (if available)
- git_status.txt
- git_log.txt
- git_diff.patch (working tree or stash)
- git_diff_cached.patch (staged; empty if stashed)
- git_diff_stat.txt
- changed_files.txt
- ticket file (if present)
- small changed files (optional)
"""

        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("README.txt", readme)
            z.writestr("git_status.txt", status_before)
            z.writestr("git_log.txt", log)
            z.writestr("git_diff.patch", diff)
            z.writestr("git_diff_cached.patch", diff_cached)
            z.writestr("git_diff_stat.txt", diff_stat)
            z.writestr(
                "changed_files.txt", "\n".join(changed) + ("\n" if changed else "")
            )

            if snap and snap.exists():
                if snap.is_relative_to(repo):
                    arcname = str(snap.relative_to(repo))
                else:
                    arcname = "docs/_generated/repo_snapshot.md"
                z.write(snap, arcname=arcname)

            # Ticket file
            if ticket:
                tf = repo / "docs" / "tickets" / f"{ticket}.md"
                if tf.exists():
                    z.write(tf, arcname=str(tf.relative_to(repo)))

            if args.include_files:
                for rel in changed:
                    add_file_if_small(z, repo, rel)
    finally:
        if stash_ref:
            restore_stash(repo, stash_ref, status_before)

    print(f"Bundle path: {out_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

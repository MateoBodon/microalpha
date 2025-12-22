#!/usr/bin/env python3
"""Scan tracked data-like files for restricted-data signatures."""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = REPO_ROOT / "scripts" / "data_policy_allowlist.txt"
DATA_EXTENSIONS = {".csv", ".parquet", ".json", ".jsonl", ".feather"}
MAX_READ_BYTES = 1_048_576

KEYWORD_PATTERNS = [
    (re.compile(r"\bsecid\b", re.IGNORECASE), "secid"),
    (re.compile(r"\bmarket_iv\b", re.IGNORECASE), "market_iv"),
    (re.compile(r"\bbest_bid\b", re.IGNORECASE), "best_bid"),
    (re.compile(r"\bbest_ask\b", re.IGNORECASE), "best_ask"),
    (re.compile(r"\bbest_offer\b", re.IGNORECASE), "best_offer"),
    (re.compile(r"\bstrike\b", re.IGNORECASE), "strike"),
    (re.compile(r"\boptionmetrics\b", re.IGNORECASE), "optionmetrics"),
    (re.compile(r"\btaq\b", re.IGNORECASE), "taq"),
    (re.compile(r"\bwrds\b", re.IGNORECASE), "wrds"),
]

PATH_PATTERNS = [
    (re.compile(r"(^|/)artifacts/heston/", re.IGNORECASE), "path: artifacts/heston/"),
    (re.compile(r"(^|/)quote_surface/", re.IGNORECASE), "path: quote_surface/"),
    (re.compile(r"(^|/)[^/]*option_[^/]*", re.IGNORECASE), "path: option_*"),
]


def load_allowlist() -> list[str]:
    patterns: list[str] = []
    if not ALLOWLIST_PATH.exists():
        return patterns
    for line in ALLOWLIST_PATH.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        patterns.append(entry)
    return patterns


def is_allowlisted(path: Path, patterns: Iterable[str]) -> bool:
    rel = path.as_posix()
    return any(fnmatch.fnmatch(rel, pattern) for pattern in patterns)


def iter_tracked_files() -> Iterable[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            yield Path(line)


def read_head_text(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            blob = handle.read(MAX_READ_BYTES)
    except OSError as exc:
        raise RuntimeError(f"read_error:{exc.__class__.__name__}") from exc
    return blob.decode("utf-8", errors="ignore")


def scan_file(rel_path: Path) -> list[str]:
    matches: list[str] = []
    rel_str = rel_path.as_posix()
    for pattern, label in PATH_PATTERNS:
        if pattern.search(rel_str):
            matches.append(label)
    text = read_head_text(REPO_ROOT / rel_path)
    for pattern, label in KEYWORD_PATTERNS:
        if pattern.search(text):
            matches.append(label)
    return matches


def main() -> int:
    allowlist = load_allowlist()
    scanned = 0
    skipped = 0
    violations: list[tuple[Path, list[str]]] = []

    for rel_path in iter_tracked_files():
        if rel_path.suffix.lower() not in DATA_EXTENSIONS:
            continue
        if is_allowlisted(rel_path, allowlist):
            skipped += 1
            continue
        scanned += 1
        try:
            matches = scan_file(rel_path)
        except RuntimeError as exc:
            matches = [str(exc)]
        if matches:
            violations.append((rel_path, matches))

    if violations:
        print("Data policy violations detected:")
        for path, matches in violations:
            unique = ", ".join(sorted(set(matches)))
            print(f"- {path.as_posix()}: {unique}")
        print(f"Scanned {scanned} files; allowlisted {skipped}.")
        print(f"Allowlist path: {ALLOWLIST_PATH.as_posix()}")
        return 2

    print(f"Data policy check passed. Scanned {scanned} files; allowlisted {skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

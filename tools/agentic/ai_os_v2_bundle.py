#!/usr/bin/env python3
"""Create AI Project OS v2 archive indexes and context bundles.

This helper is deterministic and local-only. It does not change product
behavior; it packages repository state for Pro/Heavy review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DOC_EXTS = {".md", ".txt", ".rst", ".pdf", ".docx", ".json", ".yaml", ".yml"}
BINARY_OR_LARGE_EXTS = {".zip", ".png", ".jpg", ".jpeg", ".parquet", ".feather"}
MAX_COPY_BYTES = 300_000
MAX_HASH_BYTES = 20_000_000

CANONICAL_DOCS = [
    "PROJECT.md",
    "AGENTS.md",
    "PROGRESS.md",
    "docs/strategy/GOAL_CONTEXT.md",
    "docs/strategy/STRATEGIC_OVERVIEW.md",
    "docs/strategy/PLAN_OF_RECORD.md",
    "docs/strategy/DECISIONS.md",
    "docs/strategy/RISK_REGISTER.md",
    "docs/strategy/TICKET_LEDGER.md",
    "docs/strategy/CODEX_GOALS.md",
    "docs/strategy/CONTEXT_CARRYOVER.md",
    "docs/tickets/T-000_install_ai_project_os_v2.md",
    "docs/tickets/TEMPLATE_codex_ticket.md",
    "project_state/STATE_INDEX.md",
    "project_state/RUNBOOK.md",
    "project_state/VALIDATION_MATRIX.md",
    "project_state/CLAIMS_AND_EVIDENCE.md",
    "project_state/CURRENT_EVIDENCE_SUMMARY.md",
    "project_state/DATA_ARTIFACT_INVENTORY.md",
]

SELECTED_FILES = [
    "README.md",
    "PROJECT.md",
    "AGENTS.md",
    "PROGRESS.md",
    "TRACKING_POLICY.md",
    "CHANGELOG.md",
    "Makefile",
    "pyproject.toml",
    "pytest.ini",
    "mkdocs.yml",
    ".github/workflows/ci.yml",
    ".github/workflows/docs.yml",
    "configs/flagship_sample.yaml",
    "configs/wfv_flagship_sample.yaml",
    "configs/wfv_flagship_public.yaml",
    "configs/wfv_flagship_wrds.yaml",
    "configs/wfv_flagship_wrds_sweep35.yaml",
    "src/microalpha/cli.py",
    "src/microalpha/data.py",
    "src/microalpha/engine.py",
    "src/microalpha/runner.py",
    "src/microalpha/walkforward.py",
    "src/microalpha/portfolio.py",
    "src/microalpha/broker.py",
    "src/microalpha/strategies/flagship_mom.py",
    "src/microalpha/strategies/flagship_momentum.py",
    "src/microalpha/reporting/summary.py",
    "src/microalpha/reporting/spa.py",
    "scripts/check_data_policy.py",
    "scripts/validate_run_logs.py",
    "scripts/wrds_leaderboard.py",
    "tools/agentic/ai_os_v2_bundle.py",
    "tools/agentic/project_state_refresh.py",
    "tools/agentic/gpt_bundle.py",
    "tests/test_no_lookahead.py",
    "tests/test_tplus1_execution.py",
    "tests/test_data_policy.py",
    "tests/test_runs_index.py",
    "tests/test_docs_links.py",
    "tests/test_gpt_bundle_dirty.py",
]

ARCHIVE_COPY_PATHS = [
    "PROJECT.md",
    "AGENTS.md",
    "PROGRESS.md",
    "Plan.md",
    "TRACKING_POLICY.md",
    ".agent/MASTER_PLAN.md",
    ".agent/LOGBOOK.md",
    ".agent/execplans",
    "docs/PLAN_OF_RECORD.md",
    "docs/DECISIONS.md",
    "docs/NOW.md",
    "docs/TICKETS.md",
    "docs/CODEX_SPRINT_TICKETS.md",
    "docs/DOCS_AND_LOGGING_SYSTEM.md",
    "docs/RUNBOOK.md",
    "docs/prompts",
    "docs/gpt_outputs",
    "docs/tickets",
    "docs/artifacts",
    "project_state",
]


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT)
        return 0, out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as exc:
        return exc.returncode, exc.output.decode("utf-8", errors="replace")


def git_root(start: Path) -> Path:
    code, out = run(["git", "rev-parse", "--show-toplevel"], start)
    if code != 0:
        raise SystemExit("Not inside a git repository")
    return Path(out.strip())


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str | None:
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > MAX_HASH_BYTES:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path, repo: Path) -> str:
    return path.relative_to(repo).as_posix()


def git_files(repo: Path) -> list[Path]:
    code, out = run(["git", "ls-files"], repo)
    if code != 0:
        return []
    return [repo / line for line in out.splitlines() if line.strip()]


def iter_existing_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    if root.is_dir():
        for path in sorted(root.rglob("*")):
            if path.is_file():
                yield path


def classify(path: str) -> tuple[str, str, bool, bool]:
    suffix = Path(path).suffix.lower()
    if path in CANONICAL_DOCS:
        return (
            "canonical/current",
            "Canonical AI Project OS v2 doc or root project doc.",
            True,
            False,
        )
    if path in {
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "Makefile",
        "pyproject.toml",
        "pytest.ini",
        "mkdocs.yml",
        ".pre-commit-config.yaml",
        ".secrets.baseline",
        "TRACKING_POLICY.md",
    } or path.startswith(".github/"):
        return ("do-not-touch", "Product/package/release documentation or config.", False, False)
    if path.startswith("src/") or path.startswith("tests/") or path.startswith("configs/"):
        return ("do-not-touch", "Required by product code, tests, or reproducible configs.", False, False)
    if path.startswith("docs/agent_runs/"):
        return (
            "useful historical",
            "Historical Codex run log; indexed in place to avoid duplicating the full audit log tree.",
            False,
            True,
        )
    if path.startswith(("docs/prompts/", "docs/gpt_outputs/", ".agent/", "docs/tickets/")):
        return ("useful historical", "Historical prompt, planning, ticket, or handoff material.", True, True)
    if path.startswith(("docs/gpt_bundles/", "docs/_bundles/")) or suffix == ".zip":
        return ("large artifacts", "Old generated bundle zip; indexed by path/hash instead of copied.", False, True)
    if path.startswith("project_state/_generated/"):
        return (
            "generated/redundant/stale",
            "Generated v1 project_state metadata; superseded by refreshed v2 summaries.",
            False,
            True,
        )
    if path.startswith("project_state/"):
        return ("useful historical", "Pre-AI-OS-v2 project_state snapshot; useful as prior context.", True, True)
    if path in {
        "docs/PLAN_OF_RECORD.md",
        "docs/DECISIONS.md",
        "docs/NOW.md",
        "docs/TICKETS.md",
        "docs/CODEX_SPRINT_TICKETS.md",
        "docs/DOCS_AND_LOGGING_SYSTEM.md",
        "docs/RUNBOOK.md",
        "Plan.md",
    }:
        return ("useful historical", "Pre-AI-OS-v2 planning/process doc migrated or cross-referenced.", True, True)
    if suffix in BINARY_OR_LARGE_EXTS:
        return ("large artifacts", "Binary or generated artifact; index instead of copying.", False, False)
    if path.startswith(("reports/summaries/", "docs/artifacts/")):
        return ("useful historical", "Curated result/report artifact; preserve as evidence context.", True, True)
    return ("generated/redundant/stale", "Indexed for discoverability; not authoritative current truth.", False, True)


def archive_manifest(repo: Path, archive_dir: Path) -> list[dict[str, object]]:
    copied_root = archive_dir / "copied"
    copy_targets: set[str] = set()
    for raw in ARCHIVE_COPY_PATHS:
        root = repo / raw
        for path in iter_existing_files(root):
            if path.name == ".DS_Store":
                continue
            if path.suffix.lower() in BINARY_OR_LARGE_EXTS:
                continue
            if path.stat().st_size <= MAX_COPY_BYTES:
                copy_targets.add(rel(path, repo))

    entries: list[dict[str, object]] = []
    seen: set[str] = set()
    for path in git_files(repo):
        r = rel(path, repo)
        suffix = path.suffix.lower()
        is_docish = suffix in DOC_EXTS or r.startswith((".agent/", "docs/", "project_state/"))
        is_artifact = r.startswith(("artifacts/", "reports/summaries/", "docs/gpt_bundles/", "docs/_bundles/"))
        if not (is_docish or is_artifact):
            continue
        classification, reason, should_copy, migrated_context = classify(r)
        should_copy = should_copy and r in copy_targets
        archived_path = None
        if should_copy:
            dest = copied_root / r
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
            archived_path = rel(dest, repo)
        entry = {
            "original_path": r,
            "archived_path": archived_path,
            "title_or_description": describe_path(r),
            "classification": classification,
            "why_archived_or_preserved": reason,
            "migrated_into_canonical_doc": bool(migrated_context),
            "may_contain_useful_historical_context": classification != "do-not-touch",
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        entries.append(entry)
        seen.add(r)

    large_roots = ["data_sp500", "artifacts", "docs/img", "reports/summaries"]
    for root_name in large_roots:
        root = repo / root_name
        if not root.exists():
            continue
        size = dir_size(root)
        key = f"{root_name}/"
        if key in seen:
            continue
        entries.append(
            {
                "original_path": key,
                "archived_path": None,
                "title_or_description": describe_path(key),
                "classification": "large artifacts",
                "why_archived_or_preserved": "Large directory indexed by path and size; contents are not duplicated into archive.",
                "migrated_into_canonical_doc": True,
                "may_contain_useful_historical_context": True,
                "size_bytes": size,
                "sha256": None,
            }
        )
    return sorted(entries, key=lambda item: str(item["original_path"]))


def describe_path(path: str) -> str:
    name = Path(path.rstrip("/")).name
    if path == "PROJECT.md":
        return "Pre-v2 root project identity doc"
    if path == "AGENTS.md":
        return "Pre-v2 repo-specific agent instructions"
    if path == "PROGRESS.md":
        return "Chronological project progress log"
    if path.startswith("docs/agent_runs/"):
        return "Historical Codex run log file"
    if path.startswith("docs/prompts/"):
        return "Historical model/Codex prompt"
    if path.startswith("docs/gpt_outputs/"):
        return "Historical GPT output or diagnosis"
    if path.startswith("project_state/"):
        return "Pre-v2 project_state file"
    if path.endswith(".zip"):
        return "Generated historical bundle zip"
    if path.endswith("/"):
        return f"Directory inventory: {path}"
    return name.replace("_", " ").replace("-", " ")


def dir_size(root: Path) -> int:
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            try:
                total += path.stat().st_size
            except OSError:
                pass
    return total


def write_archive(repo: Path, date: str) -> Path:
    archive_dir = repo / "docs" / "_archive" / "pre_ai_os_v2" / date
    archive_dir.mkdir(parents=True, exist_ok=True)
    entries = archive_manifest(repo, archive_dir)
    manifest = {
        "schema_version": "ai-project-os-v2-pre-archive-1",
        "created_at_utc": utc_now(),
        "repo_root": str(repo),
        "archive_dir": rel(archive_dir, repo),
        "entry_count": len(entries),
        "entries": entries,
    }
    (archive_dir / "ARCHIVE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (archive_dir / "ARCHIVE_INDEX.md").write_text(render_archive_index(manifest), encoding="utf-8")
    return archive_dir


def render_archive_index(manifest: dict[str, object]) -> str:
    entries = list(manifest["entries"])  # type: ignore[index]
    counts = Counter(str(item["classification"]) for item in entries)
    lines = [
        "# Pre-AI Project OS v2 Archive Index\n",
        "\n",
        f"- Created: `{manifest['created_at_utc']}`\n",
        f"- Archive directory: `{manifest['archive_dir']}`\n",
        f"- Entries indexed: `{manifest['entry_count']}`\n",
        "\n",
        "## Classification Counts\n",
        "\n",
    ]
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}\n")
    lines.extend(
        [
            "\n",
            "## Notes\n",
            "\n",
            "- Files with an `archived_path` were copied into this archive with their relative path preserved under `copied/`.\n",
            "- Files without an `archived_path` remain in place and are indexed here to avoid duplicating bulky logs, bundles, images, or product-required files.\n",
            "- Archived/indexed material is historical context, not current truth. Use the root docs, `docs/strategy/`, and `project_state/STATE_INDEX.md` for current AI OS v2 state.\n",
            "\n",
            "## Entries\n",
            "\n",
            "| Original path | Archived path | Description | Classification | Migrated? | Historical? | Why |\n",
            "|---|---|---|---|---:|---:|---|\n",
        ]
    )
    for item in entries:
        archived = item["archived_path"] or "(indexed in place)"
        lines.append(
            "| {original} | {archived} | {desc} | {cls} | {migrated} | {hist} | {why} |\n".format(
                original=item["original_path"],
                archived=archived,
                desc=str(item["title_or_description"]).replace("|", "/"),
                cls=item["classification"],
                migrated="yes" if item["migrated_into_canonical_doc"] else "no",
                hist="yes" if item["may_contain_useful_historical_context"] else "no",
                why=str(item["why_archived_or_preserved"]).replace("|", "/"),
            )
        )
    return "".join(lines)


def git_text(repo: Path, args: list[str]) -> str:
    code, out = run(["git", *args], repo)
    if code != 0:
        return out
    return out


def write_text(stage: Path, rel_path: str, content: str, included: list[dict[str, object]], purpose: str) -> None:
    path = stage / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    included.append(
        {
            "path": rel_path,
            "purpose": purpose,
            "source": "generated",
            "size_bytes": path.stat().st_size,
        }
    )


def copy_into_bundle(
    repo: Path,
    stage: Path,
    source_rel: str,
    bundle_rel: str,
    included: list[dict[str, object]],
    purpose: str,
) -> None:
    src = repo / source_rel
    if not src.exists() or not src.is_file():
        return
    dest = stage / bundle_rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    included.append(
        {
            "path": bundle_rel,
            "purpose": purpose,
            "source": "repo",
            "size_bytes": dest.stat().st_size,
        }
    )


def zip_dir(stage: Path, out_zip: Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(stage).as_posix())


def repo_counts(repo: Path) -> dict[str, int]:
    files = [rel(path, repo) for path in git_files(repo)]
    counts: Counter[str] = Counter()
    for item in files:
        top = item.split("/", 1)[0] if "/" in item else "(root)"
        counts[top] += 1
    return dict(sorted(counts.items()))


def make_state_summary(repo: Path) -> str:
    status = git_text(repo, ["status", "--short"]) or "(clean)\n"
    branch = git_text(repo, ["branch", "--show-current"]).strip()
    sha = git_text(repo, ["rev-parse", "HEAD"]).strip()
    counts = repo_counts(repo)
    lines = [
        "# State Summary\n",
        "\n",
        "- Repo: `microalpha`\n",
        "- Type: Python quant/research backtesting engine.\n",
        f"- Branch: `{branch}`\n",
        f"- HEAD: `{sha}`\n",
        "- Current phase: AI Project OS v2 installation, pre-Pro strategy reset.\n",
        "- Primary current evidence: `project_state/CURRENT_RESULTS.md`, `docs/artifacts/resume/`, `reports/summaries/`, and committed sample artifacts.\n",
        "- Key caution: WRDS results require local licensed exports; raw WRDS data must not be bundled or committed.\n",
        "\n",
        "## Git Status\n",
        "\n",
        "```text\n",
        status,
        "```\n",
        "\n",
        "## Tracked File Counts\n",
        "\n",
    ]
    for key, count in counts.items():
        lines.append(f"- `{key}`: {count}\n")
    return "".join(lines)


def file_purpose_index() -> str:
    rows = [
        ("README.md", "docs", "Public project overview, sample results, quickstart.", "core", "current but claims require evidence checks"),
        ("PROJECT.md", "docs", "AI OS v2 project identity and scope.", "core", "current"),
        ("AGENTS.md", "docs", "Repo-specific agent rules and validation expectations.", "core", "current"),
        ("docs/strategy/", "docs", "Canonical AI OS v2 strategy and durable memory layer.", "core", "current"),
        ("project_state/", "state", "Current factual state map, runbook, validation matrix, claims/evidence.", "core", "current with legacy files retained"),
        ("src/microalpha/", "source", "Engine, CLI, data handling, portfolio, execution, strategies, reporting.", "core", "do not touch for T-000"),
        ("tests/", "validation", "Unit/integration guardrails for leakage, CLI, artifacts, reporting, data policy.", "core", "current"),
        ("configs/", "config", "Sample, public, WRDS, and sweep YAML configs.", "core", "current"),
        ("docs/agent_runs/", "history", "Historical Codex run logs.", "support", "historical, indexed in archive"),
        ("docs/prompts/", "history", "Historical prompts and tickets.", "support", "historical, indexed in archive"),
        ("docs/artifacts/resume/", "evidence", "Curated resume-safe metric artifacts.", "core", "current evidence surface"),
        ("artifacts/", "generated", "Committed sample artifacts plus local generated run outputs.", "generated", "large; selectively included"),
        ("data_sp500/", "data", "Large S&P 500 price panel.", "support", "excluded from bundles except inventory"),
        ("reports/_runs/", "run outputs", "Run-scoped bulky/local outputs.", "generated", "ignored except README"),
        ("reports/_bundles/", "bundle outputs", "AI OS v2 context/review zip outputs.", "generated", "ignored except README"),
    ]
    lines = ["# File Purpose Index\n\n", "| Path | Type | Purpose | Strategic importance | Status |\n", "|---|---|---|---|---|\n"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |\n")
    return "".join(lines)


def artifact_result_index(repo: Path) -> str:
    candidates = [
        "artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7",
        "artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7",
        "artifacts/sample_wfv_holdout/2025-12-21T20-53-05Z-4457b33",
        "docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced",
        "docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621",
        "docs/artifacts/resume/wrds/leaderboard",
        "reports/summaries",
        "docs/img",
        "data_sp500",
    ]
    lines = [
        "# Artifact Result Index\n",
        "\n",
        "| Path | Purpose | Size | Currentness | Bundle treatment |\n",
        "|---|---|---:|---|---|\n",
    ]
    for item in candidates:
        path = repo / item
        if not path.exists():
            continue
        size = dir_size(path) if path.is_dir() else path.stat().st_size
        purpose = describe_path(item)
        if item.startswith("docs/artifacts/resume/wrds/2026-02-16"):
            currentness = "current WRDS resume-safe evidence"
        elif item.startswith("docs/artifacts/resume/public"):
            currentness = "current public mini-panel evidence; degenerate run"
        elif item.startswith("artifacts/sample"):
            currentness = "sample/demo baseline"
        elif item in {"docs/img", "data_sp500"}:
            currentness = "large supporting artifact/data"
        else:
            currentness = "supporting reports"
        treatment = "included as index/selected small files; large/raw contents excluded"
        lines.append(f"| `{item}` | {purpose} | {size} | {currentness} | {treatment} |\n")
    return "".join(lines)


def docs_index(repo: Path, archive_dir: Path | None) -> str:
    docs = [path for path in git_files(repo) if path.suffix.lower() in {".md", ".rst", ".txt"}]
    lines = [
        "# Docs Index\n",
        "\n",
        "## Canonical AI OS v2 Docs\n",
        "\n",
    ]
    for item in CANONICAL_DOCS:
        if (repo / item).exists():
            lines.append(f"- `{item}`\n")
    lines.extend(["\n## Historical Docs And Logs\n\n"])
    for path in docs:
        r = rel(path, repo)
        if r.startswith(("docs/agent_runs/", "docs/prompts/", "docs/gpt_outputs/", ".agent/")):
            lines.append(f"- `{r}`\n")
    if archive_dir:
        lines.extend(["\n## Pre-v2 Archive\n\n", f"- `{rel(archive_dir / 'ARCHIVE_INDEX.md', repo)}`\n"])
    return "".join(lines)


def recent_progress(repo: Path) -> str:
    progress = repo / "PROGRESS.md"
    if not progress.exists():
        return "# Recent Progress\n\nNo PROGRESS.md found.\n"
    text = progress.read_text(encoding="utf-8")
    marker = "## 2026-02-16"
    idx = text.find(marker)
    return "# Recent Progress\n\n" + (text[idx:] if idx >= 0 else text[-6000:])


def validation_baseline(run_dir: Path | None) -> str:
    if run_dir and (run_dir / "VALIDATION.md").exists():
        return (run_dir / "VALIDATION.md").read_text(encoding="utf-8")
    return "# Validation Baseline\n\nValidation not recorded yet for this bundle run.\n"


def git_state(repo: Path) -> str:
    return (
        "# Git State\n\n"
        "## Status\n\n```text\n"
        + (git_text(repo, ["status", "--short"]) or "(clean)\n")
        + "```\n\n## Branch\n\n```text\n"
        + git_text(repo, ["branch", "--show-current"])
        + "```\n\n## HEAD\n\n```text\n"
        + git_text(repo, ["rev-parse", "HEAD"])
        + "```\n\n## Recent Log\n\n```text\n"
        + git_text(repo, ["log", "-n", "20", "--oneline", "--decorate"])
        + "```\n"
    )


def excluded_large_artifacts(repo: Path) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for raw in ["data_sp500", "docs/img", "artifacts", "docs/gpt_bundles", "docs/_bundles"]:
        path = repo / raw
        if not path.exists():
            continue
        items.append(
            {
                "path": raw,
                "reason": "too large or generated; not needed as raw payload for strategy review",
                "replacement": "ARTIFACT_RESULT_INDEX.md, ARCHIVE_INDEX.md, or selected curated artifacts",
                "size_bytes": dir_size(path) if path.is_dir() else path.stat().st_size,
            }
        )
    return items


def bundle_manifest(
    repo: Path,
    profile: str,
    consumer: str,
    phase: str,
    ticket: str | None,
    run_dir: Path | None,
    included: list[dict[str, object]],
    validation_status: str,
) -> dict[str, object]:
    status = git_text(repo, ["status", "--short"])
    return {
        "schema_version": "context-bundle-v2",
        "created_at_utc": utc_now(),
        "repo_name": "microalpha",
        "repo_root": str(repo),
        "git_branch": git_text(repo, ["branch", "--show-current"]).strip(),
        "git_sha": git_text(repo, ["rev-parse", "HEAD"]).strip(),
        "dirty": bool(status.strip()),
        "profile": profile,
        "consumer": consumer,
        "ticket_id": ticket,
        "phase": phase,
        "run_dir": rel(run_dir, repo) if run_dir else None,
        "included_files": included,
        "excluded_large_artifacts": excluded_large_artifacts(repo),
        "validation_summary": {
            "status": validation_status,
            "commands": [],
        },
        "artifact_summary": {
            "current_artifacts": [
                "docs/artifacts/resume/wrds/leaderboard/resume_line_best.md",
                "docs/artifacts/resume/public/resume_line_best.md",
                "project_state/CURRENT_RESULTS.md",
            ],
            "stale_or_superseded_artifacts": [
                "docs/gpt_bundles/",
                "docs/_bundles/",
                "project_state/_generated/",
            ],
        },
        "known_limitations": [
            "This is a strategic state bundle, not a full repo dump.",
            "Raw WRDS/private data and large result/image directories are excluded.",
            "Strategy docs and state files reflect the repo state at bundle generation time.",
        ],
        "recommended_reader_focus": [
            "Read STATE_SUMMARY.md, docs/strategy/CONTEXT_CARRYOVER.md, project_state/CLAIMS_AND_EVIDENCE.md, and VALIDATION_BASELINE.md first.",
            "Use ARCHIVE_INDEX.md to separate old context from current truth.",
        ],
    }


def bundle_index(profile: str, consumer: str, purpose: str, manifest: dict[str, object]) -> str:
    lines = [
        "# Bundle Index\n",
        "\n",
        "## Identity\n",
        f"- Repo: `{manifest['repo_name']}`\n",
        f"- Branch/SHA: `{manifest['git_branch']}` / `{manifest['git_sha']}`\n",
        f"- Profile: `{profile}`\n",
        f"- Consumer: `{consumer}`\n",
        f"- Ticket: `{manifest['ticket_id']}`\n",
        f"- Created: `{manifest['created_at_utc']}`\n",
        "\n",
        "## Purpose\n",
        "\n",
        purpose,
        "\n\n",
        "## How To Review This Bundle\n",
        "\n",
        "Start with `STATE_SUMMARY.md`, `DOCS_INDEX.md`, `VALIDATION_BASELINE.md`, and canonical docs under `canonical_docs/`. Use `ARCHIVE_INDEX.md` only as historical context.\n",
        "\n",
        "## Included Files By Category\n",
        "\n",
    ]
    by_top: Counter[str] = Counter()
    for item in manifest["included_files"]:  # type: ignore[index]
        top = str(item["path"]).split("/", 1)[0]
        by_top[top] += 1
    for top, count in sorted(by_top.items()):
        lines.append(f"- `{top}`: {count}\n")
    lines.extend(
        [
            "\n## Important Excluded Files\n\n",
        ]
    )
    for item in manifest["excluded_large_artifacts"]:  # type: ignore[index]
        lines.append(f"- `{item['path']}`: {item['reason']} (replacement: {item['replacement']})\n")
    lines.extend(
        [
            "\n## Validation Summary\n\n",
            f"- Status: `{manifest['validation_summary']['status']}`\n",  # type: ignore[index]
            "\n## Recommended Next Consumer Action\n\n",
            "Review the included run log, changed files, diff, validation, and residual risks before choosing the next dispatch.\n",
        ]
    )
    return "".join(lines)


def create_project_bundle(repo: Path, out_zip: Path, archive_dir: Path | None, run_dir: Path | None) -> None:
    with tempfile.TemporaryDirectory() as td:
        stage = Path(td)
        included: list[dict[str, object]] = []
        write_text(stage, "STATE_SUMMARY.md", make_state_summary(repo), included, "Factual current repo summary")
        write_text(stage, "FILE_PURPOSE_INDEX.md", file_purpose_index(), included, "High-level purpose map")
        write_text(stage, "ARTIFACT_RESULT_INDEX.md", artifact_result_index(repo), included, "Artifact and result inventory")
        write_text(stage, "VALIDATION_BASELINE.md", validation_baseline(run_dir), included, "Latest validation baseline")
        write_text(stage, "DOCS_INDEX.md", docs_index(repo, archive_dir), included, "Current vs historical docs index")
        write_text(stage, "GIT_STATE.md", git_state(repo), included, "Git state and recent log")
        write_text(stage, "RECENT_PROGRESS.md", recent_progress(repo), included, "Recent progress excerpt")
        if archive_dir:
            copy_into_bundle(repo, stage, rel(archive_dir / "ARCHIVE_INDEX.md", repo), "ARCHIVE_INDEX.md", included, "Pre-v2 archive index")
            copy_into_bundle(
                repo,
                stage,
                rel(archive_dir / "ARCHIVE_MANIFEST.json", repo),
                "ARCHIVE_MANIFEST.json",
                included,
                "Pre-v2 archive manifest",
            )
        for item in CANONICAL_DOCS:
            copy_into_bundle(repo, stage, item, f"canonical_docs/{item}", included, "Canonical AI OS v2 doc")
        for item in SELECTED_FILES:
            copy_into_bundle(repo, stage, item, f"selected_repo_files/{item}", included, "Selected source/test/config/doc for strategy review")
        manifest = bundle_manifest(
            repo,
            "project_state_audit",
            "pro",
            "initial",
            None,
            run_dir,
            included,
            "pass" if run_dir and (run_dir / "VALIDATION.md").exists() else "partial",
        )
        write_text(
            stage,
            "bundle_manifest.json",
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            included,
            "Bundle manifest",
        )
        manifest["included_files"] = included
        (stage / "bundle_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_text(
            stage,
            "BUNDLE_INDEX.md",
            bundle_index(
                "project_state_audit",
                "pro",
                "Initial Project State Audit Bundle for GPT 5.5 Pro Extended strategy planning.",
                manifest,
            ),
            included,
            "Human-readable bundle index",
        )
        zip_dir(stage, out_zip)


def create_review_bundle(
    repo: Path,
    out_zip: Path,
    archive_dir: Path | None,
    run_dir: Path | None,
    ticket: str,
    purpose: str,
) -> None:
    with tempfile.TemporaryDirectory() as td:
        stage = Path(td)
        included: list[dict[str, object]] = []
        write_text(stage, "GIT_STATUS.txt", git_text(repo, ["status", "--short"]), included, "Git status")
        write_text(stage, "CHANGED_FILE_LIST.txt", git_text(repo, ["status", "--short"]), included, "Changed file list")
        write_text(stage, "DIFF.patch", git_text(repo, ["diff", "--binary"]), included, "Worktree diff")
        write_text(stage, "UNTRACKED_FILES.txt", git_text(repo, ["ls-files", "--others", "--exclude-standard"]), included, "Untracked files")
        if run_dir and run_dir.exists():
            for path in sorted(run_dir.rglob("*")):
                if path.is_file():
                    copy_into_bundle(repo, stage, rel(path, repo), f"run_log/{path.name}", included, f"{ticket} run log")
        for item in [
            "docs/tickets/T-000_install_ai_project_os_v2.md",
            "docs/tickets/TEMPLATE_codex_ticket.md",
            "tools/agentic/ai_os_v2_bundle.py",
        ]:
            copy_into_bundle(repo, stage, item, f"ticket_material/{item}", included, f"{ticket} ticket material")
        if archive_dir:
            copy_into_bundle(repo, stage, rel(archive_dir / "ARCHIVE_INDEX.md", repo), "archive/ARCHIVE_INDEX.md", included, "Archive index")
            copy_into_bundle(repo, stage, rel(archive_dir / "ARCHIVE_MANIFEST.json", repo), "archive/ARCHIVE_MANIFEST.json", included, "Archive manifest")
        for item in CANONICAL_DOCS:
            copy_into_bundle(repo, stage, item, f"changed_docs/{item}", included, f"Canonical doc included for {ticket}")
        manifest = bundle_manifest(
            repo,
            "review",
            "heavy",
            "review",
            ticket,
            run_dir,
            included,
            "pass" if run_dir and (run_dir / "VALIDATION.md").exists() else "partial",
        )
        write_text(
            stage,
            "bundle_manifest.json",
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            included,
            "Bundle manifest",
        )
        manifest["included_files"] = included
        (stage / "bundle_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        write_text(
            stage,
            "BUNDLE_INDEX.md",
            bundle_index("review", "heavy", purpose, manifest),
            included,
            "Human-readable review bundle index",
        )
        zip_dir(stage, out_zip)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-date", default=datetime.now().strftime("%Y%m%d"))
    parser.add_argument("--archive-only", action="store_true")
    parser.add_argument("--project-bundle")
    parser.add_argument("--review-bundle")
    parser.add_argument("--run-dir")
    parser.add_argument("--ticket", default="T-000")
    parser.add_argument(
        "--purpose",
        default="Ticket review bundle for Heavy review.",
        help="Human-readable purpose text for review bundle indexes.",
    )
    args = parser.parse_args()

    repo = git_root(Path.cwd())
    archive_dir = repo / "docs" / "_archive" / "pre_ai_os_v2" / args.archive_date
    if args.archive_only or not (archive_dir / "ARCHIVE_MANIFEST.json").exists():
        archive_dir = write_archive(repo, args.archive_date)
        print(f"archive={archive_dir}")
    else:
        print(f"archive={archive_dir} (existing)")
    if args.archive_only:
        return 0

    run_dir = Path(args.run_dir).resolve() if args.run_dir else None
    if args.project_bundle:
        out = repo / args.project_bundle
        create_project_bundle(repo, out, archive_dir, run_dir)
        print(f"project_bundle={out}")
    if args.review_bundle:
        out = repo / args.review_bundle
        create_review_bundle(repo, out, archive_dir, run_dir, args.ticket, args.purpose)
        print(f"review_bundle={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

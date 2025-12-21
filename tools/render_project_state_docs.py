#!/usr/bin/env python3
"""Render project_state Markdown docs from generated indices and repo files.

Stdlib only. Writes project_state/*.md with consistent metadata headers.
"""
from __future__ import annotations

import json
import os
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PS_DIR = ROOT / "project_state"
GEN_DIR = PS_DIR / "_generated"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_branch() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT, text=True
    ).strip()


def header(generated_at: str, sha: str, branch: str, commands: list[str]) -> str:
    command_lines = "\n".join(f"  - {cmd}" for cmd in commands)
    return (
        "<!--\n"
        f"generated_at: {generated_at}\n"
        f"git_sha: {sha}\n"
        f"branch: {branch}\n"
        "commands:\n"
        f"{command_lines}\n"
        "-->\n\n"
    )


def write_doc(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def summarize_module_symbols(symbol_index: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for file_path in sorted(symbol_index.keys()):
        data = symbol_index[file_path]
        rows.append(
            {
                "path": file_path,
                "module_doc": data.get("module_doc") or "",
                "classes": data.get("classes", []),
                "functions": data.get("functions", []),
            }
        )
    return rows


def format_symbol_list(items: Iterable[dict[str, Any]], kind: str) -> str:
    if not items:
        return "- (none)\n"
    lines: list[str] = []
    for item in items:
        if kind == "class":
            bases = item.get("bases") or []
            base_text = f"({', '.join(bases)})" if bases else ""
            doc = item.get("doc") or ""
            suffix = f" — {doc}" if doc else ""
            lines.append(f"- {item['name']}{base_text}{suffix}")
        else:
            sig = item.get("signature") or "()"
            doc = item.get("doc") or ""
            suffix = f" — {doc}" if doc else ""
            lines.append(f"- {item['name']}{sig}{suffix}")
    return "\n".join(lines) + "\n"


def load_make_targets() -> list[str]:
    path = GEN_DIR / "make_targets.txt"
    if not path.exists():
        return []
    return [line.strip() for line in read_text(path).splitlines() if line.strip()]


def load_repo_inventory() -> list[dict[str, Any]]:
    path = GEN_DIR / "repo_inventory.json"
    if not path.exists():
        return []
    return read_json(path)


def list_by_role(inventory: list[dict[str, Any]], role: str) -> list[str]:
    return sorted(item["path"] for item in inventory if item.get("role") == role)


def summarize_directory(inventory: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    files = [item for item in inventory if item["path"].startswith(prefix)]
    total_size = sum(item.get("size_bytes") or 0 for item in files)
    return {
        "prefix": prefix,
        "files": len(files),
        "total_size_bytes": total_size,
    }


def top_level_keys_from_yaml(path: Path) -> list[str]:
    keys: list[str] = []
    if not path.exists():
        return keys
    for line in read_text(path).splitlines():
        if not line or line.startswith("#"):
            continue
        if line.startswith(" "):
            continue
        if ":" in line:
            key = line.split(":", 1)[0].strip()
            if key:
                keys.append(key)
    return keys


def parse_readme_sample_artifacts(readme_text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for key in ("sample_flagship", "sample_wfv"):
        match = re.search(rf"artifacts/{key}/([\w\-:TZ]+)", readme_text)
        if match:
            out[key] = match.group(1)
    return out


def parse_wrds_results(results_text: str) -> dict[str, Any]:
    info: dict[str, Any] = {}
    latest_match = re.search(r"Latest run: \*\*(.+?)\*\*", results_text)
    if latest_match:
        info["latest"] = latest_match.group(1)
    rerun_match = re.search(r"Rerun status \((\d{4}-\d{2}-\d{2})\):(.+)", results_text)
    if rerun_match:
        info["rerun_status"] = rerun_match.group(0).strip()
    metrics = {}
    in_table = False
    for line in results_text.splitlines():
        if line.strip().startswith("| Metric | Value"):
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith("|"):
                break
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 2 and parts[0] != "---":
                metrics[parts[0]] = parts[1]
    if metrics:
        info["metrics"] = metrics
    return info


def render_architecture(symbol_index: dict[str, Any], inventory: list[dict[str, Any]]) -> str:
    core_modules = [
        "src/microalpha/engine.py",
        "src/microalpha/data.py",
        "src/microalpha/portfolio.py",
        "src/microalpha/broker.py",
        "src/microalpha/execution.py",
        "src/microalpha/strategies/flagship_momentum.py",
        "src/microalpha/strategies/cs_momentum.py",
        "src/microalpha/reporting/summary.py",
        "src/microalpha/reporting/tearsheet.py",
        "src/microalpha/walkforward.py",
        "src/microalpha/runner.py",
    ]
    module_notes = []
    for module in core_modules:
        data = symbol_index.get(module, {})
        doc = data.get("module_doc") or ""
        module_notes.append(f"- `{module}` — {doc if doc else 'core module'}")

    artifact_dirs = [
        summarize_directory(inventory, "artifacts/sample_flagship"),
        summarize_directory(inventory, "artifacts/sample_wfv"),
        summarize_directory(inventory, "artifacts/wrds_flagship"),
    ]
    artifact_lines = [
        f"- `{d['prefix']}`: {d['files']} files, {d['total_size_bytes']} bytes"
        for d in artifact_dirs
        if d["files"]
    ]

    return """
# Architecture

## System overview

```
DataHandler -> Engine -> Strategy -> Portfolio -> Broker -> Execution -> Artifacts
```

- `DataHandler` streams `MarketEvent`s with strict time ordering.
- `Engine` enforces the no-lookahead clock, routes signals, and applies t+1 semantics.
- `Strategy` emits `SignalEvent`s based on market data and a universe definition.
- `Portfolio` enforces risk caps, sizing, and turnover/heat constraints.
- `Broker` + `Execution` implement slippage, commissions, and order routing models.
- Reporting utilities transform artifacts into Markdown summaries and plots.

## Core modules

{module_notes}

## Entry points

- CLI: `microalpha` (`src/microalpha/cli.py`).
- Wrappers: `run.py`, `walk_forward.py`.
- Make targets: `make sample`, `make wfv`, `make report`, `make report-wrds`.

## Artifact layout (sampled)

{artifact_lines}

## Supporting subsystems

- Config parsing: `src/microalpha/config.py`, `src/microalpha/config_wfv.py`.
- Metrics & risk: `src/microalpha/metrics.py`, `src/microalpha/risk.py`, `src/microalpha/risk_stats.py`.
- Logging/manifest: `src/microalpha/logging.py`, `src/microalpha/manifest.py`.
- WRDS helpers: `src/microalpha/wrds/` and `scripts/export_wrds_flagship.py`.
""".format(
        module_notes="\n".join(module_notes),
        artifact_lines="\n".join(artifact_lines) if artifact_lines else "- (no artifacts indexed)",
    )


def render_module_summaries(symbol_index: dict[str, Any]) -> str:
    rows = summarize_module_symbols(symbol_index)

    table_lines = ["| Module | Docstring | Classes | Functions |", "| --- | --- | ---: | ---: |"]
    for row in rows:
        doc = row["module_doc"].replace("|", "\\|")
        table_lines.append(
            f"| `{row['path']}` | {doc or ''} | {len(row['classes'])} | {len(row['functions'])} |"
        )

    return """
# Module Summaries

## Inventory (AST-derived)

{table}

## Notes

- Only top-level classes/functions are indexed (no nested symbols).
- Source: `project_state/_generated/symbol_index.json`.
""".format(table="\n".join(table_lines))


def render_function_index(symbol_index: dict[str, Any]) -> str:
    sections: list[str] = ["# Function Index\n"]
    for path in sorted(symbol_index.keys()):
        data = symbol_index[path]
        classes = data.get("classes", [])
        funcs = data.get("functions", [])
        sections.append(f"## `{path}`\n")
        sections.append("### Classes\n")
        sections.append(format_symbol_list(classes, "class"))
        sections.append("### Functions\n")
        sections.append(format_symbol_list(funcs, "function"))
    sections.append("\nNotes: AST-derived; signatures are best-effort.")
    return "\n".join(sections)


def render_dependency_graph(import_graph: dict[str, list[str]]) -> str:
    total_edges = sum(len(v) for v in import_graph.values())
    lines = ["# Dependency Graph", "", f"Internal import edges (microalpha.*): {total_edges}", ""]
    lines.append("## Adjacency list (file -> internal imports)")
    for path in sorted(import_graph.keys()):
        imports = import_graph[path]
        if not imports:
            lines.append(f"- `{path}` -> (none)")
            continue
        imports_text = ", ".join(imports)
        lines.append(f"- `{path}` -> {imports_text}")
    lines.append("")
    lines.append("Source: `project_state/_generated/import_graph.json`.")
    return "\n".join(lines)


def render_pipeline_flow(make_targets: list[str]) -> str:
    targets = "\n".join(f"- `{t}`" for t in make_targets)
    return f"""
# Pipeline Flow

## Primary entrypoints

- `microalpha run --config <cfg> --out <dir>` (single backtest)
- `microalpha wfv --config <cfg> --out <dir>` (walk-forward)
- `microalpha report --artifact-dir <dir>` (summaries + plots)
- Wrappers: `run.py` and `walk_forward.py`

## Makefile targets

{targets if targets else '- (none)'}

## Typical flows

### Sample flagship

```
make sample
make report
```

### Sample walk-forward

```
make wfv
make report-wfv
```

### WRDS (guarded)

```
WRDS_DATA_ROOT=/path/to/wrds make wfv-wrds
WRDS_DATA_ROOT=/path/to/wrds make report-wrds
```

## Report pipeline

- `microalpha report` calls `src/microalpha/reporting/summary.py` and `tearsheet.py`.
- WRDS reporting chains through `reports/analytics.py`, `reports/factors.py`, `reports/spa.py`, `reports/render_wrds_flagship.py` (see Makefile).
"""


def render_dataflow() -> str:
    return """
# Dataflow

## Inputs

- Sample data: `data/sample/` (CSV panel + metadata + universe + risk-free series)
- Public data: `data/public/` (per-symbol CSVs + metadata)
- WRDS exports (local only): `${WRDS_DATA_ROOT}/...` referenced by `configs/wfv_flagship_wrds.yaml`
- Factor data: `data/factors/ff3_sample.csv` and `data/factors/ff5_mom_daily.csv`

## Processing

1. Configs in `configs/` define data paths, strategy params, execution, risk caps.
2. `DataHandler` loads CSVs and streams `MarketEvent`s (`src/microalpha/data.py`).
3. `Engine` enforces monotonic timestamps and dispatches signals (`src/microalpha/engine.py`).
4. `Portfolio` applies sizing/constraints, forwards orders to broker (`src/microalpha/portfolio.py`).
5. `Broker` + `Execution` apply slippage/impact/LOB semantics (`src/microalpha/broker.py`, `src/microalpha/execution.py`).

## Outputs

- Artifacts under `artifacts/<run_id>/`: `manifest.json`, `metrics.json`, `equity_curve.csv`, `trades.jsonl`, `bootstrap.json`.
- Summaries under `reports/summaries/`: Markdown + factor tables + SPA outputs.
- Docs assets (WRDS): `docs/img/wrds_flagship/<RUN_ID>/`.
"""


def render_experiments(inventory: list[dict[str, Any]]) -> str:
    examples = list_by_role(inventory, "example")
    notebooks = list_by_role(inventory, "notebook")
    scripts = list_by_role(inventory, "script")
    return """
# Experiments

- `experiments/` directory: **not present** in this repo snapshot.

## Related research assets

- Examples: {examples}
- Notebooks: {notebooks}
- Scripts: {scripts}

Notes: Experiments and outputs are intentionally kept out of the repo; see `reports/` for reproducible summaries.
""".format(
        examples="\n".join(f"  - `{p}`" for p in examples) if examples else "(none)",
        notebooks="\n".join(f"  - `{p}`" for p in notebooks) if notebooks else "(none)",
        scripts="\n".join(f"  - `{p}`" for p in scripts) if scripts else "(none)",
    )


def render_current_results(
    readme_text: str,
    wrds_text: str,
    wrds_smoke_text: str,
    sample_metrics: dict[str, Any],
    wfv_metrics: dict[str, Any],
) -> str:
    sample_artifacts = parse_readme_sample_artifacts(readme_text)
    wrds_info = parse_wrds_results(wrds_text)
    wrds_smoke_info = parse_wrds_results(wrds_smoke_text) if wrds_smoke_text else {}

    def fmt_metric(metrics: dict[str, Any], key: str, fmt: str = "{:.2f}") -> str:
        value = metrics.get(key)
        if value is None:
            return "n/a"
        try:
            return fmt.format(value)
        except Exception:
            return str(value)

    sample_block = """
## Sample bundle (README + artifacts)

- Run: `artifacts/sample_flagship/{sample_run}`
- Sharpe (HAC): {sample_sharpe}
- MAR (Calmar): {sample_calmar}
- Max DD: {sample_dd}
- RealityCheck p-value: {sample_p}
- Turnover: {sample_turnover}

- Walk-forward: `artifacts/sample_wfv/{wfv_run}`
- Sharpe (HAC): {wfv_sharpe}
- MAR (Calmar): {wfv_calmar}
- Max DD: {wfv_dd}
- RealityCheck p-value: {wfv_p}
- Turnover: {wfv_turnover}
""".format(
        sample_run=sample_artifacts.get("sample_flagship", "unknown"),
        sample_sharpe=fmt_metric(sample_metrics, "sharpe_ratio", "{:.2f}"),
        sample_calmar=fmt_metric(sample_metrics, "calmar_ratio", "{:.2f}"),
        sample_dd=fmt_metric(sample_metrics, "max_drawdown", "{:.2%}"),
        sample_p=fmt_metric(sample_metrics, "bootstrap_p_value", "{:.3f}"),
        sample_turnover=fmt_metric(sample_metrics, "total_turnover", "${:,.2f}"),
        wfv_run=sample_artifacts.get("sample_wfv", "unknown"),
        wfv_sharpe=fmt_metric(wfv_metrics, "sharpe_ratio", "{:.2f}"),
        wfv_calmar=fmt_metric(wfv_metrics, "calmar_ratio", "{:.2f}"),
        wfv_dd=fmt_metric(wfv_metrics, "max_drawdown", "{:.2%}"),
        wfv_p=fmt_metric(wfv_metrics, "reality_check_p_value", "{:.3f}"),
        wfv_turnover=fmt_metric(wfv_metrics, "total_turnover", "${:,.2f}"),
    )

    wrds_block = "## WRDS results (docs/results_wrds.md)\n\n"
    if wrds_info.get("latest"):
        wrds_block += f"- Latest run: {wrds_info['latest']}\n"
    metrics = wrds_info.get("metrics", {})
    if metrics:
        wrds_block += "- Snapshot:\n"
        for key, value in metrics.items():
            wrds_block += f"  - {key}: {value}\n"
    if metrics:
        wrds_block += "- Report: `reports/summaries/wrds_flagship.md`\n"
    if wrds_info.get("rerun_status"):
        wrds_block += f"- {wrds_info['rerun_status']}\n"

    smoke_block = ""
    if wrds_smoke_info.get("latest") or wrds_smoke_info.get("metrics"):
        smoke_block = "## WRDS smoke (docs/results_wrds_smoke.md)\n\n"
        if wrds_smoke_info.get("latest"):
            smoke_block += f"- Latest run: {wrds_smoke_info['latest']}\n"
        smoke_metrics = wrds_smoke_info.get("metrics", {})
        if smoke_metrics:
            smoke_block += "- Snapshot:\n"
            for key, value in smoke_metrics.items():
                smoke_block += f"  - {key}: {value}\n"
            smoke_block += "- Report: `reports/summaries/wrds_flagship_smoke.md`\n"
        smoke_block += (
            "- Note: Smoke run validates WRDS pipeline wiring; metrics are not interpretable for performance.\n"
        )

    return f"""
# Current Results

{sample_block}

{wrds_block}

{smoke_block}

Sources: `README.md`, `docs/results_wrds.md`, sample metrics under `artifacts/sample_flagship/` and `artifacts/sample_wfv/`.
"""


def render_research_notes() -> str:
    return """
# Research Notes

- Leakage safety invariants and tests: `docs/leakage-safety.md`, `tests/test_time_ordering.py`, `tests/test_tplus1_execution.py`.
- Reproducibility + manifests: `docs/reproducibility.md`, `src/microalpha/manifest.py`.
- Sample flagship design: `docs/flagship_strategy.md` (12-1 momentum, TWAP, risk-parity allocator).
- WRDS flagship specification: `docs/flagship_momentum_wrds.md` and `configs/wfv_flagship_wrds.yaml`.
- Factor regression workflow: `docs/factors.md`, `reports/factors_ff.py`.
- WRDS results + rerun guidance: `docs/results_wrds.md`.
"""


def render_open_questions() -> str:
    return """
# Open Questions

- Full WRDS walk-forward rerun with tightened caps is pending (see `docs/results_wrds.md`).
- Confirm which WRDS export schema is authoritative if additional columns are needed beyond `docs/wrds.md`.
- Decide whether to keep `Plan.md` as long-term roadmap or split into `docs/plan.md` (per `Plan.md`).
- Do we need additional public datasets beyond `data/public/` for regression tests?
"""


def render_known_issues() -> str:
    return """
# Known Issues

- WRDS runs require local exports and are blocked without `WRDS_DATA_ROOT` (see `docs/wrds.md`).
- `docs/results_wrds.md` explicitly notes metrics are from a pre-tightening config and need a rerun.
- Some large data directories (`data/`, `data_sp500/`) are present; avoid deep parsing in automation.
- WRDS smoke universe is seeded from 2019 liquidity ranks (survivorship/lookahead) to keep it small; it is **not** valid for performance claims.
- WRDS smoke run produced zero trades and flat SPA comparator t-stats; smoke reports use `--allow-zero-spa` to render despite empty activity.
"""


def render_roadmap() -> str:
    return """
# Roadmap

Based on `Plan.md`:

- S2 Drawdown reduction validation: run WRDS smoke/full WFV with tightened caps and refresh docs.
- Maintain WRDS flagship spec + docs alignment (`docs/flagship_momentum_wrds.md`).
- Continue agent-native tooling (project_state, AGENTS, Plan) improvements.
"""


def render_config_reference(config_paths: list[Path]) -> str:
    lines = ["# Config Reference", "", "| Config | Top-level keys | Notes |", "| --- | --- | --- |"]
    for path in config_paths:
        keys = top_level_keys_from_yaml(path)
        note = ""
        if "wrds" in path.name:
            note = "WRDS/CRSP (guarded by env vars)"
        elif "sample" in path.name:
            note = "Bundled sample data"
        elif "public" in path.name:
            note = "Public mini-panel"
        elif "wfv" in path.name:
            note = "Walk-forward"
        rel_path = path.relative_to(ROOT).as_posix()
        lines.append(
            f"| `{rel_path}` | {', '.join(keys) if keys else 'n/a'} | {note} |"
        )
    return "\n".join(lines) + "\n"


def render_server_environment(py_version: str, deps: list[str]) -> str:
    return """
# Server Environment

- Python: {py_version}
- Platform: {platform}
- Repo: `{root}`
- Dependencies (pyproject): {deps}

Notes:
- No virtual environment state was captured in this run; install via `python -m venv .venv` and `pip install -e '.[dev]'`.
""".format(
        py_version=py_version,
        platform=platform.platform(),
        root=ROOT.name,
        deps=", ".join(deps),
    )


def render_test_coverage(test_files: list[str]) -> str:
    return """
# Test Coverage

- Test modules: {count}
- Marker config: `pytest.ini` defines `wrds` marker.
- Primary commands: `pytest -q` or `make test`; WRDS tests via `make test-wrds`.

## Notable suites

{tests}

Coverage note: README badge reports 78% coverage for bundled suites.
""".format(
        count=len(test_files),
        tests="\n".join(f"- `{path}`" for path in sorted(test_files)),
    )


def render_style_guide() -> str:
    return """
# Style Guide

- Python 3.12+, fully type-hinted (`src/microalpha`).
- Lint: `ruff check .` (line length 88, E/F/W/I rules, E501 ignored).
- Format: Black (line length 88).
- Types: `mypy src/microalpha` (python_version=3.12).
- Docstrings required for public functions/classes.
- Prefer small composable functions; avoid clever one-liners.
"""


def render_changelog(changelog_text: str) -> str:
    return """
# Changelog (repo root)

Source: `CHANGELOG.md`.

{body}
""".format(body=changelog_text.strip())


def render_index() -> str:
    return """
# Project State Index

## How to read this folder

1. Start with `ARCHITECTURE.md` and `PIPELINE_FLOW.md` for system context.
2. Use `MODULE_SUMMARIES.md` + `FUNCTION_INDEX.md` for code navigation.
3. Check `CONFIG_REFERENCE.md` and `DATAFLOW.md` for inputs/outputs.
4. Review `CURRENT_RESULTS.md`, `KNOWN_ISSUES.md`, and `ROADMAP.md` for status.

## File map

- `ARCHITECTURE.md` – component map and entrypoints.
- `MODULE_SUMMARIES.md` – module inventory (AST-derived).
- `FUNCTION_INDEX.md` – functions/classes per module (AST-derived).
- `DEPENDENCY_GRAPH.md` – internal import adjacency list.
- `PIPELINE_FLOW.md` – CLI + Makefile flows.
- `DATAFLOW.md` – data sources to artifacts.
- `EXPERIMENTS.md` – experiments/scripts/notebooks inventory.
- `CURRENT_RESULTS.md` – latest sample + WRDS results.
- `RESEARCH_NOTES.md` – design notes and docs pointers.
- `OPEN_QUESTIONS.md` – outstanding decisions.
- `KNOWN_ISSUES.md` – known limitations.
- `ROADMAP.md` – short-term plan.
- `CONFIG_REFERENCE.md` – YAML configs overview.
- `SERVER_ENVIRONMENT.md` – environment snapshot.
- `TEST_COVERAGE.md` – testing scope + commands.
- `STYLE_GUIDE.md` – lint/type/style expectations.
- `CHANGELOG.md` – repo change history.
- `_generated/` – machine-derived JSON indices.
"""


def main() -> None:
    generated_at = os.environ.get("PROJECT_STATE_GENERATED_AT", utc_now())
    sha = git_sha()
    branch = git_branch()
    commands = [
        "python3 tools/build_project_state.py",
        "python3 tools/render_project_state_docs.py",
    ]

    symbol_index = read_json(GEN_DIR / "symbol_index.json")
    import_graph = read_json(GEN_DIR / "import_graph.json")
    inventory = load_repo_inventory()
    make_targets = load_make_targets()

    readme_text = read_text(ROOT / "README.md")
    wrds_text = read_text(ROOT / "docs" / "results_wrds.md")
    wrds_smoke_path = ROOT / "docs" / "results_wrds_smoke.md"
    wrds_smoke_text = read_text(wrds_smoke_path) if wrds_smoke_path.exists() else ""

    sample_metrics_path = ROOT / "artifacts" / "sample_flagship" / "2025-10-30T18-39-31Z-a4ab8e7" / "metrics.json"
    wfv_metrics_path = ROOT / "artifacts" / "sample_wfv" / "2025-10-30T18-39-47Z-a4ab8e7" / "metrics.json"
    sample_metrics = read_json(sample_metrics_path) if sample_metrics_path.exists() else {}
    wfv_metrics = read_json(wfv_metrics_path) if wfv_metrics_path.exists() else {}

    config_paths = sorted((ROOT / "configs").glob("*.yaml"))

    pyproject_text = read_text(ROOT / "pyproject.toml")
    deps = []
    dep_match = re.search(r"dependencies\s*=\s*\[(.*?)\]", pyproject_text, re.S)
    if dep_match:
        deps = [d.strip().strip('"') for d in dep_match.group(1).split(",") if d.strip()]

    test_files = [item["path"] for item in inventory if item.get("role") == "test" and item["path"].endswith('.py')]

    changelog_text = read_text(ROOT / "CHANGELOG.md")

    docs = {
        "ARCHITECTURE.md": render_architecture(symbol_index, inventory),
        "MODULE_SUMMARIES.md": render_module_summaries(symbol_index),
        "FUNCTION_INDEX.md": render_function_index(symbol_index),
        "DEPENDENCY_GRAPH.md": render_dependency_graph(import_graph),
        "PIPELINE_FLOW.md": render_pipeline_flow(make_targets),
        "DATAFLOW.md": render_dataflow(),
        "EXPERIMENTS.md": render_experiments(inventory),
        "CURRENT_RESULTS.md": render_current_results(
            readme_text, wrds_text, wrds_smoke_text, sample_metrics, wfv_metrics
        ),
        "RESEARCH_NOTES.md": render_research_notes(),
        "OPEN_QUESTIONS.md": render_open_questions(),
        "KNOWN_ISSUES.md": render_known_issues(),
        "ROADMAP.md": render_roadmap(),
        "CONFIG_REFERENCE.md": render_config_reference(config_paths),
        "SERVER_ENVIRONMENT.md": render_server_environment(platform.python_version(), deps),
        "TEST_COVERAGE.md": render_test_coverage(test_files),
        "STYLE_GUIDE.md": render_style_guide(),
        "CHANGELOG.md": render_changelog(changelog_text),
        "INDEX.md": render_index(),
    }

    for name, body in docs.items():
        content = header(generated_at, sha, branch, commands) + body
        write_doc(PS_DIR / name, content)


if __name__ == "__main__":
    main()

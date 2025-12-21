<!--
generated_at: 2025-12-21T19:43:02Z
git_sha: bf7e8ea58e82c009404eb0e5fa2ccde8a62a72a2
branch: feat/ticket-06-bundle-commit-consistency
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


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

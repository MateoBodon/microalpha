<!--
generated_at: 2026-01-25T23:23:20Z
git_sha: 4d08d18202a411cd831efce739cd5cb37e6deb1e
branch: codex/ticket-22-wrds-resume-metrics
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Style Guide

- Python 3.12+, fully type-hinted (`src/microalpha`).
- Lint: `ruff check .` (line length 88, E/F/W/I rules, E501 ignored).
- Format: Black (line length 88).
- Types: `mypy src/microalpha` (python_version=3.12).
- Docstrings required for public functions/classes.
- Prefer small composable functions; avoid clever one-liners.

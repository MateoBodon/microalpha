<!--
generated_at: 2025-12-21T20:56:43Z
git_sha: 4457b33773c24c5e7179bc4df0346c150e8d5876
branch: feat/ticket-02-holdout-wfv
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

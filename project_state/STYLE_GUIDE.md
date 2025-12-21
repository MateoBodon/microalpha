<!--
generated_at: 2025-12-21T19:48:07Z
git_sha: 631272f7041bff01de865fa5139a4a9e4004c3b2
branch: feat/ticket-06-bundle-commit-consistency
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

<!--
generated_at: 2025-12-21T19:43:02Z
git_sha: bf7e8ea58e82c009404eb0e5fa2ccde8a62a72a2
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

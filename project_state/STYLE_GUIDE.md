<!--
generated_at: 2025-12-21T22:42:31Z
git_sha: 2b48ef75f24acdb206db20d9f5a2681366ac5afa
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

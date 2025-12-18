# 2025-12-18
- Added cost sensitivity and metadata coverage reporting pipeline (robustness artifacts + summary section) and tests.
- Updated artifact contract docs and ran required validations: `python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'`, `ruff check`, `pytest -q`, `mkdocs build`, `microalpha report --artifact-dir artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7`, `microalpha report --artifact-dir artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7`.

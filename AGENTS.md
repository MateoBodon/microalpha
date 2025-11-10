# AGENTS.md — microalpha

## Primary Goals
- Produce WRDS-backed, leakage-safe backtests with walk-forward CV and statistically-defensible attribution/tearsheets.
- Keep runs reproducible: every change must include tests and docs updates when behavior changes.

## Local Setup
- Python: 3.11+ (uv/poetry/venv is fine)
- Install: `pip install -e .[dev]`
- Pre-commit: `pre-commit install`
- CLI help: `microalpha --help`

## Secrets & Data (mandatory rules)
- Never commit WRDS data or credentials.
- Use `.pgpass` for WRDS (host: `wrds-pgdata.wharton.upenn.edu`, port: `9737`, db: `wrds`). File perms `600`.
- If you must read env vars, they are named `WRDS_USERNAME` and `WRDS_DATA_ROOT`. Do **not** print secrets in logs.
- Artifacts to commit: manifests/metrics/PNGs/MD summaries only.

## Tasks you may run
- Unit tests: `pytest -vv --maxfail=1 --durations=25`
- WRDS smoke: `make test-wrds`
- Coverage: `pytest --cov=microalpha`
- WRDS integration tests (local only): `pytest -m wrds -vv`
- Build docs: `mkdocs build`
- Canonical WRDS WFV: `make wfv-wrds` then `make report-wrds`
- Guardrail shortcuts: `make test`, `make test-wrds`, `make docs`

## Coding Standards
- Style: black + isort + ruff; type hints required for public APIs.
- Determinism: seed RNGs via the Engine/CLI; no global randomness.
- Edits: prefer minimal diffs and use `apply_patch` operations.

## Backtesting/Leakage Rules
- Enforce t+1 semantics, monotonic timestamps, FIFO LOB when chosen.
- No peeking across folds; parameters must be trained inside each train window only.

## Testing Expectations
- Add unit tests for new modules and invariants.
- Add `@pytest.mark.wrds` integration tests that operate on local WRDS exports when present; skip gracefully if not.
- Log test results verbosely to `artifacts/logs/pytest-*.log`.

## Docs & Reporting
- If behavior/perf changes, update `docs/` and `reports/summaries/*.md`.
- WRDS results must include: equity curve, DD plot, IC/IR timeseries, deciles (P10–P1), factor table (Carhart/FF5), capacity & turnover, and reality-check/SPA p-values.
- Use `reports/analytics.py` for IC/IR + deciles + rolling betas, `reports/factors.py` for Carhart/FF5(+MOM) attribution, and `reports/spa.py` for Hansen SPA summaries. Guard outputs under `artifacts/plots/` and `reports/summaries/`.

## Git & Commits
- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `perf:`, `refactor:`).
- Commit in small, reviewable chunks; each behavior change must include tests/docs.
- Never include secrets or WRDS data.

## What you must do before finishing a task
- Run unit tests and (if applicable) `-m wrds` tests locally.
- Rebuild docs; ensure no broken links.
- Update CHANGELOG.md with a terse entry.
- Summarize work in PR body with links to artifacts.

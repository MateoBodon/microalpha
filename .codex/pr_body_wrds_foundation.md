## Summary
- add repo guardrails (pre-commit, pytest marker config, WRDS detection helpers, CHANGELOG/AGENTS) and new Makefile/test logging hooks.
- ship analytics/reporting tranche (IC/IR/deciles, FF5(+MOM) attribution, SPA tooling, WRDS config + docs + README updates) plus coverage tests.
- enhance CI to lint, test (skipping wrds by default), check coverage, cache pip, build docs, and publish HTML coverage artifacts.

## Testing
- `pytest -vv --maxfail=1 --durations=25`
- `pytest -m wrds -vv` *(skipped automatically: WRDS data root not configured on runner)*
- `mkdocs build`

## Artifacts
- `artifacts/logs/pytest-20251110-205216.log`

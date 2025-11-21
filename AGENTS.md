# microalpha – AGENTS.md

This file is for AI coding agents (Codex, Cursor, etc.) and humans who want the “project brain dump” in one place.

Always read this file **and** `Plan.md` before making changes.

---

## Core commands

### Environment

- Create venv and install dev deps:

  ```bash
  python -m venv .venv
  source .venv/bin/activate
  pip install -e '.[dev]'
Quick smoke runs (no WRDS)
Single flagship sample backtest:
bash
Copy code
make sample && make report
Flagship sample walk-forward + factor regression:
bash
Copy code
make wfv && make report-wfv
Artefacts land under:
artifacts/sample_flagship/<RUN_ID>/
artifacts/sample_wfv/<RUN_ID>/
Tests
Fast test suite (CI-safe, no WRDS):
bash
Copy code
make test          # or: pytest -q
All tests including slower ones but still no WRDS:
bash
Copy code
make test-all      # or: pytest -q -m "not wrds"
Local WRDS tests (require WRDS/CRSP data and credentials):
bash
Copy code
make test-wrds     # or: pytest -q -m "wrds"
Agents:
Always run make test (or pytest -q) before committing.
Only run WRDS tests if you detect the local WRDS data paths described in docs/wrds.md and the relevant config files.
Project structure (high level)
Key directories:
src/microalpha/ – core engine, data handlers, strategies, portfolio, broker, execution models, reporting code.
configs/ – YAML configs for backtests and walk-forward runs, including sample, public, and WRDS configs.
data/ – small bundled data (sample/public, FF3 factors). Safe to keep in repo.
data_sp500/ – larger but still non-licensed data samples (e.g. SP500-like panels or intraday samples).
artifacts/ – generated run artefacts (metrics, bootstrap, equity curves, exposures, trades). These are reproducible and may be committed selectively.
docs/ – MkDocs documentation, including methodology, WRDS guide, leakage safety, and results pages.
notebooks/ – analysis notebooks that load artefacts and produce plots/tables.
reports/ – scripts to build Markdown/HTML reports from artefacts.
tests/ – pytest tests; some may be marked wrds or slow.
Treat src/microalpha as library code. Configs, scripts, and notebooks should plug into that API rather than duplicating logic.
Code style & conventions
Python 3.12+, fully type-hinted in src/microalpha.
Prefer small, composable functions over huge classes.
Keep business logic in src/microalpha, not in CLI wrappers or notebooks.
Use docstrings on public functions and classes. Brief but specific.
Avoid clever one-liners; readability wins.
When adding a new strategy:
Put reusable components in src/microalpha/strategies/ (or equivalent module).
Wire it from YAML configs rather than hand-coding in a script.
Static checks:
Lint:
bash
Copy code
ruff check .
Type check:
bash
Copy code
mypy src/microalpha
Agents should run ruff and mypy on touched areas when refactoring engine code.
Testing conventions
All new behaviours must have tests in tests/.
Use pytest; keep tests small and deterministic.
Mark WRDS-dependent tests:
python
Copy code
import pytest

@pytest.mark.wrds
def test_wrds_pipeline_smoke(): ...
Mark slow, heavy WFV tests with @pytest.mark.slow.
Default expectations for agents:
For small changes, run targeted tests (e.g. pytest tests/test_x.py::test_y).
Before committing, run at least:
bash
Copy code
pytest -q
For changes to walk-forward, reporting, or stats:
Run the relevant make target (e.g. make sample && make report).
Spot-check artefacts: ensure metrics.json, bootstrap.json, equity_curve.png, etc. exist.
WRDS / real data rules
WRDS/CRSP data must never be committed to the repo.
WRDS-related configs live in configs/*wrds*.yaml.
The expected WRDS schema is documented in docs/wrds.md.
WRDS file paths can be user-specific and should not be hardcoded into library code:
Use config files and environment variables.
Tests that require WRDS should be marked wrds and skipped if data is missing.
Agents:
When adding or editing WRDS functionality:
Do not print raw WRDS data in logs or docs.
Operate on aggregates/metrics only.
Provide clear instructions (in Markdown or docstrings) for humans about how to export data and where to place it locally.
Git workflow
Default branch: main.
Feature branches: feature/<short-description>.
Commit rules:
Keep commits small and coherent.
Message format:
Short imperative summary on first line.
Optional detail bullets below if needed.
Examples:
Add WRDS momentum WFV config
Refine bootstrap summary report for WRDS runs
Agents:
Never reformat the entire repo in one commit.
Don’t touch .secrets.baseline or other security-related config unless explicitly prompted.
Only run git push when:
Working tree is clean.
Tests have passed.
You’ve reviewed git diff and it looks sane.
Agent behaviour
When you (agent) start a new task in this repo:
Read AGENTS.md.
Read Plan.md (or docs/plan.md) and identify the next relevant task.
Print a short plan (3–7 bullets) before making changes.
Work iteratively:
Use grep/rg to understand existing code.
Prefer minimal edits and refactors, not rewrites.
After implementing changes:
Run the relevant tests and make targets.
If WRDS data is available and the task touches WRDS logic, run at least one WRDS smoke test.
Before committing:
Ensure tests pass.
Ensure docs or comments are updated if behaviour changed.
If you hit a blocker (e.g. missing WRDS data, credentials, or environment variables):
Stop and summarise:
What you tried.
Exact command output.
What a human needs to do next (e.g. export data, set env var).
Boundaries
Do not:
Commit WRDS/CRSP data or other licensed datasets.
Delete or radically rewrite core engine modules unless the plan explicitly asks for it.
Introduce new external dependencies without updating pyproject.toml and relevant docs.
Prefer incremental improvement over large, speculative refactors.
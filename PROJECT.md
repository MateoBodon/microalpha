# PROJECT.md

## Project Profile
- Name: microalpha
- One-liner: Leakage-safe, event-driven backtesting engine with walk-forward cross-validation and reporting.
- Type: research/trading
- Risk tier: high
- Primary languages: Python
- External dependencies / services: WRDS/CRSP exports (optional), MkDocs (docs site)

## Goals (what “done” looks like)
- Leakage-safe backtesting and walk-forward validation with reproducible artifacts.
- Sample/public data runs plus an optional WRDS pipeline for real data.
- Report generation (plots + Markdown summaries) suitable for audit/review.

## Non-goals (explicitly out of scope)
- Live trading execution or brokerage integration.
- Guaranteed alpha discovery or performance claims.

## Current state
- What works: sample/public configs, WFV runs, reporting, docs + tests.
- What’s missing: real-data runs require local WRDS exports and credentials.
- What’s broken: see `project_state/KNOWN_ISSUES.md` for open issues.
- Biggest risks: leakage/survivorship bias, missing WRDS data, misreported results.

## Quickstart (how to run)
- `python -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'`
- `make sample && make report`
- `make wfv && make report-wfv`
- `pytest -q`

## Architecture (high-level)
- Modules: `src/microalpha/` (engine, data, strategies, reporting, CLI).
- Data flow: DataHandler -> Engine -> Strategy -> Portfolio -> Broker -> Trades.
- Key invariants: strict chronology, t+1 execution, point-in-time universe.

## Constraints / preferences
- Performance constraints: deterministic runs; prefer reproducible pipelines.
- Safety constraints: leakage-safe evaluation; no raw WRDS data in repo.
- Style constraints: `black`, `isort`, `ruff`.

## Links
- Docs: `README.md`, `docs/` (MkDocs site).
- Issues: GitHub Issues (if enabled).

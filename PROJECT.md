# PROJECT.md

## Project Profile
- Name: microalpha
- One-liner: Quant research evidence engine for real-data, chronology-safe, costed, walk-forward reports and adversarial correctness audits.
- Type: quantitative engineering / research infrastructure
- Risk tier: high
- Primary languages: Python
- External dependencies / services: WRDS/CRSP exports (optional), MkDocs (docs site)

## Goals (what “done” looks like)
- One-command real-data Market Risk Case plus deterministic Audit Lab evidence, each with schemas and a SHA-256 receipt.
- Event-scheduled execution, point-in-time availability, explicit cost reconciliation, and benchmark-differential selection correction.
- Clean-clone install, portable CLI/API, green cross-platform CI, and product-first docs.
- Honest public case studies; a negative research result is preserved instead of tuned away.

## Non-goals (explicitly out of scope)
- Live trading execution or brokerage integration.
- Guaranteed alpha discovery or performance claims.

## Current state
- What works: deterministic real-data Market Risk Case, Audit Lab, sample/public configs, WFV runs, reporting, verifier, docs, CLI/API, and tests.
- Optional: licensed-data workflows require authorized local exports and never ship raw rows.
- Historical research: six frozen mechanisms failed promotion gates; 2023–2025 remains sealed.
- Biggest risks: incorrect source availability metadata, survivorship bias, uncalibrated simulation costs, and claims stronger than receipts.

## Quickstart (how to run)
- `python -m venv .venv && source .venv/bin/activate && pip install .`
- `python -m microalpha market-demo && python -m microalpha verify docs/assets/market_case`
- `python -m microalpha audit-demo && python -m microalpha verify docs/assets/audit_lab`
- Contributors: `pip install -e '.[dev]' && pytest -q`

## Architecture (high-level)
- Modules: `src/microalpha/` (engine, data, strategies, reporting, CLI).
- Data flow: DataHandler -> Engine clock -> Strategy -> Portfolio -> ExecutionPlan -> Broker/materialized FillEvent -> Evidence receipt.
- Key invariants: availability at decision time, no early fill mutation, exact cost reconciliation, isolated test/holdout windows, synchronous null-centered selection correction.

## Constraints / preferences
- Performance constraints: deterministic runs; prefer reproducible pipelines.
- Safety constraints: leakage-safe evaluation; no raw WRDS data in repo.
- Style constraints: `black`, `isort`, `ruff`.

## Links
- Docs: `README.md`, `docs/` (MkDocs site).
- Issues: GitHub Issues (if enabled).

# Context Carryover

last_updated: 2026-07-03
updated_by: GPT-5.5 Pro Extended
source_event: Pro strategy package after T-000

## Compact Identity

microalpha is a Python quant/research repo for leakage-safe event-driven
backtesting, walk-forward validation, WRDS/CRSP research, reporting, and
evidence-backed portfolio claims.

## Current Strategic Phase

WRDS Prestige Evidence Phase.

T-000 installed AI Project OS v2. The next work should not be more process
scaffolding. It should verify current evidence/data and move toward stronger
defensible WRDS results.

## User Goal

Maximize prestige/performance and portfolio impact. Avoid conservative tiny
tickets and over-bureaucratic docs. Move fast, but do not allow fake validation,
unsupported claims, stale docs, or raw-data exposure.

## Current Truth

- Canonical strategy docs: `docs/strategy/`
- State map: `project_state/STATE_INDEX.md`
- Validation: `project_state/VALIDATION_MATRIX.md`
- Claims: `project_state/CLAIMS_AND_EVIDENCE.md`
- Commands: `project_state/RUNBOOK.md`
- Historical context: `docs/_archive/pre_ai_os_v2/20260703/`

## Critical Facts

- Public mini-panel evidence is degenerate with 0 trades; pipeline evidence only.
- WRDS evidence is the main prestige path but claim-sensitive and local-data-dependent.
- Changelog indicates current WRDS best eligible holdout run
  `2026-02-16T22-33-46Z-8d90621` with Sharpe_HAC `0.588`, but exact current
  artifact contents must be verified before public wording.
- The 2018-2019 WRDS holdout has been used repeatedly; a new campaign should
  prefer expanded data and fresher final evaluation if possible.
- Bare `make test-fast` had import drift in T-000; local-source validation must
  be enforced before relying on green tests.
- Raw WRDS/CRSP data must never be committed or bundled.

## Next Heavy Move

Dispatch T-001: install strategy package, verify current artifacts/claims, fix
test import drift, and create the baseline for data recovery.

Then dispatch T-002/T-003 for data/artifact recovery and WRDS baseline reproduction.

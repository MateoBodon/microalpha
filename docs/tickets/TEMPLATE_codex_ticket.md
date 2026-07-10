# T-### - Title

status: planned
owner_flow: Pro planned -> Heavy dispatched -> Codex executes -> Heavy reviews -> Pro recenter only if needed

## Goal

Describe the target outcome, not implementation micro-steps.

## Why This Matters

Explain the project value, goal alignment, and why this ticket is worth doing
now.

## Scope

### In Scope

- ...

### Out Of Scope

- ...

## Context Files

- `AGENTS.md`
- `PROJECT.md`
- `docs/strategy/GOAL_CONTEXT.md`
- `docs/strategy/PLAN_OF_RECORD.md`
- `docs/strategy/CONTEXT_CARRYOVER.md`
- `project_state/RUNBOOK.md`
- `project_state/VALIDATION_MATRIX.md`
- relevant source, tests, configs, and prior review bundles

## Acceptance Criteria

- ...

## Validation Level

Choose one:

- L0 smoke
- L1 targeted
- L2 full fast suite
- L3 integration/reproduction
- L4 release/claim audit

Expected commands:

```bash
...
```

If a command cannot run, Codex must state exactly why and run the next-best
check.

## Review Artifacts Required

- original work order;
- changed file list;
- diff or patch;
- run log;
- exact command outputs;
- validation summary;
- updated docs if relevant;
- generated artifacts required for review;
- compact review bundle with manifest and index.

## Stop-The-Line Conditions

- unsupported external-facing claim;
- failing required validation;
- suspected data leakage or chronology violation;
- raw restricted data exposure;
- broad unrelated changes;
- strategic ambiguity requiring Pro;
- hidden generated artifacts not represented in the bundle.

## Notes For Codex

Use autonomous codebase exploration. Solve the ticket end to end. Prefer robust,
maintainable changes. Ask only if missing information would materially change
implementation or create serious risk. Record what changed and how it was
validated.

# Prompt

Source prompt captured at:
- `docs/prompts/20260216_223228_ticket-35_wrds-micro-sweep.md`

## Ticket
- Ticket: `ticket-35`
- Run name: `20260216_223228_ticket-35_wrds-micro-sweep`
- Summary: WRDS micro-sweep for improved holdout metrics + resume snippet

## Goal
Run a pre-registered, bounded WRDS WFV micro-sweep and publish provenance-complete, resume-safe artifacts for the sweep winner, then refresh leaderboard outputs and current-results pointers.

## Pre-registered sweep design (fixed before execution)
- Holdout window remains fixed to canonical WRDS holdout:
  - `2018-01-02` to `2019-12-31`
- Winner rule (fixed):
  - Primary objective: maximize holdout `Sharpe_HAC`
  - Guardrails: holdout `trades >= 20` and holdout `maxdd <= 15%`
  - Tie-breakers: lower holdout `MaxDD`, then higher holdout `MAR`
- Sweep knobs (2 existing grid knobs only):
  - `lookback_months`: `[9, 12, 18]`
  - `top_frac`: `[0.15, 0.20, 0.25]`
- Fixed grid settings for this run:
  - `skip_months`: `[1]`
  - `allocator_kwargs`: `[{risk_model: "risk_parity"}]`
- Combo cap check: `3 x 3 x 1 x 1 = 9` total evaluated combos (<= 12 cap)

## Output + policy constraints
- Local-only bulky outputs:
  - `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/...`
  - `reports/_runs/20260216_223228_ticket-35_wrds-micro-sweep/...`
- Tracked resume-safe outputs only under `docs/artifacts/resume/wrds/...` (aggregates/snippets; no raw WRDS rows).

## Planned commands
1. `WRDS_DATA_ROOT=/srv/data/wrds/wrds microalpha wfv --config configs/wfv_flagship_wrds_sweep35.yaml --out artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship`
2. `WRDS_DATA_ROOT=/srv/data/wrds/wrds microalpha report --artifact-dir artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/<BEST_RUN_ID> --out reports/_runs/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship.md`
3. `python3 scripts/wrds_leaderboard.py --out docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
4. `make test-fast`

TICKET: ticket-15
TITLE: Fix SPA KeyError on WRDS flagship + block headline when inference failed

Follow AGENTS.md exactly (stop-the-line rules, data policy, docs protocol, branch/commit policy).
Do NOT write a long upfront plan. Start by inspecting the repo and reproducing the bug.

## Goal
1) Fix Hansen SPA computation so it does NOT fail with KeyError on the latest WRDS flagship artifact directory.
2) Enforce “no headline if SPA failed”: if SPA status is error/exception, results pages must clearly say so and must not present the run as headline.
3) Repair audit hygiene regressions in the previous run logs:
   - PROMPT.md must contain the EXACT prompt (no "..." truncation).
   - META.json must record concrete git SHAs (git_sha_after must not be "HEAD").

## Setup (required)
- Create feature branch: `codex/ticket-15-fix-spa-keyerror`
- Set RUN_NAME using UTC timestamp:
  - `RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-15_fix-spa-keyerror"`
- Create run log dir:
  - `mkdir -p "docs/agent_runs/$RUN_NAME"`

Write the exact prompt you are executing to:
- `docs/prompts/${RUN_NAME}_ticket-15_fix-spa-keyerror.md`
- `docs/agent_runs/$RUN_NAME/PROMPT.md`
(Exact text. No truncation. No ellipses.)

## Reproduce (must be report-only, real-data, minimal)
Use the latest WRDS flagship artifact dir referenced in the repo docs (currently appears to be):
- `artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/`

Reproduce SPA generation on that directory WITHOUT re-running WRDS exports:
- Prefer `microalpha report --artifact-dir <DIR>` or the smallest Makefile target that only regenerates reports.
- Record the exact command and output paths in COMMANDS.md.

Confirm current failure:
- `reports/summaries/wrds_flagship_spa.json` shows `status: degenerate` with a KeyError “not in index”.
We want this gone.

## Fix (code)
Inspect and fix the SPA pipeline so bootstrapping/indexing cannot KeyError:
- Likely files:
  - `src/microalpha/reporting/spa.py`
  - Any helper that builds the candidate return matrix for SPA / reality-check
  - The WRDS summary/report generator that calls SPA (e.g., `src/microalpha/reporting/summary.py` or `reports/*wrds*`)

Hard requirements:
- SPA must operate on a stable structure (recommendation: T×K DataFrame with DatetimeIndex rows and strategy-id columns; bootstrap by integer positions, not label strings).
- If SPA truly cannot run (e.g., insufficient obs, all-zero variance), output:
  - `spa_status: "degenerate"` with a REAL degeneracy reason (not an exception).
- If SPA hits an unexpected exception, output:
  - `spa_status: "error"` and include the exception string in `spa_error`.
  - Do NOT label that as “degenerate”.

## Reporting / gating (docs + reports)
If SPA status is not "ok":
- `docs/results_wrds.md` and `reports/summaries/wrds_flagship.md` must show an explicit banner like:
  - “INFERENCE FAILED (SPA error): not resume-credible / not headline”
- Do NOT silently show `SPA_p_value: n/a` without the reason.
- If the user previously asked to “headline” a run, this gating overrides that until SPA is fixed.

Also update:
- `project_state/CURRENT_RESULTS.md` to reflect SPA status and to avoid presenting the run as headline if SPA failed.

## Tests (required)
1) Add a regression unit test that would have caught the KeyError:
   - Create a small candidate-returns matrix that matches the shape/indexing used by the report.
   - Assert SPA code runs without KeyError.
   - Assert output schema includes `spa_status` and (if ok) `p_value` in [0,1].
2) Run:
   - `make test-fast`
   - `pytest -q tests/test_spa_regression_keyerror.py` (or your chosen filename)

## Real-data smoke (required)
After the fix, rerun the report-only command on:
- `artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/`

Acceptance:
- `reports/summaries/wrds_flagship_spa.json` has:
  - `spa_status: "ok"` and `p_value` in [0,1] with `n_obs > 0` and `n_strategies > 0`
  - OR `spa_status: "degenerate"` with a NON-exception reason (e.g., zero variance)
  - MUST NOT be `KeyError ... not in index`

## Run log + living docs (required)
Write:
- `docs/agent_runs/$RUN_NAME/COMMANDS.md` (every command)
- `docs/agent_runs/$RUN_NAME/RESULTS.md` (what changed, what was fixed, before/after SPA status, and links to outputs)
- `docs/agent_runs/$RUN_NAME/TESTS.md`
- `docs/agent_runs/$RUN_NAME/META.json` with:
  - git_sha_before (rev-parse HEAD at start)
  - git_sha_after (rev-parse HEAD after final commit)
  - dataset_id (wrds artifact-based, no raw data)
  - config hashes if you touch configs

Update:
- `PROGRESS.md`
- `docs/CODEX_SPRINT_TICKETS.md`:
  - mark ticket-14 as FAIL (review) with reasons
  - add ticket-15 with acceptance criteria
- `project_state/KNOWN_ISSUES.md` (new SPA KeyError issue; mark resolved if fixed)

## Commits (required)
- Small logical commits on the feature branch.
- Commit message prefix: `ticket-15: ...`
- Commit body must include:
  - `Tests: ...`
  - `Artifacts: ...`
  - `Docs: ...`

## Finish (required)
- Generate the bundle and record its path in RESULTS.md:
  - `make gpt-bundle TICKET=ticket-15 RUN_NAME=$RUN_NAME`

## Merge policy
Do NOT merge to main unless the user explicitly tells you to merge in this prompt or a follow-up.
If explicitly instructed to merge:
- Merge to main.
- Immediately regenerate the bundle post-merge and record that new bundle path in RESULTS.md.

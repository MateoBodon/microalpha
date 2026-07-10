# Claims And Evidence

last_updated: 2026-07-03
updated_by: Codex T-001
source_event: Pro strategy install and evidence inventory

This repo makes research, benchmark, and result-adjacent claims, so claims must
stay tied to artifacts and validation.

| Claim | Status | Evidence | Validation | Caveats |
|---|---|---|---|---|
| microalpha is a leakage-safe event-driven backtesting engine. | supported for tested invariants | `tests/test_no_lookahead.py`, `tests/test_tplus1_execution.py`, engine/data tests | `make test-fast`, `pytest -q` | Needs ongoing review when execution/data code changes. |
| Sample bundled results in README are reproducible demo artifacts. | supported as demo | `artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7/`, `artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7/` | artifact schema tests, README docs tests | Demo data, not investment evidence. |
| Public mini-panel resume line is current. | supported as pipeline/demo evidence only | `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/`, `resume_line_best.md`, `project_state/CURRENT_EVIDENCE_SUMMARY.md` | prior ticket-37 run log, T-001 artifact inspection, local-source `make test-fast` | Latest run is degenerate with `0` trades; do not use as alpha/performance claim. |
| WRDS resume line/leaderboard is artifact-backed. | partially supported, local-data-dependent, and claim-sensitive | `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/`, `docs/artifacts/resume/wrds/leaderboard/`, `project_state/CURRENT_EVIDENCE_SUMMARY.md` | prior ticket-35/36 logs, T-001 artifact inspection, data-policy checks | Current curated metrics are present, but local source artifacts are absent here and the promoted manifest excerpt config hash conflicts with tracked config/run-log hash; L3/L4 needed before external claims. |
| WRDS pipeline can run on local exports. | historical support, currently blocked for reproduction in this checkout | `docs/agent_runs/`, `docs/results_wrds*.md`, `project_state/CURRENT_RESULTS.md`, `project_state/DATA_ARTIFACT_INVENTORY.md` | WRDS commands when `WRDS_DATA_ROOT` is available | `WRDS_DATA_ROOT` is unset in T-001 and historical `/srv/data/wrds/wrds` is absent; T-003 requires restored/exported WRDS data. |
| AI Project OS v2 strategy layer reflects Pro's current direction. | supported | `docs/strategy/`, `project_state/STATE_INDEX.md`, `project_state/CURRENT_EVIDENCE_SUMMARY.md` | T-001 review bundle and docs build | Strategy docs are Pro-authored direction; exact metrics still come only from current repo artifacts. |

## Unsupported Or Awaiting Pro Review

- Any statement that the strategy "found alpha" on WRDS/CRSP.
- Any headline result that omits costs, baselines, holdout window, dataset id, or
  inference/caveats.
- Any conclusion drawn from old archived prompts or GPT outputs without current
  evidence.
- Any exact WRDS config-hash claim until the `2026-02-16T22-33-46Z-8d90621`
  manifest-excerpt hash mismatch is resolved by source-artifact recovery or L3
  reproduction.

## Evidence Rules

- A claim should cite a path, command, and caveat.
- If evidence is historical, label it as historical.
- If a run is degenerate, say so directly.
- If evidence depends on WRDS, state that raw data is local-only and excluded.

sou good, now i want you to go through this checklist, make sure everything is complete, then commit, merge to main and push to origin, then tell me which final bundle to upload for review,  Read docs/agent_runs/<RUN_NAME>/RESULTS.md and confirm it answers: “Where do orders collapse to zero?” with concrete stage evidence (weights/orders/broker/fills).
 Confirm no threshold/p-hacking changes: no loosening min_adv, min_price, non_degenerate.min_trades, turnover caps, etc unless there’s a bug-level justification + tests.
 Confirm tests are real and recorded:
make test-fast output logged
new diagnostics test file executed
 Inspect diff: diagnostics must be sideband only (should not change trading decisions/scoring).
 Check WRDS smoke/debug run evidence:
artifact dir exists
folds.json / manifest.json contains the new diagnostics
 Check run log completeness (PROMPT/COMMANDS/RESULTS/TESTS/META) and that META has concrete SHAs (not “HEAD”).
 Confirm docs/CODEX_SPRINT_TICKETS.md updated: ticket-13 marked DONE; ticket-14 added with acceptance criteria.
 Generate + verify bundle path recorded in RESULTS.md before merging.

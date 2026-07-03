# Results

## Summary
- Shipped ticket-32 deliverables in a tracked commit so they now appear in `DIFF.patch`.
- Reverted unrelated `tools/agentic/runlog_init.py` drift to keep scope as docs-only shipping/verification.
- Validated both run logs and generated a new GPT bundle from a clean worktree (`git_dirty: false`).

## Key outputs
- Commit: `ticket-32: ship ticket-32 deliverables cleanly` (created in this run).
- Bundle: `artifacts/_local/gpt_bundles/gpt_bundle_*_ticket-ticket-32b.zip` (generated from clean tree in this run).
- `docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice/`
- `docs/tickets/TICKET-32_wrds_resume_line_pick-the-best-defensible-metric.md`
- `docs/prompts/20260216_021416_ticket-32_wrds-resume-line-window-choice.md`
- `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/resume_line_holdout.md`
- `PROGRESS.md`
- `docs/agent_runs/20260216_025221_ticket-ticket-32b/`

## Notes
- `resume_line_holdout.md` is explicit about window (`holdout-only, 2018-01-02 to 2019-12-31`) and includes both `run_id` and `dataset_id`.
- Validation commands:
  - `python3 tools/agentic/validate_runlog.py --run-name 20260216_021416_ticket-32_wrds-resume-line-window-choice`
  - `python3 tools/agentic/validate_runlog.py --run-name 20260216_025221_ticket-ticket-32b`
- No code-path changes were shipped in this run.

# Commands

Log commands that materially change state or produce results.

- `git status --short`
  - Confirmed ticket-32 files were untracked and `tools/agentic/runlog_init.py` had extra non-ticket changes.
- `git rev-parse --abbrev-ref HEAD && git log --oneline -n 3`
  - Verified branch/head still at ticket-31 commit (`4cb27f8f...`).
- `git diff -- tools/agentic/runlog_init.py`
  - Confirmed added early-return behavior for pre-existing run dirs.
- `git restore -- tools/agentic/runlog_init.py`
  - Reverted non-ticket code drift to keep this docs-only.
- `python3 tools/agentic/runlog_init.py --ticket "ticket-32b" --summary "Ship ticket-32 deliverables cleanly (commit + clean bundle)"`
  - Created shipping run log: `docs/agent_runs/20260216_025221_ticket-ticket-32b/`.
- `python3 tools/agentic/validate_runlog.py --run-name 20260216_021416_ticket-32_wrds-resume-line-window-choice`
  - Passed (`OK`).
- `python3 tools/agentic/validate_runlog.py --run-name 20260216_025221_ticket-ticket-32b`
  - Passed (`OK`).
- `git add CHANGELOG.md PROGRESS.md docs/CODEX_SPRINT_TICKETS.md docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice docs/agent_runs/20260216_025221_ticket-ticket-32b docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/resume_line_holdout.md docs/prompts/20260216_021416_ticket-32_wrds-resume-line-window-choice.md docs/tickets/TICKET-32_wrds_resume_line_pick-the-best-defensible-metric.md`
  - Staged ticket-32 deliverables and shipping-run docs.
- `git commit -m "ticket-32: ship ticket-32 deliverables cleanly" -m "Tests: python3 tools/agentic/validate_runlog.py --run-name 20260216_021416_ticket-32_wrds-resume-line-window-choice; python3 tools/agentic/validate_runlog.py --run-name 20260216_025221_ticket-ticket-32b (docs-only ship; make test-fast N/A after reverting code drift)" -m "Artifacts: docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/resume_line_holdout.md; docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice/; docs/agent_runs/20260216_025221_ticket-ticket-32b/" -m "Docs: docs/tickets/TICKET-32_wrds_resume_line_pick-the-best-defensible-metric.md; docs/prompts/20260216_021416_ticket-32_wrds-resume-line-window-choice.md; PROGRESS.md; CHANGELOG.md; docs/CODEX_SPRINT_TICKETS.md"`
  - Committed ticket-32 shipment.
- `python3 tools/agentic/gpt_bundle.py --ticket "ticket-32b" --run-name "20260216_025221_ticket-ticket-32b"`
  - Generated fresh review bundle from clean tree.
- `git status --porcelain`
  - Verified clean worktree after commit/bundle generation.
- `unzip -p artifacts/_local/gpt_bundles/gpt_bundle_*_ticket-ticket-32b.zip BUNDLE_META.md`
  - Verified `git_dirty: false` in bundle metadata.
- `unzip -p artifacts/_local/gpt_bundles/gpt_bundle_*_ticket-ticket-32b.zip DIFF.patch | rg "20260216_021416_ticket-32_wrds-resume-line-window-choice|TICKET-32_wrds_resume_line_pick-the-best-defensible-metric.md|resume_line_holdout.md|PROGRESS.md"`
  - Verified required ticket-32 deliverables are present in `DIFF.patch`.

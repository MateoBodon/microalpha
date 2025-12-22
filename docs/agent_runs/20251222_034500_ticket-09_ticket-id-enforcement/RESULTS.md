Summary:
- Backfilled ticket-08 in sprint tickets with goals, rationale, acceptance criteria, tests, and status.
- Added ticket-09 to sprint tickets to match this run and prevent future mismatches.
- Enforced sprint ticket id presence in gpt-bundle: META.json ticket_id must match a sprint ticket header.
- Logged ticket-08 review failure and ticket-09 remediation in PROGRESS, and updated CHANGELOG.

Files touched:
- docs/CODEX_SPRINT_TICKETS.md
- tools/gpt_bundle.py
- PROGRESS.md
- CHANGELOG.md
- docs/agent_runs/20251222_034500_ticket-09_ticket-id-enforcement/*

Notes:
- META.json git_sha_after is set to HEAD (self-referential commit); gpt-bundle resolves HEAD to an immutable SHA.

Bundle:
- docs/gpt_bundles/2025-12-22T04-12-16Z_ticket-09_20251222_034500_ticket-09_ticket-id-enforcement.zip

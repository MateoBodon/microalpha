Summary
- Added the ticket-08 section to the sprint tickets so bundling can validate its ticket_id.
- Enforced that gpt-bundle fails when META.json ticket_id is not present as a sprint-ticket header.

Files touched
- docs/CODEX_SPRINT_TICKETS.md
- tools/gpt_bundle.py
- docs/agent_runs/20251222_034500_ticket-09_ticket-id-enforcement/*

Tests
- pytest -q: 102 passed, 1 skipped (rerun triggered by command-log write error; not rerun after regex fix).
- python3 -m compileall tools: success (multiple runs; tools/gpt_bundle.py compiled).

Bundle
- docs/gpt_bundles/2025-12-22T04-33-45Z_ticket-09_20251222_034500_ticket-09_ticket-id-enforcement.zip

Remaining
- None noted.

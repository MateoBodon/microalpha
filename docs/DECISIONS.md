# DECISIONS

Record non-obvious decisions. Keep it short.

Template:
- Date:
- Decision:
- Context:
- Options considered:
- Why:
- Consequences:

- Date: 2026-01-10
- Decision: Restore repo-specific Makefile, PROGRESS.md, and PLAN_OF_RECORD.md after scaffold bootstrap.
- Context: The bootstrap script overwrote existing repo docs/Makefile with generic templates.
- Options considered: Keep the templates; restore the prior files and keep agentic tools separate.
- Why: Preserve established workflows and historical logs while still adding agentic tooling.
- Consequences: Agentic scripts live under `tools/agentic/` without replacing existing repo-specific tooling.

- Date: 2026-01-24
- Decision: Remove scaffold residue and allow run logs + project_state indices to be tracked.
- Context: Bootstrap left `.bak`/`.append` files and ignored agent run logs and project_state indices.
- Options considered: Keep ignore rules and delete outputs per run; allow tracking and keep hygiene clean.
- Why: Make audit logs and indices visible to git while keeping the repo consistent.
- Consequences: `docs/agent_runs/` and `project_state/_generated/` are now visible to `git status`.

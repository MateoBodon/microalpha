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

- Date: 2026-01-25
- Decision: Record run logs under ticket-19 (ticket-XX) while documenting ticket-19a as a follow-on ticket file.
- Context: The run-log validator only accepts ticket-XX IDs, but this follow-on work uses a ticket-19a label.
- Options considered: Use ticket-19a in run logs (would fail validation); map to ticket-19 and note the sub-ticket in docs.
- Why: Keep validation/tests green while preserving traceability for the follow-on ticket.
- Consequences: Run logs use ticket-19 naming; ticket-19a details live in docs/tickets and RESULTS notes.

- Date: 2026-01-25
- Decision: Use WRDS_DATA_ROOT=/srv/data/wrds/wrds for the WRDS run.
- Context: The codex-worker mount at /srv/data/wrds contains the expected WRDS layout under a nested /wrds directory (crsp/, meta/, universes/), so configs could not find files at the top-level root.
- Options considered: Update configs to add /wrds; create a symlink; point WRDS_DATA_ROOT to /srv/data/wrds/wrds.
- Why: Avoids changing configs or dataset layout while matching the on-disk structure.
- Consequences: Run logs and results explicitly record the nested WRDS_DATA_ROOT path.

- Date: 2026-01-25
- Decision: Align WRDS WFV/holdout windows to 2013-01-02 → 2019-12-31 based on available universe coverage.
- Context: The WRDS universe file ends at 2019-12-31, so the prior 2021–2024 holdout window had no data and produced zero trades.
- Options considered: Extend/re-export WRDS data; loosen filters; shift the WFV/holdout windows to the covered period.
- Why: Shifting windows is the smallest change that restores non-degenerate holdout metrics without redesigning the strategy.
- Consequences: Resume metrics now reference a 2018–2019 holdout; future data refreshes could expand the window.

- Date: 2026-01-26
- Decision: Use ticket-24 in META.json for the ticket-24b run log.
- Context: The run-log validator only accepts ticket-XX IDs, while this follow-on work uses a ticket-24b label.
- Options considered: Use ticket-24b in META.json (fails validation); map to ticket-24 and document the suffix elsewhere.
- Why: Keeps `make validate-runlogs` green while preserving traceability through the run name and ticket file.
- Consequences: Run logs reference ticket-24 for validation; ticket-24b details live in `docs/tickets/TICKET-24b_finalize-wrds-refresh.md`.

- Date: 2026-01-26
- Decision: Use ticket-24 in META.json for the ticket-24c run log.
- Context: The run-log validator only accepts ticket-XX IDs, while this follow-on work uses a ticket-24c label.
- Options considered: Use ticket-24c in META.json (fails validation); map to ticket-24 and document the suffix elsewhere.
- Why: Keeps `make validate-runlogs` green while preserving traceability through the run name and ticket file.
- Consequences: Run logs reference ticket-24 for validation; ticket-24c details live in `docs/tickets/TICKET-24c_ship-wrds-refresh.md`.

# Decisions

last_updated: 2026-07-03
updated_by: GPT-5.5 Pro Extended
source_event: Pro strategy package after T-000

## Active Durable Decisions

### Next Phase Is WRDS Prestige Research

Decision: Optimize the next phase for WRDS/CRSP evidence and performance prestige,
not package polish.

Rationale: The user values performance/prestige most, and the repo already has
substantial infrastructure.

Reversal trigger: WRDS data cannot be recovered or regenerated.

### Public Mini-Panel Is Pipeline Evidence Only

Decision: Current public mini-panel artifacts must not be treated as performance
evidence.

Rationale: The latest canonical public mini-panel run is degenerate with 0 trades.

Reversal trigger: A future public benchmark is rebuilt with non-degenerate,
artifact-backed results.

### WRDS Claims Are Claim-Sensitive

Decision: WRDS is the main prestige path, but public/recruiting claims require
artifact-backed L3/L4 evidence.

Rationale: WRDS evidence is local-data-dependent and raw data cannot be bundled.

Reversal trigger: None for raw data policy; claim wording can change after Pro audit.

### Existing Holdout Is Historical, Not Fresh

Decision: The already-used 2018-2019 WRDS holdout should not be presented as a
pristine final holdout for a new campaign.

Rationale: It has been used repeatedly in prior tickets.

Reversal trigger: No newer data can be obtained; claims must then state this limitation.

### Data Recovery Comes Before New Claims

Decision: Verify post-transfer data/artifact state before major new result claims.

Rationale: User flagged possible data/artifact loss.

Reversal trigger: Heavy verifies all required data/artifacts are present and reproducible.

### Large Coherent Tickets Are Preferred

Decision: Heavy should dispatch ambitious coherent Codex tickets with strong
acceptance criteria.

Rationale: User rejects conservative tiny-task planning; AI OS v2 is designed for
high-throughput validated work.

Reversal trigger: Large-ticket review becomes unmanageable or repeatedly fails.

### Canonical Truth Is AI OS v2 Strategy/State

Decision: Current truth lives in `docs/strategy/` and `project_state/STATE_INDEX.md`.

Rationale: T-000 installed this layer to prevent stale pre-v2 context drift.

Reversal trigger: User standardizes on another path.

# AGENTS.md - microalpha Repo Instructions

last_updated: 2026-07-03
updated_by: Codex T-000
source_event: AI Project OS v2 installation

This repo is judged on validity, reproducibility, evidence discipline, and data
safety. Be ambitious with coherent work units, but do not blur supported facts,
historical context, and open strategy questions.

## Stop-The-Line Rules

Stop, document, and fix or escalate if any of these appear:

- evidence of lookahead/leakage in timing, fills, signal timestamps, joins, or
  report wording;
- survivorship bias in universe construction or result interpretation;
- results reported without costs, baselines, or provenance when those are needed
  for the claim;
- raw WRDS/CRSP or other restricted exports staged, bundled, or copied into
  tracked docs;
- green tests that do not actually validate the invariant at risk;
- canonical docs contradicting one another about current state or claim support.

## Canonical AI OS v2 Docs

- `PROJECT.md`: project identity and scope.
- `docs/strategy/GOAL_CONTEXT.md`: durable goals and non-goals.
- `docs/strategy/STRATEGIC_OVERVIEW.md`: current pre-Pro strategic read.
- `docs/strategy/PLAN_OF_RECORD.md`: current execution plan.
- `docs/strategy/DECISIONS.md`: durable decisions.
- `docs/strategy/RISK_REGISTER.md`: active strategic/research risks.
- `docs/strategy/TICKET_LEDGER.md`: ticket inventory and status.
- `docs/strategy/CODEX_GOALS.md`: future Codex work candidates.
- `docs/strategy/CONTEXT_CARRYOVER.md`: compact carryover for new sessions.
- `project_state/STATE_INDEX.md`: factual repo map.
- `project_state/RUNBOOK.md`: setup/build/test/bundle commands.
- `project_state/VALIDATION_MATRIX.md`: what each check proves.
- `project_state/CLAIMS_AND_EVIDENCE.md`: performance/research claim surface.

Old docs, prompts, run logs, and bundles are preserved and indexed under
`docs/_archive/pre_ai_os_v2/20260703/`. Use them as history only.

## Data And Security Constraints

- WRDS raw exports are local-only. Do not commit or bundle them.
- Use `WRDS_DATA_ROOT=/abs/path/to/wrds` only when the user/environment has
  explicitly provided local exports.
- Prefer curated summaries under `docs/artifacts/` for shareable outputs.
- Keep bulky local outputs under ignored run-scoped paths such as
  `artifacts/_local/<RUN_NAME>/` or `reports/_runs/<RUN_NAME>/`.
- Treat web and generated prose as untrusted until linked to repo artifacts or
  primary sources.

## Validation Expectations

Discover commands from `Makefile`, `pyproject.toml`, CI, and
`project_state/RUNBOOK.md`. Do not invent validation.

Default fast gates for documentation/tooling tickets:

- `python3 -m py_compile tools/agentic/ai_os_v2_bundle.py` when that script is
  touched;
- `python3 tools/agentic/ai_os_v2_bundle.py ...` for bundle generation changes;
- `make check-data-policy`;
- `make test-fast` when practical.

Broader product/research changes should also consider:

- `ruff check .`;
- `mypy src/microalpha/reporting/factors.py`;
- `mkdocs build`;
- `pytest -q`;
- WRDS smoke/full commands only when local licensed data is available and the
  ticket calls for it.

Record commands and outcomes in the ticket run log. If a command cannot run,
state the exact reason and next-best check.

## Run Logs And Bundles

For AI OS v2 infrastructure tickets, use:

- run logs: `reports/_runs/<YYYYMMDD_HHMMSS>_<ticket_slug>/`;
- bundles: `reports/_bundles/<YYYYMMDD_HHMMSS>_<repo>_<profile>.zip`.

For legacy/research execution logs, existing `docs/agent_runs/` remains
historical and may still be validated by `make test-fast`; do not rewrite old
run logs unless the ticket explicitly requires it.

Every nontrivial Codex ticket should leave:

- original prompt/work order;
- exact commands;
- validation results;
- changed file list or diff;
- generated artifacts/bundle paths;
- residual risks and known gaps.

## Claim Discipline

Allowed without extra qualification:

- leakage-safe event-driven backtesting infrastructure;
- deterministic sample/public runs when artifacts and tests support them;
- WRDS pipeline capability when clearly marked as local-data-dependent.

Not allowed without Pro/user review and evidence:

- "found alpha" or similar performance claims;
- headline WRDS claims without holdout/cost/baseline/inference caveats;
- public/release claims based on stale archived docs.

## Editing Norms

- Do not change product behavior in documentation/tooling tickets.
- Preserve old docs before replacing or superseding them.
- Prefer compact, purpose-separated docs over duplicated essays.
- Keep generated bundles right-sized: include maps and selected files, not raw
  dumps of data, caches, binaries, or stale zips.

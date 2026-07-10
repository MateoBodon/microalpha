# microalpha Project

last_updated: 2026-07-03
updated_by: Codex T-000
source_event: AI Project OS v2 installation

## What This Repo Is

microalpha is a Python quant/research repository for leakage-safe, event-driven
backtesting and walk-forward validation. It combines:

- an event-driven backtest engine;
- strategy/config plumbing for sample, public, and WRDS/CRSP workflows;
- reporting utilities for metrics, plots, factor analytics, SPA/reality checks,
  and resume-safe result summaries;
- tests and data-policy checks intended to protect chronology, reproducibility,
  and licensed-data boundaries.

The project is best understood as a research infrastructure and evidence system,
not as a live trading system.

## What This Repo Is Not

- It is not a broker or live-execution platform.
- It does not guarantee alpha discovery.
- It should not make external-facing performance claims unless the claim is
  linked to an artifact, command, config, dataset id, and validation evidence.
- It should not expose raw WRDS/CRSP exports or other restricted data.

## Audience

- Human owner/reviewer deciding strategy and claim boundaries.
- GPT 5.5 Pro Extended for strategic resets and long-horizon planning.
- GPT 5.5 Thinking Heavy / Extra High for sprint selection and review.
- Codex for implementation, validation, documentation, and bundle generation.

## Current State

- Sample and public-data workflows are present and testable without WRDS.
- WRDS workflows exist but require local licensed exports via `WRDS_DATA_ROOT`.
- The current result/evidence surface is summarized in
  `project_state/CURRENT_RESULTS.md` and `project_state/CLAIMS_AND_EVIDENCE.md`.
- Historical run logs, prompts, GPT outputs, and older project-state docs were
  indexed under `docs/_archive/pre_ai_os_v2/20260703/`.
- AI Project OS v2 canonical strategy docs now live under `docs/strategy/`.

## High-Level Layout

| Path | Purpose |
|---|---|
| `src/microalpha/` | package code: engine, data, execution, portfolio, risk, strategies, reporting |
| `configs/` | reproducible YAML configs for sample, public, WRDS, and sweep workflows |
| `tests/` | validation suite for chronology, reporting, configs, data policy, bundles, and CLI behavior |
| `docs/` | MkDocs content, historical run logs/prompts, curated resume artifacts, strategy docs |
| `docs/strategy/` | AI Project OS v2 canonical goals, plan, risks, decisions, tickets, carryover |
| `project_state/` | factual repo state, runbook, validation matrix, claims/evidence |
| `reports/` | report scripts, summaries, run-scoped outputs, and bundle output zone |
| `artifacts/` | committed sample artifacts and ignored local/generated run artifacts |
| `data/`, `data_sp500/` | bundled sample/public data and larger local data panels |
| `tools/agentic/` | deterministic helper scripts for run logs, state refresh, and bundles |

## Success Definition

Near-term success is a Pro-reviewed strategy package that separates validated
repo facts from historical context and selects the next high-leverage work
frontier. Longer-term success is a defensible, reproducible research engine
where every performance/result claim is artifact-backed, costs/baselines are
present, and leakage/survivorship risks are actively guarded.

## Non-Negotiable Constraints

- No raw WRDS exports in bundles or git.
- No lookahead, leakage, or same-tick unsafe claims in headline results.
- No performance claims without evidence links and caveats.
- No stale archived doc should be treated as current truth.
- Product behavior should not change during documentation/tooling tickets unless
  explicitly required and validated.

## Canonical Current Docs

- Agent rules: `AGENTS.md`
- Strategy memory: `docs/strategy/`
- Current state map: `project_state/STATE_INDEX.md`
- Commands: `project_state/RUNBOOK.md`
- Validation meaning: `project_state/VALIDATION_MATRIX.md`
- Claims/evidence: `project_state/CLAIMS_AND_EVIDENCE.md`
- Chronological log: `PROGRESS.md`

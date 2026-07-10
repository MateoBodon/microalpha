# State Index

last_updated: 2026-07-03
updated_by: Codex T-001
source_event: Pro strategy install and evidence inventory

## Purpose

This is the canonical factual map for the current repo state. Older
`project_state/*` files remain useful historical/reference material, and their
pre-v2 versions are copied or indexed in
`docs/_archive/pre_ai_os_v2/20260703/`.

## Repo Identity

- Name: microalpha
- Type: Python quant/research backtesting engine
- Package root: `src/microalpha/`
- CLI entrypoint: `microalpha = microalpha.cli:main`
- Build/test config: `pyproject.toml`, `pytest.ini`, `Makefile`,
  `.github/workflows/ci.yml`
- Docs site: MkDocs via `mkdocs.yml` and `docs/`

## Major Subsystems

| Area | Paths | Notes |
|---|---|---|
| Engine/data/execution | `src/microalpha/data.py`, `engine.py`, `broker.py`, `execution.py`, `portfolio.py` | Event-driven backtesting, fills, risk/portfolio flow. |
| Strategies | `src/microalpha/strategies/` | Sample, momentum, mean-reversion, market-making, WRDS flagship variants. |
| Walk-forward | `src/microalpha/walkforward.py`, `configs/wfv_*.yaml` | Parameter selection, fold metrics, holdout/public/WRDS configs. |
| Reporting | `src/microalpha/reporting/`, `reports/*.py` | Markdown summaries, plots, SPA, factors, tearsheets, WRDS rendering. |
| Validation | `tests/`, `scripts/check_data_policy.py`, `scripts/validate_run_logs.py` | Chronology, artifacts, CLI, data policy, run-log guardrails. |
| Docs/state | `PROJECT.md`, `AGENTS.md`, `docs/strategy/`, `project_state/` | Current AI OS v2 memory and factual state. |
| Historical logs | `docs/agent_runs/`, `docs/prompts/`, `docs/gpt_outputs/` | Preserved old execution context. |

## Important Artifacts And Results

- Sample flagship: `artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7/`
- Sample WFV: `artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7/`
- Public mini-panel resume artifacts:
  `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/`
- WRDS resume artifacts:
  `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/`
- WRDS leaderboard:
  `docs/artifacts/resume/wrds/leaderboard/`
- Existing result summary:
  `project_state/CURRENT_RESULTS.md`
- Current T-001 evidence audit:
  `project_state/CURRENT_EVIDENCE_SUMMARY.md`
- Current T-001 post-transfer data/artifact inventory:
  `project_state/DATA_ARTIFACT_INVENTORY.md`

## Current Documentation Authority

- Current project identity: `PROJECT.md`
- Current agent rules: `AGENTS.md`
- Current strategy memory: `docs/strategy/`
- Current command map: `project_state/RUNBOOK.md`
- Current validation map: `project_state/VALIDATION_MATRIX.md`
- Current claim map: `project_state/CLAIMS_AND_EVIDENCE.md`
- Current evidence summary: `project_state/CURRENT_EVIDENCE_SUMMARY.md`
- Data/artifact inventory: `project_state/DATA_ARTIFACT_INVENTORY.md`
- Pre-v2 archive: `docs/_archive/pre_ai_os_v2/20260703/`

## Known Gaps

- Pro's WRDS Prestige Evidence Phase strategy is installed under
  `docs/strategy/`.
- Some old docs remain in place for link/history safety; they now point to
  canonical v2 docs where practical.
- WRDS evidence depends on local licensed exports and cannot be fully reproduced
  without the correct data root.
- The current WRDS best curated manifest excerpt has a config-hash mismatch
  against the tracked config and ticket run-log metadata; see
  `project_state/CURRENT_EVIDENCE_SUMMARY.md`.

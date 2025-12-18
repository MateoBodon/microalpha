# ExecPlan — Cost sensitivity + metadata coverage reporting (2025-12-18)

## Verified current state (from repo/docs)

- `microalpha report --artifact-dir <dir>` already reads `metrics.json` / `bootstrap.json` / `equity_curve.csv` and produces PNG + Markdown summaries. (`project_state/PIPELINE_FLOW.md`)
- Cost drivers exist in configs and engine plumbing:
  - slippage models with defaults (`default_adv`, `default_spread_bps`, spread floor) + queue heuristics. (`project_state/CONFIG_REFERENCE.md`, `project_state/RESEARCH_NOTES.md`)
  - borrow costs from `borrow_fee_annual_bps`. (`project_state/DATAFLOW.md`, `project_state/RESEARCH_NOTES.md`)
- Known credibility risk: **metadata gaps cause fallback defaults → understated costs**. (`project_state/KNOWN_ISSUES.md`)
- Deterministic sample artifacts exist and are explicitly “fixtures” (not alpha claims). (`project_state/CURRENT_RESULTS.md`)

## Objective (this 1–3 day sprint)

Add **default** reporting outputs that make cost realism auditable:

1) **Cost sensitivity table** (ex-post; does *not* re-simulate fills)  
2) **Metadata coverage report** (ADV/spread/borrow fee availability + fallback rate)

…and surface both in:
- artifact directory as JSON (machine-readable),
- Markdown summary (human-readable),
- and `project_state/PIPELINE_FLOW.md` / docs as part of the “artifact contract”.

## Scope boundaries (explicit non-goals)

- No new alpha model, no new strategy logic.
- No WRDS rerun required for acceptance (but the feature must work on WRDS artifacts when you have them).
- No attempt to “calibrate” the queue model or impact parameters in this sprint.
- Sensitivity is **post-trade accounting** only (clearly labeled): it scales already-recorded cost components rather than re-running the simulator.

## Deliverables (what must land)

### D1 — New artifact-backed metrics (per run)
Create (or extend) run artifacts under `<ARTIFACT_DIR>/`:

- `cost_sensitivity.json`
  - Contains a grid over cost multipliers (at minimum: `(0.5, 1.0, 2.0)`) and, for each multiplier:
    - annualized net Sharpe (use same return series frequency as existing reporting)
    - MaxDD, CAGR, MAR (if available in existing metrics stack)
    - cost drag (bps/year) relative to baseline (multiplier 1.0)
  - Must be explicit that it is **ex-post sensitivity** (no re-simulation).

- `metadata_coverage.json`
  - Coverage for inputs used by cost models:
    - `% of traded notional` (or `% of fills`) with **non-default** ADV
    - `% with non-default spread_bps`
    - `% with borrow_fee_annual_bps present** for short positions** (if observable)
    - counts of “fallback used” by symbol bucket (top offenders)

> If trade logs don’t currently expose enough information, update the trade log schema minimally (and backwards-compatibly) to support this reporting.

### D2 — Summary integration
- `microalpha report` Markdown output must include a new section:
  - “Cost & Metadata Robustness”
  - A small table of multipliers vs Sharpe/MaxDD/cost drag
  - A small table of coverage stats

### D3 — Tests + docs updates
- Add unit/integration tests proving the new artifacts are produced and parseable.
- Update `project_state/PIPELINE_FLOW.md` artifact list to include the new files (so the “artifact contract” stays accurate).

## Commands to run (repro + validation)

### Setup
    python -m venv .venv && source .venv/bin/activate
    pip install -e '.[dev]'

### Quality gates (must be green)
    ruff check
    pytest -q
    mkdocs build

### Generate updated summaries + new artifacts on existing fixture runs
Run reporting on the committed sample run-ids (do **not** regenerate new run-ids):

    microalpha report --artifact-dir artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7
    microalpha report --artifact-dir artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7

(If paths differ in your checkout, use the ones referenced in `project_state/CURRENT_RESULTS.md`.)

## Acceptance criteria (objective, checkable)

- [x] `ruff check` passes.
- [x] `pytest -q` passes (including any schema/report tests touched).
- [x] `mkdocs build` passes (docs links and embedded plots still resolve).
- [x] After running the two `microalpha report` commands above:
  - [x] `cost_sensitivity.json` exists in each artifact directory and validates against the expected schema.
  - [x] `metadata_coverage.json` exists in each artifact directory and validates against the expected schema.
  - [x] The generated Markdown summary includes the “Cost & Metadata Robustness” section and tables.
- [x] No licensed WRDS raw data was added to git (artifacts may include derived plots/JSON only).

## Logging + commits (agent hygiene)

- Maintain a short execution log in `.agent/LOGBOOK.md` (append today’s entry: what changed + commands run).
- Update this ExecPlan in-place:
  - mark completed checkboxes,
  - note any deviations (e.g., trade log schema differences).
- Commit in small chunks:
  - (1) reporting feature + schema,
  - (2) tests,
  - (3) regenerated summaries / updated docs.

## Artifact-backed metric produced by this ExecPlan

- **New:** “Worst-case net Sharpe under 2× cost scaling” (target metric; values depend on the run)  
  Evidence: `<ARTIFACT_DIR>/cost_sensitivity.json` + Markdown table in the summary.

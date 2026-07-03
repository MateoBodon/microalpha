# TICKET-28: Pin WRDS dataset_id + refresh real-data resume metrics

## Goal

Refresh the flagship WRDS (real-data) walk-forward results and produce a resume-ready metrics snippet that is fully reproducible and pinned to a canonical WRDS export `dataset_id`.

## Context

* The repo already has a recent WRDS flagship snapshot recorded in `project_state/CURRENT_RESULTS.md` (latest run `2026-01-26T01-22-23Z-e76eb4d`) with headline metrics (Sharpe_HAC 0.27, MaxDD 3.41%, RealityCheck p 0.988, SPA p 0.015) and a linked report path `reports/summaries/wrds_flagship.md`.
* `project_state/OPEN_QUESTIONS.md` explicitly calls out the missing decision: “Which WRDS export schema/version is canonical (and should be written into META.json + configs)?”
* `project_state/BACKLOG.md` prioritizes: (1) keeping WRDS holdout fresh and (2) pinning a canonical WRDS schema/version in `docs/wrds.md` and referencing it in configs + `META.json`.
* Your resume line currently mentions performance metrics (e.g., Sharpe/MaxDD/CAGR + bootstrap p-value), but those numbers must be linked to a specific run_id + artifacts to be defensible. This ticket focuses on the **real-data** (WRDS) metrics refresh + provenance.

## Constraints

* **Tracking/logging constraints**

  * No surprise top-level directories (follow `TRACKING_POLICY.md`).
  * Bulky outputs must go to `artifacts/_local/<RUN_NAME>/...` or `reports/_runs/<RUN_NAME>/...` (ignored).
  * A run log **must** be created under `docs/agent_runs/<RUN_NAME>/` with the required files: `PROMPT.md`, `COMMANDS.md`, `RESULTS.md`, `TESTS.md`, `META.json`.
* **Repo-specific constraints**

  * Prefer the canonical config: `configs/wfv_flagship_wrds.yaml` (see `project_state/CONFIG_REFERENCE.md`).
  * Do **not** commit WRDS raw exports; only commit small curated summaries under `docs/artifacts/` and link to local run outputs from the run log.

## Plan

1. Create a short canonical WRDS export spec at `docs/wrds.md`:

   * Expected `WRDS_DATA_ROOT` layout (directories/files the pipeline requires).
   * A concrete `dataset_id` convention (e.g., `wrds_<vendor>_<asof_YYYYMMDD>_<schema_vN>`).
   * How to obtain/compute `dataset_id` from an export (e.g., require a `WRDS_EXPORT_VERSION.txt` at the root, or a simple file-list hash script).
2. Ensure `dataset_id` is written into run metadata:

   * Update the run logging path so `docs/agent_runs/<RUN_NAME>/META.json` includes `wrds.dataset_id` and `wrds.data_root` (and any other critical provenance fields).
   * Update the artifact manifest writer so `dataset_id` is recorded into the run’s manifest (search for the manifest write path with `rg -n "manifest.json" src/microalpha` and implement where appropriate).
3. Run a fresh WRDS flagship WFV + report **in non-sample mode**:

   * Initialize a run log via `python3 tools/agentic/runlog_init.py --ticket ticket-28 --summary "..."`
   * Execute `configs/wfv_flagship_wrds.yaml` with the required env vars (at least `WRDS_DATA_ROOT=...` and the chosen `WRDS_DATASET_ID=...` if applicable).
   * Force bulky outputs to a run-scoped ignored directory (override `artifacts_dir` if necessary so outputs land in `artifacts/_local/<RUN_NAME>/...` and/or `reports/_runs/<RUN_NAME>/...`).
4. Promote a small, resume-ready summary into tracked docs:

   * Write a compact metrics JSON + snippet under `docs/artifacts/resume/wrds/<RUN_ID>/` (or `<RUN_NAME>/`) including: Sharpe_HAC, MaxDD, MAR/Calmar, turnover, RealityCheck p, SPA p, and the pinned `dataset_id`.
   * Update `project_state/CURRENT_RESULTS.md` (and `docs/results_wrds*.md` if those are the repo’s canonical narrative pages) to reference the new run_id + summary path.

## Acceptance criteria

* [ ] `docs/wrds.md` exists and clearly defines (a) required WRDS export layout and (b) a canonical `dataset_id` convention.
* [ ] The WRDS flagship run log exists at `docs/agent_runs/<RUN_NAME>/` and includes the required run-log contract files from `TRACKING_POLICY.md`.
* [ ] `docs/agent_runs/<RUN_NAME>/META.json` includes `wrds.dataset_id` and the provenance needed to reproduce (at minimum: `WRDS_DATA_ROOT`, config path, git SHA, and key env flags).
* [ ] The WRDS run’s artifact manifest records the `dataset_id` (location depends on code, but it must be present in the run’s `manifest.json` or equivalent canonical manifest file).
* [ ] Bulky run outputs are stored only under `artifacts/_local/<RUN_NAME>/...` and/or `reports/_runs/<RUN_NAME>/...` (no large raw outputs added to tracked paths).
* [ ] A tracked, resume-ready summary exists at `docs/artifacts/resume/wrds/<RUN_ID>/` containing:

  * [ ] `metrics.json` (machine-readable)
  * [ ] `snippet.md` (copy/paste resume line)
  * [ ] Clear inclusion of `dataset_id` + run_id + config name
* [ ] `project_state/CURRENT_RESULTS.md` is updated to point at the new WRDS run_id and the new resume summary path.

## Test plan

* [ ] `make test-fast`
* [ ] `make check-data-policy`
* [ ] `make validate-runlogs`
* [ ] Run WRDS smoke (if available): `WRDS_DATA_ROOT=... make test-wrds` (or the repo’s documented WRDS smoke command)
* [ ] Execute the WRDS flagship run using `configs/wfv_flagship_wrds.yaml` and confirm the report + summary generation completes.

## Artifacts / Outputs

* Run log (tracked):

  * `docs/agent_runs/<RUN_NAME>/PROMPT.md`
  * `docs/agent_runs/<RUN_NAME>/COMMANDS.md`
  * `docs/agent_runs/<RUN_NAME>/RESULTS.md`
  * `docs/agent_runs/<RUN_NAME>/TESTS.md`
  * `docs/agent_runs/<RUN_NAME>/META.json`
* Bulky outputs (ignored):

  * `artifacts/_local/<RUN_NAME>/...` and/or `reports/_runs/<RUN_NAME>/...`
* Curated resume summary (tracked):

  * `docs/artifacts/resume/wrds/<RUN_ID>/metrics.json`
  * `docs/artifacts/resume/wrds/<RUN_ID>/snippet.md`
* Updated snapshot pointer (tracked):

  * `project_state/CURRENT_RESULTS.md` (WRDS section)

## Notes / Risks

* **Risk: WRDS availability / schema drift.** If the local export doesn’t match expectations, the run may fail or produce incomparable metrics; mitigate by pinning `dataset_id` + documenting export shape in `docs/wrds.md`.
* **Risk: accidental tracking of bulky outputs.** Ensure outputs go to `artifacts/_local/` or `reports/_runs/` and validate with `git status` before committing.
* **Risk: manifest schema changes.** Adding `dataset_id` to manifests may require touching downstream readers; keep the change additive/backwards-compatible.
* **Rollback plan:** If manifest changes cause breakage, revert the manifest-schema commit and keep the refreshed run log + resume summary (which can still carry `dataset_id` in `META.json`), then reintroduce manifest support in a follow-up ticket.

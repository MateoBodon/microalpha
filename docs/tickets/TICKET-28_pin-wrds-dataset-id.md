# Ticket 28 — Pin WRDS dataset_id + refresh real-data resume metrics

## Goal
Refresh the flagship WRDS walk-forward results and produce a resume-ready metrics snippet pinned to a canonical WRDS dataset_id.

## Scope
- Document the WRDS export layout + dataset_id convention in `docs/wrds.md`.
- Record the canonical dataset_id in `configs/wfv_flagship_wrds.yaml` and run metadata.
- Ensure the WRDS run manifest includes dataset_id provenance.
- Run a fresh WRDS flagship WFV + report with outputs confined to ignored run-scoped paths.
- Publish a small resume metrics artifact under `docs/artifacts/resume/wrds/<RUN_ID>/`.
- Update `project_state/CURRENT_RESULTS.md` to the new run_id + resume artifact path.
- Do not commit WRDS raw exports or large run outputs.

## Acceptance Criteria
- `docs/wrds.md` documents required WRDS export layout + canonical dataset_id convention.
- WRDS run manifest includes dataset_id provenance.
- Run log `META.json` includes `wrds.dataset_id` and `wrds.data_root`.
- Resume metrics artifacts exist under `docs/artifacts/resume/wrds/<RUN_ID>/`.
- `project_state/CURRENT_RESULTS.md` points at the new WRDS run_id and resume summary.
- Bulky outputs reside only in `artifacts/_local/<RUN_NAME>/...` and/or `reports/_runs/<RUN_NAME>/...`.

## Plan
1. Initialize run log + prompt capture for ticket-28.
2. Implement WRDS dataset_id provenance in docs/configs/manifest.
3. Run WRDS flagship WFV + report with run-scoped output paths.
4. Generate resume metrics artifact and update living docs + run logs.

## Notes
- Use `WRDS_DATASET_ID=wrds_crsp_export_20251221_v1` for the canonical export.
- Record exact commands and environment settings in the run log.

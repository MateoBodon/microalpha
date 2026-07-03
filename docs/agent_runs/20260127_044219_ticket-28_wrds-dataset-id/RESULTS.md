# Results

## Summary
- Pinned WRDS dataset_id metadata (`wrds_crsp_export_20251221_v1`) in `docs/wrds.md`, `configs/wfv_flagship_wrds.yaml`, and manifest/run logs (new `wrds` provenance payload).
- Ran WRDS flagship WFV + report into run-scoped outputs (`artifacts/_local/...`, `reports/_runs/...`) and generated a resume-ready metrics artifact under `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/`.
- Updated WRDS results docs (`docs/results_wrds.md`, `docs/results_wrds_resume.md`) and `project_state/CURRENT_RESULTS.md` to the new run_id and resume artifact path.

## Key outputs
- WFV artifacts: `artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/`
- WRDS report (run-scoped): `reports/_runs/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship.md`
- Resume artifact: `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/`
- Manifest provenance excerpt: `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/manifest_excerpt.json`
- Run log: `docs/agent_runs/20260127_044219_ticket-28_wrds-dataset-id/`

## Notes
- WRDS dataset_id is now emitted into `manifest.json` under `wrds.*` and recorded in run-log `META.json`.
- `reports/tearsheet.py` emitted a matplotlib `tight_layout` warning; outputs still generated.

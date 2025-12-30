Summary:
- Added explicit factor/return alignment with frequency inference, strict mismatch errors, and optional compounded resampling (no forward-fill), returning meta (freqs, overlap, n_obs).
- Reports and factors CLI now surface frequency + n_obs; factor summary explicitly resamples returns when using weekly sample factors.
- Added alignment tests (shifted dates, frequency mismatch with/without resample, forward-fill guard).
- Updated docs to reflect weekly sample factors and explicit resampling behavior.
- Updated `docs/CODEX_SPRINT_TICKETS.md` ticket-05 status to DONE with run log link.
- Generated updated sample WFV summary with frequency metadata in the factor section.

Code/doc changes:
- `src/microalpha/reporting/factors.py` (alignment + meta + resample flags)
- `src/microalpha/reporting/summary.py` (frequency/n_obs surfaced in factor section)
- `reports/factors_ff.py` (resample flags + meta line)
- `tests/test_factor_alignment.py`, `tests/test_factor_regression.py`
- `docs/PLAN_OF_RECORD.md`, `docs/factors.md`, `README.md`, `CHANGELOG.md`, `PROGRESS.md`, `project_state/KNOWN_ISSUES.md`, `project_state/FUNCTION_INDEX.md`

Report:
- Summary: `reports/summaries/flagship_mom_wfv.md`
- Source artifacts: `artifacts/sample_wfv/2025-12-23T18-39-59Z-82c14dc/`

Bundle:
- `docs/gpt_bundles/2025-12-30T08-58-30Z_ticket-03_20251230_082853_ticket-03_factor-regression-alignment.zip`
- Post-merge bundle: `docs/gpt_bundles/2025-12-30T09-07-28Z_ticket-03_20251230_082853_ticket-03_factor-regression-alignment.zip`
- Final bundle: `docs/gpt_bundles/2025-12-30T09-10-32Z_ticket-03_20251230_082853_ticket-03_factor-regression-alignment.zip`

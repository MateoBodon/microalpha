# Results

## Summary
- Added explicit unsafe execution guardrails with `allow_unsafe_execution` opt-in, manifest fields (`unsafe_execution`, `unsafe_reasons`, `execution_alignment`), and report banners for unsafe runs.
- Enforced signal timestamp invariants in the engine (future-dated signals now raise LookaheadError).
- Added red-team tests for future-dated signals and unsafe execution opt-in/manifest labeling.
- Bundle verification required `git_sha_after` to resolve to a commit containing META.json; updated META.json to use the branch ref (resolved SHA recorded in META.json notes) so gpt-bundle could pass.

## Code changes
- `src/microalpha/config.py`: added `allow_unsafe_execution`.
- `src/microalpha/execution_safety.py`: new helper to detect unsafe execution and alignment metadata.
- `src/microalpha/runner.py`: unsafe execution opt-in enforcement + manifest fields.
- `src/microalpha/walkforward.py`: unsafe execution opt-in enforcement + manifest fields (including holdout manifest).
- `src/microalpha/engine.py`: reject signals with timestamps later than the current market event.
- `src/microalpha/manifest.py`: new manifest fields + alignment recorded; `lob_tplus1` added to cost model.
- `src/microalpha/reporting/summary.py` and `src/microalpha/reporting/wrds_summary.py`: unsafe banner injected when `unsafe_execution` is true.
- `configs/mm_lob_same_tick.yaml`: added `allow_unsafe_execution: true`.
- `tests/test_no_lookahead.py`: added engine guard + unsafe execution opt-in/manifest tests.

## Artifacts & reports
- Sample run: `artifacts/sample_flagship/2025-12-23T21-59-20Z-ba5b480/`
- Sample report: `reports/summaries/flagship_mom.md`
- Unsafe LOB run: `artifacts/mm_lob_same_tick/2025-12-23T22-00-05Z-ba5b480/`
- Unsafe report (ignored path): `reports/summaries/_artifacts/mm_lob_same_tick.md`

## WRDS smoke status
- WRDS smoke runs skipped: `WRDS_DATA_ROOT` not set in this environment.

## Bundle
- Bundle: `docs/gpt_bundles/2025-12-23T22-22-01Z_ticket-04_20251223_214840_ticket-04_leakage-tests-unsafe-manifest.zip`

- Added manifest loading helpers in `src/microalpha/manifest.py` for safe manifest reads.
- Implemented `scripts/build_runs_index.py` + `make runs-index` to build `reports/summaries/runs_index.csv` deterministically.
- Added tests in `tests/test_runs_index.py` for deterministic ordering and invalid JSON handling.
- Documented run registry + no cherry-pick policy in `docs/RUN_REGISTRY.md`; updated `PROGRESS.md` and `CHANGELOG.md`.
- Generated `reports/summaries/runs_index.csv` from existing artifacts.

Artifacts/outputs:
- `reports/summaries/runs_index.csv`
- Bundle: `docs/gpt_bundles/2025-12-29T18-01-53Z_ticket-05_20251229_173759_ticket-05_runs-index-registry.zip`

Limitations:
- Headline metrics are only populated when `holdout_metrics_path` exists and is valid JSON; otherwise metrics stay blank.
- Optional metrics JSON parse errors are warned and skipped (manifests remain strict).

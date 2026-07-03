# Results

## Summary
- Reproduced the canonical public mini-panel WFV pipeline via `configs/wfv_flagship_public.yaml` and produced run `2026-02-17T01-02-27Z-98beced`.
- Promoted audit-linked, resume-safe public artifacts under `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/` and refreshed canonical line `docs/artifacts/resume/public/resume_line_best.md`.
- Updated project pointers to surface the public mini-panel claim in `project_state/CURRENT_RESULTS.md`.
- The reproduced run is degenerate (`num_trades=0`), so metrics are all zero and differ materially from the previously stated resume line (`Sharpe 0.46 / MaxDD 7.9% / CAGR 6.7% / p=0.23`).

## Key outputs
- Local-only run artifacts:
  - `artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public/2026-02-17T01-02-27Z-98beced/`
- Local-only report:
  - `reports/_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public.md`
- Tracked resume-safe artifacts:
  - `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/metrics.json`
  - `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/manifest_excerpt.json`
  - `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/snippet.md`
  - `docs/artifacts/resume/public/resume_line_best.md`

## Notes
- Initial canonical run failed because `data/public/universe_public.csv` lacked required `date` column; file was updated to required schema using existing public data files only.
- Dataset/version provenance for this public run is captured as `dataset_id=public_mini_panel_repo_36b421820251` (derived from deterministic SHA256 over `data/public/meta_public.csv`, `data/public/universe_public.csv`, and `data/public/prices/*.csv`).
- The generated report explicitly flags the run as degenerate and not interpretable for performance claims.
- Validation gates are green: `python3 tools/agentic/validate_runlog.py --run-name 20260217_010106_ticket-37_public-mini-panel-resume-metrics`, `make check-data-policy`, and `make test-fast`.

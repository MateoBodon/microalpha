# Results

## Summary
- Verified WRDS data availability and reran the WRDS smoke WFV + report pipeline.
- Updated WRDS smoke artifacts, reports, and docs outputs with the new run id.

## WRDS smoke run
- Run id: `2025-12-24T05-15-43Z-559a99e`
- Artifacts: `artifacts/wrds_flagship_smoke/2025-12-24T05-15-43Z-559a99e/`
- Reports:
  - `reports/summaries/wrds_flagship_smoke.md`
  - `reports/summaries/wrds_flagship_smoke_metrics.json`
  - `reports/summaries/wrds_flagship_smoke_spa.json`
  - `reports/summaries/wrds_flagship_smoke_spa.md`
  - `reports/summaries/wrds_flagship_smoke_factors.md`
- Docs:
  - `docs/results_wrds_smoke.md`
  - `docs/img/wrds_flagship_smoke/2025-12-24T05-15-43Z-559a99e/`

## Warnings
- pandas FutureWarning from `reporting/analytics.py` about `Series.fillna(method=...)` deprecation.
- Matplotlib tight_layout warning from `reporting/tearsheet.py`.

## Bundle
- Bundle: `docs/gpt_bundles/2025-12-24T05-19-48Z_ticket-04_20251224_051508_ticket-04_wrds-smoke-check.zip`

## Report-only repro (pre-fix)

Command:
`microalpha report --artifact-dir artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e`

Output:
```
/Users/mateobodon/Documents/Programming/Projects/microalpha/src/microalpha/reporting/tearsheet.py:174: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig_equity.tight_layout()
{
  "artifact_dir": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e",
  "summary_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/reports/summaries/flagship_mom.md",
  "equity_curve_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/equity_curve.png",
  "bootstrap_hist_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/bootstrap_hist.png",
  "cost_sensitivity_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/cost_sensitivity.json",
  "metadata_coverage_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/metadata_coverage.json",
  "runtime_sec": 0.641,
  "version": "0.1.0"
}
```

Command:
`microalpha report --artifact-dir artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7`

Output:
```
/Users/mateobodon/Documents/Programming/Projects/microalpha/src/microalpha/reporting/tearsheet.py:174: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig_equity.tight_layout()
{
  "artifact_dir": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7",
  "summary_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/reports/summaries/flagship_mom.md",
  "equity_curve_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/equity_curve.png",
  "bootstrap_hist_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/bootstrap_hist.png",
  "cost_sensitivity_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/cost_sensitivity.json",
  "metadata_coverage_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/metadata_coverage.json",
  "runtime_sec": 0.513,
  "version": "0.1.0"
}
```

## Tests

Command:
`pytest -q`

Output:
```
102 passed, 1 skipped, 2 warnings in 19.04s
```

Warnings:
- DeprecationWarning: ExecModelCfg.aln is deprecated; use 'commission' instead.
- FutureWarning: Series.fillna with 'method' is deprecated and will raise in a future version. Use obj.ffill() or obj.bfill() instead.

## Report verification (post-fix)

Command:
`microalpha report --artifact-dir artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e`

Output:
```
/Users/mateobodon/Documents/Programming/Projects/microalpha/src/microalpha/reporting/tearsheet.py:174: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig_equity.tight_layout()
{
  "artifact_dir": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e",
  "summary_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/reports/summaries/flagship_mom.md",
  "equity_curve_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/equity_curve.png",
  "bootstrap_hist_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/bootstrap_hist.png",
  "cost_sensitivity_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/cost_sensitivity.json",
  "metadata_coverage_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/metadata_coverage.json",
  "runtime_sec": 0.538,
  "version": "0.1.0"
}
```

Command:
`microalpha report --artifact-dir artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7`

Output:
```
/Users/mateobodon/Documents/Programming/Projects/microalpha/src/microalpha/reporting/tearsheet.py:174: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig_equity.tight_layout()
{
  "artifact_dir": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7",
  "summary_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/reports/summaries/flagship_mom.md",
  "equity_curve_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/equity_curve.png",
  "bootstrap_hist_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/bootstrap_hist.png",
  "cost_sensitivity_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/cost_sensitivity.json",
  "metadata_coverage_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/metadata_coverage.json",
  "runtime_sec": 0.502,
  "version": "0.1.0"
}
```

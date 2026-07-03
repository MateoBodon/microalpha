WRDS/CRSP flagship momentum (window=holdout-only, 2018-01-02 to 2019-12-31): Sharpe_HAC 0.588, CAGR 0.88%, MaxDD 1.38%, MAR 0.64, turnover $6.12MM (31 trades), RealityCheck p=0.941, SPA p=n/a. run_id=2026-02-16T22-33-46Z-8d90621; dataset_id=wrds_crsp_export_20251221_v1.

Window label: holdout-only
Holdout window: 2018-01-02 to 2019-12-31
Selection rule: primary=max holdout Sharpe_HAC; guardrails=dataset_id present, trades>=20, maxdd<=15%; tie-breakers=lower MaxDD then higher MAR.

Source files:
- manifest: `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/manifest.json`
- holdout_manifest: `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/holdout_manifest.json`
- holdout_metrics: `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/holdout_metrics.json`
- spa: `missing`
- reality_check: `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/reality_check.json`
- leaderboard_row: `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621`

# Current Evidence Summary

last_updated: 2026-07-03
updated_by: Codex T-001
source_event: Pro strategy install and evidence inventory

## Scope

This summary records what is directly present in the current checkout. It does
not infer metrics from memory or from Pro's strategy package.

## Public Mini-Panel

Status: safe as pipeline/demo evidence only; unsafe as performance evidence.

- Current resume line: `docs/artifacts/resume/public/resume_line_best.md`
- Current curated artifact directory:
  `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/`
- Run ID: `2026-02-17T01-02-27Z-98beced`
- Window: WFV OOS, `2024-01-02` to `2024-01-12`
- Config path: `configs/wfv_flagship_public.yaml`
- Config hash from current file:
  `e5ccee187a582855650b9d088919d3a2cc6302fb85bcc54429960ee4e476de4f`
- Config hash recorded in public manifest excerpt:
  `d6cfdda3e570c1e96cd31d6d165b915370cb1fd711768ebe8a4f317a4afb0b11`
- Dataset ID: `public_mini_panel_repo_36b421820251`
- Dataset manifest/source: derived from
  `data/public/meta_public.csv`, `data/public/universe_public.csv`, and
  `data/public/prices/*.csv`; hashes are recorded in
  `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/manifest_excerpt.json`
- Headline metrics from curated artifact: Sharpe_HAC `0.000`, MaxDD `0.00%`,
  CAGR `0.00%`, RealityCheck p-value `1.000`
- Degeneracy/trades: degenerate, `0` trades, `0` traded days
- Costs/slippage/borrow: not meaningful for performance because the run has no
  trades
- Baseline comparison: missing for the current curated public mini-panel artifact
- Source local artifact paths referenced by the curated artifact are missing in
  this checkout:
  - `artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public/2026-02-17T01-02-27Z-98beced/manifest.json`
  - `artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public/2026-02-17T01-02-27Z-98beced/metrics.json`
  - `artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public/2026-02-17T01-02-27Z-98beced/reality_check.json`
  - `artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public/2026-02-17T01-02-27Z-98beced/bootstrap.json`
  - `reports/_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public.md`

## WRDS Current Best Curated Evidence

Status: artifact-backed by small curated files, local-data-dependent,
claim-sensitive pending L3/L4 validation.

- Current resume line:
  `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`
- Current curated artifact directory:
  `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/`
- Leaderboard:
  `docs/artifacts/resume/wrds/leaderboard/leaderboard.md` and
  `docs/artifacts/resume/wrds/leaderboard/leaderboard.csv`
- Run ID: `2026-02-16T22-33-46Z-8d90621`
- Config path stated by curated artifacts: `configs/wfv_flagship_wrds_sweep35.yaml`
- Config hash from current tracked file:
  `5fb44d31684945aabad4132d4f7f5cd4eee9c83cfa61a8f8ecf55a0748755493`
- Config hash in ticket-35/ticket-36 run-log metadata:
  `5fb44d31684945aabad4132d4f7f5cd4eee9c83cfa61a8f8ecf55a0748755493`
- Config hash in promoted manifest excerpt:
  `caa000f5e885c0e7f566e435fb94a6632c19bb37282c5a36c0fe4b47a6cb7260`
- Config hash posture: claim-sensitive mismatch. The tracked config and run-log
  metadata agree, but the promoted manifest excerpt differs.
- Dataset ID: `wrds_crsp_export_20251221_v1`
- Dataset/export manifest path stated by curated artifact:
  `/srv/data/wrds/wrds/manifests/20251221_001618/manifest.json`
- Selection window: `2013-01-02` to `2017-12-29`
- Holdout window: `2018-01-02` to `2019-12-31`
- Overall WFV OOS metrics from `project_state/CURRENT_RESULTS.md` and
  `leaderboard.csv`: Sharpe_HAC `0.236204446852944`, CAGR
  `0.717998821436061%`, MaxDD `5.31559404741939%`, MAR
  `0.135074050996169`, turnover `$15.66MM`, trades `66`
- Holdout-only headline metrics from curated artifacts: Sharpe_HAC `0.588`,
  CAGR `0.88%`, MaxDD `1.38%`, MAR `0.64`, turnover `$6.12MM`, trades `31`,
  RealityCheck p-value `0.941`, SPA p-value `n/a`
- Non-degenerate trade evidence: safe to state as a curated artifact fact
  (`31` holdout trades); claim-sensitive as a performance claim until L3
  reproduction/source-artifact recovery
- Costs/slippage/borrow assumptions from `configs/wfv_flagship_wrds_sweep35.yaml`:
  commission `0.0005`, TWAP `6` slices, limit mode `ioc`, price impact `0.0`,
  linear/sqrt slippage parameters `k_lin=32.0`, `eta=105.0`,
  default ADV `$35,000,000`, default spread `8.0` bps, borrow annual fee
  `null`, borrow floor `8.0` bps, borrow multiplier `1.0`
- Baseline comparison: missing for current best run in the small curated
  artifacts. `reports/summaries/wrds_flagship.md` exists but describes older
  run `2026-01-26T01-22-23Z-e76eb4d`, not the current best
  `2026-02-16T22-33-46Z-8d90621`.
- Source local artifact paths referenced by the curated WRDS artifacts are
  missing in this checkout:
  - `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/manifest.json`
  - `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/holdout_manifest.json`
  - `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/metrics.json`
  - `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/holdout_metrics.json`
  - `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/reality_check.json`
  - `reports/_runs/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship.md`

## Claim Status Matrix

| Claim surface | Status | Reason |
|---|---|---|
| Public mini-panel ran end-to-end | safe | Curated public metrics and manifest excerpt are present. |
| Public mini-panel performance | blocked | Current curated run is degenerate with `0` trades. |
| Public mini-panel resume/public alpha wording | blocked | Degenerate demo evidence only. |
| WRDS current best holdout metrics as curated artifact facts | claim-sensitive | Small curated metrics and leaderboard are present, but local source artifacts are missing and config-hash evidence conflicts. |
| WRDS current best as externally claimable result | blocked | Needs L3 reproduction/source recovery and L4 claim audit. |
| WRDS pipeline reproducible in this checkout today | blocked | `WRDS_DATA_ROOT` is unset and historical root `/srv/data/wrds/wrds` is absent. |
| Current `reports/summaries/wrds_flagship.md` as current-best WRDS summary | stale | It references older run `2026-01-26T01-22-23Z-e76eb4d`. |
| Raw WRDS/CRSP data in repo or bundle | missing by design | No raw WRDS data should be committed or bundled. |

## Contradictions And Stops

- No material contradiction was found between Pro's strategy summary and the
  current public/WRDS headline metrics in the curated artifacts.
- Internal evidence drift was found: the current best WRDS promoted manifest
  excerpt config hash differs from both the tracked config hash and ticket run-log
  metadata. This does not require a public-claim rewrite in T-001, but it blocks
  exact config-hash claims until T-003 or source-artifact recovery resolves it.
- No evidence of leakage, survivorship bias, future-dated joins, or invalid
  holdout logic was found by this bounded artifact inspection. This was not a
  code/pathology audit and does not replace L3 validation.

- Fixed SPA grid-returns ordering to avoid KeyError, added explicit SPA error status + banner gating in WRDS summaries, and introduced a regression test for missing panel ids.
- Refreshed WRDS flagship SPA + summaries from `artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/` after the fix.
- Backfilled concrete `git_sha_after` values in prior run logs to restore audit hygiene.

Before/after (WRDS flagship SPA):
| Item | Before | After |
| --- | --- | --- |
| spa.json status | degenerate (`KeyError: ... not in index`) | ok |
| p_value | n/a | 0.031 |
| n_obs / n_strategies | 0 / 0 | 4129 / 24 |

Outputs:
- SPA artifact: `artifacts/wrds_flagship/2025-12-26T17-21-39Z-75ce3c8/spa.json`
- Summary SPA JSON: `reports/summaries/wrds_flagship_spa.json`
- Summary SPA markdown: `reports/summaries/wrds_flagship_spa.md`
- WRDS summary: `reports/summaries/wrds_flagship.md`
- Docs summary: `docs/results_wrds.md`

Bundle: `docs/gpt_bundles/2025-12-26T21-44-50Z_ticket-15_20251226_211219_ticket-15_fix-spa-keyerror.zip`

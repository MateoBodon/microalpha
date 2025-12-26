# Results

## Changes Implemented
- Added filter diagnostics in `FlagshipMomentumStrategy` and WFV tuning so each candidate records per-rebalance counts (universe → history → min_price → min_adv → sleeve selection) plus sector-cap rejections.
- WFV grid exclusions now capture filter diagnostics even when the candidate produces no trades/empty equity.
- Added regression test for diagnostics: `tests/test_flagship_filter_diagnostics.py`.

## Universe Inspection ($WRDS_DATA_ROOT)
- `universes/flagship_sector_neutral.csv` has **40 symbols**, **3325 rows**, date range **2013-01-31 → 2019-12-31**.
- Sector column is present but **all rows are `UNKNOWN`** (0 missing, 100% unknown).
- ADV/price coverage: `adv_20`, `adv_63`, `adv_126`, and `close` have **no missing values**; only **1 row** below `min_adv=50MM` and **27 rows** below `min_price=12`.
- All 40 universe symbols have matching files in `$WRDS_DATA_ROOT/crsp/daily_csv` (no missing/extra symbols).

## Single-Fold Debug WFV (No Parameter Changes)
- Config: `docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/wfv_flagship_wrds_single_fold.yaml`
- Command: `WRDS_DATA_ROOT=$WRDS_DATA_ROOT microalpha wfv --config docs/agent_runs/20251226_065226_ticket-13_fix-wrds-degeneracy/wfv_flagship_wrds_single_fold.yaml`
- Result: **Failure** — `Non-degenerate constraints rejected all candidates (min_trades=1; excluded=24).`
- Artifacts (written before failure): `artifacts/wrds_flagship_debug/2025-12-26T07-00-41Z-d4c8edf/`
- Filter diagnostics (from grid exclusions):
  - Universe size fixed at 40; `with_history` min 0 / max 40 / mean 23.38.
  - `min_price` + `min_adv` filters track `with_history` (mean 23.38).
  - Sleeve selection produces **long/short selected mean 4.67** (max 8), with **0 sector-cap rejections**.
- **Inference:** signals are being generated after the universe filters; zero trades likely occur in order sizing/risk-cap enforcement (e.g., `max_single_name_weight=0.02`) rather than in the universe/min_price/min_adv filters. Needs confirmation with order-level diagnostics.

External references consulted: none.

- Bundle: `docs/gpt_bundles/2025-12-26T07-12-26Z_ticket-13_20251226_065226_ticket-13_fix-wrds-degeneracy.zip`

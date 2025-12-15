# Current Results Snapshot

## Bundled Sample (deterministic)
- **Single flagship backtest** (`artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7/metrics.json`)  
  - Sharpe (HAC): **−0.66**, MAR: **−0.41**, Max DD: **17.3%**, Turnover: **$1.21M**, Reality‑check p ≈ **0.861**.  
  - Notes: Negative performance on toy data; used as schema/plot fixture for docs/tests.
- **Walk‑forward flagship** (`artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7/metrics.json`)  
  - Sharpe (HAC): **0.22**, MAR: **0.03**, Max DD: **34.8%**, Turnover: **$28.5M**, Reality‑check p ≈ **1.000**.  
  - Fold‑level metrics + grid returns available in same directory; docs embed equity/bootstrap plots.

## WRDS / CRSP
- **Documented run (pre‑tightening)** (`docs/results_wrds.md`, run `2025-11-21T00-28-22Z-54912a8`)  
  - Sharpe_HAC: **0.40**, MAR: **0.04**, Max DD: **82.35%**, Turnover: **$1.84B**, Reality‑check p: **0.986**, SPA p: **0.603**.  
  - Factor regression (FF5+MOM, HAC=5): Alpha 0.0008 (t=1.15), Mkt_RF 1.06 (t=6.52), MOM 0.44 (t=4.25), others modest/negative.  
  - Visuals stored under `docs/img/wrds_flagship/2025-11-21T00-28-22Z-54912a8/`.
- **Smoke rerun with tightened caps** (`docs/results_wrds.md`, run `2025-11-22T00-21-14Z-c792b44`)  
  - Reported Sharpe ≈ **0.06**, Max DD ≈ **40%** over 2015–2019; full 2005–2024 rerun still pending.
- **Latest artifacts checked in under `artifacts/wrds_flagship/` lack metrics.json/folds.json** (likely aborted mid‑run); treat results as stale until rerun completes.
- **WRDS single backtest smoke** (`artifacts/wrds_single_test/2025-11-12T00-52-17Z-65187e4/metrics.json`) shows zero trades/returns (no valid signals in that attempt).

## Other
- No committed results for CS momentum SP500 configs or MM demos; those are run ad‑hoc.
- Coverage badge indicates ~78% test coverage (CI badge in README).

## Gaps & Actions
- Full WRDS rerun with tightened risk spec (config updated 2025‑11‑21) needed to refresh headline metrics and docs assets.
- SPA/analytics outputs exist only for the 2025‑11‑21 run; new runs must regenerate signals, analytics plots, SPA, factors, and summaries.
- Public mini‑panel results are not committed; rerun `configs/wfv_flagship_public.yaml` if needed for comparisons.

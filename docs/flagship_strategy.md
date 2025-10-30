# Flagship Strategy Blueprint (Sample Edition)

The flagship package now ships with a reproducible cross-sectional momentum pipeline that demonstrates the full microstructure stack—configurable slippage, borrow accrual, limit-order queueing, covariance allocators, and bootstrap reporting.

## Dataset

- Location: `data/sample/`
- Files:
  - `prices_sample.csv`: panel of six synthetic equities (~3y of business days).
  - `prices/`: per-symbol CSVs consumed by `MultiCsvDataHandler`.
  - `meta_sample.csv`: ADV, borrow cost, and spread inputs for slippage/queue modelling.
  - `rf_sample.csv`: daily risk-free rate in basis points.
  - `universe_sample.csv`: monthly eligibility snapshot with sector and liquidity stats.

No external data vendors are required; runs are deterministic.

## Pipeline Overview

| Component | Implementation |
| --- | --- |
| Signals | 12-1 sector-neutral momentum (`FlagshipMomentumStrategy`) |
| Allocation | Budgeted risk parity with Ledoit–Wolf fallback (`microalpha.allocators`) |
| Execution | TWAP with IOC queue model, linear+sqrt impact with spread floor |
| Financing | Daily borrow accrual from `meta_sample.csv` |
| Risk Controls | Sector caps, exposure heat, ADV turnover clamp |
| Evaluation | HAC-adjusted Sharpe, Politis–White bootstrap (stationary blocks) |

## Reproduce the Single-Run Case Study

```bash
make dev          # optional helper -> pip install -e '.[dev]'
microalpha run --config configs/flagship_sample.yaml --out artifacts/sample_flagship
microalpha report --artifact-dir artifacts/sample_flagship
```

- Outputs `metrics.json`, `bootstrap.json`, `exposures.csv`, `trades.jsonl`, and `tearsheet.png`.
- `reports/summaries/flagship_mom.md` is refreshed automatically by the `report` step.

## Walk-Forward Reality Check

```bash
microalpha wfv --config configs/wfv_flagship_sample.yaml --out artifacts/sample_wfv
microalpha report --artifact-dir artifacts/sample_wfv --summary-out reports/summaries/flagship_mom_wfv.md --title \"Flagship Walk-Forward\"
```

- Sliding window: 252-day train / 63-day test.
- Grid: `{top_frac ∈ {0.3, 0.4}, skip_months ∈ {1, 2}}`.
- Stores per-fold metrics, queue-aware execution logs, and bootstrap Sharpe distributions.

## Key Metrics (generated)

Results will vary slightly with config tweaks; the shipped summary documents the canonical run and includes:

- Sharpe ratio with HAC standard errors.
- Calmar / Sortino / turnover.
- Bootstrap Sharpe histogram + p-value.
- Top absolute exposure table driven by final holdings.

## Extending Beyond the Sample

1. Swap `data_path` to a directory of per-symbol CSVs (format identical to `data/sample/prices/*.csv`).
2. Update `meta_path` with symbol-specific ADV/borrow/spread estimates.
3. Adjust allocator settings via `strategy.allocator` / `allocator_kwargs` in the config.
4. Tune queue parameters under `exec.queue_*` for different liquidity regimes.

The accompanying tests (`tests/test_flagship_momentum.py`, `tests/test_allocators.py`, `tests/test_reality_check_store.py`) codify invariants for momentum selection, covariance allocation, and bootstrap artefact persistence.

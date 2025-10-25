# Reproducibility

Microalpha emits a manifest for every run so you can replay results and audit configuration drift.

## Manifest fields

Each backtest stores `artifacts/<run_id>/manifest.json` with:

- `run_id` – UTC timestamp + short Git SHA used to scope outputs.
- `microalpha_version` – package version recorded at runtime.
- `git_sha` – repository commit used for the run.
- `config_sha256` – hash of the raw YAML bytes for integrity checking.
- `python` – interpreter version string.
- `platform` – OS information.
- `numpy_version` – NumPy version active during the run.
- `pandas_version` – pandas version active during the run.
- `seed` – RNG seed applied to the shared `numpy.random.Generator`.

The manifest is defined in [`src/microalpha/manifest.py`](https://github.com/MateoBodon/microalpha/blob/main/src/microalpha/manifest.py) and written by [`src/microalpha/runner.py`](https://github.com/MateoBodon/microalpha/blob/main/src/microalpha/runner.py).

Example snippet:

```json
{
  "run_id": "2024-03-27T14-22-19Z-4f3c1d1",
  "microalpha_version": "0.1.1",
  "git_sha": "4f3c1d1",
  "config_sha256": "2f4b32...",
  "seed": 7,
  "python": "3.11.6",
  "platform": "Ubuntu 22.04",
  "numpy_version": "1.26.4",
  "pandas_version": "2.2.2"
}
```

## Trade logs

Executions append JSON Lines to `artifacts/<run_id>/trades.jsonl` via [`JsonlWriter`](https://github.com/MateoBodon/microalpha/blob/main/src/microalpha/logging.py). Each line captures `timestamp`, `order_id`, `symbol`, `side`, `qty`, `price`, `commission`, `slippage`, `inventory`, and `cash`, enabling downstream reconciliation and deterministic comparisons ([`tests/test_trades_jsonl.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_trades_jsonl.py)).

## CLI determinism

`microalpha run` and `microalpha wfv` construct a single seeded `numpy.random.Generator` and pass it to the engine, broker, and portfolio to remove duplicate seeding. [`tests/test_determinism.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_determinism.py) verifies repeated runs produce identical manifests, metrics, and trade logs.

To reproduce a run:

```bash
microalpha run -c configs/meanrev.yaml
```

Then inspect the artifacts folder recorded in the manifest to fetch equity curves, metrics, and trades.

## Data sourcing (WRDS/CRSP)

For resume-grade, bias-aware experiments, use WRDS/CRSP daily data adjusted for corporate actions, and include delisted securities to avoid survivorship bias. We recommend a monthly universe selection (e.g., top 1000 by market cap) saved to CSVs (one file per symbol) under `data_sp500/` or `data_wrds/` with columns including at least `close` and a datetime index. Keep raw credentials and data out of the repo; only derived CSVs or aggregated artifacts should be saved.

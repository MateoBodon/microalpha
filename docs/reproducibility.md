# Reproducibility

Microalpha emits a manifest for every run so you can replay results.

## Manifest fields

- `git_sha` – repository commit used for the run.
- `python` – interpreter version string.
- `platform` – OS information.
- `seed` – RNG seed applied globally (NumPy and `random`).
- `config_path` – absolute path to the YAML config used in the run.
- `artifacts_dir` – where equity curves, metrics, and trade logs were written.

The manifest is produced in `src/microalpha/manifest.py` and stored alongside metrics in the artifacts directory.

## Trade logs

When executions occur, the portfolio writes `trades.csv` with timestamps, quantities, prices, and latency information. This allows downstream reconciliation and execution-quality analysis.

## CLI determinism

The CLI sets seeds before instantiating the engine and ensures all stochastic components draw from the seeded RNG (see `Engine.__init__`).

To reproduce a run:

```bash
python -m microalpha.cli run -c configs/meanrev.yaml
```

Then inspect the artifacts folder recorded in the manifest to fetch equity curves, metrics, and trades.

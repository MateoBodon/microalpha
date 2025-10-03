# Examples

## Mean Reversion CLI

```bash
python -m microalpha.cli run -c configs/meanrev.yaml
```

Produces equity/metrics/trade logs under `artifacts/<timestamp>` and prints a JSON manifest.

## Walk-forward validation

```bash
python -m microalpha.cli wfv -c configs/wfv_meanrev.yaml
```

Generates fold metrics, SPA-checked Sharpe ratios, and aggregate equity curves.

## Market-making visualization

```bash
python scripts/plot_mm_spread.py
```

Runs both LOB and TWAP execution variants, then writes `artifacts/mm_demo/mm_spread.png` showing realized spread against inventory.

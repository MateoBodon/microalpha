# Examples

Kick off experiments quickly using the bundled configuration files in `configs/`.

## Mean reversion backtest

```bash
microalpha run -c configs/meanrev.yaml
```

Produces equity, metrics, and trade logs under `artifacts/<run_id>/` while exercising the TWAP execution model, volume-aware slippage, and volatility-scaled capital sizing.

## Breakout momentum

```bash
microalpha run -c configs/breakout.yaml
```

Runs the breakout strategy with configurable lookbacks and writes results to its own artifact directory.

## Limit order book market making

```bash
microalpha run -c configs/mm.yaml
```

Bootstraps the level-2 order book simulator for a naive market-making strategy to showcase FIFO, partial fills, and latency.

## Walk-forward validation

```bash
microalpha wfv -c configs/wfv_meanrev.yaml
```

Executes the unified walk-forward configuration model, emitting per-fold manifests and out-of-sample metrics for each parameter combination.

## Cross-sectional momentum (multi-asset)

```bash
microalpha wfv -c configs/wfv_cs_mom.yaml
```

- Demonstrates monthly rebalanced 12-1 momentum across symbols using the `MultiCsvDataHandler`.
- Produces `folds.json`, `metrics.json`, `equity_curve.csv`, and you can render an interactive report with:

```bash
python reports/html_report.py artifacts/<run-id>/equity_curve.csv --trades artifacts/<run-id>/trades.jsonl --output artifacts/<run-id>/report.html
```

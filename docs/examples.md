# Examples

Kick off experiments quickly using the bundled configuration files in `configs/`.

## Mean reversion backtest

```bash
microalpha run -c configs/meanrev.yaml
```

Produces equity, metrics, and trade logs under `artifacts/<run_id>/` while exercising the TWAP execution model.

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

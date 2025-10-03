# API Reference

## `microalpha.runner`

- `run_from_config(path: str) -> dict`
  - Parses a YAML configuration, executes a backtest, and returns a manifest-style result containing metrics, fold summaries (for WFCV), and paths to artifacts.

## `microalpha.engine.Engine`

- `__init__(data, strategy, portfolio, broker, seed=42)`
- `run()` – processes market events in chronological order.

## `microalpha.portfolio.Portfolio`

- Tracks cash, holdings, and equity curve while enforcing exposure, drawdown, and turnover constraints.
- Collects trade records with latency metadata.

## `microalpha.execution`

- `Executor` – base class for execution models.
- `TWAP`, `SquareRootImpact`, `KyleLambda`, `LOBExecution` – built-in execution strategies.

## `microalpha.lob`

- `LimitOrderBook` – FIFO level-2 book with latency model.
- `LatencyModel` – configurable acknowledgements/fill stochastic delay.

## `microalpha.manifest`

- `build(seed, config_path)` – create manifest dataclass.
- `write(manifest, outdir)` – persist manifest JSON.

## Strategies

- `microalpha.strategies.meanrev.MeanReversionStrategy`
- `microalpha.strategies.breakout.BreakoutStrategy`
- `microalpha.strategies.mm.NaiveMarketMakingStrategy`

Refer to the source modules for full docstrings and type annotations.

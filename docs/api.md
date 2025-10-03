# API Reference

This page summarises the primary extension points for building strategies and tooling on top of Microalpha.

## Runner (`microalpha.runner`)

- `run_from_config(path: str) -> dict`
  - Loads a YAML config, resolves paths, executes the backtest, and returns a manifest-style dictionary containing artifact paths.
- `prepare_artifacts_dir(cfg_path: Path, config: dict) -> tuple[str, Path]`
  - Allocates an isolated `artifacts/<run_id>` directory for each run.

## Engine (`microalpha.engine.Engine`)

```python
Engine(data, strategy, portfolio, broker, rng: numpy.random.Generator | None = None)
```

- Streams `MarketEvent`s from the data handler, enforces monotonic timestamps, and routes signals/orders/fills between components.
- Accepts a `numpy.random.Generator` to guarantee deterministic RNG usage across the stack.

## Data (`microalpha.data.CsvDataHandler`)

```python
CsvDataHandler(csv_dir: Path, symbol: str, mode: str = "exact")
```

- Loads OHLCV CSV data and produces chronological `MarketEvent`s via `stream()`.
- `get_latest_price(ts)` supports `"exact"` and `"ffill"` modes for timestamp alignment.
- `get_future_timestamps(start_ts, n)` schedules TWAP child orders without lookahead.

## Portfolio (`microalpha.portfolio.Portfolio`)

```python
Portfolio(data_handler, initial_cash, *, max_exposure=None, max_drawdown_stop=None,
          turnover_cap=None, kelly_fraction=None, trade_logger=None)
```

- Tracks cash, inventory, and equity while enforcing exposure/drawdown/turnover limits.
- Emits fills to the `JsonlWriter` (`trade_logger`) so executions are captured in `trades.jsonl`.
- Provides `on_market`, `on_signal`, and `on_fill` hooks consumed by the engine.

## Broker & Execution (`microalpha.broker`, `microalpha.execution`)

- `SimulatedBroker(executor)` – wraps an `Executor` and enforces t+1 semantics before returning fills.
- `Executor` – base class implementing simple price-impact + commission fills against the `DataHandler`.
- `TWAP` – splits orders evenly across future timestamps supplied by the data handler.
- `SquareRootImpact` / `KyleLambda` – stylised impact models for execution cost studies.
- `LOBExecution` – routes orders to the in-memory level-2 book (`microalpha.lob.LimitOrderBook`) with latency simulation.

## Logging (`microalpha.logging.JsonlWriter`)

```python
JsonlWriter(path: str)
```

- Creates parent directories, writes JSON-serialised objects per line, and flushes eagerly so artifacts remain tail-able.

Refer to the module docstrings and tests for deeper examples of composing these components.

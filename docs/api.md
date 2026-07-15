# API Reference

This page summarises the primary extension points for building strategies and tooling on top of Microalpha.

## Audit Lab (`microalpha.audit_lab`)

```python
from microalpha.audit_lab import run_audit_lab

result = run_audit_lab("evidence", seed=20260715)
```

`run_audit_lab` returns the output directory, receipt SHA-256, and exact result
payload. Canonical files exclude clocks, hosts, and absolute paths.

## Multiple-testing control (`microalpha.multiple_testing`)

```python
from microalpha.multiple_testing import centered_max_statistic_test

result = centered_max_statistic_test(
    candidate_returns,
    benchmark_returns=benchmark_returns,
    candidate_names=["model_a", "model_b"],
    seed=7,
    num_bootstrap=2000,
)
```

The function tests whether the best candidate has a positive expected return
differential to an explicit benchmark. It null-centers the differential matrix
and synchronously resamples timestamps across all candidates.

## Point-in-time gate (`microalpha.point_in_time`)

```python
from microalpha.point_in_time import require_point_in_time

require_point_in_time(decision_at, available_at, row_ids=observation_ids)
```

The gate fails closed when any feature row becomes available after its decision
timestamp. `PointInTimeViolation` exposes exact `count` and `row_ids` fields for
auditable failure reports.

## Runner (`microalpha.runner`)

- `run_from_config(path: str, override_artifacts_dir: str | None = None) -> dict`
  - Loads a YAML config, resolves paths, executes the backtest, and returns a manifest-style dictionary containing artifact paths.
  - `override_artifacts_dir` overrides the root output directory without modifying the on-disk YAML.
- `prepare_artifacts_dir(cfg_path: Path, config: dict) -> tuple[str, Path]`
  - Allocates an isolated `artifacts/<run_id>` directory for each run.

## Engine (`microalpha.engine.Engine`)

```python
Engine(data, strategy, portfolio, broker, rng: numpy.random.Generator | None = None)
```

- Streams `MarketEvent`s from the data handler, enforces monotonic timestamps, and routes signals/orders/fills between components.
- Accepts a `numpy.random.Generator` for reproducibility; randomness is typically consumed by downstream components (e.g., latency models) rather than the engine itself.

Profiling:
- Set `MICROALPHA_PROFILE=1` or pass `--profile` via the CLI to record a `profile.pstats` under the active run’s artifact directory.

## Data (`microalpha.data.CsvDataHandler`)

```python
CsvDataHandler(csv_dir: Path, symbol: str, mode: str = "exact")
```

- Loads OHLCV CSV data and produces chronological `MarketEvent`s via `stream()`.
- `get_latest_price(ts)` supports `"exact"` and `"ffill"` modes for timestamp alignment.
- `get_future_timestamps(start_ts, n)` schedules TWAP child orders without lookahead.
- `get_recent_prices(symbol, end_ts, lookback)` for sizing; `get_volume_at(symbol, ts)` for VWAP.

## Portfolio (`microalpha.portfolio.Portfolio`)

```python
Portfolio(data_handler, initial_cash, *, max_exposure=None, max_drawdown_stop=None,
          turnover_cap=None, kelly_fraction=None, trade_logger=None,
          capital_policy=None)
```

- Tracks cash, inventory, and equity while enforcing exposure/drawdown/turnover limits.
- Emits fills to the `JsonlWriter` (`trade_logger`) so executions are captured in `trades.jsonl`.
- Provides `on_market`, `on_signal`, and `on_fill` hooks consumed by the engine.
- Adds realized PnL attribution per fill (average-cost) under `realized_pnl` and cumulative `cum_realized_pnl` in trades.
- Resolve config-driven capital policies via `capital_policy` in YAML; the runner instantiates them automatically.

## Broker & Execution (`microalpha.broker`, `microalpha.execution`)

- `SimulatedBroker(executor)` – plans execution slices and materializes each fill only when the engine reaches its scheduled market event.
- `ExecutionPlan(timestamp, order, qty)` – immutable pending slice. Market-data executors do not read a future price when creating it.
- `Executor` – base class implementing simple price-impact + commission fills against the `DataHandler`.
- `TWAP` – splits orders evenly across future timestamps supplied by the data handler.
- `VWAP` – the safe Engine planning path uses equal ex-ante slices because
  realized future volume is not available at order time. Its direct `execute()`
  compatibility method can reproduce an offline realized-volume benchmark, but
  must not be used as a chronology-safe simulation path.
- `ImplementationShortfall` – front-loaded geometric schedule controlled by `urgency`.
- `SquareRootImpact` / `KyleLambda` – stylised impact models for execution cost studies.
- `LOBExecution` – routes orders to the in-memory level-2 book (`microalpha.lob.LimitOrderBook`) with latency simulation.
- Supply `slippage` in YAML to enable `VolumeSlippageModel` without hand-wiring objects.

## Logging (`microalpha.logging.JsonlWriter`)

```python
JsonlWriter(path: str)
```

- Creates parent directories, writes JSON-serialised objects per line, and flushes eagerly so artifacts remain tail-able.

Refer to the module docstrings and tests for deeper examples of composing these components.

## Capital Allocation (`microalpha.capital`)

- `VolatilityScaledPolicy(lookback=20, target_dollar_vol=10000)` scales base order qty inversely to recent per-symbol volatility.
- Pass into `Portfolio(..., capital_policy=VolatilityScaledPolicy(...))` or declare under `capital_policy` in YAML to enable per-name risk targeting.

## CLI (`microalpha.cli`)

- `microalpha audit-demo [--out DIR] [--seed INT]`
- `microalpha run -c <cfg> [--out DIR] [--profile]`
- `microalpha wfv -c <cfg> [--out DIR] [--profile]`

`--out` overrides the artifacts root directory; `--profile` enables cProfile.

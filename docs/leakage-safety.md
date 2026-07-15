# Leakage Safety

Microalpha enforces a strict "no-peek" discipline at every layer of the simulation stack.

## Engine invariants

- **Monotonic clocks** – the `Engine` raises `LookaheadError` if market events arrive out of order. See [`tests/test_time_ordering.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_time_ordering.py).
- **t+1 execution** – strategies submit intents at time *t*. Built-in executors
  plan timestamps and quantities without reading future prices; the fill is
  materialized only when the matching market event arrives. A clock-guarded
  regression test fails on any early future-price read and proves cash and
  positions remain unchanged before t+1. See
  [`tests/test_tplus1_execution.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_tplus1_execution.py).
- **Fill ordering** – brokers acknowledge fills only after the active market event has been processed.

## Portfolio guards

- **Signal timestamps** – the portfolio refuses to act on stale signals ([`tests/test_time_ordering.py::test_strategy_cannot_backdate_signals`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_time_ordering.py)).
- **Fill timestamps** – fills older than the portfolio clock raise `LookaheadError`, ensuring fills cannot materialise from the future.

## Limit order book sequencing

The `LimitOrderBook` keeps per-level FIFO queues to ensure first-in-first-out fill priority. [`tests/test_lob_fifo.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_lob_fifo.py) and [`tests/test_lob_cancel_latency.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_lob_cancel_latency.py) cover partial fills, cancel acknowledgements, and latency offsets, guaranteeing orders are matched in arrival order without leaking future liquidity.

### LOB t+1 semantics

By default, LOB execution schedules its prepared fill for the next market
timestamp while retaining measured latency fields. The engine holds that fill
outside portfolio state until the event arrives. You can disable this behavior
only through the explicitly unsafe same-bar configuration:

```yaml
exec:
  type: lob
  lob_tplus1: false
```

## Walk-forward orchestration

During walk-forward validation, the optimizer only uses in-sample data to select parameters. Each fold records train/test windows in the JSON fold summary, providing an audit trail that the optimizer never touches out-of-sample data ([`tests/test_walkforward.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_walkforward.py)).

## Statistical inference invariants

- **Sharpe statistics** use the same deterministic return stream as performance metrics, with optional HAC adjustments (`METRICS_HAC_LAGS`) that never peek beyond the evaluated window. [`tests/test_risk_stats.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_risk_stats.py) asserts IID vs HAC behaviour on synthetic AR(1) data and validates block bootstrap coverage.
- **Selection-corrected max statistics** compare every candidate with an
  explicit benchmark, recenter candidate differentials under the null, and use
  the same stationary/circular bootstrap indices for every model to preserve
  cross-model dependence. The seed and block length are persisted.

Together, these invariants provide strong protection against accidentally leaking future information into historical tests.

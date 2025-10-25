# Leakage Safety

Microalpha enforces a strict "no-peek" discipline at every layer of the simulation stack.

## Engine invariants

- **Monotonic clocks** – the `Engine` raises `LookaheadError` if market events arrive out of order. See [`tests/test_time_ordering.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_time_ordering.py).
- **t+1 execution** – strategies submit intents at time *t* and executions occur no earlier than the next event. Verified in [`tests/test_tplus1_execution.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_tplus1_execution.py).
- **Fill ordering** – brokers acknowledge fills only after the active market event has been processed.

## Portfolio guards

- **Signal timestamps** – the portfolio refuses to act on stale signals ([`tests/test_time_ordering.py::test_strategy_cannot_backdate_signals`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_time_ordering.py)).
- **Fill timestamps** – fills older than the portfolio clock raise `LookaheadError`, ensuring fills cannot materialise from the future.

## Limit order book sequencing

The `LimitOrderBook` keeps per-level FIFO queues to ensure first-in-first-out fill priority. [`tests/test_lob_fifo.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_lob_fifo.py) and [`tests/test_lob_cancel_latency.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_lob_cancel_latency.py) cover partial fills, cancel acknowledgements, and latency offsets, guaranteeing orders are matched in arrival order without leaking future liquidity.

### LOB t+1 semantics

By default, LOB execution enforces t+1 semantics by shifting the reported `FillEvent.timestamp` to the next available market timestamp while retaining measured latency fields. This preserves the global no-peek invariant. You can disable this behavior per config with:

```yaml
exec:
  type: lob
  lob_tplus1: false
```

## Walk-forward orchestration

During walk-forward validation, the optimizer only uses in-sample data to select parameters. Each fold records train/test windows in the JSON fold summary, providing an audit trail that the optimizer never touches out-of-sample data ([`tests/test_walkforward.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_walkforward.py)).

Together, these invariants provide strong protection against accidentally leaking future information into historical tests.

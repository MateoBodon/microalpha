# Leakage Safety

Microalpha enforces a strict "no-peek" discipline at every layer of the simulation stack.

## Engine invariants

- **Monotonic clocks** – the `Engine` raises `LookaheadError` if market events arrive out of order.
- **Signal ordering** – strategies may only emit signals with timestamps greater than or equal to the current clock.
- **Fill ordering** – brokers must not acknowledge fills before the active market event.

These guards are implemented in `src/microalpha/engine.py` and validated by `tests/test_time_ordering.py`.

## Portfolio guards

- **Signal timestamps** – the portfolio refuses to act on stale signals (`tests/test_no_lookahead.py`).
- **Fill timestamps** – fills older than the portfolio clock raise `LookaheadError`.

## Limit order book sequencing

The `LimitOrderBook` keeps per-level FIFO queues to ensure first-in-first-out fill priority. The smoke test in `tests/test_lob.py` verifies that resting orders are processed ahead of new arrivals at the same price level.

## Walk-forward orchestration

During walk-forward validation, the optimizer only uses in-sample data to select parameters. Each fold records train/test windows in the JSON fold summary, providing an audit trail that the optimizer never touches out-of-sample data (`tests/test_walkforward.py`).

Together, these invariants provide strong protection against accidentally leaking future information into historical tests.

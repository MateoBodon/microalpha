"""Measure v0.3 report generation and an active event/fill workload."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import tempfile
import time
import tracemalloc
from pathlib import Path

from microalpha.broker import SimulatedBroker
from microalpha.engine import Engine
from microalpha.events import MarketEvent, SignalEvent
from microalpha.execution import Executor
from microalpha.market_case import run_market_case
from microalpha.portfolio import Portfolio


class _ActiveData:
    def __init__(self, sessions: int, symbols: int) -> None:
        self.sessions = sessions
        self.symbols = [f"S{index:02d}" for index in range(symbols)]

    def stream(self):
        for timestamp in range(self.sessions):
            for index, symbol in enumerate(self.symbols):
                yield MarketEvent(
                    timestamp,
                    symbol,
                    100.0 + index + timestamp * 0.0001,
                    10_000_000.0,
                )

    def get_latest_price(self, symbol: str, timestamp: int) -> float:
        index = int(symbol[1:])
        return 100.0 + index + timestamp * 0.0001

    def get_future_timestamps(
        self, start_timestamp: int, n: int, symbol: str | None = None
    ) -> list[int]:
        return list(
            range(
                start_timestamp + 1,
                min(start_timestamp + 1 + n, self.sessions),
            )
        )

    def get_volume_at(self, symbol: str, timestamp: int) -> float:
        return 10_000_000.0

    def get_recent_prices(
        self, symbol: str, end_timestamp: int, lookback: int
    ) -> list[float]:
        start = max(0, end_timestamp - lookback + 1)
        return [
            self.get_latest_price(symbol, timestamp)
            for timestamp in range(start, end_timestamp + 1)
        ]


class _ActiveStrategy:
    def on_market(self, event: MarketEvent):
        if event.timestamp % 21 != 0:
            return []
        phase = (event.timestamp // 21) % 2
        weight = 0.05 if phase == 0 else 0.10
        return [
            SignalEvent(
                event.timestamp,
                event.symbol,
                "LONG",
                meta={"target_weight": weight, "benchmark": "active_execution"},
            )
        ]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _active_benchmark(
    *, sessions: int = 10_000, symbols: int = 10
) -> dict[str, object]:
    data = _ActiveData(sessions, symbols)
    portfolio = Portfolio(data, initial_cash=1_000_000.0, max_exposure=2.0)
    broker = SimulatedBroker(Executor(data, commission=0.001, price_impact=0.0))
    engine = Engine(data, _ActiveStrategy(), portfolio, broker)
    tracemalloc.start()
    started = time.perf_counter()
    engine.run()
    seconds = time.perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    events = sessions * symbols
    return {
        "events": events,
        "orders_filled": len(portfolio.trades),
        "seconds": round(seconds, 4),
        "events_per_second": round(events / seconds),
        "peak_tracemalloc_mb": round(peak / 1024 / 1024, 3),
        "workload": "10 symbols; target-weight resize every 21 sessions; t+1 materialized fills; commission ledger",
    }


def _report_benchmark(runs: int = 3) -> dict[str, object]:
    times: list[float] = []
    receipts: list[str] = []
    tracemalloc.start()
    peak = 0
    with tempfile.TemporaryDirectory(prefix="microalpha-v030-bench-") as tmp:
        for run in range(runs):
            out = Path(tmp) / f"run-{run}"
            started = time.perf_counter()
            result = run_market_case(out)
            times.append(time.perf_counter() - started)
            receipts.append(str(result["receipt_sha256"]))
            _, current_peak = tracemalloc.get_traced_memory()
            peak = max(peak, current_peak)
    tracemalloc.stop()
    ordered = sorted(times)
    return {
        "runs_seconds": [round(value, 4) for value in times],
        "median_seconds": round(ordered[len(ordered) // 2], 4),
        "minimum_seconds": round(min(times), 4),
        "peak_tracemalloc_mb": round(peak / 1024 / 1024, 3),
        "deterministic_receipt": len(set(receipts)) == 1,
        "receipt_sha256": receipts[0],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    payload = {
        "schema_version": "microalpha.engineering-benchmark.v1",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "measured_on": "2026-07-15",
        "market_case": _report_benchmark(),
        "active_engine": _active_benchmark(),
        "v0_2_reference": {
            "audit_demo_median_seconds": 1.3745,
            "no_op_events_per_second": 1_464_231,
            "scope": "previous public host receipt; not directly comparable to the active order/fill workload",
        },
        "source_sha256": {
            str(path.relative_to(root)): _sha256(path)
            for path in (
                root / "benchmarks/bench_v030.py",
                root / "src/microalpha/engine.py",
                root / "src/microalpha/execution.py",
                root / "src/microalpha/portfolio.py",
                root / "src/microalpha/market_case.py",
            )
        },
        "claim_boundary": "host-dependent engineering evidence; correctness comes from tests and receipts",
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()

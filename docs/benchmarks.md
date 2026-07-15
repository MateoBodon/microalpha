# Benchmarks

This page documents the active v0.3 engineering benchmark and the retained v0.2
raw-loop reference. Runtime evidence is host-dependent; deterministic receipts
and tests remain the correctness claims.

## v0.3 active-workload receipt

The tracked [`engineering_benchmark_v030.json`](assets/engineering_benchmark_v030.json)
measures both product reproduction and a materialized order/fill workload on
Python 3.12.2, Apple arm64:

| Benchmark | Result | What is exercised |
| --- | ---: | --- |
| Market Risk Case, median of 3 clean directories | `23.7126 s` | 2,198-session report, bootstrap inference, SVGs, schemas, hashes |
| Active engine, 100,000 market events | `38,767 events/s` | 10 symbols, target-weight resize, t+1 fills, commission ledger |
| Active engine peak traced memory | `5.919 MB` | Same 100,000-event workload |

The three report runs produced the same receipt. This receipt is a conservative
single-host reference, not a performance promise. The benchmark hashes its own
source and the engine, execution, portfolio, and report sources so comparisons
cannot silently change the workload.

```bash
PYTHONPATH=src python benchmarks/bench_v030.py \
  --output docs/assets/engineering_benchmark_v030.json
```

## Retained v0.2 raw-loop reference

The earlier host-dependent receipt is tracked as
[`benchmark.json`](assets/audit_lab/benchmark.json):

| Benchmark | Result | Environment |
| --- | ---: | --- |
| Audit Lab, median of 5 clean output directories | `1.3745 s` | Python 3.12.2, Apple arm64 |
| Event loop, 1,000,000 no-op events | `1,464,231 events/s` | Python 3.12.2, Apple arm64 |

This no-op loop isolates dispatch overhead, but it does not exercise order
sizing, future fill scheduling, or a cost ledger. It is retained as a narrow
regression baseline rather than presented as application throughput.

- Script: `benchmarks/bench_engine.py`
- Purpose: Measures raw event throughput of the engine and Portfolio wiring under a no-op strategy and zero-cost execution model.

## Running the raw loop locally

```bash
python benchmarks/bench_engine.py
```

The harness prints a small JSON with the number of processed events, wall-clock seconds, and events/sec.

Historical example on Apple M2 Pro (32GB, macOS 14.6.1):

```
{"events": 1000000, "sec": 0.773, "evps": 1294141}
```

Your numbers will vary by hardware, Python version, and build flags. Use the harness to compare relative changes across code revisions (e.g., after refactoring a tight loop).

## Profiling a run

Enable profiling for any CLI run and inspect hotspots with `snakeviz` or `gprof2dot`:

```bash
microalpha run -c configs/meanrev.yaml --profile
# or
MICROALPHA_PROFILE=1 microalpha run -c configs/meanrev.yaml
```

The engine writes `profile.pstats` under the active run’s artifact directory:

```
artifacts/<run_id>/profile.pstats
```

Open it with `snakeviz`:

```bash
pip install snakeviz
snakeviz artifacts/<run_id>/profile.pstats
```

This integrates with the per-run artifacts so profiles travel alongside metrics and trades.

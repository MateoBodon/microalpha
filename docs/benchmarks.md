# Benchmarks

This page documents how to run the bundled micro-benchmark and interpret the results.

## Current receipt

The 2026-07-15 host-dependent receipt is tracked as
[`benchmark.json`](assets/audit_lab/benchmark.json):

| Benchmark | Result | Environment |
| --- | ---: | --- |
| Audit Lab, median of 5 clean output directories | `1.3745 s` | Python 3.12.2, Apple arm64 |
| Event loop, 1,000,000 no-op events | `1,464,231 events/s` | Python 3.12.2, Apple arm64 |

The receipt hashes every benchmark source file. Runtime varies by hardware,
Python, power state, and background load; it is an engineering baseline, not a
deterministic correctness artifact.

- Script: `benchmarks/bench_engine.py`
- Purpose: Measures raw event throughput of the engine and Portfolio wiring under a no-op strategy and zero-cost execution model.

## Running locally

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

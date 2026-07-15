# Examples

Kick off experiments quickly using the bundled configuration files and the reproducible sample data under `data/sample/`.

## 1. Flagship momentum quickstart

```bash
make sample
make report
```

The run command generates deterministic artifacts (metrics, bootstrap distribution, exposures, trades) using the new linear+sqrt slippage model, IOC queueing, and covariance-aware allocator. The report command renders a PNG tear sheet plus a Markdown case study.

## 2. Walk-forward reality check on the sample universe

```bash
make wfv
make report-wfv
```

The run commands create a run-ID child directory. If you call the CLI directly,
pass the `artifact_dir` printed by `run` or `wfv` to `microalpha report`.

This executes a rolling walk-forward with Politis–White bootstrap and writes `folds.json`, `bootstrap.json`, `exposures.csv`, and aggregated metrics for the flagship strategy.

## 3. Classic single-asset examples

- **Mean reversion**

  ```bash
  microalpha run --config configs/meanrev.yaml
  ```

- **Breakout momentum**

  ```bash
  microalpha run --config configs/breakout.yaml
  ```

- **Market making (LOB simulator)**

  ```bash
  microalpha run --config configs/mm.yaml
  ```

- **Parameter walk-forward (single asset)**

  ```bash
  microalpha wfv --config configs/wfv_meanrev.yaml
  ```

Each command drops a self-contained artifact directory; you can call `microalpha report --artifact-dir <dir>` on any of them to render the markdown/PNG bundle.

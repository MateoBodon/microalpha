# Microalpha

Microalpha is an event-driven research platform for reproducible quantitative strategy development. The engine prioritises leakage-safety, deterministic execution, and rich analytics so researchers can iterate quickly without sacrificing rigor.

## Why Microalpha?

- **Leakage-safe core**: strict timestamp ordering, FIFO broker interactions, and lookahead guards.
- **Execution realism**: TWAP/impact models and a configurable level-2 limit order book.
- **Reproducible pipelines**: manifest metadata, trade logs, and automation-ready CLI.
- **Extensible design**: users can plug in new strategies, data handlers, and execution layers.
- **Documentation-first**: MkDocs site with invariants, manifests, API references, and runnable demos.

## Quickstart

1. **Install the package**

   ```bash
   pip install microalpha
   # or, for local development
   pip install -e ".[dev]"
   ```

2. **Run the bundled mean-reversion backtest**

   ```bash
   microalpha run -c configs/meanrev.yaml
   ```

   The CLI writes manifests, metrics, equity curves, and trade logs under `artifacts/<run_id>/`.

3. **Explore further**

   - Inspect leakage invariants in [Leakage Safety](leakage-safety.md).
   - Review reproducibility workflows in [Reproducibility](reproducibility.md).
   - Extend components using the [API Reference](api.md).
   - Try the scenarios in [Examples](examples.md).

Use the navigation to dive into leakage guarantees, reproducibility tooling, API surfaces, and runnable examples.

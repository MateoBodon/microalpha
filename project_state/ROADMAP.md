# Roadmap

## Short‑Term (0–4 weeks)
- Complete **S2 drawdown reduction validation**: run `configs/wfv_flagship_wrds_smoke.yaml` and full `wfv_flagship_wrds.yaml` with tightened caps; regenerate SPA/analytics/factor/summary assets and refresh `docs/results_wrds.md`.
- Add quick **WRDS rerun checklist** to AGENTS/README to reduce setup friction (env vars, WRDS_DATA_ROOT, expected runtimes).
- Verify **weight contract** between FlagshipMomentumStrategy and Portfolio; document in API/strategy docstrings.

## Medium‑Term (1–3 months)
- Harden **WRDS export + data QC**: add validators for price monotonicity/volume positivity; automate manifest checks before runs.
- Expand **strategy library**: additional cross‑sectional factors (value/quality/low‑vol) sharing the same infra; include configs and small public datasets.
- Improve **performance ergonomics**: optional fold parallelism or resumable WFV runs; profile hotspots with `MICROALPHA_PROFILE` and address bottlenecks.
- Strengthen **reporting**: make factor model choice configurable in YAML/CLI; unify reality‑check vs SPA presentation.

## Long‑Term (3–12 months)
- Anchor **resume‑ready WRDS case study** with stable headline metrics, SPA, factor attribution, and capacity analysis.
- Build **agent‑native workflows**: richer `project_state/` upkeep, add Codex prompts, automate targeted test selection.
- Publish **documentation upgrades**: interactive notebooks using committed artifacts, deeper leakage demos, reproducibility stories, and universe construction walkthroughs.
- Explore **scalability**: intraday support, GPU acceleration for heavy simulations, pluggable data loaders (Parquet/Feather, database readers).

## Ordering / Dependencies
- Finish WRDS reruns before expanding docs or adding new strategies (their credibility depends on up‑to‑date metrics).
- Performance profiling/parallelism should follow completion of at least one full WRDS run to target real bottlenecks.

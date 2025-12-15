# Test Coverage

## How to Run
- Default: `pytest -vv --maxfail=1 --durations=25` (Makefile `make test`).
- WRDS‑dependent: `pytest -m wrds` (Makefile `make test-wrds`), skipped if `WRDS_DATA_ROOT` missing.
- Coverage badge in README shows ~78%.

## Test Suites (high level)
- **Engine & chronology**: `test_time_ordering.py`, `test_no_lookahead.py`, `test_tplus1_execution.py`, `test_limit_order_execution.py` ensure monotonic timestamps, t+1 fills.
- **Data handlers**: `test_data.py`, `test_multiasset_data_handler.py`, `test_price_lookup.py`, `test_multiasset_cs_momentum.py`.
- **Portfolio & risk**: `test_portfolio_risk_caps.py`, `test_portfolio_turnover_cap.py`, `test_portfolio_weight_sizing.py`, `test_risk_controls.py`, `test_borrow_costs.py`, `test_capital_and_slippage_integration.py`, `test_risk_stats.py`, `test_metrics_hac.py`, `test_metrics_invariant.py`.
- **Execution / slippage / LOB**: `test_execution.py`, `test_execution_models.py`, `test_slippage_models.py`, `test_lob.py`, `test_lob_modes.py`, `test_lob_fifo.py`, `test_lob_cancel_latency.py`, `test_vwap_is.py`, `test_profile_output.py`.
- **Strategies**: `test_flagship_momentum.py`, `test_multiasset_cs_momentum.py`, `test_strategies.py`, `test_meanrev` (covered inside).
- **Runner / manifest / CFG**: `test_runner_flagship.py`, `test_manifest_written.py`, `test_cfg_unify.py`, `test_trades_jsonl.py`.
- **Walk‑forward & reality check**: `test_walkforward.py`, `test_reality_check_store.py`.
- **Reporting**: `test_reporting_analytics.py`, `test_reporting_spa.py`, `test_wrds_summary_render.py`, `test_factor_regression.py`, `test_docs_links.py` (docs link integrity).
- **CLI**: `test_cli_help.py`, `test_cli_info.py`.
- **WRDS markers**: `test_wrds_detection.py`, `test_wrds_markers.py`, `test_wrds_flagship_spec.py`, `test_build_wrds_signals.py` (marked `wrds` where data needed).
- **Benchmarks/other**: `test_benchmarks.py`, `test_determinism.py`, `test_metrics_hac.py`.

## Gaps / Risks
- WRDS heavy tests are skipped without local data; coverage of end‑to‑end WRDS pipeline is limited.
- Performance/parallelism not tested; long WFV runs may regress silently.
- Analytics plots rely on sample artifacts; removal of committed artifacts breaks tests.
- No explicit tests for factor model selection/config plumbing or for SPA vs reality‑check consistency.

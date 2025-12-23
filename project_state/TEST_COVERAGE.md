<!--
generated_at: 2025-12-23T22:01:33Z
git_sha: ba5b48089091f6a858b065dd3a388b467dd67984
branch: codex/ticket-04-leakage-tests-unsafe-manifest
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->


# Test Coverage

- Test modules: 57
- Marker config: `pytest.ini` defines `wrds` marker.
- Primary commands: `pytest -q` or `make test`; WRDS tests via `make test-wrds`.

## Notable suites

- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_allocators.py`
- `tests/test_artifacts_schema.py`
- `tests/test_benchmarks.py`
- `tests/test_borrow_costs.py`
- `tests/test_build_wrds_signals.py`
- `tests/test_capital_and_slippage_integration.py`
- `tests/test_cfg_unify.py`
- `tests/test_cli_help.py`
- `tests/test_cli_info.py`
- `tests/test_data.py`
- `tests/test_data_policy.py`
- `tests/test_determinism.py`
- `tests/test_docs_links.py`
- `tests/test_execution.py`
- `tests/test_execution_models.py`
- `tests/test_factor_regression.py`
- `tests/test_flagship_momentum.py`
- `tests/test_limit_order_execution.py`
- `tests/test_lob.py`
- `tests/test_lob_cancel_latency.py`
- `tests/test_lob_fifo.py`
- `tests/test_lob_modes.py`
- `tests/test_manifest_written.py`
- `tests/test_metrics_hac.py`
- `tests/test_metrics_invariant.py`
- `tests/test_multiasset_cs_momentum.py`
- `tests/test_multiasset_data_handler.py`
- `tests/test_no_lookahead.py`
- `tests/test_pnl_attribution.py`
- `tests/test_pnl_integrity.py`
- `tests/test_portfolio_risk_caps.py`
- `tests/test_portfolio_risk_sizing.py`
- `tests/test_portfolio_turnover_cap.py`
- `tests/test_portfolio_weight_sizing.py`
- `tests/test_price_lookup.py`
- `tests/test_profile_output.py`
- `tests/test_reality_check_store.py`
- `tests/test_reporting_analytics.py`
- `tests/test_reporting_robustness.py`
- `tests/test_reporting_spa.py`
- `tests/test_risk_and_slippage.py`
- `tests/test_risk_controls.py`
- `tests/test_risk_stats.py`
- `tests/test_runner_flagship.py`
- `tests/test_slippage_models.py`
- `tests/test_strategies.py`
- `tests/test_time_ordering.py`
- `tests/test_tplus1_execution.py`
- `tests/test_trades_jsonl.py`
- `tests/test_vwap_is.py`
- `tests/test_walkforward.py`
- `tests/test_wrds_detection.py`
- `tests/test_wrds_flagship_spec.py`
- `tests/test_wrds_markers.py`
- `tests/test_wrds_summary_render.py`

Coverage note: README badge reports 78% coverage for bundled suites.

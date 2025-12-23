<!--
generated_at: 2025-12-23T22:01:33Z
git_sha: ba5b48089091f6a858b065dd3a388b467dd67984
branch: codex/ticket-04-leakage-tests-unsafe-manifest
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->

# Function Index

## `src/microalpha/__init__.py`

### Classes

- (none)

### Functions

- (none)

## `src/microalpha/allocators.py`

### Classes

- (none)

### Functions

- risk_parity(cov: pd.DataFrame | np.ndarray, *, tol: float=1e-08, max_iter: int=10000, ridge: float=1e-08, initial: Sequence[float] | None=None) — Compute long-only risk parity weights for a covariance matrix.
- lw_min_var(returns: pd.DataFrame | np.ndarray, *, allow_short: bool=False, epsilon: float=1e-06, return_cov: bool=False) — Ledoit–Wolf shrinkage min-variance allocator.
- budgeted_allocator(signals: Mapping[str, float] | pd.Series, cov: pd.DataFrame | np.ndarray, *, total_budget: float=1.0, ridge: float=1e-08, risk_model: str='risk_parity', returns: pd.DataFrame | None=None, allow_short: bool=False) — Allocate capital across long/short sleeves using risk parity within each bucket.
- _as_dataframe(data: pd.DataFrame | np.ndarray | Mapping[str, Mapping[str, float]], *, columns_first: bool=False)
- _as_series(data: Mapping[str, float] | pd.Series)
- _ledoit_wolf_cov(returns: np.ndarray)
- _min_var_weights(cov: np.ndarray, *, allow_short: bool, epsilon: float)
- _bucket_weights(cov: pd.DataFrame, *, ridge: float, risk_model: str, returns: pd.DataFrame | None, allow_short: bool)

## `src/microalpha/broker.py`

### Classes

- SimulatedBroker

### Functions

- (none)

## `src/microalpha/capital.py`

### Classes

- DataHandlerLike(Protocol)
- PortfolioLike(Protocol)
- CapitalPolicy(Protocol)
- VolatilityScaledPolicy — Scale base order size inversely to recent volatility.

### Functions

- (none)

## `src/microalpha/cli.py`

### Classes

- (none)

### Functions

- main()
- _build_info()
- _resolve_version()

## `src/microalpha/config.py`

### Classes

- SlippageCfg(BaseModel)
- ExecModelCfg(BaseModel)
- StrategyCfg(BaseModel)
- CapitalPolicyCfg(BaseModel)
- BorrowCfg(BaseModel)
- BacktestCfg(BaseModel)

### Functions

- parse_config(raw: Any)

## `src/microalpha/config_wfv.py`

### Classes

- WalkForwardWindow(BaseModel)
- HoldoutWindow(BaseModel)
- RealityCheckCfg(BaseModel)
- WFVCfg(BaseModel)

### Functions

- (none)

## `src/microalpha/data.py`

### Classes

- DataHandler — Base class for data handlers.
- CsvDataHandler(DataHandler)
- MultiCsvDataHandler(DataHandler) — Multi-asset CSV handler that synchronises events across symbols.
- _SymbolState

### Functions

- (none)

## `src/microalpha/engine.py`

### Classes

- Engine

### Functions

- (none)

## `src/microalpha/events.py`

### Classes

- MarketEvent
- SignalEvent
- OrderEvent
- FillEvent
- LookaheadError(Exception) — Raised when an operation would violate temporal ordering.

### Functions

- (none)

## `src/microalpha/execution.py`

### Classes

- DataHandlerProtocol(Protocol)
- Executor
- TWAP(Executor)
- VWAP(Executor) — Volume-weighted execution across future timestamps.
- ImplementationShortfall(Executor) — Front-loaded schedule approximating IS minimisation.
- SquareRootImpact(Executor)
- KyleLambda(Executor)
- LOBExecution(Executor) — Execution wrapper backed by the internal limit order book.

### Functions

- (none)

## `src/microalpha/execution_safety.py`

### Classes

- (none)

### Functions

- evaluate_execution_safety(exec_cfg: ExecModelCfg) — Return (unsafe_execution, reasons, alignment_metadata).

## `src/microalpha/integrity.py`

### Classes

- IntegrityResult

### Functions

- _equity_series(equity_records: Sequence[Mapping[str, float | int]] | None)
- _equity_is_constant(series: np.ndarray, *, tol_abs: float, tol_rel: float)
- evaluate_portfolio_integrity(portfolio: Portfolio, *, equity_records: Sequence[Mapping[str, float | int]] | None=None, slippage_total: float=0.0, tol_abs: float=1e-06, tol_rel: float=1e-08)

## `src/microalpha/lob.py`

### Classes

- LatencyModel
- LimitOrder
- BookSide
- LimitOrderBook

### Functions

- (none)

## `src/microalpha/logging.py`

### Classes

- JsonlWriter — Append-only JSON Lines writer.

### Functions

- (none)

## `src/microalpha/manifest.py`

### Classes

- Manifest

### Functions

- resolve_git_sha() — Return ``(full_sha, short_sha)`` for the current Git HEAD.
- generate_run_id(short_sha: str, timestamp: Optional[datetime]=None) — Create a run identifier using a UTC timestamp and short SHA.
- _resolve_distribution_version() — Resolve the installed distribution version for microalpha.
- build(seed: Optional[int], config_path: str, run_id: str, config_sha256: str, config_summary: Mapping[str, Any] | None=None, git_sha: Optional[str]=None, *, unsafe_execution: bool=False, unsafe_reasons: list[str] | None=None, execution_alignment: Mapping[str, Any] | None=None) — Construct a manifest and synchronise global RNG state.
- extract_config_summary(raw_config: Mapping[str, Any]) — Pull key risk/cost parameters from a config mapping for the manifest.
- write(manifest: Manifest, outdir: str) — Write the manifest to ``outdir/manifest.json``.

## `src/microalpha/market_metadata.py`

### Classes

- SymbolMeta — Snapshot of per-symbol liquidity and financing characteristics.

### Functions

- load_symbol_meta(path: str | Path) — Load symbol metadata from a CSV file.
- merge_symbol_meta(*collections: Mapping[str, SymbolMeta] | Iterable[tuple[str, SymbolMeta]]) — Merge multiple symbol metadata mappings.
- _coerce_float_or_none(value: object)

## `src/microalpha/metrics.py`

### Classes

- (none)

### Functions

- compute_metrics(equity_records: Sequence[Mapping[str, float | int]], turnover: float, periods: int=252, trades: Optional[List[Mapping[str, Any]]]=None, benchmark_equity: Optional[Sequence[Mapping[str, float | int]]]=None, rf: float=0.0, hac_lags: int | None=None)

## `src/microalpha/portfolio.py`

### Classes

- PortfolioPosition
- Portfolio

### Functions

- (none)

## `src/microalpha/reporting/__init__.py`

### Classes

- (none)

### Functions

- (none)

## `src/microalpha/reporting/analytics.py`

### Classes

- AnalyticsArtifacts

### Functions

- _resolve_plot_path(artifact_dir: Path, plots_dir: Path, stem: str)
- _pearson(x: pd.Series, y: pd.Series)
- load_signals(signals_path: Path, *, date_col: str='as_of', score_col: str='score', forward_col: str='forward_return')
- compute_ic_series(signals: pd.DataFrame, method: str='spearman')
- compute_rolling_ir(ic_series: pd.Series, window: int=63)
- compute_decile_table(signals: pd.DataFrame, deciles: int=10)
- load_equity_returns(equity_csv: Path)
- load_factor_frame(factor_csv: Path)
- compute_rolling_betas(returns: pd.Series, factors: pd.DataFrame, *, factor_cols: Sequence[str] | None=None, window: int=63)
- plot_ic_series(ic_series: pd.Series, ir_series: pd.Series, output: Path)
- plot_deciles(table: pd.DataFrame, output: Path)
- plot_rolling_betas(betas: pd.DataFrame, output: Path)
- generate_analytics(artifact_dir: Path, *, signals_path: Path | None=None, equity_path: Path | None=None, factor_path: Path | None=None, plots_dir: Path=PLOTS_DIR, analytics_dir: Path=ANALYTICS_DIR, ic_method: str='spearman', window: int=63, deciles: int=10)
- _build_arg_parser()
- main(argv: Sequence[str] | None=None)

## `src/microalpha/reporting/factors.py`

### Classes

- FactorResult

### Functions

- _prepare_returns(equity_csv: Path)
- _prepare_factors(factor_csv: Path, required: Sequence[str])
- _design_matrix(factors: pd.DataFrame, factor_names: Sequence[str], excess_returns: pd.Series)
- _newey_west_se(X: np.ndarray, residuals: np.ndarray, lag: int)
- compute_factor_regression(equity_csv: Path, factor_csv: Path, model: str='ff3', hac_lags: int=5) — Run Carhart/FF5(+MOM) regressions with Newey-West errors.
- _format_markdown_table(results: Iterable[FactorResult])
- main()

## `src/microalpha/reporting/robustness.py`

### Classes

- RobustnessArtifacts — Paths to generated robustness artifacts.

### Functions

- write_robustness_artifacts(artifact_dir: Path | str, multipliers: Sequence[float]=DEFAULT_MULTIPLIERS) — Compute and persist robustness artifacts under ``artifact_dir``.
- compute_cost_sensitivity(artifact_dir: Path | str, *, multipliers: Sequence[float]=DEFAULT_MULTIPLIERS, periods_per_year: int=252) — Ex‑post cost scaling over an existing equity curve and trade log.
- _metrics_from_returns(returns: pd.Series, *, periods_per_year: int=252)
- compute_metadata_coverage(artifact_dir: Path | str) — Compute liquidity/financing metadata coverage for executed trades.
- _load_trades(trades_path: Path)
- _resolve_trades_path(artifact_dir: Path)
- _resolve_config_path(artifact_dir: Path)
- _load_config(config_path: Path)
- _resolve_meta_path(config_path: Path | None, config: Mapping[str, object])
- _extract_defaults(config: Mapping[str, object])

## `src/microalpha/reporting/spa.py`

### Classes

- SpaSummary

### Functions

- _degenerate_summary(reason: str, *, n_obs: int, n_strategies: int, avg_block: int, num_bootstrap: int, diagnostics: list[str] | None=None)
- _coerce_numeric_frame(frame: pd.DataFrame)
- load_grid_returns(grid_path: Path)
- _stationary_bootstrap_indices(n: int, avg_block: int, rng: np.random.Generator)
- _spa_stat(diff_matrix: np.ndarray)
- compute_spa(pivot: pd.DataFrame, *, avg_block: int=63, num_bootstrap: int=2000, seed: int=0)
- write_outputs(summary: SpaSummary, json_path: Path, markdown_path: Path)
- _build_parser()
- main(argv: Sequence[str] | None=None)

## `src/microalpha/reporting/summary.py`

### Classes

- (none)

### Functions

- _load_json(path: Path)
- _load_integrity(artifact_dir: Path)
- _load_manifest(artifact_dir: Path)
- _unsafe_banner(manifest_payload: Mapping[str, object] | None)
- _integrity_reasons(payload: Mapping[str, object])
- _flatten_bootstrap(path: Path)
- _format_pct(value: float | None)
- _format_currency(value: float | None)
- _render_exposures(exposures_path: Path | None, top_n: int)
- generate_summary(artifact_dir: str | Path, output_path: str | Path=DEFAULT_OUTPUT, *, title: str | None=None, top_exposures: int=8, equity_image: str | Path | None=None, bootstrap_image: str | Path | None=None, factor_csv: str | Path | None=Path('data/factors/ff3_sample.csv'))
- _parse_args(argv: Sequence[str] | None=None)
- main(argv: Sequence[str] | None=None)
- _render_metric_table(metrics: Mapping[str, object])
- _format_metric(label: str, value: object)
- _render_exposure_summary(metrics: Mapping[str, object])
- _render_cost_breakdown(cost_path: Path)
- _to_float(value: object)
- _resolve_trades_path(artifact_dir: Path)
- _count_trades(path: Path)
- _load_returns(artifact_dir: Path)
- _detect_degenerate_reasons(metrics: Mapping[str, object], artifact_dir: Path)
- _relpath(path: Path, output_path: Path)
- _render_factor_section(*, artifact_dir: Path | str, factor_csv: Path | None, hac_lags: int=5)
- _render_cost_section(cost_path: Path)
- _render_coverage_section(coverage_path: Path)

## `src/microalpha/reporting/tearsheet.py`

### Classes

- (none)

### Functions

- _ensure_path(path: str | Path | None)
- _load_metrics(path: Path | None)
- _load_bootstrap(path: Path | None)
- _compute_drawdown(equity: pd.Series)
- render_tearsheet(equity_csv: str | Path, bootstrap_json: str | Path | None, output_path: str | Path, *, bootstrap_output: str | Path | None=None, metrics_path: str | Path | None=None, title: str | None=None) — Render equity and bootstrap plots.
- _parse_args(argv: Sequence[str] | None=None)
- main(argv: Sequence[str] | None=None)

## `src/microalpha/reporting/wrds_summary.py`

### Classes

- HeadlineMetrics
- SpaRenderResult

### Functions

- _require_file(path: Path, label: str)
- _load_json(path: Path)
- _load_integrity(artifact_dir: Path)
- _integrity_reasons(payload: dict | None)
- _unsafe_banner(manifest_payload: dict | None)
- _format_currency(value: float)
- _format_human_currency(value: float | None)
- _format_ratio(value: float | None)
- _format_p_value(value: float | None)
- _format_pct(value: float)
- _relpath(target: Path, output_path: Path)
- _normalise_section(text: str)
- _render_table(metrics: HeadlineMetrics)
- _to_float(value: object)
- _render_exposure_table(metrics_payload: dict)
- _render_cost_breakdown(cost_payload: dict | None)
- _has_trade_log(artifact_dir: Path)
- _load_cost_payload(artifact_dir: Path)
- _extract_headline(metrics_payload: dict, spa_payload: dict, *, spa_status: str)
- _parse_factor_table(markdown: str)
- _copy_asset(source: Path, destination: Path)
- _load_folds_metadata(folds_path: Path)
- _load_config_metadata(config_path: Path | None)
- _relative_to_repo(path: Path)
- _coerce_float(value: object)
- _infer_spa_dimensions(artifact_dir: Path, diagnostics: list[str])
- _write_degenerate_spa(json_path: Path, md_path: Path, *, reason: str, diagnostics: list[str], n_obs: int, n_strategies: int)
- _write_spa_markdown_from_payload(payload: dict, md_path: Path)
- _ensure_spa_payload(artifact_dir: Path, spa_json: Path | None, spa_md: Path | None)
- _spa_skip_reason(spa_payload: dict)
- _spa_status(spa_payload: dict)
- _render_spa_placeholder(destination: Path, message: str)
- _render_spa_plot(spa_payload: dict, destination: Path, *, allow_zero: bool=False)
- _resolve_trades_path(artifact_dir: Path)
- _count_trades(path: Path)
- _load_returns(artifact_dir: Path)
- _detect_degenerate_reasons(metrics_payload: dict, artifact_dir: Path)
- _write_docs_results(docs_path: Path, *, run_id: str, config_label: str, train_start: str, test_end: str, fold_count: int, testing_days: int | None, config_meta: dict[str, Any] | None, headline: HeadlineMetrics, metrics_payload: dict, cost_payload: dict | None, spa_payload: dict, spa_status: str, spa_skip_reason: str | None, factor_status: str, factor_skip_reason: str | None, factor_table_md: str, image_map: dict[str, Path], spa_md_copy: Path | None, degenerate_reasons: list[str], invalid_reasons: list[str], unsafe_lines: list[str] | None)
- render_wrds_summary(artifact_dir: Path, output_path: Path, *, factors_md: Path | None=None, spa_json: Path | None=None, spa_md: Path | None=None, equity_image: Path | None=None, bootstrap_image: Path | None=None, docs_results: Path | None=None, docs_image_root: Path | None=None, analytics_plots: Path | None=None, metrics_json_out: Path | None=None, spa_json_out: Path | None=None, spa_md_out: Path | None=None, allow_zero_spa: bool=False)
- _build_parser()
- main(argv: Sequence[str] | None=None)

## `src/microalpha/risk.py`

### Classes

- (none)

### Functions

- create_sharpe_ratio(returns, periods: int=252, *, rf: float=0.0, ddof: int=0, hac_lags: Optional[int]=None) — Calculates the annualized Sharpe ratio of a returns stream.
- create_drawdowns(equity_curve) — Calculates the maximum drawdown and the drawdown series.
- bootstrap_sharpe_ratio(returns, num_simulations: int=5000, periods: int=252, *, rf: float=0.0, ddof: int=0, hac_lags: Optional[int]=None, method: str='stationary', block_len: Optional[int]=None, rng: Optional[np.random.Generator]=None) — Performs a bootstrap analysis on a returns stream to determine the

## `src/microalpha/risk_stats.py`

### Classes

- (none)

### Functions

- _as_series(returns: Iterable[float])
- _newey_west_lrv(values: np.ndarray, max_lag: int) — Estimate the long-run variance using Newey-West weights.
- sharpe_stats(returns: pd.Series, rf: float=0.0, periods: int=252, ddof: int=0, hac_lags: Optional[int]=None) — Compute Sharpe ratio statistics with optional HAC standard errors.
- _default_block_len(n: int)
- block_bootstrap(returns: np.ndarray, B: int=5000, method: Literal['stationary', 'circular']='stationary', block_len: Optional[int]=None, rng: Optional[np.random.Generator]=None) — Yield bootstrap samples that preserve serial dependence via block resampling.

## `src/microalpha/runner.py`

### Classes

- (none)

### Functions

- run_from_config(config_path: str, override_artifacts_dir: str | None=None) — Execute a backtest described by ``config_path``.
- prepare_artifacts_dir(cfg_path: Path, config: Dict[str, Any], base_run_id: str)
- persist_config(cfg_path: Path, artifacts_dir: Path)
- _persist_metrics(metrics: Dict[str, Any], artifacts_dir: Path, *, extra_metrics: Mapping[str, Any] | None=None)
- _persist_integrity(result, artifacts_dir: Path)
- _update_manifest_integrity(artifacts_dir: Path, integrity_path: str, *, run_invalid: bool)
- persist_exposures(portfolio: Portfolio, artifacts_dir: Path, filename: str='exposures.csv', factor_filename: str='factor_exposure.csv')
- _persist_bootstrap(metrics: Dict[str, Any], artifacts_dir: Path, *, periods: int=252, simulations: int=1024)
- _stable_metrics(metrics: Dict[str, Any])
- _persist_trades(portfolio: Portfolio, artifacts_dir: Path)
- resolve_path(value: str, cfg_path: Path)
- resolve_capital_policy(cfg: CapitalPolicyCfg | None)
- resolve_slippage_model(cfg: SlippageCfg | None, symbol_meta: Mapping[str, Any] | None=None)

## `src/microalpha/slippage.py`

### Classes

- SlippageModel — Base class for slippage models with optional symbol metadata support.
- VolumeSlippageModel(SlippageModel) — Legacy quadratic volume model retained for backward compatibility.
- _ImpactBase(SlippageModel)
- LinearImpact(_ImpactBase) — Linear impact respecting a spread floor.
- SquareRootImpact(_ImpactBase) — Square-root impact with spread floor.
- LinearPlusSqrtImpact(_ImpactBase) — Hybrid linear + square-root impact with spread floor.

### Functions

- (none)

## `src/microalpha/strategies/breakout.py`

### Classes

- BreakoutStrategy — Breakout momentum strategy with simple exits.

### Functions

- (none)

## `src/microalpha/strategies/cs_momentum.py`

### Classes

- CrossSectionalMomentum — 12-1 style cross-sectional momentum with monthly rebalance.

### Functions

- (none)

## `src/microalpha/strategies/flagship_mom.py`

### Classes

- SleeveSelection
- FlagshipMomentumStrategy — Cross-sectional momentum with sector normalisation and sleeve controls.

### Functions

- (none)

## `src/microalpha/strategies/flagship_momentum.py`

### Classes

- (none)

### Functions

- (none)

## `src/microalpha/strategies/meanrev.py`

### Classes

- MeanReversionStrategy — A simple mean-reversion strategy based on z-scores.

### Functions

- (none)

## `src/microalpha/strategies/mm.py`

### Classes

- NaiveMarketMakingStrategy — Toy market-making strategy that oscillates inventory.

### Functions

- (none)

## `src/microalpha/walkforward.py`

### Classes

- (none)

### Functions

- load_wfv_cfg(path: str) — Load a walk-forward validation configuration.
- run_walk_forward(config_path: str, override_artifacts_dir: str | None=None, reality_check_method: str | None=None, reality_check_block_len: int | None=None)
- _optimise_parameters(data_handler: DataHandler, train_start: pd.Timestamp, train_end: pd.Timestamp, strategy_class, param_grid: Mapping[str, Sequence[Any]], base_params: Dict[str, Any], cfg: BacktestCfg, rng: np.random.Generator, reality_cfg: RealityCheckCfg, symbol_meta: Mapping[str, Any] | None=None)
- _build_portfolio(data_handler, cfg: BacktestCfg, trade_logger: JsonlWriter | None=None, symbol_meta: Mapping[str, Any] | None=None)
- _build_executor(data_handler, exec_cfg: ExecModelCfg, rng: np.random.Generator, symbol_meta: Mapping[str, Any] | None=None)
- _spawn_rng(parent: np.random.Generator)
- _collect_warmup_prices(data_handler: CsvDataHandler, train_end: pd.Timestamp, lookback: int)
- _collect_cs_warmup_history(data_handler: MultiCsvDataHandler, train_start: pd.Timestamp, train_end: pd.Timestamp, symbols: Sequence[str])
- _summarise_walkforward(equity_records: List[Dict[str, Any]], artifacts_dir: Path, total_turnover: float, hac_lags: int | None=None, extra_metrics: Mapping[str, Any] | None=None)
- _stable_metrics(metrics: Dict[str, Any])
- _persist_integrity_checks(artifacts_dir: Path, overall_ok: bool, checks: Sequence[Mapping[str, Any]])
- _update_manifest_integrity(artifacts_dir: Path, integrity_path: str, *, run_invalid: bool)
- _build_grid_payload(entries: List[Dict[str, Any]])
- _grid_summary_from_payload(payload: List[Dict[str, Any]])
- _aggregate_selection_summary(grid_summaries: Sequence[List[Dict[str, Any]]])
- _grid_rows_for_fold(payload: List[Dict[str, Any]], fold_index: int, phase: str)
- _format_param_label(params: Mapping[str, Any])
- _metrics_summary(metrics: Dict[str, Any])
- _format_ts(value: Any)
- _annualised_sharpe(returns: np.ndarray, periods: int=252)
- bootstrap_reality_check(results: List[Dict[str, Any]], seed: int, n_bootstrap: int=200, method: str='stationary', block_len: int | None=None)
- _strategy_params(strategy_cfg)
- _strategy_kwargs(params: Dict[str, Any], warmup_prices=None)

## `src/microalpha/wrds/__init__.py`

### Classes

- (none)

### Functions

- pgpass_path() — Return the expected ~/.pgpass location.
- has_pgpass_credentials(host: str=WRDS_HOST) — Check whether ~/.pgpass contains a WRDS entry without leaking contents.
- has_wrds_credentials() — True when ~/.pgpass or WRDS_USERNAME provides credentials.
- _local_wrds_doc_path()
- _parse_wrds_root(line: str)
- _load_local_wrds_data_root()
- get_wrds_data_root() — Resolve WRDS data root from WRDS_DATA_ROOT (with local-doc fallback).
- has_wrds_data(min_entries: int=1) — Return True if WRDS_DATA_ROOT exists and looks non-empty.
- wrds_status() — Structured status for debugging/logging (no secrets).
- is_wrds_path(path: Path) — Return True if ``path`` resolves under WRDS_DATA_ROOT.
- guard_no_wrds_copy(path: Path, *, operation: str='copy') — Raise if attempting to copy data directly from WRDS_DATA_ROOT.

## `tools/build_project_state.py`

### Classes

- (none)

### Functions

- rg_files(root: Path)
- add_explicit_dirs(files: list[str], root: Path, extra_dirs: list[Path])
- classify_role(path: str)
- is_binary_extension(path: str)
- repo_inventory(files: list[str])
- module_name_for_file(path: Path)
- unparse(node: ast.AST | None)
- format_args(args: ast.arguments)
- first_line(doc: str | None)
- symbol_index(py_files: list[Path])
- import_graph(py_files: list[Path])
- make_targets(makefile: Path)
- main()

## `tools/gpt_bundle.py`

### Classes

- (none)

### Functions

- _env(name: str)
- _copy_path(src: Path, dest_root: Path, missing: list[str])
- _load_meta_shas(meta_path: Path)
- _load_meta(meta_path: Path)
- _require_ticket_defined(meta_path: Path, sprint_path: Path, expected_ticket: str | None=None)
- _require_results_ready(results_path: Path)
- _resolve_ref(ref: str)
- _derive_diff_range(meta_path: Path)
- _write_commits(stage: Path, base: str, head: str, source: str)
- _require_clean_worktree()
- _collect_check_files(stage: Path, run_name: str)
- _hydrate_base_file(base: str, rel_path: Path, dest_root: Path)
- _verify_patch_matches(diff_path: Path, stage: Path, base: str, head: str, run_name: str)
- main()

## `tools/render_project_state_docs.py`

### Classes

- (none)

### Functions

- read_text(path: Path)
- read_json(path: Path)
- latest_run_dir(root: Path)
- utc_now()
- git_sha()
- git_branch()
- header(generated_at: str, sha: str, branch: str, commands: list[str])
- write_doc(path: Path, content: str)
- summarize_module_symbols(symbol_index: dict[str, Any])
- format_symbol_list(items: Iterable[dict[str, Any]], kind: str)
- load_make_targets()
- load_repo_inventory()
- list_by_role(inventory: list[dict[str, Any]], role: str)
- summarize_directory(inventory: list[dict[str, Any]], prefix: str)
- top_level_keys_from_yaml(path: Path)
- parse_readme_sample_artifacts(readme_text: str)
- parse_wrds_results(results_text: str)
- latest_progress_section(progress_text: str)
- summarize_results(text: str)
- recent_run_summaries(root: Path, limit: int=3)
- extract_progress_issues(progress_text: str)
- wrds_caveat(results_text: str)
- render_architecture(symbol_index: dict[str, Any], inventory: list[dict[str, Any]])
- render_module_summaries(symbol_index: dict[str, Any])
- render_function_index(symbol_index: dict[str, Any])
- render_dependency_graph(import_graph: dict[str, list[str]])
- render_pipeline_flow(make_targets: list[str])
- render_dataflow()
- render_experiments(inventory: list[dict[str, Any]])
- render_current_results(readme_text: str, wrds_text: str, wrds_smoke_text: str, sample_metrics: dict[str, Any], wfv_metrics: dict[str, Any], holdout_run: str | None, holdout_metrics: dict[str, Any], progress_text: str, recent_runs: list[dict[str, str]])
- render_research_notes()
- render_open_questions()
- render_known_issues(progress_text: str, wrds_text: str)
- render_roadmap()
- render_config_reference(config_paths: list[Path])
- render_server_environment(py_version: str, deps: list[str])
- render_test_coverage(test_files: list[str])
- render_style_guide()
- render_changelog(changelog_text: str)
- render_index()
- main()


Notes: AST-derived; signatures are best-effort.

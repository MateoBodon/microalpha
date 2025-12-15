# Configuration Reference

## Single Backtest (`BacktestCfg`, `configs/*.yaml`)
- **data_path**: Directory of per‑symbol CSVs (env/tilde expanded).  
- **meta_path**: Optional symbol metadata CSV for ADV/spread/borrow fees.  
- **symbol**: Primary symbol (ignored for strategies that supply `symbols` list/universe).  
- **cash/seed**: Starting cash and RNG seed.
- **Risk limits**: `max_exposure`, `max_drawdown_stop`, `turnover_cap`, `kelly_fraction`, `max_portfolio_heat`, `max_positions_per_sector`, `sectors` mapping.
- **Metrics**: `metrics_hac_lags` (falls back to env `METRICS_HAC_LAGS`).
- **Date bounds**: `start_date`, `end_date` (sliced inside DataHandler).
- **Capital policy**: `capital_policy.type = volatility_scaled` with `lookback`, `target_dollar_vol`, `min_qty`.

### Execution (`exec` / `ExecModelCfg`)
- **type**: `instant|linear|twap|vwap|is|sqrt|kyle|lob` (mapped in `runner.EXECUTION_MAPPING`).
- **commission** (alias `aln`), **price_impact** (or `lam` for Kyle), **slices**, **urgency** (IS), **book_levels/level_size/tick_size/mid_price** (LOB), **lob_tplus1** (bool).
- **limit_mode**: `ioc|po|market`; queue params `queue_coefficient`, `queue_passive_multiplier`, `queue_seed`, `queue_randomize`, `volatility_lookback`, `min_fill_qty`.
- **slippage** (`SlippageCfg`): `type` = `volume|linear|sqrt|linear_sqrt`; coefficients `impact/k_lin/eta`, `default_adv`, `default_spread_bps`, `spread_floor_multiplier`.

### Strategy (`strategy` / `StrategyCfg`)
- **name**: Strategy class string (`MeanReversionStrategy`, `BreakoutStrategy`, `NaiveMarketMakingStrategy`, `CrossSectionalMomentum`, `FlagshipMomentumStrategy`).
- **lookback/z**: Optional legacy parameters auto‑mapped into `params`.
- **params**: Strategy‑specific kwargs (e.g., Flagship: `universe_path`, `lookback_months`, `skip_months`, `top_frac`, `bottom_frac`, `max_positions_per_sector`, `min_adv`, `min_price`, `turnover_target_pct_adv`, `cov_lookback_days`, `rebalance_frequency`, `allocator`, `allocator_kwargs`, `total_risk_budget`).
- **allocator / allocator_params**: Additional allocator choices for non‑flagship strategies.

## Walk‑Forward (`WFVCfg`, `configs/wfv_*.yaml`)
- **template**: Full `BacktestCfg` block used for each fold (env expansion allowed).
- **walkforward**: `start`, `end`, `training_days`, `testing_days` defining rolling windows.
- **grid**: Parameter grid; keys are strategy params (e.g., `lookback_months`, `skip_months`, `top_frac`, `allocator_kwargs`), values are lists.
- **artifacts_dir**: Optional override for output root (default `artifacts`).
- **reality_check**: `method` = `stationary|circular|iid`, `samples` (# bootstrap draws), `block_length` (optional override of Politis–White default).

## Key Config Files
- `configs/flagship_sample.yaml` – Sample single flagship; ADV/spread floors tuned to sample metadata.
- `configs/wfv_flagship_sample.yaml` – Sample walk‑forward; grid over `top_frac`, `skip_months`.
- `configs/wfv_flagship_public.yaml` – Public mini‑panel walk‑forward.
- `configs/wfv_flagship_wrds.yaml` – Full WRDS flagship (2005–2024), tightened risk limits, grid over lookback/skip/top_frac/allocator risk model.
- `configs/wfv_flagship_wrds_smoke.yaml` – Faster WRDS sanity (2015–2019, reduced grid).
- `configs/wfv_cs_mom*.yaml` – Cross‑sectional momentum variants for SP500 subsets.
- `configs/meanrev.yaml`, `configs/breakout.yaml`, `configs/mm*.yaml` – Single‑asset baselines and MM execution demos.
- `configs/flagship_wrds_single.yaml` – Single WRDS backtest (no walk‑forward).

## Environment Variables Affecting Configs
- `WRDS_DATA_ROOT` – Required for WRDS configs; paths like `${WRDS_DATA_ROOT}/crsp/daily_csv`.
- `MICROALPHA_PROFILE` – If set, engine dumps `profile.pstats` to `MICROALPHA_ARTIFACTS_DIR` or `artifacts/`.
- `MICROALPHA_ARTIFACTS_DIR` – Profiling output path hint.
- `METRICS_HAC_LAGS` – Overrides HAC lags in metrics if `metrics_hac_lags` is unset.


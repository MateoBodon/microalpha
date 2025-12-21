<!--
generated_at: 2025-12-21T21:29:21Z
git_sha: 33c9c2a0bab056c4296a66ee652af49cc646f7df
branch: feat/ticket-02-holdout-wfv
commands:
  - python3 tools/build_project_state.py
  - python3 tools/render_project_state_docs.py
-->

# Config Reference

| Config | Top-level keys | Notes |
| --- | --- | --- |
| `configs/breakout.yaml` | data_path, symbol, cash, seed, exec, strategy |  |
| `configs/flagship_mom.yaml` | data_path, symbol, cash, seed, max_exposure, max_drawdown_stop, turnover_cap, max_portfolio_heat, max_positions_per_sector, kelly_fraction, start_date, end_date, exec, strategy, capital_policy |  |
| `configs/flagship_sample.yaml` | data_path, meta_path, symbol, cash, seed, max_exposure, max_drawdown_stop, turnover_cap, max_portfolio_heat, max_positions_per_sector, metrics_hac_lags, start_date, end_date, exec, strategy, capital_policy | Bundled sample data |
| `configs/flagship_wrds_single.yaml` | data_path, meta_path, symbol, cash, seed, max_exposure, max_gross_leverage, max_single_name_weight, max_drawdown_stop, turnover_cap, max_portfolio_heat, max_positions_per_sector, metrics_hac_lags, start_date, end_date, borrow, exec, strategy, capital_policy | WRDS/CRSP (guarded by env vars) |
| `configs/meanrev.yaml` | data_path, symbol, cash, seed, max_exposure, max_drawdown_stop, turnover_cap, kelly_fraction, exec, strategy, capital_policy |  |
| `configs/mm.yaml` | data_path, symbol, cash, seed, exec, strategy |  |
| `configs/mm_lob_same_tick.yaml` | data_path, symbol, cash, seed, exec, strategy |  |
| `configs/mm_lob_tplus1.yaml` | data_path, symbol, cash, seed, exec, strategy |  |
| `configs/wfv_cs_mom.yaml` | template, walkforward, grid, artifacts_dir | Walk-forward |
| `configs/wfv_cs_mom_small.yaml` | template, walkforward, grid, artifacts_dir | Walk-forward |
| `configs/wfv_cs_mom_sp500_med.yaml` | template, walkforward, grid, artifacts_dir | Walk-forward |
| `configs/wfv_cs_mom_sp500_small.yaml` | template, walkforward, grid, artifacts_dir | Walk-forward |
| `configs/wfv_flagship_mom.yaml` | template, walkforward, grid, artifacts_dir | Walk-forward |
| `configs/wfv_flagship_public.yaml` | template, walkforward, grid, reality_check | Public mini-panel |
| `configs/wfv_flagship_sample.yaml` | template, walkforward, grid, reality_check | Bundled sample data |
| `configs/wfv_flagship_sample_holdout.yaml` | artifacts_dir, template, walkforward, holdout, grid, reality_check | Bundled sample data |
| `configs/wfv_flagship_wrds.yaml` | artifacts_dir, template, walkforward, holdout, grid, reality_check | WRDS/CRSP (guarded by env vars) |
| `configs/wfv_flagship_wrds_smoke.yaml` | artifacts_dir, template, walkforward, holdout, grid, reality_check | WRDS/CRSP (guarded by env vars) |
| `configs/wfv_meanrev.yaml` | data, walkforward, strategy, portfolio, broker_settings, random_seed, artifacts_dir | Walk-forward |

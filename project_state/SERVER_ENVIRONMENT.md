# Server / Runtime Environment

- **Python**: 3.12 recommended (pyproject sets python_version for mypy to 3.12; requires >=3.9).  
- **Package manager**: `pip`; local dev uses `pip install -e '.[dev]'` (Makefile target `make dev`).
- **Core dependencies**: `numpy`, `pandas`, `pyyaml`, `pydantic>=2`, `matplotlib>=3.7`.
- **Dev/optional dependencies**: `pytest`, `pytest-cov`, `hypothesis`, `mypy`, `ruff`, `black`, `plotly`, `pyarrow`, `types-PyYAML`, `pandas-stubs`, `mkdocs`, `mkdocs-material`, `isort`, `detect-secrets`, `wrds` (for export script).
- **Entry points**: console script `microalpha` (`microalpha.cli:main`); wrappers `run.py`, `walk_forward.py`; reporting scripts under `reports/`.
- **Environment variables**:
  - `WRDS_DATA_ROOT` – root of local WRDS/CRSP export (required for WRDS configs and report-wrds target).
  - `WRDS_USERNAME` or `~/.pgpass` – WRDS credentials (0600 perms).
  - `MICROALPHA_PROFILE` – enable cProfile; `MICROALPHA_ARTIFACTS_DIR` controls profile output location.
  - `METRICS_HAC_LAGS` – override HAC lag count at runtime.
- **Data paths expected**:
  - `$WRDS_DATA_ROOT/crsp/daily_csv/` (per-symbol CSV), `$WRDS_DATA_ROOT/crsp/dsf/` (Parquet), `$WRDS_DATA_ROOT/meta/crsp_security_metadata.csv`, `$WRDS_DATA_ROOT/universes/flagship_sector_neutral.csv`.
  - Bundled data lives under `data/`, `data_sp500_enriched/`, `data/flagship_universe/`, `data/factors/`.
- **Hardware assumptions**: CPU workflows; WRDS walk-forward can be long (>hours) but not GPU-bound. Matplotlib/Plotly used for plotting.
- **CI**: GitHub Actions CI badge present; coverage badge (78%) suggests pytest + coverage used in pipeline.
- **MkDocs**: `mkdocs.yml` with `docs/` site; `mkdocs serve` for local preview, `mkdocs build` in CI/docs workflow.

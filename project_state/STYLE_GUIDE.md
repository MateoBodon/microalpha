# Style Guide (observed & recommended)

- **Type hints everywhere**: Core modules use Python 3.12 type hints and Pydantic models. Keep new code fully typed; prefer `Path`/`Mapping` over bare dicts.
- **Readable > clever**: Small, composable functions; avoid dense one‑liners. Follow existing naming (snake_case functions, CamelCase classes).
- **Docstrings**: Public functions/classes include short, specific docstrings (seen in reporting/risk). Add when introducing new APIs.
- **Data shapes**: Price data as pandas DataFrame/Series; timestamps normalised to pandas `Timestamp` or `int ns`. Equity curves store columns `timestamp,equity,exposure,returns`.
- **Error handling**: Raise descriptive `ValueError`/`FileNotFoundError` early (see configs/data handlers). Preserve `LookaheadError` for chronology violations.
- **Slippage/execution**: Normalise modes to lowercase/standard values (see `ExecModelCfg._normalise_legacy_fields`). Reuse existing mappings (`STRATEGY_MAPPING`, `EXECUTION_MAPPING`).
- **Testing**: Mark WRDS‑dependent tests with `@pytest.mark.wrds`; keep tests deterministic. Default command `pytest -q` before commits (per AGENTS.md).
- **Lint/format**: Use `ruff check`, `black` (line length 88), `mypy` on touched areas (esp. reporting/factors). Avoid repo‑wide reformatting.
- **Artifacts**: Do not commit licensed WRDS data. Committed artifacts are deterministic sample runs; keep paths stable for docs/tests.
- **Configs**: Prefer YAML configs over hardcoded params; support env/tilde expansion. Keep new strategy knobs in configs with sane defaults.
- **Logging**: Use `JsonlWriter` for structured trade logs; avoid verbose stdout in core engine.

# Known Issues & Limitations

- **Stale WRDS metrics**: Committed WRDS runs pre‑date tightened risk caps; latest artifacts in `artifacts/wrds_flagship/` are incomplete (no `metrics.json`/`folds.json`). Docs numbers may not match current configs until rerun.
- **Zero‑activity WRDS smoke**: `artifacts/wrds_single_test/.../metrics.json` shows zero trades/returns, indicating missing/unusable signals for that attempt.
- **Sample performance is intentionally poor**: Negative Sharpe in sample bundle is expected but can confuse newcomers; clarify in docs when presenting metrics.
- **Runtime for full WRDS WFV**: End‑to‑end run can exceed interactive time (>2h) on modest hardware; Makefile does not chunk folds, so partial outputs are left behind.
- **Metadata gaps**: Slippage/borrow models fall back to global defaults when ADV/spread/borrow_fee are missing; this can understate transaction costs for thin names.
- **Queue model realism**: IOC/PO fill probabilities are heuristic and unvalidated; may misrepresent fills in illiquid environments.
- **Tests rely on committed artifacts**: Schema/tests (`tests/test_artifacts_schema.py`, docs link checks) assume sample artifacts exist; deleting them will break CI.

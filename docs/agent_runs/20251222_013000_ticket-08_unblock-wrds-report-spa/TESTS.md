## Report-only repro (pre-fix)

Command:
`microalpha report --artifact-dir artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e`

Output:
```
/Users/mateobodon/Documents/Programming/Projects/microalpha/src/microalpha/reporting/tearsheet.py:174: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig_equity.tight_layout()
{
  "artifact_dir": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e",
  "summary_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/reports/summaries/flagship_mom.md",
  "equity_curve_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/equity_curve.png",
  "bootstrap_hist_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/bootstrap_hist.png",
  "cost_sensitivity_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/cost_sensitivity.json",
  "metadata_coverage_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/metadata_coverage.json",
  "runtime_sec": 0.641,
  "version": "0.1.0"
}
```

Command:
`microalpha report --artifact-dir artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7`

Output:
```
/Users/mateobodon/Documents/Programming/Projects/microalpha/src/microalpha/reporting/tearsheet.py:174: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig_equity.tight_layout()
{
  "artifact_dir": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7",
  "summary_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/reports/summaries/flagship_mom.md",
  "equity_curve_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/equity_curve.png",
  "bootstrap_hist_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/bootstrap_hist.png",
  "cost_sensitivity_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/cost_sensitivity.json",
  "metadata_coverage_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/metadata_coverage.json",
  "runtime_sec": 0.513,
  "version": "0.1.0"
}
```

## Tests

Command:
`pytest -q`

Output:
```
102 passed, 1 skipped, 2 warnings in 19.04s
```

Warnings:
- DeprecationWarning: ExecModelCfg.aln is deprecated; use 'commission' instead.
- FutureWarning: Series.fillna with 'method' is deprecated and will raise in a future version. Use obj.ffill() or obj.bfill() instead.

## Report verification (post-fix)

Command:
`microalpha report --artifact-dir artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e`

Output:
```
/Users/mateobodon/Documents/Programming/Projects/microalpha/src/microalpha/reporting/tearsheet.py:174: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig_equity.tight_layout()
{
  "artifact_dir": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e",
  "summary_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/reports/summaries/flagship_mom.md",
  "equity_curve_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/equity_curve.png",
  "bootstrap_hist_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/bootstrap_hist.png",
  "cost_sensitivity_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/cost_sensitivity.json",
  "metadata_coverage_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e/metadata_coverage.json",
  "runtime_sec": 0.538,
  "version": "0.1.0"
}
```

Command:
`microalpha report --artifact-dir artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7`

Output:
```
/Users/mateobodon/Documents/Programming/Projects/microalpha/src/microalpha/reporting/tearsheet.py:174: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig_equity.tight_layout()
{
  "artifact_dir": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7",
  "summary_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/reports/summaries/flagship_mom.md",
  "equity_curve_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/equity_curve.png",
  "bootstrap_hist_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/bootstrap_hist.png",
  "cost_sensitivity_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/cost_sensitivity.json",
  "metadata_coverage_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/wrds_flagship/2025-12-21T22-32-44Z-2b48ef7/metadata_coverage.json",
  "runtime_sec": 0.502,
  "version": "0.1.0"
}
```

## make report

Command:
`make report`

Output:
```
/Users/mateobodon/Documents/Programming/Projects/microalpha/src/microalpha/reporting/tearsheet.py:174: UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect.
  fig_equity.tight_layout()
{
  "artifact_dir": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_flagship/2025-12-20T23-30-48Z-f8b316f",
  "summary_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/reports/summaries/flagship_mom.md",
  "equity_curve_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_flagship/2025-12-20T23-30-48Z-f8b316f/equity_curve.png",
  "bootstrap_hist_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_flagship/2025-12-20T23-30-48Z-f8b316f/bootstrap_hist.png",
  "cost_sensitivity_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_flagship/2025-12-20T23-30-48Z-f8b316f/cost_sensitivity.json",
  "metadata_coverage_path": "/Users/mateobodon/Documents/Programming/Projects/microalpha/artifacts/sample_flagship/2025-12-20T23-30-48Z-f8b316f/metadata_coverage.json",
  "runtime_sec": 0.541,
  "version": "0.1.0"
}
```

## Negative tests for bundler

Command:
`RUN_NAME=20251222_013000_ticket-08_unblock-wrds-report-spa python3 tools/gpt_bundle.py`

Exit code: 1

Output:
```
TICKET must be set
```

Command:
`TICKET=ticket-08 RUN_NAME=missing_run_zzz python3 tools/gpt_bundle.py`

Exit code: 1

Output:
```
docs/gpt_bundles/2025-12-22T03-12-45Z_ticket-08_missing_run_zzz.zip
Missing bundle items: docs/agent_runs/missing_run_zzz
Missing bundle items: docs/agent_runs/missing_run_zzz
```

## Secret scan

Command:
`rg -n "WRDS_PASSWORD|WRDS_USERNAME|password|token|secret" -S .`

Output:
```
./scripts/export_wrds_flagship.py
85:    env_user = os.environ.get("WRDS_USERNAME")

./project_state/CHANGELOG.md
22:- Pre-commit automation (black, isort, ruff, detect-secrets) plus tightened `.gitignore`.

./project_state/_generated/symbol_index.json
1491:        "doc": "True when ~/.pgpass or WRDS_USERNAME provides credentials.",
1509:        "doc": "Structured status for debugging/logging (no secrets).",

./project_state/FUNCTION_INDEX.md
550:- has_wrds_credentials() — True when ~/.pgpass or WRDS_USERNAME provides credentials.
553:- wrds_status() — Structured status for debugging/logging (no secrets).

./src/microalpha/wrds/__init__.py
49:    """True when ~/.pgpass or WRDS_USERNAME provides credentials."""
53:    return bool(os.getenv("WRDS_USERNAME"))
83:    """Structured status for debugging/logging (no secrets)."""
87:        "env_username": bool(os.getenv("WRDS_USERNAME")),

./pyproject.toml
34:    "detect-secrets>=1.5",

./CHANGELOG.md
8:- Pre-commit automation (black, isort, ruff, detect-secrets) plus tightened `.gitignore`.
```

## Quote-surface scan

Command:
`rg -n "strike,.*market_iv|\\bsecid\\b|best_bid|best_ask|best_offer" -S .`

Exit code: 1 (no matches)

## Bundle listing check

Command:
`unzip -l docs/gpt_bundles/2025-12-22T02-56-09Z_ticket-08_20251222_013000_ticket-08_unblock-wrds-report-spa.zip | rg -n "AGENTS.md|docs/PLAN_OF_RECORD.md|docs/DOCS_AND_LOGGING_SYSTEM.md|docs/CODEX_SPRINT_TICKETS.md|PROGRESS.md|project_state/CURRENT_RESULTS.md|project_state/KNOWN_ISSUES.md|project_state/CONFIG_REFERENCE.md|docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa"`

Output:
```
5:     1906  12-21-2025 21:51   PROGRESS.md
7:     3337  12-21-2025 15:02   AGENTS.md
11:     1906  12-21-2025 21:56   .patch_check/PROGRESS.md
13:      534  12-21-2025 21:56   .patch_check/.patch_PROGRESS.md
16:    10254  12-21-2025 21:56   docs/CODEX_SPRINT_TICKETS.md
17:     5604  12-21-2025 15:02   docs/DOCS_AND_LOGGING_SYSTEM.md
18:     8039  12-21-2025 15:02   docs/PLAN_OF_RECORD.md
19:     2863  12-21-2025 18:16   project_state/CONFIG_REFERENCE.md
20:     2051  12-21-2025 20:38   project_state/CURRENT_RESULTS.md
21:     1048  12-21-2025 21:51   project_state/KNOWN_ISSUES.md
22:     3510  12-21-2025 21:56   .patch_check/docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/COMMANDS.md
23:     4724  12-21-2025 21:56   .patch_check/docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/PROMPT.md
24:     5665  12-21-2025 21:56   .patch_check/docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/TESTS.md
25:     1623  12-21-2025 21:56   .patch_check/docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/RESULTS.md
26:      955  12-21-2025 21:56   .patch_check/docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/META.json
27:     3510  12-21-2025 21:54   docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/COMMANDS.md
28:     4724  12-21-2025 21:49   docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/PROMPT.md
29:     5665  12-21-2025 21:53   docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/TESTS.md
30:     1623  12-21-2025 21:53   docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/RESULTS.md
31:      955  12-21-2025 21:53   docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/META.json
```

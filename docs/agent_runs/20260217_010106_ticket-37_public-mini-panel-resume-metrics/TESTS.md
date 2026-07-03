# Tests

- [x] `source .venv/bin/activate && MPLCONFIGDIR=/tmp/matplotlib microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public` (attempt 1)
  - Result: fail.
  - Failure detail: `ValueError: Universe file must contain at least 'symbol' and 'date' columns.`

- [x] `source .venv/bin/activate && MPLCONFIGDIR=/tmp/matplotlib microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public` (attempt 2 after schema fix)
  - Result: pass (run_id=`2026-02-17T01-02-27Z-98beced`).

- [x] `source .venv/bin/activate && MPLCONFIGDIR=/tmp/matplotlib microalpha report --artifact-dir artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public/2026-02-17T01-02-27Z-98beced --summary-out reports/_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public.md`
  - Result: pass (matplotlib `tight_layout` warning only).

- [x] `python3 tools/agentic/validate_runlog.py --run-name 20260217_010106_ticket-37_public-mini-panel-resume-metrics`
  - Result: pass (`OK: /home/codex/repos/microalpha/docs/agent_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics`).

- [x] `source .venv/bin/activate && make check-data-policy`
  - Result: pass (`Data policy check passed. Scanned 1073 files; allowlisted 61.`).

- [x] `source .venv/bin/activate && make test-fast`
  - Result: pass (`All run logs validated successfully.` and `128 passed, 1 skipped, 1 warning`).

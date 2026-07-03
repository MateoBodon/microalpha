# Commands

1. `python3 tools/agentic/runlog_init.py --run-name "20260217_010106_ticket-37_public-mini-panel-resume-metrics" --ticket "ticket-37" --summary "Public mini-panel WFV resume metrics (audit-linked)"`
   - Outcome: created `docs/agent_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics/`.

2. `source .venv/bin/activate && MPLCONFIGDIR=/tmp/matplotlib microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public`
   - Outcome: failed (`ValueError: Universe file must contain at least 'symbol' and 'date' columns.`).

3. `python3` (CSV transform) to rebuild `data/public/universe_public.csv` with required columns from `data/public/meta_public.csv` and `data/public/prices/*.csv`.
   - Outcome: wrote 54 rows with columns: `symbol,date,sector,adv_20,adv_63,adv_126,market_cap_proxy,close`.

4. `source .venv/bin/activate && MPLCONFIGDIR=/tmp/matplotlib microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public`
   - Outcome: pass; produced run `2026-02-17T01-02-27Z-98beced`.

5. `source .venv/bin/activate && MPLCONFIGDIR=/tmp/matplotlib microalpha report --artifact-dir artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public/2026-02-17T01-02-27Z-98beced --summary-out reports/_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public.md`
   - Outcome: pass; report generated (matplotlib `tight_layout` warning only).

6. `sha256sum configs/wfv_flagship_public.yaml data/public/meta_public.csv data/public/universe_public.csv data/public/prices/*.csv`
   - Outcome: recorded config/data hashes for dataset/version provenance.

7. `python3` (artifact writer) to create tracked resume-safe outputs:
   - `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/metrics.json`
   - `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/manifest_excerpt.json`
   - `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/snippet.md`
   - `docs/artifacts/resume/public/resume_line_best.md`

8. Documentation updates:
   - `docs/prompts/20260217_010106_ticket-37_public-mini-panel-resume-metrics.md`
   - `project_state/CURRENT_RESULTS.md`
   - `docs/CODEX_SPRINT_TICKETS.md`
   - `PROGRESS.md`
   - `CHANGELOG.md`

9. Gate commands (recorded in TESTS.md):
   - `python3 tools/agentic/validate_runlog.py --run-name 20260217_010106_ticket-37_public-mini-panel-resume-metrics`
   - `source .venv/bin/activate && make check-data-policy`
   - `source .venv/bin/activate && make test-fast`

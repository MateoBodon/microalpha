# Prompt

TICKET-37 — Reproduce and ship the “public mini-panel” resume metrics (audit-linked).

Goal:
- Reproduce or update the public-data mini-panel resume line using `configs/wfv_flagship_public.yaml` and ship audit-linked run logs + tracked resume-safe artifacts.

Required flow:
1. Initialize run log with `tools/agentic/runlog_init.py`.
2. Run `microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/_local/<RUN_NAME>/wfv_flagship_public`.
3. Run `microalpha report --artifact-dir <BEST_ARTIFACT_DIR> --summary-out reports/_runs/<RUN_NAME>/wfv_flagship_public.md`.
4. Promote tracked outputs to `docs/artifacts/resume/public/<RUN_ID>/`:
   - `metrics.json`
   - `manifest_excerpt.json`
   - `snippet.md`
5. Create/update `docs/artifacts/resume/public/resume_line_best.md` with explicit window label, Sharpe_HAC, MaxDD, CAGR, p-value, run_id, config_path, and dataset/version id when available.
6. Update `project_state/CURRENT_RESULTS.md` with a Public mini-panel subsection pointing to the new artifacts.
7. Run and record in `TESTS.md`:
   - `python3 tools/agentic/validate_runlog.py --run-name <RUN_NAME>`
   - `make check-data-policy`
   - `make test-fast`

Acceptance constraints:
- Keep bulky outputs local-only under `artifacts/_local/` and `reports/_runs/`.
- No raw price panels committed; only resume-safe small aggregates.
- Keep tracking policy/run-log contract compliance.
- If reproduced metrics differ from prior resume claim (`0.46 / 7.9% / 6.7% / p=0.23`), update resume line artifact and document discrepancy in run results.

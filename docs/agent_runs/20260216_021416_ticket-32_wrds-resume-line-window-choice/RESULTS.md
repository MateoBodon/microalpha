# Results

## Summary
- Chose **holdout-only** as the single best-defensible reporting window for resume claims.
- Added tracked snippet: `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/resume_line_holdout.md`.
- Added ticket, prompt capture, and full run-log files for ticket-32.
- Generated GPT review bundle: `artifacts/_local/gpt_bundles/gpt_bundle_20260216_022630_ticket-ticket-32.zip`.

## Window decision (with exact source paths)
Selected window: **holdout-only (2018-01-02 to 2019-12-31)**.

Why this is more defensible than overall WFV OOS for a resume headline:
- The holdout window is explicitly separated from model selection in the run manifest:
  - `artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/manifest.json`
    - `walkforward.selection_window_start/end`: `2013-01-02` to `2017-12-29`
    - `walkforward.holdout_start/end`: `2018-01-02` to `2019-12-31`
- The holdout manifest records selected-model handoff into final evaluation:
  - `artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/holdout_manifest.json`
    - `selected_model` + holdout boundaries.
- Holdout metrics are the untouched final-evaluation outputs:
  - `artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/holdout_metrics.json`
- Overall WFV OOS metrics are still useful diagnostics, but they come from the selection-era WFV aggregate:
  - `artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/metrics.json`

Metric comparison used for the decision:

| Window | Sharpe_HAC | CAGR | MaxDD | Turnover | Trades |
|---|---:|---:|---:|---:|---:|
| overall WFV OOS (`metrics.json`) | 0.2718 | 0.72% | 3.41% | $14.75MM | 64 |
| holdout-only (`holdout_metrics.json`) | 0.1398 | 0.31% | 3.49% | $5.22MM | 26 |

Interpretation:
- The overall WFV OOS numbers are stronger, but they are less conservative for headline claims because that phase drives model selection.
- The holdout-only window is stricter and more leakage-resistant for a single resume line.

## Key outputs
- `docs/artifacts/resume/wrds/2026-01-27T04-47-22Z-31fe553/resume_line_holdout.md`
- `docs/tickets/TICKET-32_wrds_resume_line_pick-the-best-defensible-metric.md`
- `docs/prompts/20260216_021416_ticket-32_wrds-resume-line-window-choice.md`
- `docs/agent_runs/20260216_021416_ticket-32_wrds-resume-line-window-choice/`
- `artifacts/_local/gpt_bundles/gpt_bundle_20260216_022630_ticket-ticket-32.zip`

## Notes
- No backtests were re-run; this ticket is extraction/decision-only from existing artifacts.
- `run_id` and `dataset_id` in the snippet come from:
  - `artifacts/_local/20260127_044219_ticket-28_wrds-dataset-id/wrds_flagship/2026-01-27T04-47-22Z-31fe553/manifest.json` (`run_id`, `wrds.dataset_id`).
- Run-log integrity check passed:
  - `python3 tools/agentic/validate_runlog.py --run-name 20260216_021416_ticket-32_wrds-resume-line-window-choice`

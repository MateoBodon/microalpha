<!--
generated_at: 2026-02-17T01:04:53Z
git_sha: 98beced67a7acfc6b5d9c8d51b2859b1a12dd44f
branch: codex/ticket-36-ship-ticket-35-cleanly
commands:
  - python3 tools/agentic/project_state_refresh.py --zip
-->


# Current Results


## CRSP-v2 pre-holdout research (2026-07-11)

- A single annual quality/value/profitability/investment composite was
  preregistered before return computation using 2005-2022 Compustat annual
  files, historical primary CCM links, a fixed six-month availability lag, and
  the existing 2017-2022 validation panel. Coverage was `1,092` to `1,278`
  complete names per formation month with zero ambiguous CCM rows.
- The QVPI mechanism was structurally valid but failed the frozen economic
  gates: net HAC Sharpe `-0.0234` (t-stat `-0.0462`), CAGR `-0.56%`, max
  drawdown `32.17%`, and total one-way turnover `14.33x`. At 600 bps borrow plus
  2x nonborrow costs, Sharpe was `-0.2782` and CAGR `-2.71%`. It is archived
  without sign, weight, lag, missing-value, or threshold changes.
- Fundamental evidence:
  `docs/artifacts/resume/wrds/2026-07-11T19-06-16Z-fundamental-qvpi/`;
  external result-manifest SHA-256
  `72b378035b736c50f26be8e11bff1f72dc2478365971294694336c9945332fb2`.
- The Compustat source is a current snapshot, not a historical vintage. The
  availability lag protects basic chronology but does not remove later-
  restatement leakage; this result is not true vintage-accounting evidence.
- A pure one-month FF12-industry-residual reversal mechanism was preregistered
  separately from momentum and low volatility. It was structurally valid but
  economically poor after costs: validation HAC Sharpe `-0.4542`, t-stat
  `-1.4131`, CAGR `-3.82%`, max drawdown `23.44%`, and one-way turnover
  `63.27x`. At 600 bps borrow plus 2x nonborrow costs, Sharpe was `-1.0268`
  and CAGR `-8.10%`. It is archived without direction inversion or retuning.
- Reversal evidence:
  `docs/artifacts/resume/wrds/2026-07-11T17-12-35Z-short-term-reversal/`;
  external result-manifest SHA-256
  `573dd7c74bc6e2bcea0ab22bde30efdc1fcfc9b4eef0ec6e7665c800bfe28b02`.
- A separately preregistered one-candidate low-volatility mechanism used
  negative point-in-time trailing 126-session volatility, equal weighting, and
  the unchanged FF12-neutral cost/capacity portfolio. It failed decisively:
  validation HAC Sharpe `-0.0906`, t-stat `-0.1943`, CAGR `-2.20%`, and max
  drawdown `43.83%`. At 600 bps borrow plus 2x nonborrow costs, Sharpe was
  `-0.2553` and CAGR `-4.41%`. The mechanism is archived without retuning.
- Low-volatility evidence:
  `docs/artifacts/resume/wrds/2026-07-11T17-05-10Z-low-volatility/`;
  external result-manifest SHA-256
  `fba7c4f4b4e96f6b310da13103921817db4a04bc910ea451fdd1f79ff8653ad0`.
- Frozen panel: `4ed2b33e2496e224a7701c3d0d71d593909d8fc7547ecdcbc483b2c83686206a`
  covering only permitted data through 2022-12-31.
- Previous six-candidate winner: `blend_12_2_6_2__inverse_vol_126d`;
  validation HAC Sharpe `0.2407`, CAGR `1.70%`, max drawdown `11.42%`.
- Economically distinct preregistered family: three equal-weight
  FF12-industry-residual momentum signals at runner commit `ecb3def0`.
- Best distinct-family candidate: `residual_mom_12_2__equal`; validation HAC
  Sharpe `0.3198` (t-stat `1.2174`), CAGR `2.48%`, max drawdown `9.39%`.
- Decision: archive the family as a validation negative. It improved on the
  previous winner by only `0.0791` Sharpe, below the predeclared `0.10` margin;
  it also trailed identical-universe classic momentum (`0.3260`) and produced
  CAGR `-0.20%` at the harsh `600 bps` borrow plus `2x` nonborrow-cost stress.
- Evidence: `docs/artifacts/resume/wrds/2026-07-11T16-22-00Z-distinct-residual-family/`;
  external result-manifest SHA-256
  `9e3a8818211a9ef9c81816bb2fadf6165636cc9a344f9284698adec3499ef107`.
- The 2023-2025 final holdout was not opened in any of these campaigns. No
  alpha or promotion claim is supported.


## Sample bundle (README + artifacts)

- Run: `artifacts/sample_flagship/2025-10-30T18-39-31Z-a4ab8e7`
- Sharpe (HAC): -0.66
- MAR (Calmar): -0.41
- Max DD: 17.26%
- RealityCheck p-value: 0.861
- Turnover: $1,211,971.84

- Walk-forward: `artifacts/sample_wfv/2025-10-30T18-39-47Z-a4ab8e7`
- Sharpe (HAC): 0.22
- MAR (Calmar): 0.03
- Max DD: 34.79%
- RealityCheck p-value: 1.000
- Turnover: $28,525,695.10

- Holdout WFV: `artifacts/sample_wfv_holdout/2025-12-22T00-40-53Z-99a072e`
- Holdout Sharpe (HAC): 1.29
- Holdout MAR (Calmar): 4.03
- Holdout Max DD: 9.36%
- Holdout Turnover: $5,417,903.30


## Public mini-panel (resume artifact-backed)

- Latest run: `2026-02-17T01-02-27Z-98beced`
- Window: WFV OOS (`2024-01-02` to `2024-01-12`)
- Snapshot:
  - Sharpe_HAC: 0.000
  - Max Drawdown: 0.00%
  - CAGR: 0.00%
  - Reality Check p-value: 1.000
  - Trades: 0 (degenerate run)
- Canonical resume line: `docs/artifacts/resume/public/resume_line_best.md`
- Resume artifact directory: `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/`
- Config: `configs/wfv_flagship_public.yaml`
- Dataset ID: `public_mini_panel_repo_36b421820251`
- Local report: `reports/_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public.md`


## WRDS results (docs/results_wrds.md)

- Latest run: 2026-02-16T22-33-46Z-8d90621
- Snapshot (overall WFV OOS):
  - Sharpe_HAC: 0.24
  - MAR: 0.14
  - Max Drawdown: 5.32%
  - Turnover: $15.66MM
  - Reality Check p-value: 0.889
- Holdout snapshot (resume rule window 2018-01-02 to 2019-12-31):
  - Sharpe_HAC: 0.588
  - MAR: 0.64
  - Max Drawdown: 1.38%
  - Turnover: $6.12MM
  - Trades: 31
  - Reality Check p-value: 0.941
  - SPA p-value: n/a
- Dataset ID: `wrds_crsp_export_20251221_v1`
- Report: `reports/_runs/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship.md`
- Resume summary: `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/`
- Real-data leaderboard (artifact scan; no rerun): `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`
- Best resume line (window=holdout-only, pre-registered holdout Sharpe rule): `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md`


## WRDS smoke (docs/results_wrds_smoke.md)

- Latest run: 2025-12-24T05-15-43Z-559a99e
- Snapshot:
  - Sharpe_HAC: 0.00
  - MAR: 0.00
  - Max Drawdown: 0.07%
  - Turnover: $434.24K
  - Reality Check p-value: 1.000
  - SPA p-value: n/a
- Report: `reports/summaries/wrds_flagship_smoke.md`
- Note: Smoke run validates WRDS pipeline wiring; metrics are not interpretable for performance.


## Latest progress (PROGRESS.md)

- Date: 2026-02-17
- ### Done
- - Ticket-37: reproduced the canonical public mini-panel WFV run and promoted audit-linked resume-safe artifacts under `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/`; run is explicitly marked degenerate (`0` trades). Run log: `docs/agent_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics/`.
- - Ticket-35: ran a pre-registered 9-combo WRDS micro-sweep and promoted run `2026-02-16T22-33-46Z-8d90621` as the new best provenance-complete holdout resume line (Sharpe_HAC 0.588, MaxDD 1.38%, 31 trades). Run log: `docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/`.
- - Ticket-36: shipped ticket-35 deliverables as tracked files, fixed ticket-36 run-log schema to unblock validation gates, and prepared clean-bundle regeneration evidence. Run log: `docs/agent_runs/20260216_232907_ticket-ticket-36/`.


## Recent run logs (docs/agent_runs, last 3)

- `20260217_010106_ticket-37_public-mini-panel-resume-metrics` — Ran the canonical public mini-panel WFV config, generated local report artifacts, and promoted tracked resume-safe public metrics/snippet artifacts for run `2026-02-17T01-02-27Z-98beced` (degenerate: 0 trades). (docs/agent_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics/RESULTS.md)
- `20260216_232907_ticket-ticket-36` — Shipped ticket-35 deliverables into tracked state, repaired run-log schema debt for ticket-36, and prepared clean-bundle regeneration with explicit gate runs. (docs/agent_runs/20260216_232907_ticket-ticket-36/RESULTS.md)
- `20260216_223228_ticket-35_wrds-micro-sweep` — Executed pre-registered WRDS sweep (`<=12` combos), generated local WRDS report, and promoted run `2026-02-16T22-33-46Z-8d90621` as the top eligible holdout resume row. (docs/agent_runs/20260216_223228_ticket-35_wrds-micro-sweep/RESULTS.md)


Sources: `README.md`, `PROGRESS.md`, `docs/results_wrds.md`, `docs/results_wrds_smoke.md`, sample metrics under `artifacts/sample_flagship/`, `artifacts/sample_wfv/`, `artifacts/sample_wfv_holdout/`, and recent `docs/agent_runs/*/RESULTS.md`.

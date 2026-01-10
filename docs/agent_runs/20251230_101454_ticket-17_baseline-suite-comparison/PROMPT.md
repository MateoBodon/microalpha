TICKET: ticket-17
RUN_NAME: YYYYMMDD_HHMMSS_ticket-17_baseline-suite-comparison
BRANCH: codex/ticket-17-baseline-suite-comparison

You are Codex operating inside the microalpha repo.

Hard requirements (binding):
- Follow AGENTS.md stop-the-line rules.
- Follow docs/DOCS_AND_LOGGING_SYSTEM.md exactly: create a run log under docs/agent_runs/<RUN_NAME>/ with PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json.
- Do NOT write a long upfront plan. Inspect → implement → test → document → bundle.
- Do NOT fabricate metrics. If you didn’t run it, don’t claim it.
- Data policy: do NOT commit raw WRDS data. Only commit license-safe summaries/plots/tables.
- Tests: must run `make test-fast` minimum and record outputs in TESTS.md.
- Finish by generating a bundle:
  `make gpt-bundle TICKET=ticket-17 RUN_NAME=<RUN_NAME>`
  and record the bundle path in RESULTS.md.

Ticket goal (what to build):
Implement a baseline suite and baseline comparison reporting so that every “headline” run can be contextualized without cherry-picking:
- Equal-weight universe portfolio (monthly rebalance)
- Market proxy (CRSP value-weighted if available; otherwise explicit documented fallback)
- Naive 12–1 momentum baseline (monthly rebalance; equal-weight top decile long, bottom decile short OR long-only if shorts unavailable — choose ONE default and document it)
- Cash / risk-free baseline (RF series if available; else 0 with explicit label)

Acceptance criteria (objective; must satisfy all):
1) Baselines are computed on the SAME calendar + universe rules as the evaluated run.
2) Baselines are saved in the artifact dir in a single file with a stable schema:
   - `artifacts/<run_id>/baselines.csv` with columns:
     `date, flagship_net, eqw_universe, market_proxy, mom_12_1, cash_rf`
   (If flagship series isn’t available in the same place, adjust names but keep one row per date + a README in the artifact dir.)
3) Reports include a baseline comparison section:
   - table with Sharpe_HAC, MaxDD, CAGR, turnover (where applicable)
   - a single overlay plot (flagship vs baselines cumulative)
   - clear label if any baseline is unavailable (“missing market proxy: <reason>”)
4) Tests:
   - synthetic test that would FAIL if the baseline uses future returns (lookahead), e.g. formation window bug
   - deterministic test that baselines.csv schema and ordering is stable
5) Run log complete and `make test-fast` passes.
6) Produce at least one baseline-enabled report on the bundled sample artifacts (no WRDS required).
7) If WRDS_DATA_ROOT is available: run a WRDS *smoke* baseline-enabled report (do not commit raw data; commit only license-safe report output if allowed).

Do this in order (no long pre-plan):

0) Setup + required logging
- Create branch:
  git checkout -b codex/ticket-17-baseline-suite-comparison
- Choose RUN_NAME in UTC: YYYYMMDD_HHMMSS_ticket-17_baseline-suite-comparison
- Create run log dir:
  mkdir -p docs/agent_runs/<RUN_NAME>/
- Write this prompt verbatim to:
  - docs/agent_runs/<RUN_NAME>/PROMPT.md
  - docs/prompts/<RUN_NAME>_ticket-17_baseline-suite-comparison.md
- Start docs/agent_runs/<RUN_NAME>/COMMANDS.md and append every command you run, in order.

IMPORTANT: ticket-id enforcement exists. Before running tests, ensure ticket-17 exists in docs/CODEX_SPRINT_TICKETS.md.
- If ticket-17 is not present, add a new section at the bottom:
  - ticket-17 title + goal + acceptance criteria + minimal commands
  - keep it consistent with PLAN_OF_RECORD baselines
- Commit that early if needed.

1) Inspect repo: find the best integration point
- Identify where the report currently gets the flagship return series:
  - likely from `artifacts/<run_id>/equity_curve.csv` or similar.
- Identify what data is available in artifacts to compute baselines:
  - do we have per-asset returns, universe membership, market caps, etc?
- Identify whether a market proxy already exists (e.g., exported CRSP vwretd series).
- Decide the minimal correct path:
  A) compute baselines during the run and write baselines.csv into artifacts, OR
  B) compute baselines during report generation using available artifact data.
Prefer the smallest change that guarantees “same calendar + same universe rules”.

2) Implement baseline computation
- Add a module like:
  - `src/microalpha/reporting/baselines.py`
  containing:
  - `compute_baselines(artifact_dir: Path, *, ...) -> pd.DataFrame`
  Requirements:
  - explicit month-end rebalance logic (no implicit resampling)
  - momentum formation window uses only returns strictly before formation date (no leakage)
  - outputs a DataFrame indexed by date, then written to CSV with stable column order
  - if a baseline cannot be computed, write the column but fill with NaN and record a `baselines_status.json` explaining why.

3) Wire baselines into reporting
- Update the main report generator (likely `src/microalpha/reporting/summary.py`) to:
  - call baseline computation (or load baselines.csv if already present)
  - render:
    - “Baselines” table (flagship vs baselines)
    - overlay plot saved under the report output dir
  - ensure the report links back to `artifacts/<run_id>/baselines.csv`

4) Tests (synthetic; no WRDS)
- Add tests e.g. `tests/test_baselines.py`:
  - build a tiny synthetic panel where momentum is obvious
  - assert baseline uses only past returns:
    - create a case where using future returns would flip the ranking and detect it
  - assert output schema and deterministic ordering

5) Generate artifacts/reports (minimum)
- Run `make test-fast` and record results.
- Generate a baseline-enabled sample report:
  - use existing Make targets (`make report` / `make report-wfv`) or CLI.
  - ensure a report file is updated/created under `reports/summaries/` and references baselines.csv.
- If WRDS_DATA_ROOT is set and WRDS smoke targets exist:
  - run the smallest WRDS smoke report command
  - record commands + resulting artifact dir path in RESULTS.md
  - do NOT commit raw WRDS data or huge artifacts

6) Documentation updates (required)
- Update `PROGRESS.md` with ticket-17 status + run log link.
- Update `docs/PLAN_OF_RECORD.md` only if baseline definitions differ from what’s implemented (prefer making code match the doc).
- If you add/rename artifact fields: update `project_state/CONFIG_REFERENCE.md` / `project_state/CURRENT_RESULTS.md` only if headline reporting changed.

7) Commits (required)
- Small logical commits only.
- Commit message starts with `ticket-17: ...`
- Commit body includes:
  - Tests: ...
  - Artifacts: ...
  - Docs: ...

8) Finish (mandatory)
- Create bundle and record its path in RESULTS.md:
  make gpt-bundle TICKET=ticket-17 RUN_NAME=<RUN_NAME>
- Ensure run log is complete and `make test-fast` is green.
- Do NOT merge unless the human explicitly instructs you to merge.
- If the human instructs a merge, merge and then generate a post-merge bundle and record it too.

TICKET: ticket-03
RUN_NAME: YYYYMMDD_HHMMSS_ticket-03_factor-regression-alignment
BRANCH: codex/ticket-03-factor-regression-alignment

You are Codex working in the microalpha repo. Follow AGENTS.md and docs/DOCS_AND_LOGGING_SYSTEM.md as binding.
Do NOT write a long upfront plan. Inspect → implement → test → document → bundle.

Goal:
- Make factor regression frequency-safe and alignment-safe (no silent index drift, no accidental forward-fill leakage).
- Document and surface the *true* factor frequency used (daily/weekly/monthly) in reports and run artifacts.

Acceptance criteria (objective):
1) Regression utility detects and enforces alignment:
   - If factor index and return index cannot be aligned without changing frequency, it must:
     - either raise a clear error, OR
     - perform an explicit, documented resample step (no implicit magic).
   - It must record: factor frequency, return frequency, overlap start/end, n_obs.
2) Tests:
   - A test FAILS if factor and return indexes are misaligned (e.g., shifted dates) or if sample length changes silently.
   - A test FAILS if an implementation tries to forward-fill factor data onto returns (explicitly disallow).
3) Reporting:
   - The factor regression section/table in the report includes the declared frequency and n_obs.
4) `make test-fast` passes.
5) Run log + bundle created per docs system.

Work steps (do these, in order):

0) Setup (required)
- Create feature branch:
  git checkout -b codex/ticket-03-factor-regression-alignment
- Set RUN_NAME with UTC timestamp and create run log dir:
  mkdir -p docs/agent_runs/<RUN_NAME>/
- Save this exact prompt verbatim to:
  - docs/prompts/<RUN_NAME>_ticket-03_factor-regression-alignment.md
  - docs/agent_runs/<RUN_NAME>/PROMPT.md
- Initialize COMMANDS.md/RESULTS.md/TESTS.md/META.json in the run log dir.

1) Inspect current factor regression pipeline (fast)
- Read:
  - reports/factors_ff.py
  - src/microalpha/reporting/summary.py (where factor regression is computed/printed)
  - tests/test_reporting_analytics.py (or any existing reporting tests)
- Identify:
  - where factor data is loaded from (repo data/factors/ vs fetched)
  - the factor frequency actually present (daily/monthly)
  - how returns series is built (daily net returns on holdout)

2) Implement alignment + frequency handling (minimal, explicit)
- Add a helper in reports/factors_ff.py (or the existing factor module) that:
  - infers frequency from a DatetimeIndex robustly:
    - prefer pandas.infer_freq; fallback to median timedelta bucket
  - validates monotonic increasing indexes
- Add an alignment function, e.g.:
  align_factor_panel(returns: pd.Series, factors: pd.DataFrame, *, allow_resample: bool, resample_rule: Optional[str]) -> (aligned_returns, aligned_factors, meta)
  Requirements:
  - default is strict: if frequencies differ, raise with a message like:
    “returns are daily, factors are monthly; set allow_resample=True with rule='M' (or use daily factors)”
  - if allow_resample is enabled:
    - resample returns to factor frequency explicitly using a documented method:
      - use compounded returns: (1+r).prod()-1 per period (NOT sum unless using log-returns explicitly)
    - NEVER forward-fill factors to match returns
  - meta must include:
    - returns_freq, factors_freq
    - overlap_start/end
    - n_obs used
- Ensure any report table prints meta (freq + n_obs) next to alpha/t-stat.

3) Tests (required)
- Add tests (extend tests/test_reporting_analytics.py or new tests/test_factor_alignment.py):
  A) misaligned index test:
     - daily returns with dates shifted by 1 day vs factors -> must raise
  B) frequency mismatch test:
     - daily returns vs monthly factors -> must raise by default
     - if allow_resample=True, must succeed and n_obs must equal number of factor periods
  C) forward-fill disallow test:
     - ensure code path does not use ffill to align (assert via explicit check or by designing case where ffill would “make it pass” and ensure it still fails)
- Keep tests synthetic; no WRDS dependency.

4) Minimal runs (required)
- Run tests:
  - make test-fast
- Run a minimal report generation on sample artifacts (no WRDS required):
  - use the smallest existing make target / command that generates a summary and includes factor regression output
  - if no target exists, run the report module directly on an existing sample artifact dir and document the command.
- Record all commands in COMMANDS.md and summarize in TESTS.md / RESULTS.md.

5) Docs updates (required)
- Update PROGRESS.md (ticket-03 entry + run log path).
- Update docs that mention factor frequency (PLAN_OF_RECORD may already mention FF5+Mom daily; if actual data is monthly, document the reality and the chosen protocol).
- If you discover a real mismatch bug, update project_state/KNOWN_ISSUES.md.

6) Run log completion (required)
- Fill docs/agent_runs/<RUN_NAME>/RESULTS.md with:
  - what changed
  - how alignment is enforced
  - what frequency is used and where it comes from
  - any behavior changes in report output
- Fill META.json with:
  - git_sha_before/after (real SHAs)
  - dataset_id (e.g., “repo_factor_sample”)
  - report_paths (if generated)

7) Commits (required)
- Make small logical commits on the feature branch.
- Each commit message must start with: “ticket-03: …”
- Commit body must include:
  - Tests: …
  - Artifacts: …
  - Docs: …

8) Finish (required)
- If the human instructs you to merge after review, do so; otherwise do NOT merge.
- Always generate a bundle and record its path in RESULTS.md:
  make gpt-bundle TICKET=ticket-03 RUN_NAME=<RUN_NAME>

Suggested Codex invocations (human chooses):
- Safer approvals: codex --sandbox workspace-write --ask-for-approval on-request
- More autonomous: codex --full-auto
Avoid bypassing approvals/sandbox unless explicitly instructed and in a dedicated sandbox VM.

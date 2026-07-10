# Risk Register

last_updated: 2026-07-03
updated_by: GPT-5.5 Pro Extended
source_event: Pro strategy package after T-000

| Severity | Risk | Mitigation | Owner | Escalation Trigger |
|---|---|---|---|---|
| Critical | Raw WRDS/CRSP data exposure | Keep raw exports local-only; run data-policy check; promote only safe summaries | Codex/Heavy | Any restricted raw file staged, copied, or bundled |
| Critical | Leakage or survivorship bias | Preserve chronology/t+1 tests; require point-in-time universe evidence | Codex/Heavy | Failed leakage test or suspicious data join/fill timing |
| Critical | Unsupported public performance claims | Require artifact/evidence path for every claim; L4 before public use | Pro/Heavy | README/resume/doc claim lacks evidence |
| High | Post-transfer data/artifact loss | Create data/artifact inventory and exact missing-data request | Heavy/Codex/User | Current WRDS baseline cannot run |
| High | Overfitting from ambitious sweeps | Pre-register search space and final evaluation rule | Pro/Heavy | Campaign tunes repeatedly on final holdout |
| High | Existing 2018-2019 holdout no longer pristine | Treat as historical evidence; prefer expanded data/fresh final holdout | Pro/Heavy | New claim calls old holdout pristine |
| High | Wrong checkout imported during tests | Fix Makefile/env or verify import path in run logs | Codex/Heavy | Bare fast gate imports another checkout |
| High | Exact current results missing from audit bundle | T-001 must inspect actual current result artifacts | Heavy/Codex | Artifact contents contradict bundle summary |
| Medium | Stale docs confuse future sessions | Keep canonical docs explicit; clean old docs only when claim-relevant | Heavy/Codex | Old docs contradict active strategy |
| Medium | MkDocs warnings hide stale claim surfaces | Defer broad cleanup but fix claim-relevant links before release | Codex | Warning affects current/public result page |
| Medium | Process drag | Keep docs compact and ticket-enabling | Pro/Heavy | Sprint produces mostly meta-docs |
| Medium | Public mini-panel weakens presentation | Label as pipeline-only; later build non-degenerate public benchmark | Heavy/Codex | Public docs imply alpha evidence |

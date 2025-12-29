# Results

## Summary
- Repaired legacy run-log META.json files to satisfy the required schema and valid JSON.
- Added a run-log validator script and Make target; `make test-fast` now runs the validator.

## META.json files repaired
- `docs/agent_runs/2025-12-20T21-31-14Z_project_state_rebuild/META.json`
- `docs/agent_runs/20251220_223500_ticket-01_wrds-tighten-caps/META.json`
- `docs/agent_runs/20251221_154039_ticket-02_holdout-wfv/META.json`
- `docs/agent_runs/20251221_162711_ticket-02_holdout-wfv-wrds/META.json`
- `docs/agent_runs/20251221_173223_ticket-02_holdout-wfv-wrds-full/META.json`
- `docs/agent_runs/20251221_175417_ticket-02_holdout-wfv-wrds-report/META.json`
- `docs/agent_runs/20251221_190000_ticket-06_bundle-commit-consistency/META.json`
- `docs/agent_runs/20251222_001500_ticket-07_ticket-02-evidence-and-bundle-fix/META.json`
- `docs/agent_runs/20251222_013000_ticket-08_unblock-wrds-report-spa/META.json`
- `docs/agent_runs/20251222_034500_ticket-09_ticket-id-enforcement/META.json`
- `docs/agent_runs/20251222_051500_ticket-10_block-placeholder-runlogs/META.json`
- `docs/agent_runs/20251222_123806_ticket-11_data-policy-guardrails/META.json`
- `docs/agent_runs/20251222_191759_ticket-00_project_state_rebuild/META.json`
- `docs/agent_runs/20251224_051508_ticket-04_wrds-smoke-check/META.json`

## Validator enforcement
- Required run-log files exist per run directory.
- META.json parses and includes the required keys.
- `run_name` matches the run directory name.
- `ticket_id` matches `ticket-XX` and exists in `docs/CODEX_SPRINT_TICKETS.md`.
- `git_sha_before`/`git_sha_after` are 40-hex SHAs.
- `started_at_utc`/`finished_at_utc` and `dataset_id` are present as strings.
- `config_paths`, `artifact_paths`, `report_paths`, and `web_sources` are typed as lists; `config_sha256` is a dict.

## Known limitations
- The validator does not enforce timestamp formatting beyond string type.
- It does not verify that listed paths exist or that `config_sha256` matches file contents.

## Bundle
- Bundle: `docs/gpt_bundles/2025-12-29T12-00-05Z_ticket-16_20251229_105919_ticket-16_runlog-json-integrity.zip`

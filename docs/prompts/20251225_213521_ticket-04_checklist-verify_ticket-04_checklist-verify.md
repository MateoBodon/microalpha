good work, go through this checklist, make sure everythiG is complete, when it is, commit, merge to main, push to oirign, and tell me which
  ticket to upload for reviewConfirm ticket-04 branch exists and commits are small + have “Tests/Artifacts/Docs” in commit bodies.

Run locally:

make test-fast

pytest -q tests/test_no_lookahead.py

Validate behavior:

A future-dated (or otherwise invalid) signal hard-errors.

Unsafe execution requires explicit opt-in and produces:

manifest.json with unsafe_execution: true + reason

report summary with an obvious “UNSAFE / NOT LEAKAGE-SAFE” banner

Check diff for data-policy violations:

no raw WRDS exports; only derived metrics/plots.

Verify run log completeness:

docs/agent_runs/<RUN_NAME>/{PROMPT,COMMANDS,RESULTS,TESTS,META}.(md|json) exists

META.json contains real before/after SHAs (not “HEAD”)

Ensure make gpt-bundle TICKET=ticket-04 RUN_NAME=<RUN_NAME> exists and path is recorded in RESULTS.md.

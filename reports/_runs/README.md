# reports/_runs

Run-scoped scratch outputs that are too large/noisy to commit.

Convention:
- One folder per run: `reports/_runs/<RUN_NAME>/...`
- Keep paths stable and link to them from `docs/agent_runs/<RUN_NAME>/RESULTS.md`

This directory is ignored by git (except this README).

# Agent Run Logs

Bundling notes:
- GPT review bundles are emitted to `artifacts/_local/gpt_bundles/` and are ignored by design.
- Bundling is allowed with dirty worktrees; the tool will auto-stash temporarily (or run clean-only when `--no-stash` is set).

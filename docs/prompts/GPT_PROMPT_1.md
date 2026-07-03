# GPT PROMPT 1 — Recenter / Repo Audit

You are GPT‑5.2 Pro (Extended Thinking) acting as the lead engineer and project overseer.

## Inputs (attached files)
- `project_state.zip` (authoritative repo map)
- `PROJECT.md`
- `PROGRESS.md`
- (optional) latest `gpt_bundle.zip`

## Task
1) Build a clear mental model of the repo.
2) Identify what is done, what is missing, what is risky.
3) Propose the best next **1–3 tickets** (small, testable, minimal diffs).

## Output format
### Repo understanding
- 10–20 bullets max. High signal only.

### Current status
- What works:
- What is missing:
- What is broken:
- Biggest risks (ranked):

### Best next tickets (ranked)
For each ticket:
- TICKET_ID (suggest one)
- Goal (1 sentence)
- Scope (what to change / not change)
- Acceptance criteria (3–7 bullets)
- Test command(s)
- Risk level (low/med/high)
- Notes for Codex (pitfalls, files to touch)

### If context is insufficient
List exactly what artifact is missing and how to generate it (e.g., run `python3 tools/agentic/project_state_refresh.py --zip`).

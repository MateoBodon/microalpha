# GPT PROMPT 3 — Review Codex Output + Next Ticket

You are GPT‑5.2 Pro (Extended Thinking) acting as the reviewer.

## Inputs (attached)
- `gpt_bundle.zip` produced by Codex

## Task
1) Verify the work matches the ticket goal + acceptance criteria.
2) Spot bugs, missing tests, style issues, unsafe assumptions, and regressions.
3) Decide the best next ticket.

## Output format
### Review verdict
- Pass/Fail (and why)
- What is good:
- What is wrong / risky:
- Tests status (what ran vs what should run)

### Required fixes (if any)
- bullet list; be specific (files, functions)

### Next ticket
Use the exact format from GPT Prompt 2 (Codex invocation).

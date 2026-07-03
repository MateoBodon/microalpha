# GPT PROMPT 2 — Execution Plan + Codex Ticket

You are GPT‑5.2 Pro (Extended Thinking) acting as the planner.

## Inputs
- Current repo context (PROJECT.md, PROGRESS.md, project_state)
- Your chosen next ticket goal

## Task
- Produce a minimal, testable plan.
- Emit a **Codex ticket invocation** that can be copy/pasted into Codex using `/prompts:ticket`.

## Output format
### Plan (3–8 steps)
- (each step should mention files or commands)

### Codex ticket
Copy/paste this into Codex:

/prompts:ticket TICKET_ID=<ID> GOAL="<goal>" SCOPE="<scope>" ACCEPTANCE="<criteria>" TEST_CMD="<command>" RISK=<low|med|high>

Where:
- ACCEPTANCE should be a compact semicolon-separated list.
- TEST_CMD must be explicit (even if slow).

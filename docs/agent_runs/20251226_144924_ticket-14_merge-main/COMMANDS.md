# Commands

1. `date "+%Y%m%d_%H%M%S"`
2. `mkdir -p docs/agent_runs/20251226_144924_ticket-14_merge-main`
3. `cat > docs/prompts/20251226_144924_ticket-14_merge-main.md <<'EOF' ... EOF`
4. `cat > docs/agent_runs/20251226_144924_ticket-14_merge-main/PROMPT.md <<'EOF' ... EOF`
5. `ls -l docs/gpt_bundles/2025-12-26T17-54-40Z_ticket-14_20251226_122058_ticket-14_wrds-full-run.zip`
6. `git fetch origin`
7. `git checkout main`
8. `git merge codex/ticket-14-order-flow-trace`
9. `git push origin main`
10. `git rev-parse HEAD`
11. `git rev-parse origin/main`
12. `date -u "+%Y-%m-%dT%H:%M:%SZ"`
13. `cat > docs/agent_runs/20251226_144924_ticket-14_merge-main/TESTS.md <<'EOF' ... EOF`
14. `cat > docs/agent_runs/20251226_144924_ticket-14_merge-main/RESULTS.md <<'EOF' ... EOF`
15. `cat > docs/agent_runs/20251226_144924_ticket-14_merge-main/META.json <<'EOF' ... EOF`
16. `git add -f docs/agent_runs/20251226_144924_ticket-14_merge-main/COMMANDS.md docs/agent_runs/20251226_144924_ticket-14_merge-main/PROMPT.md docs/agent_runs/20251226_144924_ticket-14_merge-main/RESULTS.md docs/agent_runs/20251226_144924_ticket-14_merge-main/TESTS.md docs/agent_runs/20251226_144924_ticket-14_merge-main/META.json docs/prompts/20251226_144924_ticket-14_merge-main.md` (failed: missing prompt path)
17. `ls -1 docs/prompts | rg '20251226_144924'`
18. `git add -f docs/agent_runs/20251226_144924_ticket-14_merge-main/COMMANDS.md docs/agent_runs/20251226_144924_ticket-14_merge-main/PROMPT.md docs/agent_runs/20251226_144924_ticket-14_merge-main/RESULTS.md docs/agent_runs/20251226_144924_ticket-14_merge-main/TESTS.md docs/agent_runs/20251226_144924_ticket-14_merge-main/META.json docs/prompts/20251226_144924_ticket-14_merge-main_ticket-14_merge-main.md`
19. `git status -sb`
20. `git commit -m "ticket-14: log merge to main" -m "Tests: not run (merge-only log)" -m "Artifacts: none" -m "Docs: docs/agent_runs/20251226_144924_ticket-14_merge-main/"`
21. `git push origin main`
22. `git rev-parse HEAD`
23. `git rev-parse origin/main`
24. `apply_patch` (update docs/agent_runs/20251226_144924_ticket-14_merge-main/META.json finished_at_utc + git_sha_after)
25. `git add -f docs/agent_runs/20251226_144924_ticket-14_merge-main/COMMANDS.md docs/agent_runs/20251226_144924_ticket-14_merge-main/META.json`
26. `git commit -m "ticket-14: update merge run log" -m "Tests: not run (merge-only log)" -m "Artifacts: none" -m "Docs: docs/agent_runs/20251226_144924_ticket-14_merge-main/"`
27. `git push origin main`
28. `git rev-parse HEAD`
29. `git rev-parse origin/main`
30. `git status -sb`

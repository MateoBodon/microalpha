# Commands

1. `git status -sb`
2. `rg -n "direct commits to `main`|main" AGENTS.md`
3. `date -u +%Y%m%d_%H%M%S`
4. `git log -n 3 --format=fuller -- AGENTS.md`
5. `mkdir -p docs/agent_runs/20251225_220947_ticket-04_merge-main`
6. `cat <<'EOF' | tee docs/prompts/20251225_220947_ticket-04_merge-main_ticket-04_merge-main.md docs/agent_runs/20251225_220947_ticket-04_merge-main/PROMPT.md`
7. `cat <<'EOF' > docs/agent_runs/20251225_220947_ticket-04_merge-main/TESTS.md`
8. `git rev-parse HEAD`
9. `git fetch origin`
10. `git log --oneline origin/main..codex/ticket-04-leakage-tests-unsafe-manifest | head`
11. `git log --oneline codex/ticket-04-leakage-tests-unsafe-manifest..origin/main | head`
12. `git switch main`
13. `git pull origin main`
14. `git merge --ff-only codex/ticket-04-leakage-tests-unsafe-manifest`
15. `git switch codex/ticket-04-leakage-tests-unsafe-manifest`
16. `apply_patch <<'PATCH'` (PROGRESS.md update)
17. `git status -sb`
18. `git stash push -m "ticket-04 merge run log" PROGRESS.md`
19. `git switch main`
20. `git push origin main`
21. `git switch codex/ticket-04-leakage-tests-unsafe-manifest`
22. `git stash pop`
23. `date -u +%Y-%m-%dT%H:%M:%SZ`
24. `cat <<'EOF' > docs/agent_runs/20251225_220947_ticket-04_merge-main/RESULTS.md`
25. `cat <<'EOF' > docs/agent_runs/20251225_220947_ticket-04_merge-main/META.json`
26. `cat <<'EOF' > docs/agent_runs/20251225_220947_ticket-04_merge-main/COMMANDS.md`
27. `git add -f docs/agent_runs/20251225_220947_ticket-04_merge-main docs/prompts/20251225_220947_ticket-04_merge-main_ticket-04_merge-main.md PROGRESS.md`
28. `git status -sb`
29. `git commit -m "ticket-04: merge main run log" -m "Tests: not run (merge + docs only)" -m "Artifacts: none" -m "Docs: PROGRESS.md, docs/agent_runs/20251225_220947_ticket-04_merge-main/, docs/prompts/20251225_220947_ticket-04_merge-main_ticket-04_merge-main.md"`
30. `git switch main`
31. `git merge --ff-only codex/ticket-04-leakage-tests-unsafe-manifest`
32. `git push origin main`
33. `git push origin codex/ticket-04-leakage-tests-unsafe-manifest`

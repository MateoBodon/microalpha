# Commands

1. `git status -sb`
2. `git log -n 8 --format=fuller`
3. `make test-fast`
4. `pytest -q tests/test_no_lookahead.py`
5. `ls -t artifacts/mm_lob_same_tick | head -1`
6. `python - <<'PY'`
   ```
   import json
   from pathlib import Path
   run_id = '2025-12-23T22-00-05Z-ba5b480'
   path = Path('artifacts/mm_lob_same_tick')/run_id/'manifest.json'
   with path.open() as f:
       data = json.load(f)
   print('manifest_path', path)
   print('unsafe_execution', data.get('unsafe_execution'))
   print('unsafe_reasons', data.get('unsafe_reasons'))
   print('execution_alignment', data.get('execution_alignment'))
   PY
   ```
7. `python3 - <<'PY'`
   ```
   import json
   from pathlib import Path
   run_id = '2025-12-23T22-00-05Z-ba5b480'
   path = Path('artifacts/mm_lob_same_tick')/run_id/'manifest.json'
   with path.open() as f:
       data = json.load(f)
   print('manifest_path', path)
   print('unsafe_execution', data.get('unsafe_execution'))
   print('unsafe_reasons', data.get('unsafe_reasons'))
   print('execution_alignment', data.get('execution_alignment'))
   PY
   ```
8. `rg -n "UNSAFE / NOT LEAKAGE-SAFE" reports/summaries/_artifacts/mm_lob_same_tick.md`
9. `git diff --name-only main...HEAD`
10. `sed -n '1,220p' docs/DOCS_AND_LOGGING_SYSTEM.md`
11. `date -u +%Y%m%d_%H%M%S`
12. `git rev-parse HEAD`
13. `mkdir -p docs/agent_runs/20251225_213521_ticket-04_checklist-verify`
14. `cat <<'EOF' | tee docs/prompts/20251225_213521_ticket-04_checklist-verify_ticket-04_checklist-verify.md docs/agent_runs/20251225_213521_ticket-04_checklist-verify/PROMPT.md`
15. `ls docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest`
16. `ls docs/agent_runs/20251224_051508_ticket-04_wrds-smoke-check`
17. `rg -n "HEAD" docs/agent_runs/20251223_214840_ticket-04_leakage-tests-unsafe-manifest/META.json docs/agent_runs/20251224_051508_ticket-04_wrds-smoke-check/META.json`
18. `sw_vers -productVersion`
19. `python3 --version`
20. `shasum -a 256 configs/mm_lob_same_tick.yaml`
21. `tail -n 20 PROGRESS.md`
22. `rg -n "gpt-bundle" -S .`
23. `sed -n '1,240p' tools/gpt_bundle.py`
24. `rg -n "BUNDLE_TIMESTAMP|bundle" tools/gpt_bundle.py`
25. `sed -n '240,340p' tools/gpt_bundle.py`
26. `date -u +%Y-%m-%dT%H-%M-%SZ`
27. `cat <<'EOF' > docs/agent_runs/20251225_213521_ticket-04_checklist-verify/TESTS.md`
28. `cat <<'EOF' > docs/agent_runs/20251225_213521_ticket-04_checklist-verify/RESULTS.md`
29. `apply_patch <<'PATCH'` (PROGRESS.md update)
30. `date -u +%Y-%m-%dT%H:%M:%SZ`
31. `cat <<'EOF' > docs/agent_runs/20251225_213521_ticket-04_checklist-verify/META.json`
32. `git status -sb`
33. `git status --porcelain`
34. `git config --get status.showUntrackedFiles`
35. `rg -n "agent_runs" -S .gitignore`
36. `git ls-files docs/agent_runs/20251225_213521_ticket-04_checklist-verify`
37. `git check-ignore -v docs/agent_runs/20251225_213521_ticket-04_checklist-verify/PROMPT.md docs/prompts/20251225_213521_ticket-04_checklist-verify_ticket-04_checklist-verify.md`
38. `cat docs/agent_runs/20251224_051508_ticket-04_wrds-smoke-check/META.json`
39. `cat <<'EOF' > docs/agent_runs/20251225_213521_ticket-04_checklist-verify/COMMANDS.md`
40. `git add -f docs/agent_runs/20251225_213521_ticket-04_checklist-verify docs/prompts/20251225_213521_ticket-04_checklist-verify_ticket-04_checklist-verify.md PROGRESS.md`
41. `git status -sb`
42. `git commit -m "ticket-04: checklist verification logs" -m "Tests: make test-fast; pytest -q tests/test_no_lookahead.py" -m "Artifacts: artifacts/mm_lob_same_tick/2025-12-23T22-00-05Z-ba5b480/ (validation only)" -m "Docs: PROGRESS.md, docs/agent_runs/20251225_213521_ticket-04_checklist-verify/, docs/prompts/20251225_213521_ticket-04_checklist-verify_ticket-04_checklist-verify.md"`
43. `git status -sb`
44. `BUNDLE_TIMESTAMP=2025-12-25T21-43-58Z make gpt-bundle TICKET=ticket-04 RUN_NAME=20251225_213521_ticket-04_checklist-verify`
45. `git add -f docs/gpt_bundles/2025-12-25T21-43-58Z_ticket-04_20251225_213521_ticket-04_checklist-verify.zip`
46. `git commit -m "ticket-04: add checklist verification bundle" -m "Tests: not run (bundle only)" -m "Artifacts: docs/gpt_bundles/2025-12-25T21-43-58Z_ticket-04_20251225_213521_ticket-04_checklist-verify.zip" -m "Docs: docs/agent_runs/20251225_213521_ticket-04_checklist-verify/RESULTS.md"`
47. `git status -sb`
48. `git push origin codex/ticket-04-leakage-tests-unsafe-manifest`

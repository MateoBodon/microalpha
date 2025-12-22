pytest -q
- Run 1: 102 passed, 1 skipped in 21.74s
- Run 2: 102 passed, 1 skipped in 24.73s (rerun triggered by command-log write error)
- Warnings:
  - DeprecationWarning: ExecModelCfg.aln is deprecated; use 'commission' instead.
  - FutureWarning: Series.fillna with 'method' is deprecated; use ffill()/bfill().

python3 -m compileall tools
- Run 1: Listing 'tools'... Compiling 'tools/gpt_bundle.py'... Compiling 'tools/render_project_state_docs.py'...
- Run 2: Listing 'tools'... (no additional compiler output captured)

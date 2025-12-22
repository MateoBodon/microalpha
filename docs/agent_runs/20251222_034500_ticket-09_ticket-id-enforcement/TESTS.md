pytest -q
- Result: 102 passed, 1 skipped in 21.74s
- Warnings:
  - DeprecationWarning: ExecModelCfg.aln is deprecated; use 'commission' instead.
  - FutureWarning: Series.fillna with 'method' is deprecated; use ffill()/bfill().

python3 -m compileall tools
- Listing 'tools'...
- Compiling 'tools/gpt_bundle.py'...
- Compiling 'tools/render_project_state_docs.py'...

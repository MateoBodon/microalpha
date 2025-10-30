# Factor Regression Example

Microalpha ships a tiny, fully offline Fama–French three-factor sample under
`data/factors/ff3_sample.csv`. The file contains daily observations for
`Mkt_RF`, `SMB`, `HML`, and the risk-free rate expressed in decimal form. You
can run a quick factor attribution against any Microalpha artifact with the
utility script `reports/factors_ff.py`:

```bash
python reports/factors_ff.py artifacts/sample_wfv/<RUN_ID> \
  --factors data/factors/ff3_sample.csv \
  --output reports/summaries/factors_sample.md
```

The script performs an ordinary-least-squares regression of excess portfolio
returns on the factor panel, estimating Newey–West HAC standard errors (default
lag = 5). Microalpha’s reporting pipeline automatically incorporates the table
into `reports/summaries/flagship_mom_wfv.md` when the factor CSV is present, so
the published walk-forward summary highlights factor loadings and alpha quality.

Because the sample datasets are bundled, no external downloads or API keys are
required—ideal for CI environments and reproducible research notes.

# CRSP-v2 short-term reversal mechanism result

The preregistered `short_term_reversal_1_1__equal` mechanism ranked the
negative formation-month FF12-industry-residual return and executed in the
following month. Under the unchanged $15MM portfolio, capacity, and primary
costs, net HAC Sharpe was `-0.4542` (t-stat `-1.4131`), CAGR was `-3.82%`, max
drawdown was `23.44%`, and one-way turnover was `63.27x`.

The mechanism failed the frozen strength gates. Under 600 bps short borrow and
2x nonborrow costs, Sharpe was `-1.0268` and CAGR was `-8.10%`. It is archived
without post-hoc direction inversion, thresholding, or reweighting. The
2023-2025 final holdout was not opened, and no alpha or promotion claim is
supported.

Exact evidence bindings are in `metrics.json`. The external result-manifest
SHA-256 is
`573dd7c74bc6e2bcea0ab22bde30efdc1fcfc9b4eef0ec6e7665c800bfe28b02`.

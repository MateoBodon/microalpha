# CRSP-v2 low-volatility mechanism result

The preregistered `low_volatility_126d__equal` mechanism was evaluated on the
2017-2022 validation window under the unchanged $15MM portfolio, point-in-time
FF12 industry neutrality, capacity, commission, spread, impact, and 300 bps
short-borrow contract. Net HAC Sharpe was `-0.0906` (t-stat `-0.1943`), CAGR
was `-2.20%`, and max drawdown was `43.83%`.

Every frozen mechanism gate failed. Under 600 bps short borrow and 2x
nonborrow costs, Sharpe was `-0.2553` and CAGR was `-4.41%`. The mechanism is
archived without threshold, direction, weighting, or sleeve retuning. The
2023-2025 final holdout was not opened, and no alpha or promotion claim is
supported.

Exact evidence bindings are in `metrics.json`. The external result-manifest
SHA-256 is
`fba7c4f4b4e96f6b310da13103921817db4a04bc910ea451fdd1f79ff8653ad0`.

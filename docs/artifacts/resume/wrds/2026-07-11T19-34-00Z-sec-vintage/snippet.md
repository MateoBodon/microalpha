# First-filed SEC cash-earnings acceleration

The preregistered `sec_cash_earnings_acceleration__equal` mechanism used only
values bound to the earliest original XBRL 10-K accession for each CIK/report
date and made them available at that filing's SEC acceptance timestamp. Across
2017-2022 validation it produced net HAC Sharpe `0.4736` (t-stat `1.0651`),
CAGR `1.73%`, max drawdown `7.71%`, and `13.57x` total one-way turnover.

This improved on frozen momentum by `0.2330` Sharpe but missed the absolute
`0.50` gate. At the frozen harsh stress of 600 bps annual short borrow and 2x
nonborrow costs, Sharpe was `-0.1034` and CAGR `-0.45%`. The mechanism is
therefore archived without feature, sign, weight, concept, threshold, or
availability changes. The 2023-2025 final holdout remains sealed; no current
Compustat accounting value or restricted identifier row was used in Git.

Contract SHA-256:
`707a257a628cd14813961299093fffa469ca527f921f608d80a24098ee6c419b`.
External result-manifest SHA-256:
`1ea92a323a254422772a8edfd86d0fd8d70b806a296190acaec1fb816379a3be`.

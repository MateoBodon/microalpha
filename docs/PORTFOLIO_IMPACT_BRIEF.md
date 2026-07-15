# Microalpha v0.3 Portfolio Impact Brief

## Positioning

Microalpha is a **quantitative research evidence engine**: it turns a market
hypothesis into source-hashed data, point-in-time decisions, target-position
orders, next-session fills, explicit costs, walk-forward folds, corrected
inference, and a machine-verifiable report.

The one-minute proof has two layers: the [Market Risk Case](market-case.md)
shows real empirical usefulness; [Audit Lab](audit-lab.md) proves the research
discipline rejects leakage, impossible execution, omitted costs, and selection
overfitting.

Public product: [GitHub](https://github.com/MateoBodon/microalpha) ·
[Pages](https://mateobodon.github.io/microalpha/) ·
[latest release](https://github.com/MateoBodon/microalpha/releases/latest)

## Independent gap audit and disposition

The live v0.2.0 tree and Pages site were evaluated as a senior quant researcher,
quant developer, first-time user, reproducibility reviewer, and visual portfolio
reviewer. It was compared with the official repositories for
[NautilusTrader](https://github.com/nautechsystems/nautilus_trader),
[LEAN](https://github.com/QuantConnect/Lean),
[Qlib](https://github.com/microsoft/qlib), and
[vectorbt](https://github.com/polakowo/vectorbt). Microalpha should not match
their breadth; it should win on auditability and one defensible empirical report.

| Rank | v0.2 gap | v0.3 disposition |
| ---: | --- | --- |
| 1 | Synthetic fixture dominated; no public real-data report | Added the fixed 2017–2025 Market Risk Case with a daily ledger, baselines, folds, uncertainty, corrected inference, and polished charts |
| 2 | Dataset lineage was asserted but absent from product evidence | Added publisher/source URL, logical path, SHA-256, schema, rows, dates, availability rule, units, and survivorship boundary |
| 3 | `weight` meant full order size, not target-position delta | Added explicit `target_weight` semantics, repeated resize/flip tests, and drawdown-halt deleveraging behavior |
| 4 | Costs were not decomposed on a real-data path | Added per-row commission, half-spread, nonlinear impact, turnover, participation, stressed costs, and exact reconciliation |
| 5 | Artifact schemas were tests, not a user product | Added `microalpha verify` for schema, chronology, cost identity, and receipt hashes |
| 6 | Performance proof emphasized a no-op loop | Added report runtime/peak-memory and active execution evidence to the engineering receipt |
| 7 | CI was Linux-only and portable invocation was not prominent | Added Python 3.13, macOS/Windows empirical smoke, and `python -m microalpha` |
| 8 | Pages was polished but only synthetic above the fold | Put the real-data report first; Audit Lab remains the correctness layer |

The bundled 92 MB `data_sp500/` panel is preserved as history but excluded from
v0.3 claims: source, constituent history, calendar, and adjustment semantics
are not pinned strongly enough.

## Before / after evaluator

Scores are a compact independent-review rubric, not objective performance
metrics. Each after-score is backed by executable evidence.

| Evaluator | v0.2 | v0.3 | Evidence for the change |
| --- | ---: | ---: | --- |
| Senior quant researcher / hiring manager | 3.3/5 | 4.7/5 | Fixed real-data design, risk-matched baseline, folds, uncertainty, all variants disclosed, no-alpha conclusion |
| Quant developer / performance engineer | 3.8/5 | 4.7/5 | Target-position semantics, strict t+1 clock, cost identity, verifier, portable CI, objective benchmarks |
| First-time open-source user | 4.0/5 | 4.7/5 | One offline command builds the report; the next verifies it; the result appears first |
| Scientific reproducibility / lineage | 3.4/5 | 4.8/5 | Source hash, schema, availability rule, daily ledger, and artifact receipt |
| Visual portfolio reviewer | 4.2/5 | 4.8/5 | Real-data hero, equity/drawdown panel, lineage graphic, concise claim boundary |

## Evidence that matters

The fixed 21-session, 10%-volatility rule was evaluated from 2017 through
September 2025. Net annualized return was **11.77%** versus **15.14%** for the
market; realized volatility was **11.37%** versus **19.25%**; Sharpe was **1.04**
versus **0.83**; maximum drawdown was **−15.31%** versus **−34.22%**. A static
risk-matched market exposure produced Sharpe **0.90** and drawdown **−22.38%**.

The best disclosed lookback did not beat the risk-matched baseline after
synchronous stationary max-statistic correction (`p=0.467`). The accurate
conclusion is: **risk management improved materially in this sample; alpha was
not established.**

Canonical evidence: [`metrics.json`](assets/market_case/metrics.json) ·
[`daily.csv`](assets/market_case/daily.csv) ·
[`folds.csv`](assets/market_case/folds.csv) ·
[`selection.json`](assets/market_case/selection.json) ·
[`data_manifest.json`](assets/market_case/data_manifest.json) ·
[`receipt.json`](assets/market_case/receipt.json)

## Resume bullets

- Built an event-driven Python quant research engine that enforces point-in-time
  data availability, next-session execution, target-position rebalancing, and
  reconciled commission/spread/impact costs across walk-forward studies.
- Shipped a deterministic public-factor risk case over 2,198 OOS sessions:
  reduced maximum drawdown from 34.2% to 15.3% and raised descriptive Sharpe
  from 0.83 to 1.04, while withholding an alpha claim after multiple-testing
  correction (`p=0.467`).
- Designed machine-verifiable research artifacts with source/output SHA-256
  receipts, versioned schemas, annual folds, block-bootstrap uncertainty,
  cross-platform CI, and clean-clone replay.

## 90-second interview explanation

“Microalpha is built around the idea that a backtest result is not evidence
until its data clock, execution clock, costs, selection process, and provenance
are inspectable. In the real-data case, I use a fixed volatility-targeting rule
on a public US market factor. Every signal is lagged one session, portfolio
orders are deltas to target exposure, and commission, spread, and nonlinear
impact reconcile exactly to net returns. I compare against both the market and
a risk-matched static exposure, emit yearly folds and bootstrap uncertainty,
and correct across every lookback I tried. The rule cut drawdown and improved
descriptive Sharpe, but corrected differential return was not significant, so
the product says ‘useful risk engineering, no alpha claim.’ A separate Audit
Lab proves the pipeline catches four classic ways a backtest can lie. Both
reports rebuild offline and verify from hashes.”

## Screenshots

The product pages lead with the real-data result and preserve the exact claim
boundary in the visual itself:

![Market Risk Case headline](assets/market_case/market_case.svg)

![Equity and drawdown baselines](assets/market_case/equity_drawdown.svg)

The live [GitHub README](https://github.com/MateoBodon/microalpha#readme) and
[Pages site](https://mateobodon.github.io/microalpha/) are the provider-rendered
views; both are checked at desktop and narrow viewport after release.

## Remaining weaknesses

- The input is a published factor return, not an executable security; costs and
  participation are transparent sensitivities, not venue calibration or capacity proof.
- The historical `data_sp500/` panel remains large and inadequately sourced. It
  is preserved for history and excluded from v0.3 claims.
- Retrospective walk-forward evidence is not prospective live confirmation.
- Microalpha is research software, not a broker, venue, or live trading system.

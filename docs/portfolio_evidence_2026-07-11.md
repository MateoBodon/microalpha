# Pre-holdout research evidence — 2026-07-11

Status: reviewed aggregate evidence; licensed source rows are not distributed

Selection window: 2017–2022

Final holdout: 2023–2025, sealed throughout this campaign

Interpretation: validation evidence only; no alpha, promotion, or live-performance claim

This note is a public-safe summary of a frozen research campaign. Each candidate
was specified before its return computation and kept or rejected using its
predeclared gate. Results include implemented costs; stress results increase
borrow to 600 bps and double non-borrow costs where stated.

## Aggregate results

| Mechanism | HAC Sharpe | t-stat | CAGR | Max drawdown | One-way turnover | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Frozen classic momentum baseline | 0.2407 | — | 1.70% | 11.42% | — | Baseline; validation proxy only |
| Industry-residual momentum | 0.3198 | 1.2174 | 2.48% | 9.39% | — | Rejected: Sharpe improvement 0.0791 was below the required 0.10; harsh-cost CAGR -0.20% |
| Point-in-time low volatility | -0.0906 | -0.1943 | -2.20% | 43.83% | — | Rejected; harsh-cost Sharpe -0.2553 and CAGR -4.41% |
| One-month industry-residual reversal | -0.4542 | -1.4131 | -3.82% | 23.44% | 63.27× | Rejected; harsh-cost Sharpe -1.0268 and CAGR -8.10% |
| Annual QVPI accounting composite | -0.0234 | -0.0462 | -0.56% | 32.17% | 14.33× | Rejected; harsh-cost Sharpe -0.2782 and CAGR -2.71% |
| First-filed SEC cash-earnings acceleration | 0.4736 | 1.0651 | 1.73% | 7.71% | 13.57× | Rejected: below absolute 0.50 Sharpe gate; harsh-cost Sharpe -0.1034 and CAGR -0.45% |

The SEC candidate used values present in two consecutive original 10-K XBRL
accessions and availability dates bound to exact SEC acceptance timestamps. Its
formation-month universe contained 796–1,730 complete names (median 1,084.5)
with zero ambiguous CCM rows. No current Compustat value was used for that
candidate.

The QVPI candidate used a current Compustat snapshot with a fixed six-month
availability lag. That protects basic chronology but does not remove the risk of
later restatements; it is therefore not true vintage-accounting evidence.

## Provenance

- Frozen panel digest: `4ed2b33e2496e224a7701c3d0d71d593909d8fc7547ecdcbc483b2c83686206a`
- Industry-residual result manifest: `9e3a8818211a9ef9c81816bb2fadf6165636cc9a344f9284698adec3499ef107`
- Low-volatility result manifest: `fba7c4f4b4e96f6b310da13103921817db4a04bc910ea451fdd1f79ff8653ad0`
- Reversal result manifest: `573dd7c74bc6e2bcea0ab22bde30efdc1fcfc9b4eef0ec6e7665c800bfe28b02`
- QVPI result manifest: `72b378035b736c50f26be8e11bff1f72dc2478365971294694336c9945332fb2`
- SEC-vintage result manifest: `1ea92a323a254422772a8edfd86d0fd8d70b806a296190acaec1fb816379a3be`

These digests bind the local reviewed artifacts without publishing restricted
rows. Reproduction requires authorized access to the same licensed snapshots.

## Claim boundary

Supported: the tested engine contracts, the aggregate validation statistics
above, the rejection decisions, and the fact that the recorded runners did not
open 2023–2025 outcomes.

Not supported: final-holdout performance, alpha discovery, deployment, live
trading, or a claim that any mechanism is ready for promotion.

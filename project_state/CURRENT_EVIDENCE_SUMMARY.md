# Current Evidence Summary

last_updated: 2026-07-10
updated_by: Project OS v3 microalpha worker
source_event: first-principles recovery audit and CRSP-v2 flagship predeclaration

## Current Flagship

Status: predeclared and source-validated; full empirical execution has not
started.

- Protocol: `docs/strategy/MICROALPHA_FLAGSHIP_20260710.yaml`
- Protocol ID: `crsp-v2-industry-neutral-momentum-20260710`
- Protocol SHA256:
  `f88df6c93d3a83ddf76be6e198fc567122f18b39204b8565290e09969f1af75e`
- Real-data scope: CRSP CIZ `dsf_v2`, 2005-2025, 40,402,817 daily rows,
  point-in-time `stocknames_v2`, `stkdelists`, CRSP DSI, and manifest-bound Ken
  French factor/momentum files.
- Windows: warmup 2005-2006; training 2007-2016; validation 2017-2022; sealed
  final holdout 2023-2025.
- Candidate grid: 12-2 momentum, 6-2 momentum, or their blend; equal or
  inverse-126-day-volatility weights; six candidates total.
- Direct objective: net final-holdout evidence after validation-only selection,
  with industry neutrality, point-in-time eligibility, measured turnover,
  participation capacity, contemporaneous spread, impact, commission, and
  borrow stress.
- Baselines: CRSP value/equal-weight markets, an identical-universe classic
  12-2 strategy, Ken French MOM and momentum deciles, cash/RF, and the legacy
  result as historical-only context.

## Source And Adapter Evidence

The live audit verified both WRDS manifest digests, all 21 selected CRSP-v2
partitions, both side tables, DSI, the public acquisition manifest, and all
three public file digests. The source manifests have unrelated failed items,
but every item used by this protocol is independently `ok` and path-bound.

The adapter now:

- physically omits post-2022 partitions from selection-stage DuckDB inputs;
- truthfully records that unpartitioned gzip side tables require full-file byte
  scans, while materializing and reconciling only rows matching opened daily
  rows through the stage cutoff;
- requires a protocol-hash-bound frozen model receipt before final-stage input;
- resolves formation attributes from exactly one date-valid stocknames row;
- reconciles CIZ delisting pseudo-days to `stkdelists` and uses `dlyret` once;
- constructs the exact FF12 point-in-time universe and industry-neutral weights
  under the required 15% industry gross cap;
- publishes the panel and manifest through staged, no-clobber artifact paths;
- records turnover, capacity constraints, cost components, source partitions,
  output digest, and split coverage in derived manifests; and
- records canonical-YAML and exact-file config hashes separately in standard
  run manifests.

Bounded validation: ten targeted unit/integration tests pass, including a tiny
synthetic DuckDB panel that proves selection-stage holdout exclusion, frozen
model gating, side-table sentinel exclusion, one-time delisting aggregation,
industry-cap redistribution, and no-clobber/failed-build behavior. Synthetic
fixtures are only mechanism tests and are not research results.

No 2023-2025 return performance, signal-return correlation, candidate ranking,
or threshold result was inspected. No full panel or flagship result exists yet.

## Legacy WRDS Evidence

The curated historical facts remain:

- run `2026-02-16T22-33-46Z-8d90621`;
- reported 2018-2019 Sharpe_HAC `0.588`, CAGR `0.88%`, MaxDD `1.38%`, 31
  trades, and RealityCheck p-value `0.941`;
- small curated metrics/leaderboard files present; referenced source artifacts
  and run report absent.

This run is not promotion-grade evidence. Ticket 35 explicitly selected among
candidates by maximizing the stated holdout Sharpe, so the 2018-2019 window is
tuned rather than pristine. The 40-security export lacks defensible CRSP
manifest provenance, its universe labels all sectors `UNKNOWN`, and the reported
RealityCheck p-value does not reject the null. It may be cited only as a
historical, non-comparable artifact fact.

The former config-hash warning is resolved: `5fb44d...` is the exact file-byte
hash and `caa000...` is the canonical-YAML runtime hash. New manifests label and
record both.

## Claim Status

| Claim surface | Status | Reason |
|---|---|---|
| CRSP-v2 real-data sources are locally available and protocol-bound | supported | Live digest, item, size, count, and header audit passed. |
| Adapter enforces the declared split, truthful side-table scan boundary, delisting/identity mechanics, industry cap, and no-clobber output | supported for bounded tests | Unit and synthetic integration coverage pass; the large real panel is not built yet. |
| 2023-2025 holdout remains sealed from model selection | supported to date | Only permitted metadata/header checks occurred; no holdout outcome analysis occurred. |
| Legacy curated numbers are historical artifact facts | supported with caveats | Small curated files exist, but source artifacts are missing. |
| Legacy run is an independent holdout or alpha result | blocked | The stated holdout was used for model selection and RC p=`0.941`. |
| New flagship performance or alpha | awaiting execution | No real-data result has been computed. |

## Next Authorized Action

When the portfolio's single memory-heavy slot is released, build the selection
panel through 2022 only, validate integrity, execute the six predeclared
candidates, and freeze the selected model before any 2023-2025 daily outcome is
opened beyond header verification or any post-validation side-table row is
materialized.

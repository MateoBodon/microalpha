# Microalpha showcase scorecard

Frozen: 2026-07-15  
Baseline public commit: `9abb834117820dc479246fc9486ae7301d309110`  
Evaluator: senior quant engineer, open-source user, scientific red team, and
portfolio reviewer  
Objective: make the repository an interview-ready quantitative-engineering
product. Positive investment performance is not an objective.

## Positioning decision

**Microalpha is a quant research audit laboratory:** an event-driven Python
system that makes chronology, execution, cost, selection, and provenance errors
observable before a backtest is allowed to become a claim.

The public flagship must be a deterministic synthetic correctness fixture with
known ground truth. It may deliberately create inflated positive results only
to prove that the safe pipeline detects and removes the inflation. It must never
be presented as alpha.

## Independent baseline audit

| Perspective | Baseline | Most material gap |
| --- | ---: | --- |
| Hiring manager | 2.7 / 5 | Strong engineering is buried; there is no memorable, executable proof. |
| Open-source user | 2.9 / 5 | Clean-clone works, but there is no compact correctness receipt, Mypy fails, and release/license surfaces conflict. |
| Scientific red team | 2.4 / 5 | Future fills mutate state early; the existing reality check is not a valid centered multiple-testing correction. |
| Visual/portfolio | 2.6 / 5 | README and Pages are readable but text-heavy, generic, and missing a flagship demo visual. |

### Direct baseline evidence

- Clean temporary checkout from the public commit: editable source install
  `10.341 s`; `make sample` `14.916 s`; `make report` `1.903 s`; total
  `27.161 s` on the manager host.
- The sample uses a wall-clock run id and writes absolute local paths, so its
  complete output tree is not byte-stable across clean locations.
- Latest public CI: 128 tests passed on Python 3.10, 3.11, and 3.12; 77% line
  coverage; Ruff, Black, isort, detect-secrets, and MkDocs passed.
- Independent clean-clone verification found 129 focused tests passing, the
  data-policy scan and strict docs build passing, but the README-advertised Mypy
  command failing with five pandas index-type errors.
- `LICENSE` is empty and GitHub reports no asserted license. The release workflow
  can publish the `microalpha` distribution to PyPI even though the docs warn
  that the PyPI namesake is an unrelated project.
- Public GitHub `main` and Pages were green at the baseline commit. The Pages
  deployment commit was `34163e141941638670a99fe3a2f5d2d6380bbc36`.
- Desktop and narrow screenshots taken after that deployment show no broken
  layout, but the first fold contains no generated correctness proof; the Pages
  home is generic and gives disproportionate navigation weight to WRDS history.

## Ranked gaps frozen before implementation

1. Correct the engine so a future fill cannot change positions, cash, logs, or
   risk state before the corresponding market timestamp is processed.
2. Replace the current pseudo reality-check claim with a centered, synchronous,
   benchmark-differential max-statistic correction and tests.
3. Add one deterministic `microalpha audit-demo` command that contrasts:
   leaky versus point-in-time data; same-tick versus queued t+1 execution; gross
   versus reconciled costs; naive selection versus walk-forward plus the valid
   max-statistic correction.
4. Produce one compact JSON/CSV/SVG evidence set and a SHA-256 receipt that is
   byte-identical across clean paths and repeated runs.
5. Rebuild the README and Pages first fold around the generated demo, architecture
   and data lineage, one command, exact proof, and explicit limitations.
6. Disable unsafe PyPI publication, adopt a real license if ownership intent is
   supported, fix the advertised type check, and align package metadata,
   repository description/topics, docs navigation, version/release language,
   and the public negative-research case study.

## Frozen acceptance scorecard

| Dimension | Baseline | Done threshold | Required direct evidence |
| --- | ---: | ---: | --- |
| 30-second product clarity | 2.0 / 5 | 4.5 / 5 | Top fold states problem, mechanism, exact demo result, one command, and non-alpha boundary. |
| Chronology correctness | 2.0 / 5 | 4.5 / 5 | Regression test proves future fills cannot mutate state early; same-timestamp ordering is deterministic. |
| Statistical safeguards | 1.0 / 5 | 4.0 / 5 | Centered synchronous max-statistic test includes a benchmark, controls a frozen null canary, and detects a planted positive control. |
| Deterministic flagship demo | 0.5 / 5 | 5.0 / 5 | Two clean runs have identical canonical files and receipt hash; no clock, host, or absolute path enters the receipt. |
| Install-to-proof usability | 2.5 / 5 | 4.5 / 5 | Clean clone/source install and one demo command pass in a reasonable time with no licensed data. |
| API/CLI coherence | 3.0 / 5 | 4.0 / 5 | Public Python API and CLI share the same implementation and schemas; help and errors are tested. |
| Evidence and provenance | 2.5 / 5 | 4.5 / 5 | Input, config, schema, code version, and every canonical output are hash-bound with relative paths. |
| Tests/static/security | 3.8 / 5 | 4.5 / 5 | Focused and full tests, lint, format, type/static checks, coverage, docs, links, data-policy, and secret scan pass. |
| Docs/navigation | 2.5 / 5 | 4.5 / 5 | Demo, architecture, API, reproducibility, and limitations form the primary path; process history is secondary. |
| Visual/mobile quality | 2.6 / 5 | 4.5 / 5 | README and live Pages inspected at desktop and narrow widths; charts are legible and no overflow/broken images remain. |
| Claim honesty | 3.0 / 5 | 5.0 / 5 | No alpha claim; configurable costs are not called calibrated; licensed/public/synthetic boundaries are explicit. |
| Live publication | 3.5 / 5 | 5.0 / 5 | Reviewed commit is on public `main`; CI/Docs green; Pages and repository metadata read back and match. |

## Non-negotiable scientific tests

- Every feature row used at a decision satisfies `available_at <= decision_at`;
  an unsafe join fails closed with row identifiers and counts.
- A scheduled fill remains pending until its timestamp; no position, cash,
  turnover, realized P&L, trade log, or risk state changes early.
- Net P&L reconciles exactly to gross P&L minus commission, spread, impact, and
  borrow components in the correctness fixture.
- The multiple-testing correction recenters candidate-minus-benchmark returns
  under the null and resamples candidates synchronously to preserve dependence.
- The demo includes both a noise-only family and a clearly labeled planted-signal
  positive control; neither is evidence of market alpha.
- Generated public artifacts contain no private absolute path, credential,
  licensed row, or sealed 2023–2025 confirmation observation.

## Publication comparison

The final report must compare the shipped public commit directly with
`9abb834117820dc479246fc9486ae7301d309110`, including changed evaluator scores,
demo runtime and hashes, test/coverage counts, rendered screenshots, live CI and
Pages URLs, remaining weaknesses, and the next highest-value improvement.

## Reviewed outcome before publication

- Product commit: `1fe57117ebcf3fcabce9048002265c914ecd28aa`.
- Final receipt: `feb7e57ade26575942d10d21c4bd9c1a86724b2ab4f959bf1741eb46106b7b4b`.
- Full verification: 146 tests, 77.73% coverage, all quality/static/security/docs
  gates passing, clean wheel proof passing.
- Independent final hiring, open-source, and scientific reviews report no
  remaining P0/P1 product issue.
- Final hiring scores: clarity 4.9, depth 4.7, memorability 4.9, honesty 5.0,
  resume usefulness 4.9.
- Publication and live desktop/narrow readback remain the final release gate.

# Claims And Evidence

last_updated: 2026-07-10
updated_by: Project OS v3 microalpha worker
source_event: CRSP-v2 flagship predeclaration and adapter validation

Research, benchmark, and result-adjacent claims must remain bound to exact
artifacts, source manifests, split policy, costs, baselines, and validation.

| Claim | Status | Evidence | Caveats |
|---|---|---|---|
| microalpha is a leakage-aware event-driven backtesting engine for tested invariants. | supported for tested invariants | `tests/test_no_lookahead.py`, `tests/test_tplus1_execution.py`, engine/data tests | Revalidate when execution or data paths change. |
| The CRSP-v2 flagship source set is available and manifest-bound. | supported | `docs/strategy/MICROALPHA_FLAGSHIP_20260710.yaml`; live `scripts/crsp_v2_flagship.py audit`; `project_state/DATA_ARTIFACT_INVENTORY.md` | Raw licensed data remains external; unrelated acquisition failures are not relied upon. |
| Selection never opens sealed daily partitions and cannot materialize or reconcile post-validation side-table rows. | supported for code contract and bounded integration | `src/microalpha/research/crsp_v2_panel.py`; `tests/test_crsp_v2_panel.py` | The unpartitioned gzip side-table source bytes must be scanned to apply date/key filters; the derived receipt states this explicitly. Recheck the eventual real derived manifest before model selection. |
| Point-in-time stocknames and CIZ delisting semantics are enforced. | supported for code contract and bounded tests | `src/microalpha/research/crsp_v2.py`; `src/microalpha/research/crsp_v2_panel.py`; related tests | Full real-panel integrity audit is pending. |
| Industry-neutral universe, required 15% industry gross cap, turnover, capacity, and cost accounting primitives are implemented. | supported for bounded tests | `tests/test_crsp_v2_research.py` | No empirical performance claim follows from mechanism tests. |
| Panel and manifest publication is staged, atomic per artifact, and no-clobber. | supported for bounded tests | `src/microalpha/research/crsp_v2_panel.py`; `tests/test_crsp_v2_panel.py` | A full real-panel build has not run. |
| Legacy 2018-2019 numbers are curated historical artifact facts. | supported with material caveats | `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/`; leaderboard; ticket-35 records | Source run artifacts are missing, provenance is weak, and ticket 35 selected on the stated holdout. |
| The legacy run found alpha or passed an independent holdout. | blocked | Ticket-35 prompt/results and RC p-value `0.941` | Do not promote externally. |
| The new CRSP-v2 flagship has positive performance or alpha. | awaiting execution | predeclared protocol only | No full real-data panel or result has been produced. |

## Unsupported Until New Evidence Exists

- Any statement that the new flagship has positive performance, beats a
  baseline, survives costs, has capacity, or found alpha.
- Any use of 2023-2025 to choose signals, weighting, thresholds, costs, or
  eligibility rules before a protocol-bound frozen-model receipt exists.
- Any headline result that omits dataset/protocol digests, date windows,
  universe, baselines, costs, capacity, inference, or caveats.
- Any empirical claim based on synthetic data.
- Any promotion of the legacy "sector-neutral" result; its recovered universe
  contains only `UNKNOWN` sector labels.

## Evidence Rules

- Cite the exact protocol, source manifest, derived manifest, command, and
  artifact for consequential claims.
- Keep raw/restricted data outside Git; commit only safe code, metadata, and
  aggregate evidence.
- Label historical and proxy evidence explicitly.
- Preserve negative/null results and reject promotion when gates fail.

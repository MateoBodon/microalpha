# Audit Lab

Audit Lab is a deterministic, known-ground-truth correctness fixture. It creates
invalid positive results on purpose, runs the corresponding safe controls, and
writes a byte-stable evidence set.

```bash
microalpha audit-demo
```

No network, provider, credential, licensed row, or hidden holdout is accessed.
The only inputs are schema `microalpha.audit-lab.v1`, seed `20260715`, and
NumPy-generated arrays bound by `input_sha256`.

The fixture uses transparent NumPy oracle constructions so every injected
failure has known ground truth. The production `Engine` and `ExecutionPlan`
path is guarded by
[`test_tplus1_execution.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_tplus1_execution.py),
while the shared max-statistic implementation is guarded by
[`test_multiple_testing.py`](https://github.com/MateoBodon/microalpha/blob/main/tests/test_multiple_testing.py).

## Four paired audits

### 1. Point-in-time availability

The unsafe feature is a revised value that contains the contemporaneous return
but is not available until two sessions later. Using it at the decision time
creates Sharpe `+20.5276`. The safe path enforces
`available_at <= decision_at`, blocks all 756 unavailable rows, and produces
Sharpe `−0.1728` from the information actually available.

The same public `require_point_in_time` gate raises `PointInTimeViolation` with
the exact violating row IDs and count instead of silently dropping late data.

### 2. Event-time execution

The unsafe oracle observes a return and fills on the same tick, producing Sharpe
`+21.8860`. The safe vector fixture shifts the signal to the next observation;
its Sharpe is `+0.1739`.

The separate production regression test uses a clock-guarded data handler: any attempt to read a
future price before its event raises immediately. It also records cash and
positions at each strategy callback, proving the future fill cannot mutate
state early.

### 3. Cost reconciliation

A labeled planted control has gross Sharpe `+0.5668`. Commission, half-spread,
impact, and borrow costs reduce it to `−0.6753`. Net returns reconcile exactly:

```text
net = gross - commission - half_spread - impact - borrow
max absolute residual = 0.0
```

These costs are fixture parameters, not empirical venue calibration.

### 4. Model-selection control

Searching 128 noise strategies over the full sample finds an apparent winner at
Sharpe `+1.3802`. A model selected only on the first 504 observations scores
`−1.2781` on the untouched final 252 observations.

The max-statistic test evaluates every candidate as a return differential to an
explicit zero-return benchmark. It recenters differentials under the null and
uses the same stationary-bootstrap timestamps for every candidate, preserving
cross-model dependence. The noise family is not promoted (`p=0.601`); a labeled
planted positive control is detected (`p=0.001`).

## Canonical artifacts

| File | Purpose |
| --- | --- |
| [`audit_results.json`](assets/audit_lab/audit_results.json) | Exact metrics and claim boundary |
| [`comparison.csv`](assets/audit_lab/comparison.csv) | Four-row machine-readable comparison |
| [`audit_lab.svg`](assets/audit_lab/audit_lab.svg) | Reviewer-facing result graphic |
| [`data_lineage.svg`](assets/audit_lab/data_lineage.svg) | Architecture and data-lineage graphic |
| [`receipt.json`](assets/audit_lab/receipt.json) | Input and artifact SHA-256 hashes |

The receipt itself has SHA-256
`feb7e57ade26575942d10d21c4bd9c1a86724b2ab4f959bf1741eb46106b7b4b`.
Paths, clocks, hostnames, and Git metadata are excluded from canonical bytes.

## Python API

```python
from microalpha.audit_lab import run_audit_lab

result = run_audit_lab("evidence")
assert result["receipt_sha256"] == (
    "feb7e57ade26575942d10d21c4bd9c1a86724b2ab4f959bf1741eb46106b7b4b"
)
```

This equality verifies the fixture and generator version used by this release;
it is not a universal hash across future schema versions.

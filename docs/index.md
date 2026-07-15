# Microalpha

**A quantitative research audit lab that makes invalid backtests visibly fail.**

Microalpha separates market-data availability, signal time, portfolio state,
execution events, cost accounting, model selection, and artifact provenance.
The flagship Audit Lab injects four common research failures into deterministic
synthetic data and proves the safe path removes them.

![Audit Lab paired results](assets/audit_lab/audit_lab.svg)

## Run the proof

```bash
git clone https://github.com/MateoBodon/microalpha.git
cd microalpha
python -m venv .venv
source .venv/bin/activate
python -m pip install .
microalpha audit-demo
```

The output is tracked under `docs/assets/audit_lab/`. A correct clean run leaves
that directory unchanged:

```bash
git diff --exit-code -- docs/assets/audit_lab
```

Receipt SHA-256:
`feb7e57ade26575942d10d21c4bd9c1a86724b2ab4f959bf1741eb46106b7b4b`.

Install from this repository: the namesake package on PyPI is an unrelated third-party project.

## What the fixture proves

| Audit | Naive | Safe | Enforcement |
| --- | ---: | ---: | --- |
| Revised value before availability | Sharpe `+20.53` | `−0.17` | 756 rows blocked |
| Same-tick signal and fill | Sharpe `+21.89` | `+0.17` | queued t+1 fill |
| Omitted costs | Sharpe `+0.57` | `−0.68` | four-part cost ledger |
| Best of 128 noise models | Sharpe `+1.38` | OOS `−1.28` | corrected `p=0.601` |

The planted positive control is detected at `p=0.001`. All results are synthetic
software fixtures, never market or alpha claims.

![Clock and hash lineage](assets/audit_lab/data_lineage.svg)

## Product path

1. [Audit Lab](audit-lab.md) — exact fixture, method, schemas, and hashes.
2. [Architecture](architecture.md) — event scheduling and component boundaries.
3. [API](api.md) — CLI and Python extension points.
4. [Reproducibility](reproducibility.md) — manifests, deterministic evidence,
   and clean-run checks.
5. [Limitations](limitations.md) — what the system does not prove.

The [research case study](portfolio_evidence_2026-07-11.md) shows the other side
of the same discipline: six licensed-data mechanisms failed frozen promotion
gates while the 2023–2025 confirmation set remained sealed.

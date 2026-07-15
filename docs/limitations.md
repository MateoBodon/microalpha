# Limitations and claim boundary

Microalpha demonstrates research-engineering controls. It does not certify that
a strategy is profitable, data is correctly licensed, or a simulation matches a
specific live venue.

## What Audit Lab proves

- the shipped generator blocks a known unavailable-data fixture;
- built-in engine execution plans cannot mutate portfolio state before the due
  market event;
- the fixture's net returns reconcile to four explicit cost components;
- the shipped benchmark-differential max-statistic test rejects a frozen noise
  family and detects a frozen planted control;
- canonical artifacts reproduce byte-for-byte for the same schema and seed.

## What it does not prove

- market predictability or alpha;
- calibration of commission, spread, impact, borrow, or capacity for a real
  asset and venue;
- correctness of provider availability metadata supplied by a user;
- survivorship-free coverage for arbitrary external universes;
- statistical power for every dependence structure or sample size;
- live trading, broker connectivity, or operational risk management.

## Data boundaries

Synthetic fixtures are public and generated locally. Small public examples are
wiring demonstrations. Licensed WRDS/CRSP/OptionMetrics rows stay outside the
repository; only reviewed aggregates may be published. The 2023–2025 research
confirmation set remains sealed and is not used by Audit Lab.

## Packaging boundary

The `microalpha` name on PyPI belongs to an unrelated project. This repository
does not publish there. Install from the source checkout or an attached GitHub
release wheel and verify its GitHub artifact attestation.

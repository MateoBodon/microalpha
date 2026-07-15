# Limitations and claim boundary

Microalpha demonstrates research-engineering controls. It does not certify that
a strategy is profitable, data is correctly licensed, or a simulation matches a
specific live venue.

## What the public evidence proves

- the Market Risk Case applies a fixed volatility-targeting rule with a strict
  one-session decision/execution gap and exact commission/spread/impact identity;
- its public-factor input and every generated artifact are hash-bound;
- the shipped Audit Lab generator blocks a known unavailable-data fixture;
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

The Market Risk Case uses a published factor return rather than an executable
security. Its cost and participation inputs are transparent sensitivity
scenarios, not venue calibration, constituent-level capacity, or a claim that
the factor can be traded at those prices. The factor construction does not
establish survivorship-free coverage for arbitrary stock universes.

Synthetic fixtures are public and generated locally. Licensed
WRDS/CRSP/OptionMetrics rows stay outside the repository; only reviewed
aggregates may be published. The historical 92 MB `data_sp500/` panel has
inadequate pinned constituent and adjustment provenance and is explicitly
excluded from v0.3 evidence. The sealed 2023–2025 CRSP confirmation set remains
unread by both public showcases.

## Packaging boundary

The `microalpha` name on PyPI belongs to an unrelated project. This repository
does not publish there. Install from the source checkout or an attached GitHub
release wheel and verify its GitHub artifact attestation.

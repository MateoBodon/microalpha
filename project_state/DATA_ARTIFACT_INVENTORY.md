# Data Artifact Inventory

last_updated: 2026-07-10
updated_by: Project OS v3 microalpha worker
source_event: live flagship source audit and legacy artifact reconciliation

## Policy

This inventory records metadata only. Raw licensed rows remain outside Git and
must not enter docs, logs, reports, bundles, or commits. Synthetic data is
permitted only in unit/integration fixtures and is never empirical evidence.

## Canonical Real-Data Authorities

| Role | Authority | Verified state |
|---|---|---|
| CRSP CIZ daily panel | `/Volumes/Storage/Data/wrds/_manifests/20260707_full_p1_core_fast_csvgz/manifest.json` | manifest SHA256 `17858b58455131da22e184dbe04091b3e3c8b4e2b0f336a2325561a52063b2c6`; 21 successful `dsf_v2` year partitions for 2005-2025; 40,402,817 rows; 3,358,516,505 compressed bytes |
| Point-in-time security names | same manifest, `stocknames_v2` | one successful item; 87,766 rows; required identity, date-range, exchange, security-type, US-incorporation, and SIC columns present |
| Delisting audit | same manifest, `stkdelists` | one successful item; 29,833 rows; `delret`, missing-code, and daily delisting-date columns present |
| CRSP market baselines | `/Volumes/Storage/Data/wrds/_manifests/20260707T141203Z_resume_90m_fast_csvgz/manifest.json` | manifest SHA256 `1d17b6035088ea3bca454cf848e7b8aca37dfb1a50289a9d89833e503f310a0f`; one successful `dsi` item; 26,051 rows |
| Ken French baselines | `/Volumes/Storage/Data/NON_WRDS/_runs/20260709_012831_non_wrds_max_acquisition/DOWNLOADS_MANIFEST.csv` | manifest SHA256 `9f3d85e32db3795d2b4e686d034f6578224f6c6c0562d5a1eacd380dbdd8cc24`; FF5 daily, MOM daily, and prior-12-2 deciles files each match their predeclared SHA256 |

The two WRDS acquisition manifests contain unrelated failed items (`16` and
`34` respectively). The protocol relies only on the independently successful,
path-bound items above and fails closed if any required item, size, row count,
header, or manifest digest changes.

## Flagship Binding

- Protocol: `docs/strategy/MICROALPHA_FLAGSHIP_20260710.yaml`
- Protocol ID: `crsp-v2-industry-neutral-momentum-20260710`
- Current protocol SHA256:
  `b51d50ccfcf1cc368558d49afc5bd9386120efe92bdd03a7d43d7791be971743`
- Selection data: warmup 2005-2006, training 2007-2016, validation 2017-2022.
- Sealed final holdout: 2023-2025.
- Live audit command:
  `PYTHONPATH=src python3 scripts/crsp_v2_flagship.py --protocol docs/strategy/MICROALPHA_FLAGSHIP_20260710.yaml audit`
- Live audit result: all bound inputs verified; only permitted manifest,
  metadata, byte-size, digest, and header checks touched holdout partitions;
  holdout outcome rows were not read.

## Legacy 40-Security Export

The recovered legacy input contains 40 per-security CSV files, 69,733 rows,
and dates 2013-01-02 through 2019-12-31. Its universe metadata assigns every
security to `UNKNOWN`, so the old "sector-neutral" label is not supported.
The configured export manifest at
`/Volumes/Storage/Data/wrds/manifests/20251221_001618/manifest.json` has
`no_crsp: true` and records only an OptionMetrics result; it does not establish
provenance for those CRSP CSVs.

The legacy config hashes are not contradictory:

- exact file SHA256:
  `5fb44d31684945aabad4132d4f7f5cd4eee9c83cfa61a8f8ecf55a0748755493`
- canonical `yaml.safe_dump` SHA256 used by runtime manifests:
  `caa000f5e885c0e7f566e435fb94a6632c19bb37282c5a36c0fe4b47a6cb7260`

New manifests record both definitions explicitly.

## Artifact Availability

Small curated legacy metrics and leaderboard files remain under
`docs/artifacts/resume/wrds/`. The referenced source run directory and report
for `2026-02-16T22-33-46Z-8d90621` remain absent, so exact historical source
reproduction is unavailable. This does not block the new manifest-bound CRSP-v2
campaign.

## Conclusion

`READY_FOR_SELECTION_PANEL_BUILD`

The source contract and bounded adapter tests are ready. The 40.4M-row build is
intentionally deferred until Portfolio OS releases the single memory-heavy
empirical-job slot.

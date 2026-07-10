# Data Artifact Inventory

last_updated: 2026-07-03
updated_by: Codex T-001
source_event: Post-transfer data/artifact inventory for WRDS recovery

## Policy

This inventory records metadata only. It does not copy raw WRDS/CRSP data and
does not hash raw licensed data.

## WRDS Data Root

- `WRDS_DATA_ROOT` environment variable: unset during T-001 inspection.
- Historical WRDS root recorded in curated artifacts: `/srv/data/wrds/wrds`
- Historical WRDS root exists on this machine: no.
- Current conclusion: WRDS inputs are unavailable in this checkout/session.

## Expected Current WRDS Dependencies

From `configs/wfv_flagship_wrds.yaml` and
`configs/wfv_flagship_wrds_sweep35.yaml`:

| Dependency | Expected path pattern | Status |
|---|---|---|
| Export manifest | `${WRDS_DATA_ROOT}/manifests/20251221_001618/manifest.json` | missing/unknown because `WRDS_DATA_ROOT` is unset; historical `/srv/data/wrds/wrds` absent |
| CRSP daily CSV directory | `${WRDS_DATA_ROOT}/crsp/daily_csv` | missing/unknown because `WRDS_DATA_ROOT` is unset; historical `/srv/data/wrds/wrds` absent |
| Security metadata | `${WRDS_DATA_ROOT}/meta/crsp_security_metadata.csv` | missing/unknown because `WRDS_DATA_ROOT` is unset; historical `/srv/data/wrds/wrds` absent |
| Flagship universe | `${WRDS_DATA_ROOT}/universes/flagship_sector_neutral.csv` | missing/unknown because `WRDS_DATA_ROOT` is unset; historical `/srv/data/wrds/wrds` absent |

Expected dataset id for current WRDS configs:
`wrds_crsp_export_20251221_v1`.

## Config Metadata

| Config | SHA256 in current checkout | Data class |
|---|---|---|
| `configs/wfv_flagship_wrds.yaml` | `1e15555f18a45dcc1c97c76a4fcee1d4eaa03ab656e695a0a8e3b4ea49e15175` | safe config metadata |
| `configs/wfv_flagship_wrds_sweep35.yaml` | `5fb44d31684945aabad4132d4f7f5cd4eee9c83cfa61a8f8ecf55a0748755493` | safe config metadata |
| `configs/wfv_flagship_public.yaml` | `e5ccee187a582855650b9d088919d3a2cc6302fb85bcc54429960ee4e476de4f` | safe config metadata |

Note: the promoted WRDS manifest excerpt for run
`2026-02-16T22-33-46Z-8d90621` records config hash
`caa000f5e885c0e7f566e435fb94a6632c19bb37282c5a36c0fe4b47a6cb7260`, while the
tracked config and ticket-35/ticket-36 run-log metadata record
`5fb44d31684945aabad4132d4f7f5cd4eee9c83cfa61a8f8ecf55a0748755493`.

## Artifact Directories Present

| Path | Metadata | Classification |
|---|---|---|
| `artifacts/` | 119 files, about 2924 KiB, mtime `2026-07-02T21:12:48-0400` | generated/sample artifacts plus one older WRDS artifact directory; not raw data bundle material |
| `docs/artifacts/resume/` | 16 files, about 76 KiB, mtime `2026-07-02T21:11:53-0400` | small curated resume-safe public/WRDS artifacts |
| `reports/summaries/` | 17 files, about 656 KiB, mtime `2026-07-02T21:09:52-0400` | small summaries and images; current WRDS summary is stale versus leaderboard best |
| `data/` | 30 files, about 2016 KiB, mtime `2026-07-02T21:09:51-0400` | bundled sample/public data and factors; not WRDS raw export |
| `data_sp500/` | 936 files, about 94540 KiB, mtime `2026-07-02T21:09:52-0400` | large supporting local data panel; not included in review bundle |

## Current Artifact Paths

| Artifact | Path | Availability | Classification |
|---|---|---|---|
| Public current resume line | `docs/artifacts/resume/public/resume_line_best.md` | present | small curated artifact |
| Public current metrics | `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/metrics.json` | present | small curated artifact |
| Public current manifest excerpt | `docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/manifest_excerpt.json` | present | small curated metadata |
| Public source local artifacts | `artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/...` | missing | large/generated local artifact, not required in git |
| WRDS current resume line | `docs/artifacts/resume/wrds/leaderboard/resume_line_best.md` | present | small curated artifact |
| WRDS leaderboard | `docs/artifacts/resume/wrds/leaderboard/leaderboard.md`, `leaderboard.csv` | present | small curated artifacts |
| WRDS current metrics | `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/metrics.json` | present | small curated aggregate artifact |
| WRDS current manifest excerpt | `docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/manifest_excerpt.json` | present | small curated metadata |
| WRDS current source local artifacts | `artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/...` | missing | large/generated local artifacts, not raw data but needed for exact source recovery |
| WRDS current source report | `reports/_runs/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship.md` | missing | generated local report |
| Current `reports/summaries/wrds_flagship.md` | `reports/summaries/wrds_flagship.md` | present | stale summary for older run `2026-01-26T01-22-23Z-e76eb4d` |

## Missing Data / Export Request

To unblock T-003, provide or regenerate a local WRDS data root and set:

```bash
export WRDS_DATA_ROOT=/absolute/path/to/wrds
```

The path should contain, at minimum:

- `manifests/20251221_001618/manifest.json`
- `crsp/daily_csv/` with the CRSP daily price/return CSV exports used by
  `wrds_crsp_export_20251221_v1`
- `meta/crsp_security_metadata.csv`
- `universes/flagship_sector_neutral.csv`

If the original export cannot be restored, regenerate an equivalent or newer
WRDS/CRSP export with:

- CRSP daily stock data for the configured windows;
- delisting returns where available;
- security metadata sufficient for point-in-time ticker/security handling;
- the flagship sector-neutral universe file;
- a manifest with dataset id, export time, source tables, row/file counts, and
  hashes for safe metadata/manifests only.

Do not copy the raw WRDS/CRSP data into git, docs, reports, run logs, or review
bundles.

## Conclusion

`BLOCKED_FOR_T003_MISSING_DATA`

T-003 should not run a WRDS baseline reproduction until `WRDS_DATA_ROOT` is set
to a restored or regenerated local licensed data root containing the dependencies
above.

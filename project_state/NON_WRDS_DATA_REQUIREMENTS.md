# Non-WRDS Data Requirements

last_updated: 2026-07-08
updated_by: Codex
scope: planning_only_no_data_downloads

## Human Summary

This map covers data and state dependencies for microalpha that are not raw WRDS
tables or WRDS downloads. It is based on the live repository at
`/Volumes/Storage/Projects/microalpha/repo`, including README/docs, configs,
scripts, notebooks, tests, current `project_state/` files, artifact manifests,
the existing WRDS requirements map, and tracked data-policy surfaces.

No data was downloaded, no credentials were used, and no raw private/vendor data
was copied into the repo. The current non-WRDS surface has four important
classes:

- **Current reproduction/state preservation inputs**: bundled sample data,
  public mini-panel data, tracked sample artifacts, curated public resume
  artifacts, run logs, and metadata manifests.
- **Large local/public panels**: the tracked `data_sp500/` panel and its
  inventory/derived-enrichment path, which are useful but have provenance and
  survivorship questions that should be cleaned before serious claims.
- **Public/free refresh sources**: Ken French factors, FRED/Treasury/macro
  regimes, public OHLCV and benchmark series, CBOE volatility indexes, SEC
  EDGAR, FINRA/SEC short-sale and fails data, and public constituent snapshots.
- **Private/vendor/platform expansions**: account or platform exports, broker
  fills, GitHub CI logs, Norgate/Polygon/Tiingo/Sharadar/S&P/FactSet/Refinitiv,
  securities-lending data, options/quotes/order-book data, news/sentiment, and
  specialized alternative data.

The highest non-WRDS priority is not to acquire exotic data. It is to preserve
the current project truth: verify the tracked sample/public inputs, restore or
regenerate missing local source artifacts for the public run, preserve the small
curated public/WRDS aggregate artifacts, and keep factor/baseline inputs pinned
with provenance. For future non-WRDS credibility, the best next step is a
shareable, non-degenerate public benchmark package with documented source,
corporate actions, constituents, market/risk-free baselines, and leakage-safe
data manifests.

## Machine-Readable Map

```yaml
project:
  name: "microalpha"
  repo_path: "/Volumes/Storage/Projects/microalpha/repo"
  analysis_timestamp_utc: "2026-07-08T01:14:18Z"
  purpose: "Leakage-safe event-driven quant backtesting and walk-forward validation with evidence-backed sample, public, and WRDS workflows."
  current_non_wrds_dependency_summary: "Current non-WRDS dependencies include tracked synthetic sample data, a tracked public mini-panel, tracked sample/public result artifacts, local run logs, factor CSV snippets, a large tracked S&P 500-style panel, data-policy manifests, and curated resume-safe aggregate artifacts. Missing local source artifacts for current public and WRDS-derived runs should be restored or regenerated; raw WRDS and private/vendor data remain out of repo."

requirements:
  - requirement_id: "NWRDS-N0-001-bundled-sample-price-panel"
    priority: "N0_BLOCKING"
    dataset_name: "Bundled synthetic sample price panel"
    source_type: "local_artifact"
    source_owner_or_provider: "microalpha repository"
    source_url_or_location: "data/sample/prices/*.csv and data/sample/prices_sample.csv"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Reproduce README sample workflows, CI tests, leakage checks, and demo reports without external data."
    quant_use_case: "Deterministic multi-symbol event streams for strategy, execution, walk-forward, baseline, cost, and factor-report smoke tests."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: false
    date_range:
      minimum_required: "2020-01-02 to 2021-12-31"
      optimal: "Current tracked sample window with stable hashes"
    frequency: "daily"
    expected_size_class: "small"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo: data/sample/prices/"
    safe_to_commit_to_repo: true
    required_user_action: "None unless sample fixtures are intentionally regenerated."
    acquisition_method: "Use tracked repository files; regenerate only through a documented fixture generator if one is added."
    validation_method: "make test-fast; artifact schema tests; config paths in configs/flagship_sample.yaml and configs/wfv_flagship_sample*.yaml"
    joins_to_wrds_or_project_data: ["configs/flagship_sample.yaml", "configs/wfv_flagship_sample.yaml", "configs/wfv_flagship_sample_holdout.yaml", "artifacts/sample_*"]
    bias_or_leakage_risks: ["Synthetic data is not investment evidence.", "Fixture dates must remain within configured windows.", "Do not tune public claims on synthetic sample metrics."]
    notes: "This is a demo/CI dataset, not an alpha dataset."

  - requirement_id: "NWRDS-N0-002-bundled-sample-metadata-universe-rf"
    priority: "N0_BLOCKING"
    dataset_name: "Bundled sample metadata, universe, and risk-free snippets"
    source_type: "local_artifact"
    source_owner_or_provider: "microalpha repository"
    source_url_or_location: "data/sample/meta_sample.csv, data/sample/universe_sample.csv, data/sample/rf_sample.csv"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Provide liquidity, sector, borrow/spread, universe, and RF inputs for sample workflows and reporting tests."
    quant_use_case: "Sector caps, ADV filters, borrow/cost metadata coverage, monthly universe snapshots, and cash/risk-free baselines."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: false
    date_range:
      minimum_required: "2019-01-02 to 2021-12-31 depending on file"
      optimal: "Current tracked fixture coverage"
    frequency: "mixed"
    expected_size_class: "small"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo: data/sample/"
    safe_to_commit_to_repo: true
    required_user_action: "None."
    acquisition_method: "Use tracked fixture files."
    validation_method: "make test-fast; cost/metadata coverage tests; sample WFV reports"
    joins_to_wrds_or_project_data: ["src/microalpha/market_metadata.py", "src/microalpha/reporting/baselines.py", "artifacts/sample_wfv/*"]
    bias_or_leakage_risks: ["Universe rows are synthetic and should not be interpreted as point-in-time real universe evidence.", "RF sample cadence must be aligned explicitly."]
    notes: "Critical for offline reproducibility and cost-model sanity checks."

  - requirement_id: "NWRDS-N0-003-tracked-sample-result-artifacts"
    priority: "N0_BLOCKING"
    dataset_name: "Tracked sample run artifacts"
    source_type: "derived_dataset"
    source_owner_or_provider: "microalpha repository"
    source_url_or_location: "artifacts/sample_flagship/, artifacts/sample_wfv/, artifacts/sample_wfv_holdout/"
    access_status: "available_now"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Support README sample result tables, artifact schema tests, documentation links, and regression checks."
    quant_use_case: "Metrics, equity curves, bootstrap summaries, folds, cost_sensitivity, metadata_coverage, trades, and plots for deterministic fixtures."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: false
    date_range:
      minimum_required: "Sample run windows recorded in each manifest"
      optimal: "All tracked fixture artifacts with manifests and config hashes"
    frequency: "mixed"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo: artifacts/sample_* for small committed fixtures"
    safe_to_commit_to_repo: true
    required_user_action: "None; regenerate only if README/sample claims are intentionally refreshed."
    acquisition_method: "Run make sample, make wfv, or configured sample WFV holdout commands; keep run manifests."
    validation_method: "tests/test_artifacts_schema.py; tests/test_docs_links.py; make test-fast"
    joins_to_wrds_or_project_data: ["README.md", "reports/summaries/flagship_mom*.md", "project_state/CURRENT_RESULTS.md"]
    bias_or_leakage_risks: ["Do not overstate synthetic artifact metrics.", "Manifest config paths from older machines may differ from current checkout paths."]
    notes: "Current README sample claims depend on these tracked artifacts."

  - requirement_id: "NWRDS-N0-004-public-mini-panel-inputs"
    priority: "N0_BLOCKING"
    dataset_name: "Tracked public mini-panel inputs"
    source_type: "local_artifact"
    source_owner_or_provider: "microalpha repository, derived from public ticker samples"
    source_url_or_location: "data/public/prices/*.csv, data/public/meta_public.csv, data/public/universe_public.csv"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Reproduce the current public mini-panel pipeline/demo evidence and validate dataset hash provenance."
    quant_use_case: "Shareable small real-symbol panel for non-WRDS pipeline smoke, public WFV config, and resume-safe aggregate artifact provenance."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2024-01-02 to 2024-01-12"
      optimal: "At least 3 to 5 years of public OHLCV plus corporate actions for non-degenerate public benchmark"
    frequency: "daily"
    expected_size_class: "tiny"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo: data/public/"
    safe_to_commit_to_repo: true
    required_user_action: "None for current files; user/Pro should approve any public benchmark rebuild."
    acquisition_method: "Use tracked files for current reproduction; future refresh via documented public API or bulk source with hashes."
    validation_method: "Hash manifest in docs/artifacts/resume/public/.../manifest_excerpt.json; make test-fast; public WFV command"
    joins_to_wrds_or_project_data: ["configs/wfv_flagship_public.yaml", "docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/manifest_excerpt.json"]
    bias_or_leakage_risks: ["Current run is degenerate with zero trades.", "Small hand-curated universe is not representative.", "Corporate-action provenance is not enough for serious performance claims."]
    notes: "Safe as pipeline evidence only; not alpha evidence."

  - requirement_id: "NWRDS-N0-005-public-mini-panel-curated-resume-artifacts"
    priority: "N0_BLOCKING"
    dataset_name: "Curated public mini-panel resume artifacts"
    source_type: "derived_dataset"
    source_owner_or_provider: "microalpha repository"
    source_url_or_location: "docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/ and docs/artifacts/resume/public/resume_line_best.md"
    access_status: "available_now"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Preserve current public-run truth and prevent degenerate pipeline evidence from being misread as performance evidence."
    quant_use_case: "Aggregate metrics, manifest excerpt, dataset hash, and explicitly caveated resume line for public mini-panel WFV."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: false
    date_range:
      minimum_required: "2024-01-02 to 2024-01-12"
      optimal: "Current tracked artifact plus regenerated source run if needed"
    frequency: "mixed"
    expected_size_class: "tiny"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo: docs/artifacts/resume/public/"
    safe_to_commit_to_repo: true
    required_user_action: "None; maintain caveat that run has zero trades."
    acquisition_method: "Use tracked artifact files; regenerate from local public run only if source artifacts are restored/rebuilt."
    validation_method: "project_state/CURRENT_EVIDENCE_SUMMARY.md cross-check; make check-data-policy"
    joins_to_wrds_or_project_data: ["data/public/*", "configs/wfv_flagship_public.yaml", "project_state/CLAIMS_AND_EVIDENCE.md"]
    bias_or_leakage_risks: ["Risk is wording, not data leakage: this must remain demo-only.", "Config hash mismatch in manifest excerpt should be resolved before exact config-hash claims."]
    notes: "N0 because it records current project/account truth."

  - requirement_id: "NWRDS-N0-006-missing-public-source-run-artifacts"
    priority: "N0_BLOCKING"
    dataset_name: "Missing source artifacts for public mini-panel run"
    source_type: "derived_dataset"
    source_owner_or_provider: "microalpha local run outputs"
    source_url_or_location: "artifacts/_local/20260217_010106_ticket-37_public-mini-panel-resume-metrics/... and reports/_runs/20260217_010106_ticket-37_public-mini-panel-resume-metrics/wfv_flagship_public.md"
    access_status: "unknown"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Recover exact source evidence behind the current curated public mini-panel artifact."
    quant_use_case: "Full manifest, metrics, bootstrap, reality_check, report, and run-local provenance for audit-grade reproduction."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: false
    date_range:
      minimum_required: "2024-01-02 to 2024-01-12"
      optimal: "Exact run_id 2026-02-17T01-02-27Z-98beced source artifacts"
    frequency: "mixed"
    expected_size_class: "small"
    refresh_cadence: "one_time"
    storage_target: "ignored local artifact zone: artifacts/_local/ and reports/_runs/"
    safe_to_commit_to_repo: false
    required_user_action: "Restore from prior machine/backups or authorize regeneration of the public WFV run."
    acquisition_method: "Recover local run directory or rerun microalpha wfv --config configs/wfv_flagship_public.yaml --out artifacts/_local/<run>/wfv_flagship_public."
    validation_method: "Compare run_id, config hash, dataset hash, metrics, and degenerate status against curated artifacts."
    joins_to_wrds_or_project_data: ["docs/artifacts/resume/public/2026-02-17T01-02-27Z-98beced/metrics.json"]
    bias_or_leakage_risks: ["Regeneration may produce a different config hash or run_id unless exact historical checkout is restored.", "Do not overwrite current curated artifact without recording provenance drift."]
    notes: "These are missing in the current checkout according to project_state/CURRENT_EVIDENCE_SUMMARY.md."

  - requirement_id: "NWRDS-N0-007-large-local-sp500-style-panel"
    priority: "N0_BLOCKING"
    dataset_name: "Tracked S&P 500-style daily panel"
    source_type: "local_artifact"
    source_owner_or_provider: "unknown public/local source"
    source_url_or_location: "data_sp500/*.csv"
    access_status: "available_now"
    data_policy_status: "unknown"
    project_need: "Preserve and characterize the large non-WRDS panel used by cross-sectional momentum configs and data inventory docs."
    quant_use_case: "Non-WRDS cross-sectional momentum tests, public-market research prototypes, liquidity diagnostics, and broad benchmark experiments."
    required_for_current_reproduction: true
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-01-03 to 2024-12-31 as documented in reports/data_inventory_sp500.json"
      optimal: "Provenance-pinned, survivorship-controlled panel with delisted names and corporate actions"
    frequency: "daily"
    expected_size_class: "large"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo currently; future large refresh should move to shared vault with curated subset in repo"
    safe_to_commit_to_repo: true
    required_user_action: "Confirm original source/licensing and whether the tracked panel should remain in git long term."
    acquisition_method: "Use current tracked files; future rebuild should use a documented public or licensed provider and manifest hashes."
    validation_method: "reports/data_inventory_sp500.json; docs/data_sp500.md; scripts/augment_sp500.py sanity checks"
    joins_to_wrds_or_project_data: ["configs/wfv_cs_mom*.yaml", "scripts/augment_sp500.py", "scripts/build_flagship_universe.py"]
    bias_or_leakage_risks: ["Likely survivorship and constituent-history risk unless source is proven PIT.", "Missing/non-positive volume issues exist.", "Ticker reuse and corporate actions require audit."]
    notes: "Tracked size is about 94.8 MB across 936 files; keep out of bundles unless explicitly needed."

  - requirement_id: "NWRDS-N0-008-sp500-inventory-and-enrichment-artifacts"
    priority: "N0_BLOCKING"
    dataset_name: "S&P 500 panel inventory, sector overrides, and enrichment outputs"
    source_type: "derived_dataset"
    source_owner_or_provider: "microalpha repository"
    source_url_or_location: "reports/data_inventory_sp500.json, metadata/sp500_sector_overrides.csv, expected data_sp500_enriched/, metadata/sp500_enriched.csv, data/flagship_universe/all.csv"
    access_status: "available_now"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Document quality of data_sp500 and support non-WRDS flagship universe construction."
    quant_use_case: "Missingness audit, sector metadata, ADV/market-cap proxy enrichment, liquidity filters, and monthly universe snapshots."
    required_for_current_reproduction: true
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-01-03 to 2024-12-31 inventory; enrichment outputs are currently expected but not present as tracked current artifacts"
      optimal: "Versioned enrichment package with source maps, per-symbol stats, hashes, and PIT constituent metadata"
    frequency: "mixed"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo for small manifests/overrides; shared vault or ignored local zone for enriched panel"
    safe_to_commit_to_repo: true
    required_user_action: "Confirm whether to regenerate enriched panel and flagship universe outside git."
    acquisition_method: "Run scripts/augment_sp500.py then scripts/build_flagship_universe.py using approved source panel and sector maps."
    validation_method: "Check reports/data_sp500_cleaning.json and reports/flagship_universe_summary.json if regenerated; inspect missing/UNKNOWN sector counts."
    joins_to_wrds_or_project_data: ["data_sp500/*.csv", "configs/flagship_mom.yaml", "configs/wfv_flagship_mom.yaml"]
    bias_or_leakage_risks: ["Current sector overrides are not complete PIT sector history.", "Market-cap proxy is heuristic, not shares-out truth.", "Generated all.csv can become stale versus source panel."]
    notes: "Important because flagship_mom configs currently reference data_sp500_enriched and data/flagship_universe/all.csv paths that may be absent."

  - requirement_id: "NWRDS-N0-009-local-factor-csvs"
    priority: "N0_BLOCKING"
    dataset_name: "Local factor CSV bundles"
    source_type: "local_artifact"
    source_owner_or_provider: "Ken French-style public factor data, normalized in repo"
    source_url_or_location: "data/factors/ff3_sample.csv and data/factors/ff5_mom_daily.csv"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Support README factor table, report factor regression, WRDS/public analytics, baselines, and factor-alignment tests."
    quant_use_case: "FF3, Carhart, FF5+MOM factor regression, risk-free return alignment, rolling betas, and cash baseline."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "FF3 sample 2020-2021; FF5+MOM daily from 2010 onward for current report windows"
      optimal: "Full current Ken French daily and monthly FF3, FF5, MOM, industry portfolios, and RF through latest available"
    frequency: "mixed"
    expected_size_class: "small"
    refresh_cadence: "monthly"
    storage_target: "project repo for small pinned factor CSVs; shared vault for full refresh archive"
    safe_to_commit_to_repo: true
    required_user_action: "None for current files; approve refresh cadence and source pinning for full factor history."
    acquisition_method: "Use tracked files now; future refresh from Ken French Data Library with source URL, download timestamp, and hash manifest."
    validation_method: "tests/test_factor_regression.py; tests/test_factor_alignment.py; reports/factors.py smoke on artifacts"
    joins_to_wrds_or_project_data: ["reports/factors.py", "reports/analytics.py", "src/microalpha/reporting/factors.py", "src/microalpha/reporting/baselines.py"]
    bias_or_leakage_risks: ["Factor frequency must match or be explicitly resampled.", "Do not forward-fill lower-frequency factors into daily returns.", "Factor library revisions can change exact historical numbers."]
    notes: "The WRDS map also lists WRDS-served Fama-French tables; this row is the non-WRDS/public-source equivalent."

  - requirement_id: "NWRDS-N0-010-run-logs-manifests-and-state-artifacts"
    priority: "N0_BLOCKING"
    dataset_name: "Project run logs, manifests, and current state artifacts"
    source_type: "local_artifact"
    source_owner_or_provider: "microalpha repository and Codex run logs"
    source_url_or_location: "docs/agent_runs/, reports/_runs/, reports/summaries/runs_index.csv, metadata/codex_sessions.md, project_state/"
    access_status: "available_now"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Preserve project/account truth, commands, dataset IDs, validation evidence, and claim caveats across sessions."
    quant_use_case: "Audit trail for exact commands, run IDs, configs, dataset hashes, validation gates, and artifact provenance."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "All current tracked run logs and state docs"
      optimal: "All future runs with standard PROMPT, COMMANDS, RESULTS, TESTS, META, and manifest hashes"
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo for tracked run logs/state; reports/_runs for bulky local logs"
    safe_to_commit_to_repo: true
    required_user_action: "None; continue run-log discipline."
    acquisition_method: "Generated by repo scripts and Codex ticket workflow."
    validation_method: "make validate-runlogs; make test-fast"
    joins_to_wrds_or_project_data: ["scripts/validate_run_logs.py", "scripts/build_runs_index.py", "project_state/CURRENT_RESULTS.md", "project_state/CLAIMS_AND_EVIDENCE.md"]
    bias_or_leakage_risks: ["Logs can become stale if artifacts are moved.", "Do not include credentials or raw data paths with secrets.", "Archived docs are history, not current truth."]
    notes: "This is data in the project-state sense: not market data, but required to validate claims."

  - requirement_id: "NWRDS-N0-011-missing-current-wrds-derived-source-artifacts"
    priority: "N0_BLOCKING"
    dataset_name: "Missing local source artifacts for current best WRDS-derived run"
    source_type: "derived_dataset"
    source_owner_or_provider: "microalpha local run outputs"
    source_url_or_location: "artifacts/_local/20260216_223228_ticket-35_wrds-micro-sweep/wrds_flagship/2026-02-16T22-33-46Z-8d90621/ and reports/_runs/20260216_223228_ticket-35_wrds-micro-sweep/"
    access_status: "unknown"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Validate current best WRDS aggregate claims without exposing raw WRDS data."
    quant_use_case: "Source metrics, holdout metrics, manifests, reality_check, grid_returns, signals, reports, plots, and factor tables for audit-grade evidence."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: false
    date_range:
      minimum_required: "Selection 2013-01-02 to 2017-12-29; holdout 2018-01-02 to 2019-12-31"
      optimal: "Exact run_id 2026-02-16T22-33-46Z-8d90621 source artifacts plus regenerated L3 reproduction"
    frequency: "mixed"
    expected_size_class: "medium"
    refresh_cadence: "one_time"
    storage_target: "ignored local artifact zone; promote only small aggregate artifacts to docs/artifacts/"
    safe_to_commit_to_repo: false
    required_user_action: "Restore local artifacts from backup or regenerate after WRDS data root is restored; do not copy raw WRDS into repo."
    acquisition_method: "Restore artifact directories or rerun configured WRDS pipeline once WRDS_DATA_ROOT is available."
    validation_method: "Compare metrics and config hashes against docs/artifacts/resume/wrds/leaderboard and project_state/CURRENT_EVIDENCE_SUMMARY.md."
    joins_to_wrds_or_project_data: ["docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/", "project_state/WRDS_DATA_REQUIREMENTS.md"]
    bias_or_leakage_risks: ["Raw WRDS must remain excluded.", "Current manifest excerpt has config-hash mismatch.", "Regeneration may not reproduce historical run if data export changed."]
    notes: "Although derived from WRDS, this row is included because the deliverable is local aggregate artifacts, not WRDS data acquisition."

  - requirement_id: "NWRDS-N0-012-data-policy-allowlist-and-scan-results"
    priority: "N0_BLOCKING"
    dataset_name: "Data-policy guardrail surfaces"
    source_type: "local_artifact"
    source_owner_or_provider: "microalpha repository"
    source_url_or_location: "scripts/data_policy_allowlist.txt, scripts/check_data_policy.py, validation logs"
    access_status: "available_now"
    data_policy_status: "derived_safe_if_aggregated"
    project_need: "Prevent raw restricted data from being accidentally committed or bundled while allowing safe aggregates."
    quant_use_case: "Data governance and release safety for WRDS, vendor, account, and large local artifacts."
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current repository state"
      optimal: "Every ticket touching data-like files"
    frequency: "event"
    expected_size_class: "tiny"
    refresh_cadence: "ad_hoc"
    storage_target: "project repo plus run logs"
    safe_to_commit_to_repo: true
    required_user_action: "None."
    acquisition_method: "Generated by running make check-data-policy."
    validation_method: "make check-data-policy"
    joins_to_wrds_or_project_data: ["AGENTS.md", "TRACKING_POLICY.md", ".gitignore", "reports/_runs/*/VALIDATION.md"]
    bias_or_leakage_risks: ["Allowlist drift can hide restricted data if reviewed casually.", "Keyword scans are not a substitute for manual inspection of new vendor files."]
    notes: "Treat as a required control dataset for future data work."

  - requirement_id: "NWRDS-N1-013-ken-french-public-factor-library-refresh"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Ken French public factor library full refresh"
    source_type: "public_bulk_download"
    source_owner_or_provider: "Kenneth R. French Data Library"
    source_url_or_location: "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Replace snippets with source-pinned full factor histories for stronger baselines and claim validation."
    quant_use_case: "FF3, FF5, momentum, short-term reversal, long-term reversal, industry portfolios, RF, factor timing, regime controls, and factor-neutral diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current result windows plus public mini-panel window"
      optimal: "Earliest available to latest available, daily and monthly"
    frequency: "mixed"
    expected_size_class: "small"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/ken_french/ with curated CSVs in data/factors/"
    safe_to_commit_to_repo: true
    required_user_action: "Approve whether full factor files should be committed or only pinned snippets."
    acquisition_method: "Manual/public bulk download with manifest; normalize columns to Mkt_RF, SMB, HML, RMW, CMA, MOM, RF."
    validation_method: "Check dates, frequency, percent-to-decimal conversion, no forward-fill, hash manifest, factor regression smoke."
    joins_to_wrds_or_project_data: ["data/factors/ff3_sample.csv", "data/factors/ff5_mom_daily.csv", "reports/factors.py"]
    bias_or_leakage_risks: ["Factor files may be revised.", "Percent versus decimal conversion errors can dominate reports.", "Use only data available by evaluation date for real-time claims if needed."]
    notes: "Easy, high-value, public, and should be the canonical non-WRDS factor source."

  - requirement_id: "NWRDS-N1-014-fred-treasury-macro-rates"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "FRED, Treasury, and macro regime series"
    source_type: "public_api"
    source_owner_or_provider: "Federal Reserve Economic Data, U.S. Treasury, NBER"
    source_url_or_location: "FRED API or CSV exports; Treasury daily rates; NBER recession dates"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Improve risk-free baselines, rate-regime diagnostics, and macro stress reporting."
    quant_use_case: "SOFR/Fed Funds/T-bill cash proxy, yield curve slope, inflation/unemployment regimes, recession bucket metrics, 2008/2020/rate-hike regime controls."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for data_sp500 and future public benchmark"
      optimal: "Earliest available to latest available with vintage metadata if doing real-time macro signals"
    frequency: "mixed"
    expected_size_class: "small"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/macro_public/"
    safe_to_commit_to_repo: true
    required_user_action: "Optional FRED API key if higher rate limits are desired; otherwise use public CSV/manual export."
    acquisition_method: "Public API or bulk CSV with source and observation_date/vintage_date where available."
    validation_method: "Calendar alignment, units checks, vintage/as-of checks, hash manifest."
    joins_to_wrds_or_project_data: ["src/microalpha/reporting/baselines.py", "future regime_metrics.csv"]
    bias_or_leakage_risks: ["Lookahead if revised macro data or release dates are ignored.", "Forward-filling monthly/quarterly macro series into daily signals needs as-of release discipline."]
    notes: "Best public complement to WRDS and public equities for regime-aware reporting."

  - requirement_id: "NWRDS-N1-015-public-benchmark-market-series"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Public benchmark ETF and index proxy series"
    source_type: "public_api"
    source_owner_or_provider: "Stooq, Yahoo Finance, Nasdaq Data Link public/free, or similar public provider"
    source_url_or_location: "SPY, QQQ, IWM, sector ETFs, broad index proxies"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Strengthen non-WRDS and public benchmark comparisons."
    quant_use_case: "Market proxy, buy-and-hold comparison, sector-regime diagnostics, public demo baselines, and sanity checks for flagship returns."
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current sample/public windows"
      optimal: "2005-present or earliest available to latest"
    frequency: "daily"
    expected_size_class: "small"
    refresh_cadence: "monthly"
    storage_target: "shared vault plus curated safe repo CSVs such as data/benchmarks/"
    safe_to_commit_to_repo: true
    required_user_action: "Choose canonical public provider and license posture."
    acquisition_method: "Public API or CSV download; store adjusted close, raw close, volume, splits/dividends if available."
    validation_method: "Compare overlapping providers; validate adjusted returns; ensure no duplicate dates; hash source files."
    joins_to_wrds_or_project_data: ["src/microalpha/reporting/baselines.py expects SPY.csv or market_proxy.csv", "configs/* symbol: SPY"]
    bias_or_leakage_risks: ["ETF inception limits history.", "Adjusted close methodology differs by provider.", "Public APIs can revise or throttle."]
    notes: "A clean SPY/QQQ/IWM/sector benchmark pack would immediately improve non-WRDS reports."

  - requirement_id: "NWRDS-N1-016-public-equity-ohlcv-refresh"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Public equity OHLCV refresh package"
    source_type: "public_api"
    source_owner_or_provider: "Stooq, Yahoo Finance, Alpha Vantage free, IEX Cloud public/free tiers, or selected public provider"
    source_url_or_location: "Provider-specific bulk/API endpoint"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Refresh public mini-panel and optionally rebuild data_sp500 with documented provenance."
    quant_use_case: "Shareable non-WRDS benchmark, latest holdout/live-era public tests, daily liquidity filters, and public demos."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for fresh non-WRDS holdout"
      optimal: "2005-present with delisted/history support if provider allows"
    frequency: "daily"
    expected_size_class: "medium"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/public_equities/; curated small panels in project repo"
    safe_to_commit_to_repo: true
    required_user_action: "Select provider and confirm terms permit local storage/redistribution of curated snippets."
    acquisition_method: "Provider API/download with manifest, symbol list, calendar, corporate-action fields, and hashes."
    validation_method: "Schema checks, missingness report, provider cross-checks, split/dividend event checks, config smoke."
    joins_to_wrds_or_project_data: ["data/public/prices/", "data_sp500/", "scripts/augment_sp500.py"]
    bias_or_leakage_risks: ["Survivorship if symbol list is current-only.", "Adjusted prices can use future corporate-action knowledge.", "Ticker changes and delistings are weak in many free sources."]
    notes: "Use for shareable evidence, not as a replacement for WRDS/CRSP prestige evidence."

  - requirement_id: "NWRDS-N1-017-public-corporate-actions-calendar"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Public splits, dividends, and corporate-action calendar"
    source_type: "public_api"
    source_owner_or_provider: "Yahoo/Stooq/Nasdaq/public exchange feeds or selected public provider"
    source_url_or_location: "Provider-specific corporate actions endpoints or CSVs"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Audit adjusted-price correctness and improve public benchmark credibility."
    quant_use_case: "Split/dividend adjustment validation, total-return calculation, event-date leakage checks, and price-panel reconciliation."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "All public benchmark/security windows"
      optimal: "Earliest available to latest for all public panel symbols"
    frequency: "event"
    expected_size_class: "small"
    refresh_cadence: "monthly"
    storage_target: "shared vault plus small manifest summaries in project_state/"
    safe_to_commit_to_repo: true
    required_user_action: "Choose provider and decide whether event details can be committed."
    acquisition_method: "Public provider event exports with ex-date/pay-date/ratio/cash amount fields."
    validation_method: "Check large return days against split events; compare adjusted/raw price continuity."
    joins_to_wrds_or_project_data: ["data/public/prices/", "data_sp500/*.csv", "future data_hygiene.json"]
    bias_or_leakage_risks: ["Using final adjusted prices can embed future corporate actions.", "Dividend reinvestment assumptions must match benchmark claims."]
    notes: "Essential before a public non-WRDS panel becomes performance evidence."

  - requirement_id: "NWRDS-N1-018-public-constituent-and-sector-snapshots"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Public index constituent and sector snapshots"
    source_type: "public_bulk_download"
    source_owner_or_provider: "Wikipedia, public S&P 500 lists, archived pages, SEC/company metadata"
    source_url_or_location: "Wikipedia current and historical snapshots, public archives, local metadata/sp500_sector_overrides.csv"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Improve non-WRDS universe construction and document survivorship limitations."
    quant_use_case: "Sector-neutral public benchmark, approximate constituent snapshots, sector caps, and universe audit trail."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for new public holdout"
      optimal: "2005-present monthly PIT snapshots"
    frequency: "monthly"
    expected_size_class: "small"
    refresh_cadence: "quarterly"
    storage_target: "shared vault for raw snapshots; project repo for curated small universe manifests"
    safe_to_commit_to_repo: true
    required_user_action: "Approve use of approximate public constituent history versus licensed PIT data."
    acquisition_method: "Archive public pages or curated public CSVs; hash each snapshot and record retrieval date."
    validation_method: "Compare current lists to known benchmark constituents; flag additions/deletions and missing sectors."
    joins_to_wrds_or_project_data: ["metadata/sp500_sector_overrides.csv", "scripts/build_flagship_universe.py", "data_sp500/"]
    bias_or_leakage_risks: ["Public current lists are survivorship biased.", "Archived snapshots can miss intra-month changes.", "GICS sector labels may be current rather than historical."]
    notes: "For high-stakes claims, prefer Norgate/S&P/WRDS PIT constituents; use this for public/demo benchmarks."

  - requirement_id: "NWRDS-N1-019-sec-edgar-public-company-data"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "SEC EDGAR company facts, filings, and ticker-CIK mapping"
    source_type: "public_bulk_download"
    source_owner_or_provider: "U.S. Securities and Exchange Commission"
    source_url_or_location: "SEC companyfacts, submissions, ticker mapping, bulk filing downloads"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Support public fundamentals, filing-event features, identifier hygiene, and future research extensions."
    quant_use_case: "PIT-ish fundamentals with filing dates, earnings/fundamental event controls, ticker/CIK mapping, restatement diagnostics, and post-filing signal experiments."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for modern public experiments"
      optimal: "Earliest EDGAR structured data to latest"
    frequency: "event"
    expected_size_class: "large"
    refresh_cadence: "weekly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/sec_edgar/"
    safe_to_commit_to_repo: false
    required_user_action: "None beyond respecting SEC fair-access headers and rate limits."
    acquisition_method: "SEC bulk/API downloads with user-agent, local manifest, accession numbers, filing dates, and source hashes."
    validation_method: "Validate CIK/ticker mapping, accession uniqueness, filing date chronology, and XBRL units."
    joins_to_wrds_or_project_data: ["data_sp500 symbols", "future feature pipeline", "project_state/CLAIMS_AND_EVIDENCE.md"]
    bias_or_leakage_risks: ["Use filing acceptance date, not period end, for as-of features.", "Restatements and amended filings require explicit handling.", "Ticker-CIK mapping changes over time."]
    notes: "Strong public feature source for non-WRDS expansion."

  - requirement_id: "NWRDS-N1-020-cboe-volatility-indexes"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Cboe volatility and option-implied regime indexes"
    source_type: "public_bulk_download"
    source_owner_or_provider: "Cboe"
    source_url_or_location: "Cboe public historical CSVs for VIX, VIX9D, VIX3M, VVIX, SKEW if available"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Add volatility-regime context and baseline stress diagnostics."
    quant_use_case: "Volatility regimes, crisis buckets, drawdown conditioning, cost stress proxies, and option-implied risk controls."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present for data_sp500 experiments"
      optimal: "Earliest available to latest"
    frequency: "daily"
    expected_size_class: "small"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/cboe/"
    safe_to_commit_to_repo: true
    required_user_action: "None if using public CSVs; confirm redistribution posture before committing full files."
    acquisition_method: "Public CSV downloads with source URL and hash manifest."
    validation_method: "Date/calendar alignment, duplicate checks, level sanity, and regime-bucket report."
    joins_to_wrds_or_project_data: ["future regime_metrics.csv", "reports/analytics.py"]
    bias_or_leakage_risks: ["Index methodology changes over time.", "Do not use same-day close VIX to decide trades filled earlier that day without a timing rule."]
    notes: "High signal for diagnostics, not necessarily alpha."

  - requirement_id: "NWRDS-N1-021-finra-sec-short-sale-and-ftd-public-data"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "FINRA short volume, Reg SHO, and SEC fails-to-deliver public data"
    source_type: "public_bulk_download"
    source_owner_or_provider: "FINRA and SEC"
    source_url_or_location: "FINRA short sale volume files; SEC fails-to-deliver CSVs"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Add public shorting pressure, borrow stress proxies, and diagnostics for long-short feasibility."
    quant_use_case: "Short-leg crowding, short-volume ratio, fail-to-deliver risk, borrow-cost proxy, and capacity/shortability diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for modern holdout"
      optimal: "Earliest available to latest"
    frequency: "mixed"
    expected_size_class: "medium"
    refresh_cadence: "weekly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/short_sale_public/"
    safe_to_commit_to_repo: false
    required_user_action: "None; confirm terms before redistributing derived per-symbol history."
    acquisition_method: "Public bulk downloads with symbol/date partitions and manifest."
    validation_method: "Ticker/date parse checks, exchange/source code checks, join coverage to universe, outlier diagnostics."
    joins_to_wrds_or_project_data: ["data_sp500 symbols", "src/microalpha/market_metadata.py", "future borrow proxy fields"]
    bias_or_leakage_risks: ["Short volume is not short interest.", "Settlement/fail dates must be handled as-of.", "Ticker changes and OTC/exchange coverage differ."]
    notes: "Useful public proxy when paid borrow/short-interest data is unavailable."

  - requirement_id: "NWRDS-N1-022-public-holiday-and-trading-calendar"
    priority: "N1_PUBLIC_CORE"
    dataset_name: "Exchange calendars and holiday schedules"
    source_type: "public_bulk_download"
    source_owner_or_provider: "NYSE/Nasdaq public calendars or exchange-calendars package metadata"
    source_url_or_location: "Public exchange calendars and package-pinned calendar definitions"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Make calendar alignment, missing days, and cross-source joins auditable."
    quant_use_case: "Trading-day validation, walk-forward fold boundaries, factor/returns alignment, holiday gaps, and intraday session checks."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "All tested data windows"
      optimal: "Earliest data date to latest available"
    frequency: "static"
    expected_size_class: "tiny"
    refresh_cadence: "quarterly"
    storage_target: "project repo for pinned calendar config; shared vault for source exports"
    safe_to_commit_to_repo: true
    required_user_action: "None."
    acquisition_method: "Pin package version or public calendar CSV with source hash."
    validation_method: "Assert price/factor series dates are subsets of valid trading sessions unless intentionally non-trading."
    joins_to_wrds_or_project_data: ["walk-forward configs", "src/microalpha/data.py", "tests/test_time_ordering.py"]
    bias_or_leakage_risks: ["Half-days and unscheduled closures can distort intraday/volume assumptions.", "Calendar mismatch can create hidden forward-fill leakage."]
    notes: "Small but high leverage for data hygiene."

  - requirement_id: "NWRDS-N2-023-github-ci-and-pages-artifacts"
    priority: "N2_PLATFORM_EXPORTS"
    dataset_name: "GitHub Actions CI and Pages deployment logs"
    source_type: "platform_export"
    source_owner_or_provider: "GitHub"
    source_url_or_location: "GitHub Actions workflow runs for mateobodon/microalpha"
    access_status: "needs_credentials"
    data_policy_status: "private_account_data"
    project_need: "Preserve external validation status, docs deploy evidence, and release-readiness history."
    quant_use_case: "Reproducibility and engineering evidence: CI pass/fail, docs build, lint/test matrix, artifacts from releases."
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current branch and latest main runs"
      optimal: "All release-tag and claim-update runs"
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "private account archive or reports/_runs summaries; do not commit bulky raw logs"
    safe_to_commit_to_repo: false
    required_user_action: "Authorize GitHub access/export if needed."
    acquisition_method: "GitHub UI/API export of selected workflow logs and artifacts; summarize paths and statuses."
    validation_method: "Compare commit SHA, workflow name, conclusion, and timestamp to repo claims."
    joins_to_wrds_or_project_data: [".github/workflows/ci.yml", ".github/workflows/docs.yml", "README badges"]
    bias_or_leakage_risks: ["CI logs may include environment details; inspect before sharing.", "External badge status can drift after local claims are written."]
    notes: "Useful for public/release confidence, not market alpha."

  - requirement_id: "NWRDS-N2-024-broker-paper-or-live-fill-exports"
    priority: "N2_PLATFORM_EXPORTS"
    dataset_name: "Broker/paper trading fills and execution reports"
    source_type: "platform_export"
    source_owner_or_provider: "IBKR, Alpaca, Tradier, broker/platform chosen by user"
    source_url_or_location: "User account exports or API reports"
    access_status: "needs_user_export"
    data_policy_status: "private_account_data"
    project_need: "Calibrate slippage/commission/borrow models if the project ever validates execution realism beyond simulation."
    quant_use_case: "Implementation shortfall, queue/latency calibration, commission/fee reconciliation, borrow availability, participation-rate sanity, and live-paper drift diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Representative paper/live test period if execution calibration is pursued"
      optimal: "All fills/orders/account statements for the calibration campaign"
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "private account archive outside repo; only anonymized aggregate summaries in project docs"
    safe_to_commit_to_repo: false
    required_user_action: "Explicit user export and approval; never use credentials automatically."
    acquisition_method: "Manual account export/API pull performed by user or with explicit scoped authorization."
    validation_method: "Reconcile fills to orders, timestamps, commissions, quantities, prices, and broker statement totals."
    joins_to_wrds_or_project_data: ["src/microalpha/execution.py", "src/microalpha/slippage.py", "src/microalpha/broker.py"]
    bias_or_leakage_risks: ["Private account data must not be exposed.", "Paper fills may not represent live liquidity.", "Calibration on strategy-generated fills can overfit execution model."]
    notes: "Not needed now because project is not a live trading system."

  - requirement_id: "NWRDS-N2-025-cloud-compute-run-logs"
    priority: "N2_PLATFORM_EXPORTS"
    dataset_name: "Cloud compute run logs and resource metrics"
    source_type: "platform_export"
    source_owner_or_provider: "AWS, GCP, local workstation, or CI provider"
    source_url_or_location: "Cloud console/API exports, tmux logs, resource-monitor outputs"
    access_status: "needs_user_export"
    data_policy_status: "private_account_data"
    project_need: "Support long WRDS/non-WRDS campaign reproducibility, runtime sizing, and cost control."
    quant_use_case: "Runtime/memory benchmarks, failed-run recovery, machine sizing, reproducibility of large sweeps, and performance-engineering evidence."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Future heavy campaign runs"
      optimal: "All long-running sweep executions with machine type, wall time, memory, and cost"
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "private ops archive; summarized in reports/_runs/"
    safe_to_commit_to_repo: false
    required_user_action: "Export only if a cloud/heavy run is launched."
    acquisition_method: "Cloud logging/API export or local resource monitor captured in run directory."
    validation_method: "Match logs to git SHA, config, command, run_id, and output artifact hashes."
    joins_to_wrds_or_project_data: ["reports/_runs/", "benchmarks/", "project_state/RUNBOOK.md"]
    bias_or_leakage_risks: ["Logs may include paths, machine names, or environment variables.", "Partial/failed runs must not be promoted as completed evidence."]
    notes: "Infrastructure evidence, not market data."

  - requirement_id: "NWRDS-N2-026-external-alpha-platform-exports"
    priority: "N2_PLATFORM_EXPORTS"
    dataset_name: "External alpha platform exports"
    source_type: "platform_export"
    source_owner_or_provider: "Numerai, WorldQuant BRAIN, Kaggle, QuantConnect, or similar platforms"
    source_url_or_location: "User account exports or public competition artifacts"
    access_status: "needs_user_export"
    data_policy_status: "private_account_data"
    project_need: "Optional future comparison between microalpha research workflow and platform alpha workflows."
    quant_use_case: "Benchmarking research process, comparing validation metrics, stress-testing feature ideas, and preserving account-specific results where relevant."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Only if a platform-comparison ticket is opened"
      optimal: "All relevant account exports with exact timestamps and platform metric definitions"
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "ad_hoc"
    storage_target: "private account archive; aggregate summaries only in repo"
    safe_to_commit_to_repo: false
    required_user_action: "Explicit user export/authorization; no submissions or account mutations."
    acquisition_method: "Manual export or read-only API access under a separate, approved ticket."
    validation_method: "Record platform metric definitions, export timestamp, model ID, and whether values are public/private."
    joins_to_wrds_or_project_data: ["docs/strategy/GOAL_CONTEXT.md", "future benchmark docs"]
    bias_or_leakage_risks: ["Account/private results can leak identity or strategy details.", "Platform validation schemes differ from microalpha WFV and must not be mixed casually."]
    notes: "Not a current dependency; included only as a plausible future quant-research comparison source."

  - requirement_id: "NWRDS-N3-027-norgate-survivorship-bias-free-equities"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Norgate Data survivorship-bias-free U.S. equities"
    source_type: "private_vendor"
    source_owner_or_provider: "Norgate Data"
    source_url_or_location: "Norgate local subscription/export"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Provide a non-WRDS survivorship-bias-controlled alternative for public/shareable workflow development."
    quant_use_case: "Delisted equities, historical index membership, adjusted OHLCV, corporate actions, sectors, broad U.S. universe, and out-of-sample public-like research."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present"
      optimal: "Earliest available to latest"
    frequency: "daily"
    expected_size_class: "large"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/norgate/"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription/license and export permissions."
    acquisition_method: "Vendor export outside repo with manifest and license notes."
    validation_method: "Check delisted coverage, index constituent snapshots, split/dividend adjustments, and symbol mapping."
    joins_to_wrds_or_project_data: ["data_sp500 replacement", "scripts/augment_sp500.py", "configs/wfv_cs_mom*.yaml"]
    bias_or_leakage_risks: ["License restricted.", "Vendor adjustment choices must be documented.", "PIT membership fields must be used as-of."]
    notes: "One of the strongest non-WRDS substitutes for survivorship-safe equity research."

  - requirement_id: "NWRDS-N3-028-commercial-ohlcv-api-modern-panel"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Commercial daily/intraday OHLCV API panel"
    source_type: "private_vendor"
    source_owner_or_provider: "Polygon.io, Tiingo, Intrinio, Nasdaq Data Link, IEX Cloud, or similar"
    source_url_or_location: "Vendor API or bulk export"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Extend non-WRDS holdouts to the latest live era and improve public panel robustness."
    quant_use_case: "Daily/intraday prices, volumes, corporate actions, quotes/trades, latest holdout/live-era validation, execution modeling, and benchmark refresh."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present"
      optimal: "2005-present daily plus 2018-present intraday/quotes if subscribed"
    frequency: "mixed"
    expected_size_class: "large"
    refresh_cadence: "daily"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/vendor_ohlcv/"
    safe_to_commit_to_repo: false
    required_user_action: "Choose provider, subscription, and license posture."
    acquisition_method: "Authenticated vendor API/export outside repo; store manifests and sample-safe summaries."
    validation_method: "Provider cross-check, split/dividend checks, missingness, timezone/calendar checks, and schema validation."
    joins_to_wrds_or_project_data: ["data/public refresh", "data_sp500 replacement", "examples/demo_minute_data.csv"]
    bias_or_leakage_risks: ["Vendor survivorship and delisting coverage varies.", "Terms may forbid redistribution.", "Intraday timestamps/timezones can create execution lookahead."]
    notes: "Useful when WRDS is unavailable or for post-WRDS latest-era checks."

  - requirement_id: "NWRDS-N3-029-sharadar-or-nasdaq-data-link-fundamentals"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Sharadar/Nasdaq Data Link fundamentals and equity data"
    source_type: "private_vendor"
    source_owner_or_provider: "Nasdaq Data Link / Sharadar or similar"
    source_url_or_location: "Vendor subscription datasets"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Add non-WRDS fundamental and corporate-action features with easier local export than raw SEC parsing."
    quant_use_case: "Value, quality, profitability, growth, revisions around filing dates, sector controls, and non-WRDS benchmark features."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2010-present"
      optimal: "Earliest available to latest with filing dates and restatement handling"
    frequency: "mixed"
    expected_size_class: "large"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/fundamentals_vendor/"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription and redistribution rules."
    acquisition_method: "Vendor bulk/API export with as-of/filing-date fields."
    validation_method: "Check point-in-time availability dates, restatements, unit scaling, identifier joins, and lookahead."
    joins_to_wrds_or_project_data: ["SEC EDGAR public data", "data_sp500 symbols", "future feature pipeline"]
    bias_or_leakage_risks: ["Fundamental restatements and filing-date lag are critical.", "Ticker-based joins are unsafe.", "License restrictions likely."]
    notes: "High value if the project expands beyond price momentum."

  - requirement_id: "NWRDS-N3-030-pit-constituents-gics-and-security-master"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Non-WRDS point-in-time constituents, GICS, and security master"
    source_type: "private_vendor"
    source_owner_or_provider: "S&P Global, FactSet, Refinitiv/LSEG, Bloomberg, Norgate, or similar"
    source_url_or_location: "Vendor subscription exports"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Control survivorship and sector-history risk in non-WRDS equity research."
    quant_use_case: "Historical index membership, ticker/CUSIP/ISIN mapping, GICS sector history, corporate actions, share classes, delistings, and universe as-of snapshots."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2005-present"
      optimal: "Earliest available to latest"
    frequency: "event"
    expected_size_class: "medium"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/security_master_vendor/"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm entitlement and allowed derived outputs."
    acquisition_method: "Vendor export with effective dates and stable identifiers."
    validation_method: "As-of join checks, ticker-change tests, sector drift reports, and missing identifier coverage."
    joins_to_wrds_or_project_data: ["metadata/sp500_sector_overrides.csv", "scripts/build_flagship_universe.py", "project_state/WRDS_DATA_REQUIREMENTS.md"]
    bias_or_leakage_risks: ["Latest-only sectors cause lookahead.", "Index membership must be effective-date aware.", "Identifier changes around mergers/spinoffs are fragile."]
    notes: "This is the non-WRDS version of a core WRDS/CRSP/Compustat control."

  - requirement_id: "NWRDS-N3-031-commercial-options-iv-and-greeks"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Commercial options implied volatility, Greeks, and surfaces"
    source_type: "private_vendor"
    source_owner_or_provider: "OptionMetrics direct, ORATS, Cboe DataShop, LiveVol, Polygon options, or similar"
    source_url_or_location: "Vendor subscription export"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Support volatility-regime, crash-risk, skew, and option-informed feature expansion."
    quant_use_case: "IV rank, skew, term structure, realized-vs-implied vol, option volume/open-interest, borrow proxies, volatility filters, and tail-risk diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present"
      optimal: "2005-present or earliest available to latest"
    frequency: "mixed"
    expected_size_class: "huge"
    refresh_cadence: "monthly"
    storage_target: "shared vault: /Volumes/Storage/Data/NON_WRDS/options_vendor/"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription and whether WRDS equivalent is already covered."
    acquisition_method: "Vendor export outside repo with symbol/security links and option-root mapping."
    validation_method: "Check option identifiers, expiration/strike calendars, no stale Greeks, underlying joins, and moneyness filters."
    joins_to_wrds_or_project_data: ["data_sp500 symbols", "future risk/regime feature pipeline"]
    bias_or_leakage_risks: ["Massive size.", "As-of IV surface construction can leak closing option quotes into same-day signals.", "Corporate action/option root changes are hard."]
    notes: "P3 because powerful but expensive/heavy."

  - requirement_id: "NWRDS-N3-032-intraday-quotes-trades-and-order-book"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Intraday quotes, trades, and order-book data"
    source_type: "private_vendor"
    source_owner_or_provider: "LOBSTER, Nasdaq TotalView/ITCH, Polygon, Cboe, NYSE TAQ direct, or similar"
    source_url_or_location: "Vendor/direct exchange exports"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Calibrate LOB simulation, VWAP/TWAP/slippage, latency, spread, and implementation-shortfall models."
    quant_use_case: "Bid/ask spreads, depth, queue position, volume curves, microstructure regimes, fill simulation, and market-making strategy validation."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Representative recent sample for symbols used in execution calibration"
      optimal: "2018-present for liquid U.S. equities and ETFs"
    frequency: "intraday"
    expected_size_class: "huge"
    refresh_cadence: "ad_hoc"
    storage_target: "shared vault only; commit only tiny synthetic examples"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription and target symbols/date windows before acquisition."
    acquisition_method: "Vendor/export outside repo with strict partitions and manifests."
    validation_method: "Timezone/session validation, NBBO sanity, crossed/locked quote filters, duplicate event checks, replay tests against LOB simulator."
    joins_to_wrds_or_project_data: ["src/microalpha/lob.py", "src/microalpha/execution.py", "examples/demo_minute_data.csv"]
    bias_or_leakage_risks: ["Huge data and strict licenses.", "Same-day signal/execution timing must be explicit.", "Survivorship if only current tickers are sampled."]
    notes: "Current LOB tests are synthetic; this would make execution modeling much more serious."

  - requirement_id: "NWRDS-N3-033-securities-lending-borrow-and-short-interest"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Borrow fees, lendable inventory, utilization, and short interest"
    source_type: "private_vendor"
    source_owner_or_provider: "S3 Partners, Markit/IHS, DataLend, Ortex, broker inventory, or similar"
    source_url_or_location: "Vendor/account exports"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Make long-short cost and shortability assumptions defensible."
    quant_use_case: "Borrow fee model, hard-to-borrow flags, short-sale feasibility, crowding, utilization, recall risk, and cost sensitivity."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "Current WRDS/public benchmark windows if shorting claims are made"
      optimal: "2010-present or earliest available to latest"
    frequency: "daily"
    expected_size_class: "large"
    refresh_cadence: "daily"
    storage_target: "private/vendor vault only; aggregate coverage stats in repo"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm entitlement and license; export only if short-leg realism becomes a claim gate."
    acquisition_method: "Vendor/API/account export with as-of dates and identifiers."
    validation_method: "Join coverage, fee outliers, missing short availability, date alignment to trade/fill dates."
    joins_to_wrds_or_project_data: ["src/microalpha/market_metadata.py", "trades.jsonl", "metadata_coverage.json"]
    bias_or_leakage_risks: ["Borrow data is highly proprietary.", "Using end-of-day borrow to trade earlier same day can leak.", "Missing data can understate costs."]
    notes: "High value for any serious long-short result."

  - requirement_id: "NWRDS-N3-034-commercial-news-and-sentiment"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Commercial news and sentiment feeds"
    source_type: "private_vendor"
    source_owner_or_provider: "RavenPack, Refinitiv News Analytics, Bloomberg, Benzinga, Dow Jones, or similar"
    source_url_or_location: "Vendor subscription export"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Enable event/news sentiment research if price-only momentum saturates."
    quant_use_case: "News sentiment, novelty, event classification, earnings/news windows, risk-off controls, and post-news drift features."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present"
      optimal: "2005-present with timestamps and entity mapping"
    frequency: "event"
    expected_size_class: "huge"
    refresh_cadence: "daily"
    storage_target: "vendor vault only; commit only aggregate feature-importance summaries if license permits"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription and allowed derived artifacts."
    acquisition_method: "Vendor API/export with entity IDs, timestamps, source, and sentiment fields."
    validation_method: "Timestamp timezone checks, publication-versus-ingestion time, ticker/entity mapping, duplicate article handling."
    joins_to_wrds_or_project_data: ["future feature pipeline", "data_sp500 symbols"]
    bias_or_leakage_risks: ["Publication timestamp must be point-in-time.", "Vendor entity mapping may be current-biased.", "News backfills can leak unavailable historical articles."]
    notes: "Ambitious extension, not a near-term blocker."

  - requirement_id: "NWRDS-N3-035-earnings-estimates-and-calendar"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Earnings calendar, analyst estimates, and transcripts"
    source_type: "private_vendor"
    source_owner_or_provider: "IBES direct, Visible Alpha, FactSet, Refinitiv, AlphaSense, BamSEC, Quartr, or similar"
    source_url_or_location: "Vendor subscription export"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Add event-aware features and avoid accidental earnings-event risk in future strategies."
    quant_use_case: "Earnings announcement windows, estimate revisions, surprise, transcript sentiment, blackout/risk filters, and post-earnings drift."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present"
      optimal: "2005-present or earliest available with PIT timestamps"
    frequency: "event"
    expected_size_class: "large"
    refresh_cadence: "daily"
    storage_target: "vendor vault only; aggregate diagnostics in repo"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription and license."
    acquisition_method: "Vendor export with announcement timestamps, estimate vintage dates, and identifier links."
    validation_method: "As-of revision checks, announcement-time timezone, entity mapping, and restatement handling."
    joins_to_wrds_or_project_data: ["future feature pipeline", "SEC EDGAR data", "data_sp500 symbols"]
    bias_or_leakage_risks: ["Actuals and estimates have severe lookahead risk if vintage dates are ignored.", "Transcripts can be backfilled after calls.", "Identifier mapping must be PIT."]
    notes: "High-value research extension if moving beyond price momentum."

  - requirement_id: "NWRDS-N3-036-institutional-ownership-and-flows"
    priority: "N3_PRIVATE_VENDOR"
    dataset_name: "Institutional ownership, fund flows, ETF holdings, and 13F-enhanced data"
    source_type: "private_vendor"
    source_owner_or_provider: "FactSet, Refinitiv, Morningstar, WhaleWisdom, ETF providers, or similar"
    source_url_or_location: "Vendor/API/account exports and public filings where available"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Support crowding, ownership, flow, and liquidity-risk diagnostics."
    quant_use_case: "Institutional crowding, ETF ownership/flow pressure, delayed 13F signal controls, liquidity stress, and portfolio overlap diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present"
      optimal: "2005-present with filing/publication dates"
    frequency: "mixed"
    expected_size_class: "large"
    refresh_cadence: "quarterly"
    storage_target: "vendor/private vault; commit only aggregate diagnostics"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm provider and redistribution rules."
    acquisition_method: "Vendor export or public 13F parsing with report date and filing date."
    validation_method: "Use filing date as availability date; reconcile issuer identifiers; check lag distribution."
    joins_to_wrds_or_project_data: ["data_sp500 symbols", "future diagnostics"]
    bias_or_leakage_risks: ["13F reporting lag is long and must not be ignored.", "Current holdings backfills are lookahead.", "License restrictions likely."]
    notes: "Good for diagnostics and robust-story building."

  - requirement_id: "NWRDS-N4-037-gdelt-and-open-news-event-data"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "GDELT and open news/event data"
    source_type: "public_bulk_download"
    source_owner_or_provider: "GDELT Project and open news sources"
    source_url_or_location: "GDELT 2.1 events/mentions/GKG public files"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Low-cost exploratory event/sentiment features without licensed news."
    quant_use_case: "Macro/geopolitical event regimes, public attention shocks, event clustering, and rough sentiment overlays."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present"
      optimal: "2015-present or full available history"
    frequency: "event"
    expected_size_class: "huge"
    refresh_cadence: "daily"
    storage_target: "shared vault only; derived aggregate features in repo if small"
    safe_to_commit_to_repo: false
    required_user_action: "None, but approve large storage before bulk acquisition."
    acquisition_method: "Public bulk download by date partitions with manifest."
    validation_method: "Timestamp, language/source filters, entity matching precision, and leakage review."
    joins_to_wrds_or_project_data: ["future feature pipeline", "macro regime docs"]
    bias_or_leakage_risks: ["Entity matching is noisy.", "News availability/backfill timing can leak.", "Public event data can be very sparse for single-name equity alpha."]
    notes: "Experimental; do after core public/WRDS data foundations."

  - requirement_id: "NWRDS-N4-038-social-sentiment-and-retail-attention"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "Social sentiment and retail attention"
    source_type: "public_api"
    source_owner_or_provider: "StockTwits, Reddit, X/Twitter, Google Trends, Wikipedia pageviews, app/public APIs"
    source_url_or_location: "Provider-specific public/API exports"
    access_status: "needs_credentials"
    data_policy_status: "unknown"
    project_need: "Explore attention and retail-flow overlays for modern-era strategies."
    quant_use_case: "Meme/attention filters, sentiment momentum, crowding flags, event risk, and alternative regime labels."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present"
      optimal: "Earliest API history to latest"
    frequency: "mixed"
    expected_size_class: "large"
    refresh_cadence: "daily"
    storage_target: "shared/private vault depending on provider terms; anonymized aggregates only in repo"
    safe_to_commit_to_repo: false
    required_user_action: "Approve API accounts and terms; avoid private user data."
    acquisition_method: "Provider APIs or public bulk downloads with strict terms review."
    validation_method: "Timestamp/as-of checks, ticker disambiguation, bot/spam filters, and train/test split by time."
    joins_to_wrds_or_project_data: ["data_sp500 symbols", "future attention features"]
    bias_or_leakage_risks: ["API terms and privacy constraints vary.", "Backfilled historical posts can leak if availability is unclear.", "Ticker cashtags are ambiguous."]
    notes: "Potentially interesting, not urgent."

  - requirement_id: "NWRDS-N4-039-web-traffic-app-and-card-spend-altdata"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "Web traffic, app usage, and card-spend alternative data"
    source_type: "private_vendor"
    source_owner_or_provider: "Similarweb, Sensor Tower, Earnest, YipitData, Second Measure, or similar"
    source_url_or_location: "Vendor subscriptions"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Ambitious consumer/company-specific feature expansion for future research."
    quant_use_case: "Demand nowcasting, revenue surprise proxies, consumer-sector signals, and event diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present for modern single-name studies"
      optimal: "Full vendor history with vintage/revision metadata"
    frequency: "mixed"
    expected_size_class: "large"
    refresh_cadence: "monthly"
    storage_target: "vendor vault only; commit only tiny derived summaries if license allows"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm subscription, license, and privacy constraints."
    acquisition_method: "Vendor export with point-in-time vintage fields where available."
    validation_method: "Map entities to tickers, verify revision/vintage timing, and test out-of-sample by sector."
    joins_to_wrds_or_project_data: ["future feature pipeline", "SEC/company identifiers"]
    bias_or_leakage_risks: ["Selection bias, restatement/backfill risk, and license restrictions are high.", "Often expensive and hypothesis-specific."]
    notes: "Long-tail, not needed for current microalpha roadmap."

  - requirement_id: "NWRDS-N4-040-public-patent-innovation-and-labor-data"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "Patent, innovation, job postings, and labor-market open data"
    source_type: "public_bulk_download"
    source_owner_or_provider: "USPTO, PatentsView, Lens, BLS, public job-posting aggregations where legal"
    source_url_or_location: "Public bulk data portals"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Explore slow-moving innovation and labor signals for sector/company research."
    quant_use_case: "Patent intensity, R&D proxies, hiring momentum, skill demand, and long-horizon quality/growth features."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2010-present"
      optimal: "Full available history with publication/grant dates"
    frequency: "mixed"
    expected_size_class: "huge"
    refresh_cadence: "quarterly"
    storage_target: "shared vault; derived aggregates in repo if small"
    safe_to_commit_to_repo: false
    required_user_action: "Approve storage and entity-mapping effort."
    acquisition_method: "Public bulk downloads with company/entity mapping layer."
    validation_method: "Use publication/grant dates as availability dates, entity/ticker mapping QA, lag analysis."
    joins_to_wrds_or_project_data: ["SEC/company identifiers", "future slow-moving feature pipeline"]
    bias_or_leakage_risks: ["Entity resolution is hard.", "Grant dates versus application/publication dates matter.", "Slow signal may not suit current daily momentum engine."]
    notes: "Specialized research extension."

  - requirement_id: "NWRDS-N4-041-esg-climate-and-supply-chain-data"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "ESG, climate, supply-chain, and controversy datasets"
    source_type: "private_vendor"
    source_owner_or_provider: "MSCI, Sustainalytics, RepRisk, CDP, OpenAQ, FactSet Revere, public climate datasets"
    source_url_or_location: "Vendor/public portals"
    access_status: "needs_subscription"
    data_policy_status: "licensed_restricted"
    project_need: "Support thematic robustness and sector/controversy experiments if strategy scope broadens."
    quant_use_case: "ESG controversy risk, climate transition exposure, supplier/customer shocks, regulatory event overlays, and sector stress diagnostics."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present"
      optimal: "Full vendor/public history with vintage timestamps"
    frequency: "mixed"
    expected_size_class: "large"
    refresh_cadence: "monthly"
    storage_target: "vendor/shared vault; aggregate summaries only in repo"
    safe_to_commit_to_repo: false
    required_user_action: "Confirm provider, entitlement, and redistribution terms."
    acquisition_method: "Vendor/public exports with as-of/vintage fields and entity mapping."
    validation_method: "Check point-in-time availability, entity mapping, controversy event timing, and sector coverage."
    joins_to_wrds_or_project_data: ["future feature pipeline", "sector metadata"]
    bias_or_leakage_risks: ["ESG scores are often revised and backfilled.", "Coverage bias is large.", "License restrictions are severe."]
    notes: "Long-tail unless a specific hypothesis is selected."

  - requirement_id: "NWRDS-N4-042-crypto-fx-and-cross-asset-public-data"
    priority: "N4_EXPERIMENTAL_ALT"
    dataset_name: "Crypto, FX, rates futures, and cross-asset public data"
    source_type: "public_api"
    source_owner_or_provider: "Crypto exchanges, FRED, CME public delayed data where available, Stooq, Alpha Vantage, or vendor APIs"
    source_url_or_location: "Provider-specific public/API endpoints"
    access_status: "available_now"
    data_policy_status: "safe_public"
    project_need: "Add cross-asset regime controls or test whether equity momentum behaves differently under crypto/FX/rates stress."
    quant_use_case: "Risk-on/risk-off regimes, liquidity stress, dollar/rates proxies, weekend risk, and alternative benchmark overlays."
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-present"
      optimal: "Earliest reliable history to latest"
    frequency: "mixed"
    expected_size_class: "medium"
    refresh_cadence: "daily"
    storage_target: "shared vault with small derived regime labels in repo"
    safe_to_commit_to_repo: true
    required_user_action: "Choose instruments and provider; verify terms."
    acquisition_method: "Public APIs/bulk downloads with timezone and calendar normalization."
    validation_method: "Timezone/session checks, missingness, holiday/weekend handling, and return scaling."
    joins_to_wrds_or_project_data: ["future regime metrics", "FRED macro data"]
    bias_or_leakage_risks: ["24/7 crypto calendars do not align with equities.", "Free APIs can change history and rate limits.", "Cross-asset signals can become kitchen-sink overfit features."]
    notes: "Useful only after core equity evidence is stronger."

highest_priority_acquisition_order:
  - requirement_id: "NWRDS-N0-004-public-mini-panel-inputs"
    reason: "Already tracked and required to reproduce the current public mini-panel dataset hash and demo evidence."
  - requirement_id: "NWRDS-N0-005-public-mini-panel-curated-resume-artifacts"
    reason: "Preserves current public-run truth and the explicit zero-trade caveat."
  - requirement_id: "NWRDS-N0-006-missing-public-source-run-artifacts"
    reason: "Restoring or regenerating these closes the source-evidence gap behind current public curated artifacts."
  - requirement_id: "NWRDS-N0-009-local-factor-csvs"
    reason: "Required for current factor/baseline reporting and easy to validate without private data."
  - requirement_id: "NWRDS-N0-003-tracked-sample-result-artifacts"
    reason: "README and tests depend on these artifacts staying coherent with sample data and configs."
  - requirement_id: "NWRDS-N0-007-large-local-sp500-style-panel"
    reason: "Large present dataset should be provenance-classified before future non-WRDS claims or bundle work."
  - requirement_id: "NWRDS-N0-011-missing-current-wrds-derived-source-artifacts"
    reason: "Current best WRDS claims need source aggregate artifacts restored, even though raw WRDS acquisition is covered separately."
  - requirement_id: "NWRDS-N1-013-ken-french-public-factor-library-refresh"
    reason: "Best low-friction public refresh for stronger baselines and factor diagnostics."
  - requirement_id: "NWRDS-N1-015-public-benchmark-market-series"
    reason: "Needed for non-WRDS market baselines and public evidence packages."
  - requirement_id: "NWRDS-N1-016-public-equity-ohlcv-refresh"
    reason: "Foundation for a non-degenerate shareable public benchmark."
  - requirement_id: "NWRDS-N1-017-public-corporate-actions-calendar"
    reason: "Required before a public OHLCV refresh can support serious performance claims."
  - requirement_id: "NWRDS-N1-014-fred-treasury-macro-rates"
    reason: "Small public dataset with high value for RF and regime controls."
  - requirement_id: "NWRDS-N1-018-public-constituent-and-sector-snapshots"
    reason: "Improves public universe discipline while documenting remaining survivorship caveats."
  - requirement_id: "NWRDS-N3-027-norgate-survivorship-bias-free-equities"
    reason: "Best private non-WRDS substitute if the project needs survivorship-safe public-style equity data."

user_access_questions:
  - "What is the original source and license posture for the tracked data_sp500/ panel and root data/*.csv Yahoo-style files?"
  - "Do you want full public factor histories committed as small safe CSVs, or kept in a shared non-WRDS vault with curated snippets in repo?"
  - "Can the missing artifacts/_local and reports/_runs source directories for ticket-37 and ticket-35 be restored from backups?"
  - "If building a non-WRDS public benchmark, should the canonical free provider be Stooq, Yahoo Finance, Nasdaq Data Link, Alpha Vantage, or another source?"
  - "Do you have or want a Norgate/Polygon/Tiingo/Sharadar subscription for non-WRDS survivorship-safe or latest-era research?"
  - "Should platform/account exports such as broker fills, GitHub Actions logs, Numerai, or WorldQuant remain out of scope until a dedicated ticket?"

non_wrds_data_policy_notes:
  - "Do not download data or use credentials from this planning artifact."
  - "Do not commit raw private/vendor/account exports; keep them in shared or private vaults and promote only safe aggregate summaries."
  - "Public/free does not automatically mean safe to redistribute; record provider terms and source URLs before committing refreshed data."
  - "Every external dataset needs a manifest with source, retrieval timestamp, date coverage, schema, row/file counts, hashes, provider terms, and known caveats."
  - "Use filing/publication/effective timestamps for as-of joins; never join latest metadata into historical signals."
  - "Large local artifacts should live under ignored/shared-vault paths, not bundles or source docs, unless explicitly curated."
  - "For non-WRDS performance claims, distinguish demo/public-shareable evidence from prestige WRDS/CRSP evidence and carry survivorship/corporate-action caveats."
```

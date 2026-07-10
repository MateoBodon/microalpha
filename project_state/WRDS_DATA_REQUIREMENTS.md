# WRDS Data Requirements

last_updated: 2026-07-07
updated_by: Codex
scope: planning_only_no_raw_wrds_download

## Human Summary

This map is based on the live repo at
`/Volumes/Storage/Projects/microalpha/repo`, the current AI OS v2 state docs,
WRDS configs/scripts/tests/notebooks, curated WRDS result artifacts, and local
WRDS catalog metadata under `/Volumes/Storage/Data/WRDS/_catalog/`.

No raw WRDS data was downloaded or copied. The catalog files used were metadata
only:

- `/Volumes/Storage/Data/WRDS/_catalog/20260706_223405_tables.csv`
- `/Volumes/Storage/Data/WRDS/_catalog/20260706_223405_columns.csv`
- `/Volumes/Storage/Data/WRDS/_catalog/20260706_223405_full_catalog.json`

Current reproduction is blocked in this checkout because `WRDS_DATA_ROOT` is
unset and the historical `/srv/data/wrds/wrds` root is absent. The current best
curated WRDS evidence depends on dataset id `wrds_crsp_export_20251221_v1`,
selection window `2013-01-02` to `2017-12-29`, and holdout window `2018-01-02`
to `2019-12-31`. The original export script targets `2000-01-03` to
`2025-06-30`, so exact dataset recreation should prefer that full export window
even though the current claim-validation minimum is narrower.

Highest-priority work is to restore or regenerate the current WRDS export
package, then rebuild the source-backed current run with CRSP daily stock data,
point-in-time security names, delisting returns, sector metadata, CRSP market
proxy returns, and Ken French daily factors. The next serious expansion should
extend CRSP coverage to a fresh post-2019 holdout and add stronger baselines,
borrow/cost realism, liquidity/spread diagnostics, and fundamental/factor
features before any public performance claim is upgraded.

## Machine-Readable Map

```yaml
project:
  name: "microalpha"
  repo_path: "/Volumes/Storage/Projects/microalpha/repo"
  analysis_timestamp_utc: "2026-07-07T04:46:40Z"
  purpose: "Leakage-safe event-driven quant backtesting and walk-forward validation with WRDS/CRSP real-data research support."
  current_claims_or_results_summary: "Current best curated WRDS evidence is local-data-dependent and claim-sensitive: run 2026-02-16T22-33-46Z-8d90621, dataset_id wrds_crsp_export_20251221_v1, selection window 2013-01-02 to 2017-12-29, holdout 2018-01-02 to 2019-12-31, holdout Sharpe_HAC 0.588, MaxDD 1.38%, 31 trades, RC p-value 0.941, SPA n/a. Source local artifacts and WRDS_DATA_ROOT are missing in this checkout; config-hash evidence has a known mismatch."
  data_policy_notes:
    raw_wrds_must_not_enter_repo: true
    shared_vault_root: "/Volumes/Storage/Data/WRDS"

requirements:
  - requirement_id: "WRDS-P0-001-current-derived-export-package"
    priority: "P0_BLOCKING"
    project_need: "Restore or regenerate the local WRDS export layout expected by configs and current curated artifacts."
    quant_use_case: "Exact reproduction of wrds_crsp_export_20251221_v1 and current best WRDS run; provides per-symbol CSVs, metadata, universe snapshots, and export manifest."
    wrds_availability: "not_wrds"
    wrds_schema: "local_derived"
    wrds_table: "crsp/daily_csv + meta/crsp_security_metadata.csv + universes/flagship_sector_neutral.csv + manifests/20251221_001618/manifest.json"
    wrds_product_or_library: "Local derived WRDS/CRSP export package"
    logical_dataset: "wrds_crsp_export_20251221_v1_local_layout"
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: false
    date_range:
      minimum_required: "2012-01-03 to 2019-12-31, plus any earlier warmup rows needed for 12-1 momentum"
      optimal: "2000-01-03 to 2025-06-30, matching scripts/export_wrds_flagship.py"
      tier_split: "recent_critical"
    frequency: "mixed"
    expected_size_class: "medium"
    partition_strategy: "unknown"
    key_columns:
      identifiers: ["symbol", "permno", "permco", "dataset_id"]
      dates: ["timestamp", "date", "effective_date", "exported_at"]
      measures: ["close", "volume", "shares_out", "ret", "dlret", "total_return", "adv_20", "adv_63", "adv_126", "market_cap_proxy", "sector", "borrow_fee_annual_bps", "spread_bps", "volatility_bps"]
    joins:
      required_link_tables: ["crsp.dsenames", "crsp.dsedelist", "crsp.ccmxpf_linktable", "comp.company"]
      joins_to_project_data: ["configs/wfv_flagship_wrds.yaml", "configs/wfv_flagship_wrds_sweep35.yaml", "docs/artifacts/resume/wrds/2026-02-16T22-33-46Z-8d90621/manifest_excerpt.json"]
      point_in_time_risks: ["Local package must preserve export manifest, dataset_id, date coverage, and as-of universe dates; do not silently replace with a later export without new dataset_id."]
    bias_risks:
      survivorship: "High if universe is rebuilt from current constituents or ticker-only lists instead of historical PIT snapshots."
      lookahead: "High if universe rows, metadata, sector labels, ADV, or close prices use dates after the rebalance effective date."
      restatement: "Low for CRSP prices; medium for sector/GICS if sourced from current company records only."
      delisting: "High if dlret is omitted or terminal returns are not applied."
      corporate_actions: "Medium if prices/returns are inconsistently adjusted across CSV and universe construction."
    notes: "This is the immediate missing package identified in project_state/DATA_ARTIFACT_INVENTORY.md. It is local derived data, not a WRDS table, and must stay outside git."

  - requirement_id: "WRDS-P0-002-crsp-daily-stock-prices-returns"
    priority: "P0_BLOCKING"
    project_need: "Source daily OHLCV, shares, and returns needed to reproduce the WRDS price panel and flagship strategy."
    quant_use_case: "Daily event stream, t+1 execution, momentum score history, ADV/liquidity filters, turnover/capacity diagnostics, realized returns, and source dataset recreation."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsf"
    wrds_product_or_library: "CRSP US Stock/Security Daily Stock File"
    logical_dataset: "crsp_daily_stock_legacy_dsf"
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2012-01-03 to 2019-12-31"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["permno", "permco", "cusip"]
      dates: ["date"]
      measures: ["openprc", "bidlo", "askhi", "prc", "vol", "ret", "shrout", "retx", "bid", "ask", "numtrd"]
    joins:
      required_link_tables: ["crsp.dsenames", "crsp.dsedelist", "crsp.ccmxpf_linktable"]
      joins_to_project_data: ["${WRDS_DATA_ROOT}/crsp/daily_csv/*.csv", "${WRDS_DATA_ROOT}/crsp/dsf", "configs/wfv_flagship_wrds*.yaml"]
      point_in_time_risks: ["Filter by shrcd/exchcd through name-date ranges, not static ticker membership; use returns and prices from the same date convention."]
    bias_risks:
      survivorship: "High if only surviving tickers or current names are selected."
      lookahead: "High if close t signals are filled at close t or if future universe rows are visible."
      restatement: "Low; CRSP corrections can still alter exact reproduction if exports are refreshed."
      delisting: "High if joined delisting returns are omitted."
      corporate_actions: "Medium; use CRSP returns or consistent adjustment factors, not raw price deltas alone."
    notes: "The repo export script currently queries crsp.dsf and writes per-symbol CSVs with timestamp/open/high/low/close/volume/shares_out/ret/dlret/total_return."

  - requirement_id: "WRDS-P0-003-crsp-security-names-share-exchange-history"
    priority: "P0_BLOCKING"
    project_need: "Point-in-time ticker, share code, exchange code, SIC, CUSIP, and status metadata for CRSP rows."
    quant_use_case: "Common-stock universe filters shrcd 10/11 and exchcd 1/2/3, ticker/permno resolution, PIT symbol mapping, survivorship control, and metadata export."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsenames"
    wrds_product_or_library: "CRSP stock names/security history"
    logical_dataset: "crsp_daily_names_security_history"
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2012-01-03 to 2019-12-31"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "permco", "ticker", "cusip", "ncusip"]
      dates: ["namedt", "nameendt"]
      measures: ["shrcd", "exchcd", "siccd", "naics", "trdstat", "secstat", "comnam", "primexch"]
    joins:
      required_link_tables: []
      joins_to_project_data: ["scripts/export_wrds_flagship.py", "${WRDS_DATA_ROOT}/meta/crsp_security_metadata.csv"]
      point_in_time_risks: ["Rows must be joined where dsf.date is between namedt and nameendt; ticker-only joins are unsafe."]
    bias_risks:
      survivorship: "Critical control table; omitting it makes ticker filters survivorship-prone."
      lookahead: "High if latest ticker/share/exchange fields are backfilled into older rows."
      restatement: "Low."
      delisting: "Medium because inactive securities must remain in historical universe."
      corporate_actions: "Medium because name/CUSIP changes can coincide with corporate actions."
    notes: "Catalog also confirms crsp.stocknames, crsp.msenames, and CIZ-style crsp.stksecurityinfohist as useful alternatives."

  - requirement_id: "WRDS-P0-004-crsp-delisting-returns"
    priority: "P0_BLOCKING"
    project_need: "Delisting return and delisting status data for terminal-return correctness."
    quant_use_case: "Apply (1 + ret) * (1 + dlret) - 1 and avoid overstating returns for delisted names."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsedelist"
    wrds_product_or_library: "CRSP delisting event file"
    logical_dataset: "crsp_daily_delisting_returns"
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2012-01-03 to 2019-12-31"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "permco", "cusip", "nwperm", "nwcomp"]
      dates: ["dlstdt", "nextdt", "dlpdt"]
      measures: ["dlstcd", "dlret", "dlretx", "dlprc", "dlamt"]
    joins:
      required_link_tables: ["crsp.dsf", "crsp.dsenames"]
      joins_to_project_data: ["scripts/export_wrds_flagship.py", "total_return column in local CSV exports"]
      point_in_time_risks: ["Join delisting return only on the delisting date; do not smear terminal returns over earlier dates."]
    bias_risks:
      survivorship: "High if delisted names are dropped or terminal losses missing."
      lookahead: "Medium if dlret is known before dlstdt in signal construction."
      restatement: "Low to medium if CRSP later corrects delisting records."
      delisting: "This is the primary control."
      corporate_actions: "Medium for mergers and successor permnos."
    notes: "Catalog also confirms crsp.msedelist and CIZ-style crsp.stkdelists."

  - requirement_id: "WRDS-P0-005-crsp-market-index-returns"
    priority: "P0_BLOCKING"
    project_need: "Market proxy for current claim validation and baseline reporting."
    quant_use_case: "CRSP value-weighted/equal-weighted market benchmark, SPY fallback replacement, drawdown/Sharpe comparison, and market regime context."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsi"
    wrds_product_or_library: "CRSP daily stock index returns"
    logical_dataset: "crsp_daily_market_proxy"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2013-01-02 to 2019-12-31"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "tiny"
    partition_strategy: "table"
    key_columns:
      identifiers: []
      dates: ["date"]
      measures: ["vwretd", "vwretx", "ewretd", "ewretx", "sprtrn", "spindx", "totval", "totcnt"]
    joins:
      required_link_tables: []
      joins_to_project_data: ["src/microalpha/reporting/baselines.py expects crsp_vwretd.csv, vwretd.csv, market_proxy.csv, or SPY.csv"]
      point_in_time_risks: ["Use same trading calendar as strategy returns; avoid filling market returns over non-trading days."]
    bias_risks:
      survivorship: "Low for CRSP index series."
      lookahead: "Low if aligned on date."
      restatement: "Low."
      delisting: "Index construction handles delistings internally."
      corporate_actions: "Low."
    notes: "Current best WRDS curated artifact lacks current-best baselines; this is required for stronger claim validation. Monthly equivalent crsp.msi is also confirmed."

  - requirement_id: "WRDS-P0-006-ken-french-daily-factors"
    priority: "P0_BLOCKING"
    project_need: "Risk-free series and factor model inputs for FF3, Carhart, FF5 plus momentum reporting."
    quant_use_case: "Cash baseline, excess returns, HAC factor regression, rolling betas, and market/style exposure diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "ff"
    wrds_table: "fivefactors_daily"
    wrds_product_or_library: "Fama-French factors via WRDS"
    logical_dataset: "ken_french_daily_ff5_momentum"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2013-01-02 to 2019-12-31"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "tiny"
    partition_strategy: "table"
    key_columns:
      identifiers: []
      dates: ["date"]
      measures: ["mktrf", "smb", "hml", "rmw", "cma", "rf", "umd"]
    joins:
      required_link_tables: ["ff.factors_daily"]
      joins_to_project_data: ["data/factors/ff5_mom_daily.csv", "reports/factors.py", "src/microalpha/reporting/factors.py", "reports/analytics.py"]
      point_in_time_risks: ["Align factor frequency exactly; avoid resampling daily returns to lower frequency unless documented."]
    bias_risks:
      survivorship: "Low for factor portfolios."
      lookahead: "Low if factor dates are aligned after returns are observed."
      restatement: "Low; factor history can be revised, so pin export timestamp for exact reproduction."
      delisting: "Handled by factor provider."
      corporate_actions: "Handled by factor provider."
    notes: "Catalog confirms ff.factors_daily with mktrf/smb/hml/rf/umd and ff.fivefactors_daily with FF5 fields. Repo currently expects columns Mkt_RF, SMB, HML, RMW, CMA, MOM, RF after export/normalization."

  - requirement_id: "WRDS-P0-007-ccm-link-and-compustat-sector-metadata"
    priority: "P0_BLOCKING"
    project_need: "Map CRSP permnos to Compustat gvkeys and GICS sector metadata for sector caps and sector-neutral scoring."
    quant_use_case: "Sector-aware universe construction, max positions per sector, sector z-scores, GICS diagnostics, and metadata export."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "ccmxpf_linktable"
    wrds_product_or_library: "CRSP/Compustat Merged link table plus Compustat company"
    logical_dataset: "ccm_permno_gvkey_gics"
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2012-01-03 to 2019-12-31"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["gvkey", "lpermno", "lpermco", "liid"]
      dates: ["linkdt", "linkenddt"]
      measures: ["linktype", "linkprim", "usedflag"]
    joins:
      required_link_tables: ["comp.company"]
      joins_to_project_data: ["scripts/export_wrds_flagship.py", "${WRDS_DATA_ROOT}/meta/crsp_security_metadata.csv", "${WRDS_DATA_ROOT}/universes/flagship_sector_neutral.csv"]
      point_in_time_risks: ["Use linkdt/linkenddt validity windows; avoid latest-only company fields for historical sector assignment unless explicitly accepted."]
    bias_risks:
      survivorship: "Medium if dead/inactive firms fail to link."
      lookahead: "Medium if future link information is applied before effective date."
      restatement: "Medium because GICS/company attributes may be current or corrected."
      delisting: "Medium through missing links on delisted firms."
      corporate_actions: "Medium for mergers, spin-offs, and identifier changes."
    notes: "Repo script joins crsp.ccmxpf_linktable to comp.company for gsector/gsubind. Catalog also confirms crsp.ccmxpf_lnkhist."

  - requirement_id: "WRDS-P0-008-pit-flagship-universe-snapshots"
    priority: "P0_BLOCKING"
    project_need: "Monthly point-in-time universe snapshots compatible with FlagshipMomentumStrategy."
    quant_use_case: "Eligible symbol set, sector caps, min ADV, min price, market cap/liquidity ranking, and 12-1 momentum candidate selection."
    wrds_availability: "not_wrds"
    wrds_schema: "local_derived"
    wrds_table: "universes/flagship_sector_neutral.csv"
    wrds_product_or_library: "Derived from CRSP daily/monthly stock, CRSP names, delisting, and sector metadata"
    logical_dataset: "flagship_sector_neutral_monthly_universe"
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2013-01-02 to 2019-12-31 with prior lookback history"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "monthly"
    expected_size_class: "medium"
    partition_strategy: "date_range"
    key_columns:
      identifiers: ["symbol", "permno", "sector"]
      dates: ["date", "effective_date", "rebalance"]
      measures: ["close", "adv_20", "adv_63", "adv_126", "market_cap_proxy", "price_ma_20", "adv_rank"]
    joins:
      required_link_tables: ["crsp.dsf", "crsp.dsenames", "crsp.dsedelist", "crsp.ccmxpf_linktable", "comp.company"]
      joins_to_project_data: ["configs/wfv_flagship_wrds*.yaml", "src/microalpha/strategies/flagship_mom.py", "scripts/build_wrds_signals.py"]
      point_in_time_risks: ["Snapshot date must be effective next rebalance and must never use later closes, ADV, or sector membership."]
    bias_risks:
      survivorship: "Critical if universe starts from current S&P 500 or surviving tickers."
      lookahead: "Critical if month-end snapshot is visible before effective date."
      restatement: "Medium for sector and shares metadata."
      delisting: "High if symbols disappear without terminal return handling."
      corporate_actions: "Medium for ticker/permno transitions."
    notes: "The current strategy code expects symbol/date/sector plus optional adv_20/adv_63/adv_126/market_cap_proxy and close."

  - requirement_id: "WRDS-P1-009-crsp-monthly-stock-file"
    priority: "P1_CORE"
    project_need: "Lower-volume monthly source for market cap ranking, baseline portfolios, monthly return diagnostics, and cross-checks against daily-derived monthly returns."
    quant_use_case: "Top N by lagged market cap, monthly equal-weight and 12-1 momentum baselines, universe turnover, and date coverage checks."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "msf"
    wrds_product_or_library: "CRSP monthly stock file"
    logical_dataset: "crsp_monthly_stock_returns"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2012-01-31 to 2019-12-31"
      optimal: "1970-01-31 to latest available, or full CRSP history if storage permits"
      tier_split: "full_history"
    frequency: "monthly"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["permno", "permco", "cusip"]
      dates: ["date"]
      measures: ["prc", "ret", "retx", "vol", "shrout", "bid", "ask", "cfacpr", "cfacshr"]
    joins:
      required_link_tables: ["crsp.msenames", "crsp.msedelist"]
      joins_to_project_data: ["future universe builder", "future baseline suite"]
      point_in_time_risks: ["Use lagged market cap effective next period; do not use same-month-end rank for trades before month-end."]
    bias_risks:
      survivorship: "High without monthly names/delist support."
      lookahead: "High if market cap ranks are not lagged."
      restatement: "Low to medium."
      delisting: "High without msedelist or daily dsedelist cross-check."
      corporate_actions: "Medium if returns and adjusted prices are mixed."
    notes: "Monthly equivalent is useful even if daily data is available because it provides cheaper validation and robust universe snapshots."

  - requirement_id: "WRDS-P1-010-crsp-monthly-names-delist"
    priority: "P1_CORE"
    project_need: "Monthly PIT name/share/exchange and delisting support."
    quant_use_case: "Monthly universe filters, baseline alignment, survivorship checks, and low-cost reconstitution."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "msenames"
    wrds_product_or_library: "CRSP monthly names plus monthly delisting"
    logical_dataset: "crsp_monthly_names_delist"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2012-01-31 to 2019-12-31"
      optimal: "1970-01-31 to latest available, or full CRSP history if storage permits"
      tier_split: "full_history"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "permco", "ticker", "cusip", "ncusip"]
      dates: ["namedt", "nameendt", "dlstdt"]
      measures: ["shrcd", "exchcd", "siccd", "dlret", "dlstcd"]
    joins:
      required_link_tables: ["crsp.msf", "crsp.msedelist"]
      joins_to_project_data: ["future monthly universe builder", "future baseline suite"]
      point_in_time_risks: ["Name history and delisting events must be joined by validity windows."]
    bias_risks:
      survivorship: "High if inactive names are excluded."
      lookahead: "Medium."
      restatement: "Low."
      delisting: "Primary monthly control."
      corporate_actions: "Medium."
    notes: "Catalog confirms crsp.msenames and crsp.msedelist."

  - requirement_id: "WRDS-P1-011-crsp-corporate-actions-and-adjustments"
    priority: "P1_CORE"
    project_need: "Corporate action, distribution, and adjustment-factor correctness for price/return reconstruction."
    quant_use_case: "Validate split/dividend adjustments, raw-to-adjusted price construction, return decomposition, and odd corporate-action diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsedist"
    wrds_product_or_library: "CRSP distributions and adjustment factors"
    logical_dataset: "crsp_corporate_actions_adjustments"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2012-01-03 to 2019-12-31"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "permco", "cusip"]
      dates: ["dclrdt", "exdt", "rcrddt", "paydt", "date"]
      measures: ["distcd", "divamt", "facpr", "facshr", "cfacpr", "cfacshr"]
    joins:
      required_link_tables: ["crsp.dsf", "crsp.dse", "crsp.stkdlycumulativeadjfactor"]
      joins_to_project_data: ["future WRDS ETL validation reports"]
      point_in_time_risks: ["Distinguish declaration, ex, record, and pay dates; never use pay-date data to trade before ex date."]
    bias_risks:
      survivorship: "Medium through missing action history for inactive names."
      lookahead: "Medium for declaration/pay dates."
      restatement: "Low to medium."
      delisting: "Medium when distributions interact with delisting events."
      corporate_actions: "Primary control."
    notes: "Catalog confirms crsp.dsedist, crsp.dse, and CIZ-style crsp.stkdlycumulativeadjfactor/crsp.stkmthcumulativeadjfactor."

  - requirement_id: "WRDS-P1-012-crsp-ciz-modern-stock-files"
    priority: "P1_CORE"
    project_need: "Modern CRSP CIZ-compatible stock/security files for future-proof exports and cross-validation of legacy DSF/MSF logic."
    quant_use_case: "Cross-check daily and monthly returns, CIZ field conventions, adjustment factors, delisting, and security history before a refreshed modern holdout."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "dsf_v2"
    wrds_product_or_library: "CRSP CIZ-style daily/monthly stock files"
    logical_dataset: "crsp_ciz_stock_security_files"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available"
      optimal: "2000-01-03 to latest available"
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["permno", "permco", "hdrcusip", "cusip", "ticker"]
      dates: ["dlycaldt", "mthcaldt", "secinfostartdt", "secinfoenddt", "delistingdt"]
      measures: ["dlyprc", "dlyret", "dlyretx", "dlyvol", "dlyclose", "dlyopen", "dlylow", "dlyhigh", "dlycumfacpr", "dlycumfacshr", "mthret", "mthcap", "shrout"]
    joins:
      required_link_tables: ["crsp.stksecurityinfohist", "crsp.stkdelists", "crsp.stkdistributions"]
      joins_to_project_data: ["future refreshed WRDS ETL", "future CIZ compatibility tests"]
      point_in_time_risks: ["Map CIZ security history date ranges exactly; do not mix CIZ and legacy fields without a conversion audit."]
    bias_risks:
      survivorship: "High unless paired with security history and delists."
      lookahead: "Medium."
      restatement: "Medium during migration from legacy CRSP naming."
      delisting: "High unless crsp.stkdelists is included."
      corporate_actions: "Medium unless cumulative adjustment factors and distributions are checked."
    notes: "Catalog confirms crsp.dsf_v2, crsp.msf_v2, crsp.stkdlysecuritydata, crsp.stksecurityinfohist, crsp.stkdelists, and crsp.stkdistributions."

  - requirement_id: "WRDS-P1-013-compustat-annual-fundamentals"
    priority: "P1_CORE"
    project_need: "Fundamental annual features and controls for stronger baselines, value/quality factors, and publication-grade robustness."
    quant_use_case: "Book-to-market, profitability, investment, leverage, size/fundamental controls, accounting quality filters, and feature expansion."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "comp"
    wrds_table: "funda"
    wrds_product_or_library: "Compustat North America annual fundamentals"
    logical_dataset: "compustat_annual_fundamentals"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available for modern research"
      optimal: "1960-01-01 to latest available if full-history factors are desired"
      tier_split: "modern_research"
    frequency: "annual"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["gvkey", "tic", "cusip", "conm"]
      dates: ["datadate", "fyear", "pdate", "fdate"]
      measures: ["at", "ceq", "seq", "txditc", "revt", "ni", "sale", "cogs", "xsga", "capx", "ppent", "dltt", "dlc", "che", "oancf"]
    joins:
      required_link_tables: ["crsp.ccmxpf_linktable", "comp.company", "comp.security"]
      joins_to_project_data: ["future feature store", "future factor benchmark suite"]
      point_in_time_risks: ["Use filing/availability lag; datadate alone is not investable availability."]
    bias_risks:
      survivorship: "Medium unless inactive firms and link histories are retained."
      lookahead: "High unless accounting data is lagged by report/filing availability."
      restatement: "High; restated fundamentals can leak future corrections unless vintage data or conservative lags are used."
      delisting: "Medium through CRSP link coverage."
      corporate_actions: "Medium through gvkey/permno changes."
    notes: "Catalog confirms comp.funda with datadate and many accounting fields."

  - requirement_id: "WRDS-P1-014-compustat-quarterly-fundamentals"
    priority: "P1_CORE"
    project_need: "Quarterly fundamentals and announcement timing for timelier features and earnings/fundamental surprise controls."
    quant_use_case: "Quarterly profitability, balance-sheet changes, earnings announcement timing, value/quality signals, and restatement/lag diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "comp"
    wrds_table: "fundq"
    wrds_product_or_library: "Compustat North America quarterly fundamentals"
    logical_dataset: "compustat_quarterly_fundamentals"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "1980-01-01 to latest available if storage permits"
      tier_split: "modern_research"
    frequency: "quarterly"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["gvkey", "tic", "cusip", "conm"]
      dates: ["datadate", "fyearq", "fqtr", "rdq", "pdateq", "fdateq"]
      measures: ["atq", "ceqq", "saleq", "revtq", "niq", "epspxq", "cshoq", "cheq", "dlttq", "dlcq", "capxy"]
    joins:
      required_link_tables: ["crsp.ccmxpf_linktable", "comp.company", "comp.security"]
      joins_to_project_data: ["future feature store", "future event study module"]
      point_in_time_risks: ["Use rdq or conservative filing lag; do not use quarterly values before public release."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High without rdq/filing lag."
      restatement: "High for restated quarterly values."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms comp.fundq with rdq and quarterly accounting fields."

  - requirement_id: "WRDS-P1-015-compustat-security-company-descriptors"
    priority: "P1_CORE"
    project_need: "Company/security descriptors for sector, industry, identifiers, listing metadata, and joins."
    quant_use_case: "GICS/SIC/NAICS controls, sector/industry neutrality, gvkey/security identifier hygiene, and Compustat feature joins."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "comp"
    wrds_table: "company"
    wrds_product_or_library: "Compustat company and security descriptors"
    logical_dataset: "compustat_company_security_metadata"
    required_for_current_reproduction: true
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2012-01-03 to 2019-12-31"
      optimal: "2000-01-03 to latest available"
      tier_split: "table_level"
    frequency: "static"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: ["gvkey", "tic", "cusip", "cik", "conm"]
      dates: ["ipodate", "dldte", "dldtei"]
      measures: ["gsector", "gind", "ggroup", "gsubind", "sic", "naics", "costat", "fic", "loc", "curr_sp500_flag"]
    joins:
      required_link_tables: ["comp.security", "crsp.ccmxpf_linktable"]
      joins_to_project_data: ["scripts/export_wrds_flagship.py", "${WRDS_DATA_ROOT}/meta/crsp_security_metadata.csv"]
      point_in_time_risks: ["Current descriptor fields can be stale for old dates; document if used as approximate sector labels."]
    bias_risks:
      survivorship: "Medium if only current active firms are retained."
      lookahead: "Medium if current GICS is backfilled."
      restatement: "Medium for classification updates."
      delisting: "Medium if inactive securities missing."
      corporate_actions: "Medium."
    notes: "Catalog confirms comp.company and comp.security."

  - requirement_id: "WRDS-P1-016-index-constituents-and-membership"
    priority: "P1_CORE"
    project_need: "Point-in-time benchmark/index membership when evaluating S&P-like universes or public benchmark comparisons."
    quant_use_case: "S&P 500 membership baselines, survivorship-bias checks, index-relative results, and public-data comparison panels."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "comp"
    wrds_table: "idxcst_his"
    wrds_product_or_library: "Compustat index constituents history"
    logical_dataset: "index_membership_history"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2012-01-03 to 2019-12-31"
      optimal: "1990-01-01 to latest available"
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "table"
    key_columns:
      identifiers: ["gvkey", "iid", "gvkeyx"]
      dates: ["from", "thru"]
      measures: []
    joins:
      required_link_tables: ["crsp.ccmxpf_linktable", "comp.security", "crsp.dsf"]
      joins_to_project_data: ["future S&P benchmark universe", "data_sp500 survivorship audit"]
      point_in_time_risks: ["Membership changes must be effective by from/thru dates; avoid current constituent lists for historical tests."]
    bias_risks:
      survivorship: "Critical if replacing historical membership with current S&P members."
      lookahead: "High if additions/removals are known before announcement/effective date."
      restatement: "Medium if index history is corrected."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Current strategy prefers top-N liquidity/market-cap PIT universes, but this is needed for defensible S&P-style comparisons."

  - requirement_id: "WRDS-P1-017-wrdsapps-financial-ratios-and-signals"
    priority: "P1_CORE"
    project_need: "Precomputed ratios and broad signal panels for fast robust baselines and feature sanity checks."
    quant_use_case: "Reference implementations for common accounting/market ratios, cross-sectional signal benchmarking, and factor model comparisons."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "wrdsapps"
    wrds_table: "firm_ratio_ccm"
    wrds_product_or_library: "WRDS financial ratios and backtest signal applications"
    logical_dataset: "wrdsapps_ratios_and_signals"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "mixed"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["gvkey", "permno", "cusip"]
      dates: ["adate", "fdate", "date"]
      measures: ["ratio fields", "signal fields"]
    joins:
      required_link_tables: ["wrdsapps.id_ccm", "crsp.ccmxpf_linktable"]
      joins_to_project_data: ["future feature store", "future benchmark factor library"]
      point_in_time_risks: ["Confirm WRDS app fields are lagged/point-in-time enough for trading use; otherwise use as diagnostics only."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High unless app construction lag is documented."
      restatement: "High for accounting-derived ratios."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms wrdsapps.firm_ratio, firm_ratio_ccm, firm_ratio_ibes, signals_raw_basic, signals_raw_plus, mastertable, and chars."

  - requirement_id: "WRDS-P2-018-ibes-eps-summary-detail-actuals"
    priority: "P2_HIGH_VALUE"
    project_need: "Analyst earnings expectations, revisions, and actuals for feature expansion and earnings-surprise controls."
    quant_use_case: "Earnings estimate revisions, forecast dispersion, surprise, analyst coverage, post-earnings drift controls, and event study diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "ibes"
    wrds_table: "statsum_epsus"
    wrds_product_or_library: "IBES US EPS summary/detail/actuals"
    logical_dataset: "ibes_eps_estimates_actuals"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "mixed"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["ticker", "cusip", "oftic", "cname"]
      dates: ["statpers", "fpedats", "anndats", "actdats", "revdats"]
      measures: ["numest", "meanest", "medest", "stdev", "highest", "lowest", "actual", "value"]
    joins:
      required_link_tables: ["wrdsapps_link_crsp_ibes.ibcrsphist", "crsp.dsenames"]
      joins_to_project_data: ["future event/feature store"]
      point_in_time_risks: ["Use announcement/revision timestamps, not fiscal period end alone; IBES identifiers need historical link windows."]
    bias_risks:
      survivorship: "Medium through coverage and identifier links."
      lookahead: "High if estimates/actuals are keyed by period end instead of announcement/revision date."
      restatement: "Medium for restated actuals."
      delisting: "Medium."
      corporate_actions: "Medium for ticker/CUSIP changes."
    notes: "Catalog confirms ibes.statsum_epsus, ibes.det_epsus, ibes.act_epsus, ibes.id, ibes.recddet, and ibes.recdsum."

  - requirement_id: "WRDS-P2-019-ibes-recommendations-price-targets"
    priority: "P2_HIGH_VALUE"
    project_need: "Analyst recommendation, sentiment, and price-target style signals."
    quant_use_case: "Revision momentum, recommendation breadth, analyst sentiment, signal interaction tests, and alternative baselines."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "ibes"
    wrds_table: "recdsum"
    wrds_product_or_library: "IBES recommendations and related analyst datasets"
    logical_dataset: "ibes_recommendations_targets"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["ticker", "cusip", "oftic"]
      dates: ["statpers", "actdats", "anndats", "revdats"]
      measures: ["meanrec", "medrec", "stdev", "numrec", "numup", "numdown", "buypct", "sellpct", "holdpct"]
    joins:
      required_link_tables: ["wrdsapps_link_crsp_ibes.ibcrsphist"]
      joins_to_project_data: ["future analyst feature store"]
      point_in_time_risks: ["Use action/revision date; stale recommendations must be aged or expired."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High without date discipline."
      restatement: "Low to medium."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Price-target exact table names should be verified before download; recommendation summary/detail tables are catalog-confirmed."

  - requirement_id: "WRDS-P2-020-ibes-crsp-link"
    priority: "P2_HIGH_VALUE"
    project_need: "Historical identifier bridge between IBES tickers and CRSP permnos."
    quant_use_case: "Safe joins for analyst estimates/recommendations to daily returns and holdings."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "wrdsapps_link_crsp_ibes"
    wrds_table: "ibcrsphist"
    wrds_product_or_library: "WRDS CRSP-IBES link"
    logical_dataset: "crsp_ibes_link_history"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "table_level"
    frequency: "event"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "ticker"]
      dates: ["sdate", "edate"]
      measures: ["score"]
    joins:
      required_link_tables: ["ibes.id", "crsp.dsenames"]
      joins_to_project_data: ["future analyst feature store"]
      point_in_time_risks: ["Use sdate/edate validity and score filters; do not join by current ticker."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "Medium."
      restatement: "Low."
      delisting: "Medium."
      corporate_actions: "High if ticker/CUSIP transitions ignored."
    notes: "Catalog confirms wrdsapps_link_crsp_ibes.ibcrsphist and wrdsapps.ibcrsphist."

  - requirement_id: "WRDS-P2-021-liquidity-diagnostics-taq-derived"
    priority: "P2_HIGH_VALUE"
    project_need: "Daily liquidity/spread diagnostics without immediately pulling full intraday TAQ."
    quant_use_case: "Validate slippage defaults, spread_bps metadata, impact parameters, capacity filters, and liquidity regime controls."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "contrib_liquidity_taq"
    wrds_table: "bbd"
    wrds_product_or_library: "WRDS/contributed TAQ liquidity summaries"
    logical_dataset: "daily_liquidity_spread_summaries"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to 2019-12-31"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["permno", "ticker", "cusip"]
      dates: ["date", "year_month_end_date"]
      measures: ["spread measures", "illiquidity measures", "liquidity measures"]
    joins:
      required_link_tables: ["crsp.dsenames", "wrdsapps_link_crsp_taqm.taqmclink"]
      joins_to_project_data: ["future meta/crsp_security_metadata.csv spread_bps and volatility_bps fields", "slippage calibration"]
      point_in_time_risks: ["Use only same-day or lagged liquidity measures for trading decisions; use contemporaneous values only for ex post diagnostics."]
    bias_risks:
      survivorship: "Medium through identifier coverage."
      lookahead: "High if same-day closing liquidity is used before execution."
      restatement: "Low to medium."
      delisting: "Medium."
      corporate_actions: "Medium through ticker/link changes."
    notes: "Catalog confirms contrib_liquidity_taq.bbd and contrib_liquidity_taq.ilc. These should be preferred before full TAQ if the goal is cost realism."

  - requirement_id: "WRDS-P2-022-taq-intraday-trades-quotes-nbbo"
    priority: "P2_HIGH_VALUE"
    project_need: "Intraday trades/quotes/NBBO for execution model validation and serious cost/slippage research."
    quant_use_case: "Spread at trade time, realized impact, TWAP/VWAP calibration, queue/latency model validation, intraday volatility, and market microstructure diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "taqm_YYYY"
    wrds_table: "complete_nbbo_YYYYMMDD + cqm_YYYYMMDD + ctm_YYYYMMDD"
    wrds_product_or_library: "NYSE TAQ millisecond/daily TAQ"
    logical_dataset: "taq_intraday_nbbo_trades_quotes"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to 2019-12-31 for current holdout cost audit"
      optimal: "2018-01-02 to latest available first; older history only after core modern data"
      tier_split: "recent_critical"
    frequency: "intraday"
    expected_size_class: "huge"
    partition_strategy: "month"
    key_columns:
      identifiers: ["symbol", "permno", "cusip", "exchange"]
      dates: ["date", "time", "datetime"]
      measures: ["bid", "ask", "best_bid", "best_ask", "price", "size", "volume", "condition", "exchange"]
    joins:
      required_link_tables: ["wrdsapps_link_crsp_taqm.taqmclink", "wrdsapps_link_crsp_taq.tclink", "crsp.dsenames"]
      joins_to_project_data: ["src/microalpha/execution.py", "src/microalpha/slippage.py", "src/microalpha/lob.py", "future slippage calibration artifacts"]
      point_in_time_risks: ["Do not use post-trade NBBO or end-of-day aggregates for pre-trade execution assumptions unless lagged."]
    bias_risks:
      survivorship: "Medium through symbol/linking coverage."
      lookahead: "High if quote/trade timestamps are not aligned before simulated child orders."
      restatement: "Low."
      delisting: "Medium."
      corporate_actions: "Medium through symbol changes."
    notes: "Catalog shows yearly TAQM schemas with complete_nbbo, cqm, and ctm partitions, plus link tables. Pull only narrow date/symbol partitions after higher P0/P1 data is stable."

  - requirement_id: "WRDS-P2-023-taq-crsp-link"
    priority: "P2_HIGH_VALUE"
    project_need: "Identifier bridge from TAQ symbols to CRSP permnos."
    quant_use_case: "Safe TAQ joins for spread/impact calibration on the same securities as CRSP backtests."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "wrdsapps_link_crsp_taqm"
    wrds_table: "taqmclink"
    wrds_product_or_library: "WRDS CRSP-TAQ/TAQM link"
    logical_dataset: "crsp_taq_link_history"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to 2019-12-31"
      optimal: "full available TAQ coverage"
      tier_split: "table_level"
    frequency: "event"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: ["permno", "cusip", "symbol"]
      dates: ["date", "date1"]
      measures: ["score"]
    joins:
      required_link_tables: ["crsp.dsenames", "taqm_YYYY.complete_nbbo_YYYYMMDD"]
      joins_to_project_data: ["future TAQ calibration pipeline"]
      point_in_time_risks: ["Use link validity dates; ticker changes around corporate actions require careful mapping."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "Medium."
      restatement: "Low."
      delisting: "Medium."
      corporate_actions: "High if symbol changes ignored."
    notes: "Catalog also confirms wrdsapps_link_crsp_taq.tclink."

  - requirement_id: "WRDS-P2-024-optionmetrics-underlying-prices-security"
    priority: "P2_HIGH_VALUE"
    project_need: "OptionMetrics security and underlying daily price metadata."
    quant_use_case: "Implied-volatility features, option liquidity filters, borrow/cost joins, and volatility regime controls."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "secprd"
    wrds_product_or_library: "OptionMetrics IvyDB US underlying security price data"
    logical_dataset: "optionmetrics_underlying_security"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available"
      optimal: "2000-01-03 to latest available"
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["secid", "cusip", "ticker"]
      dates: ["date"]
      measures: ["low", "high", "close", "open", "volume", "return", "cfadj", "cfret", "shrout"]
    joins:
      required_link_tables: ["optionm.securd", "wrdsapps_link_crsp_optionm.opcrsphist"]
      joins_to_project_data: ["future volatility/option feature store"]
      point_in_time_risks: ["Use CRSP-OptionMetrics link validity dates; option identifiers differ from CRSP permnos."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "Medium."
      restatement: "Low."
      delisting: "Medium."
      corporate_actions: "Medium through cfadj and security mapping."
    notes: "Catalog confirms optionm.secprd and optionm.securd."

  - requirement_id: "WRDS-P2-025-optionmetrics-option-prices-greeks"
    priority: "P2_HIGH_VALUE"
    project_need: "Option-level prices, implied volatility, greeks, open interest, and option liquidity."
    quant_use_case: "Volatility-risk features, skew/smile diagnostics, option-implied sentiment, risk regime controls, and option market liquidity filters."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "opprcdYYYY"
    wrds_product_or_library: "OptionMetrics IvyDB US option price files"
    logical_dataset: "optionmetrics_option_prices_greeks"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available for recent research"
      optimal: "1996-01-01 to latest available if storage/entitlement permits"
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["secid", "optionid", "symbol", "root", "suffix"]
      dates: ["date", "exdate", "last_date"]
      measures: ["strike_price", "best_bid", "best_offer", "volume", "open_interest", "impl_volatility", "delta", "gamma", "vega", "theta", "cp_flag"]
    joins:
      required_link_tables: ["optionm.securd", "optionm.secprd", "wrdsapps_link_crsp_optionm.opcrsphist"]
      joins_to_project_data: ["future option feature store", "future regime/volatility models"]
      point_in_time_risks: ["Use option records available on trade date only; avoid forward-looking expiration outcomes in features."]
    bias_risks:
      survivorship: "Medium through option availability and underlying link coverage."
      lookahead: "High if future implied-vol surfaces or expiration outcomes are used."
      restatement: "Low to medium."
      delisting: "Medium."
      corporate_actions: "High if split-adjusted option terms are mishandled."
    notes: "Catalog confirms yearly optionm.opprcd1996 through optionm.opprcd2025 style partitions."

  - requirement_id: "WRDS-P2-026-optionmetrics-borrow-rates"
    priority: "P2_HIGH_VALUE"
    project_need: "Security-level borrow-rate estimates to replace or validate static borrow floor assumptions."
    quant_use_case: "Short-cost realism, borrow sensitivity, hard-to-borrow filters, net return validation, and cost decomposition."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "borrateYYYY"
    wrds_product_or_library: "OptionMetrics borrow rate files"
    logical_dataset: "optionmetrics_borrow_rates"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to 2019-12-31"
      optimal: "1996-01-01 to latest available"
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["secid", "securityid"]
      dates: ["date", "expirationdate"]
      measures: ["days", "borrowrate"]
    joins:
      required_link_tables: ["wrdsapps_link_crsp_optionm.opcrsphist", "optionm.securd"]
      joins_to_project_data: ["src/microalpha/portfolio.py borrow_cost_total", "src/microalpha/market_metadata.py borrow_fee_annual_bps"]
      point_in_time_risks: ["Borrow rates must be lagged or same-day available according to execution assumption; expiration-specific rates need documented selection."]
    bias_risks:
      survivorship: "Medium through option/underlying coverage."
      lookahead: "Medium if future borrow term structure is used."
      restatement: "Low."
      delisting: "Medium."
      corporate_actions: "Medium through secid/permno link."
    notes: "Current configs use borrow annual fee null, floor 8 bps, multiplier 1.0. This dataset can make that assumption empirical."

  - requirement_id: "WRDS-P2-027-optionmetrics-vol-surfaces-historical-vol"
    priority: "P2_HIGH_VALUE"
    project_need: "Volatility surfaces and historical volatility for regime controls and option-implied diagnostics."
    quant_use_case: "Implied volatility/skew features, vol regime controls, realized/implied spread, and risk scaling diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "optionm"
    wrds_table: "vsurfdYYYY + historical_volatility"
    wrds_product_or_library: "OptionMetrics volatility surfaces and historical volatility"
    logical_dataset: "optionmetrics_volatility_surfaces"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available"
      optimal: "1996-01-01 to latest available"
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["secid", "securityid"]
      dates: ["date"]
      measures: ["days", "delta", "impl_volatility", "impl_strike", "impl_premium", "dispersion", "cp_flag", "volatility"]
    joins:
      required_link_tables: ["wrdsapps_link_crsp_optionm.opcrsphist", "optionm.securd"]
      joins_to_project_data: ["future volatility feature store"]
      point_in_time_risks: ["Surfaces must be date-aligned and not filled forward across missing option-market days without a rule."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High if surfaces computed after close are used for same-close trades."
      restatement: "Low to medium."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms optionm.historical_volatility, yearly hvoldYYYY files, and sample US vsurfdYYYY partitions; exact full US volatility-surface yearly table names should be verified before download."

  - requirement_id: "WRDS-P2-028-optionmetrics-crsp-link"
    priority: "P2_HIGH_VALUE"
    project_need: "Historical CRSP permno to OptionMetrics secid bridge."
    quant_use_case: "Safe option/borrow/volatility joins to CRSP-based strategy universe."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "wrdsapps_link_crsp_optionm"
    wrds_table: "opcrsphist"
    wrds_product_or_library: "WRDS CRSP-OptionMetrics link"
    logical_dataset: "crsp_optionmetrics_link_history"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available"
      optimal: "full available OptionMetrics coverage"
      tier_split: "table_level"
    frequency: "event"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: ["secid", "permno"]
      dates: ["sdate", "edate"]
      measures: ["score"]
    joins:
      required_link_tables: ["optionm.securd", "crsp.dsenames"]
      joins_to_project_data: ["future option/borrow feature store"]
      point_in_time_risks: ["Use sdate/edate and score filters; do not join by ticker alone."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "Medium."
      restatement: "Low."
      delisting: "Medium."
      corporate_actions: "High if link validity ignored."
    notes: "Catalog confirms wrdsapps_link_crsp_optionm.opcrsphist and wrdsapps.opcrsphist."

  - requirement_id: "WRDS-P2-029-securities-lending-short-costs"
    priority: "P2_HIGH_VALUE"
    project_need: "Actual securities lending, utilization, short availability, rebate, and hard-to-borrow data beyond OptionMetrics borrow proxies."
    quant_use_case: "Realistic short constraints, capacity, borrow-cost stress tests, unavailable-to-short filters, and net-of-costs claim validation."
    wrds_availability: "entitlement_gap"
    wrds_schema: "markit_msf_or_vendor_specific"
    wrds_table: "to_be_verified"
    wrds_product_or_library: "Markit Securities Finance, IHS/S3, or similar lending data if entitled"
    logical_dataset: "securities_lending_borrow_availability"
    required_for_current_reproduction: false
    required_for_current_claim_validation: true
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to 2019-12-31"
      optimal: "2018-present first; full available later"
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["isin", "cusip", "sedol", "permno"]
      dates: ["date"]
      measures: ["borrow_fee", "rebate_rate", "utilization", "shares_on_loan", "lendable_quantity", "short_availability"]
    joins:
      required_link_tables: ["crsp.dsenames", "crsp.stocknames", "wrdsapps_link_crsp_factset.fscrsplink if FactSet-based"]
      joins_to_project_data: ["src/microalpha/market_metadata.py", "future borrow-cost metadata"]
      point_in_time_risks: ["Use only rates/availability known before trade; entitlement-specific timestamps must be documented."]
    bias_risks:
      survivorship: "Medium to high because coverage can be vendor/lender dependent."
      lookahead: "High if end-of-day availability is used before execution."
      restatement: "Low to medium."
      delisting: "Medium."
      corporate_actions: "Medium through identifier changes."
    notes: "The catalog shows Markit metadata references and OptionMetrics borrate tables, but an exact US lending base table was not pinned in the bounded scan. Treat as entitlement/question before planning downloads."

  - requirement_id: "WRDS-P2-030-us-short-interest"
    priority: "P2_HIGH_VALUE"
    project_need: "Exchange/FINRA short interest and short-sale pressure data."
    quant_use_case: "Crowded-short diagnostics, borrow stress proxy, squeeze risk, and short-leg feasibility."
    wrds_availability: "uncertain_or_external"
    wrds_schema: "to_be_verified"
    wrds_table: "to_be_verified"
    wrds_product_or_library: "US short interest if available through WRDS entitlement; otherwise external FINRA/exchange source"
    logical_dataset: "us_short_interest"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available"
      optimal: "2000-present if available"
      tier_split: "modern_research"
    frequency: "monthly"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["cusip", "ticker", "permno"]
      dates: ["settlement_date", "publication_date"]
      measures: ["short_interest", "days_to_cover", "shares_out", "short_ratio"]
    joins:
      required_link_tables: ["crsp.dsenames", "crsp.msf"]
      joins_to_project_data: ["future short-feasibility diagnostics"]
      point_in_time_risks: ["Use publication/release date, not settlement date alone, for tradable features."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High if publication lag ignored."
      restatement: "Low."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "No exact US short-interest table was confirmed in the bounded catalog scan; do not assume availability without entitlement/catalog verification."

  - requirement_id: "WRDS-P2-031-thomson-refinitiv-13f-holdings"
    priority: "P2_HIGH_VALUE"
    project_need: "Institutional ownership, concentration, and flow features."
    quant_use_case: "Crowding, institutional demand, ownership breadth, flow momentum, and liquidity/capacity diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "tfn"
    wrds_table: "s34"
    wrds_product_or_library: "Thomson/Refinitiv 13F institutional holdings"
    logical_dataset: "institutional_13f_holdings"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "quarterly"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["mgrno", "cusip", "ticker"]
      dates: ["fdate", "rdate", "prdate"]
      measures: ["shares", "sole", "shared", "no", "change", "prc", "shrout1", "shrout2", "typecode"]
    joins:
      required_link_tables: ["crsp.dsenames", "crsp.msf"]
      joins_to_project_data: ["future ownership feature store"]
      point_in_time_risks: ["Use report/publication date lag; 13F fdate is quarter-end, not public availability."]
    bias_risks:
      survivorship: "Medium through manager and CUSIP coverage."
      lookahead: "High if report lag ignored."
      restatement: "Medium because amended filings can revise history."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms tfn.s34, tfn.s34type3, tfn.s34type6, and related 13F tables."

  - requirement_id: "WRDS-P3-032-mutual-fund-holdings-and-returns"
    priority: "P3_SPECIALIZED"
    project_need: "Mutual fund ownership/flow context and mutual fund benchmark/flow features."
    quant_use_case: "Fund-flow induced demand, ownership pressure, benchmark crowding, and institutional sponsorship diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "tfn"
    wrds_table: "s12"
    wrds_product_or_library: "Thomson mutual fund holdings plus CRSP mutual funds"
    logical_dataset: "mutual_fund_holdings_returns"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "quarterly"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["fundno", "crsp_fundno", "crsp_portno", "cusip", "ticker"]
      dates: ["fdate", "rdate", "prdate", "caldt"]
      measures: ["shares", "change", "assets", "mret", "dead_flag", "index_fund_flag"]
    joins:
      required_link_tables: ["crsp_q_mutualfunds.fund_hdr", "crsp_q_mutualfunds.monthly_returns", "crsp.dsenames"]
      joins_to_project_data: ["future fund flow/crowding feature store"]
      point_in_time_risks: ["Use report/availability lag and preserve dead funds to avoid survivorship."]
    bias_risks:
      survivorship: "High if dead/merged funds are removed."
      lookahead: "High if holdings are available at fiscal/report date rather than filing date."
      restatement: "Medium."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms tfn.s12 and CRSP mutual fund tables such as crsp_q_mutualfunds.fund_hdr and monthly_returns."

  - requirement_id: "WRDS-P3-033-bond-credit-trace"
    priority: "P3_SPECIALIZED"
    project_need: "Credit and bond-market context for equity regime, distress, and capital-structure features."
    quant_use_case: "Credit-spread regime controls, issuer distress indicators, bond-equity lead/lag diagnostics, and cross-asset robustness."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "wrdsapps_bondret"
    wrds_table: "trace_enhanced_clean"
    wrds_product_or_library: "TRACE cleaned bond trades and WRDS Bond Return"
    logical_dataset: "trace_bondret_credit_context"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available"
      optimal: "full available TRACE/Bond Return history"
      tier_split: "recent_critical"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["cusip", "issuer", "permno", "gvkey"]
      dates: ["trd_exctn_dt", "date"]
      measures: ["price", "yield", "spread", "volume", "return"]
    joins:
      required_link_tables: ["wrdsapps_link_crsp_bond.bondcrsp_link", "crsp.dsenames", "comp.company"]
      joins_to_project_data: ["future cross-asset feature store"]
      point_in_time_risks: ["Bond data may publish with lags/corrections; use conservative availability assumptions."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "Medium."
      restatement: "Medium."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms wrdsapps_bondret.trace_enhanced_clean, trace_standard_clean, bondret, bondret_std, and bondcrsp_link."

  - requirement_id: "WRDS-P2-034-macro-regime-factor-controls"
    priority: "P2_HIGH_VALUE"
    project_need: "Market, macro, and factor-regime controls beyond FF factors."
    quant_use_case: "Regime segmentation, robustness by macro state, q-factor comparisons, uncertainty controls, and stress-period diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "macrofin"
    wrds_table: "q_factors_daily"
    wrds_product_or_library: "Macro Finance factors and uncertainty datasets"
    logical_dataset: "macro_regime_controls"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-03 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "mixed"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: []
      dates: ["date"]
      measures: ["q-factor returns", "financial_uncertainty", "macro_uncertainty", "cay", "fxdata"]
    joins:
      required_link_tables: []
      joins_to_project_data: ["future regime diagnostics", "future factor report extensions"]
      point_in_time_risks: ["Macro releases may be revised; use release-date/vintage discipline for predictive features."]
    bias_risks:
      survivorship: "Low."
      lookahead: "High for revised macro series if used predictively."
      restatement: "High for macro releases unless vintages are used."
      delisting: "Low."
      corporate_actions: "Low."
    notes: "Catalog confirms macrofin.q_factors_daily/weekly/monthly/quarterly and macrofin_comm_trade financial_uncertainty/macro_uncertainty tables."

  - requirement_id: "WRDS-P3-035-cboe-options-market-regime"
    priority: "P3_SPECIALIZED"
    project_need: "Options-market regime controls such as volatility and option-market factor data."
    quant_use_case: "Risk-on/off segmentation, implied volatility regime tests, option volume/put-call context, and crash-risk controls."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "cboe"
    wrds_table: "eqfactor"
    wrds_product_or_library: "CBOE EOD/options-market datasets"
    logical_dataset: "cboe_regime_controls"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available"
      optimal: "2000-01-03 to latest available"
      tier_split: "modern_research"
    frequency: "daily"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["ticker", "option_symbol"]
      dates: ["startdate", "date"]
      measures: ["option factor fields", "equity factor fields", "volatility measures"]
    joins:
      required_link_tables: ["crsp.dsenames if equity-level join needed"]
      joins_to_project_data: ["future regime diagnostics"]
      point_in_time_risks: ["Confirm each CBOE field's timestamp and public availability before predictive use."]
    bias_risks:
      survivorship: "Low to medium."
      lookahead: "Medium."
      restatement: "Low."
      delisting: "Low."
      corporate_actions: "Low."
    notes: "Catalog confirms cboe.eqfactor and cboe.optfactor. Exact VIX-table availability was not pinned; treat VIX-specific downloads as catalog/entitlement checks."

  - requirement_id: "WRDS-P3-036-audit-analytics-accounting-events"
    priority: "P3_SPECIALIZED"
    project_need: "Accounting, restatement, audit, and legal event data for risk/event features."
    quant_use_case: "Quality risk, restatement/AAER flags, audit opinion changes, going-concern warnings, legal event filters, and event studies."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "audit"
    wrds_table: "feed91_aaer"
    wrds_product_or_library: "Audit Analytics"
    logical_dataset: "audit_analytics_events"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["company_fkey", "cik", "gvkey"]
      dates: ["first_release_date", "file_date", "opinion_file_date", "event_date", "breach_disclosure_date"]
      measures: ["severity fields", "event_type", "release fields", "violation fields"]
    joins:
      required_link_tables: ["audit.wrds_lookup_edgar_company_block", "comp.company", "crsp.ccmxpf_linktable"]
      joins_to_project_data: ["future risk/event feature store"]
      point_in_time_risks: ["Use filing/release/disclosure date; do not use event windows before disclosure."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High if fiscal/event periods are used before disclosure date."
      restatement: "High by dataset nature; use release chronology."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms audit.feed91_aaer, audit.feed74_aqrm, audit.feed86_audit_firm_events, audit.f39_restatement_filings, audit.feed85_cybersecurity, and related support tables."

  - requirement_id: "WRDS-P3-037-ma-transactions-and-corporate-events"
    priority: "P3_SPECIALIZED"
    project_need: "M&A/corporate event controls for abnormal returns and universe/identifier disruptions."
    quant_use_case: "Merger event filters, delisting/terminal return diagnostics, corporate action event studies, and takeover-risk controls."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "audit"
    wrds_table: "feed18_merger_acquisition"
    wrds_product_or_library: "Audit Analytics M&A / SDC if separately entitled"
    logical_dataset: "ma_corporate_events"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["company_fkey", "cik", "gvkey", "cusip"]
      dates: ["comm_date", "transaction_date", "file_date"]
      measures: ["deal fields", "transaction status", "consideration fields"]
    joins:
      required_link_tables: ["audit.wrds_lookup_edgar_company_block", "comp.company", "crsp.ccmxpf_linktable"]
      joins_to_project_data: ["future event filters", "future corporate action diagnostics"]
      point_in_time_risks: ["Use announcement/publication date for tradable features; completion dates are often future outcomes."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High if completed-deal outcomes are used before announcement."
      restatement: "Medium."
      delisting: "High for acquired/delisted securities."
      corporate_actions: "High."
    notes: "Catalog confirms Audit Analytics merger/acquisition tables. Exact SDC tables were not pinned in the bounded scan and should be treated as entitlement/catalog verification if needed."

  - requirement_id: "WRDS-P3-038-boardex-executives-compensation-governance"
    priority: "P3_SPECIALIZED"
    project_need: "Governance, board, executive, and compensation features."
    quant_use_case: "Governance quality, insider/executive incentives, board network effects, executive turnover, and firm-risk controls."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "boardex"
    wrds_table: "na_wrds_company_profile"
    wrds_product_or_library: "BoardEx and CIQ compensation"
    logical_dataset: "governance_executive_compensation"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "annual"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["companyid", "directorid", "gvkey", "cik", "ticker"]
      dates: ["annualreportdate", "datestartrole", "effectivedate", "filingdate"]
      measures: ["board fields", "director characteristics", "compensation fields", "network fields"]
    joins:
      required_link_tables: ["wrdsapps.boardex_ciq_link", "wrdsapps.exec_ciq_link", "comp.company", "crsp.ccmxpf_linktable"]
      joins_to_project_data: ["future governance feature store"]
      point_in_time_risks: ["Annual report date and role start dates must be lagged to public availability; governance data often arrives after fiscal year-end."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High without report/filing lag."
      restatement: "Medium."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms BoardEx NA/EUR/ROW/UK families, wrdsapps BoardEx-CIQ links, and CIQ compensation tables such as ciq.wrds_compensation."

  - requirement_id: "WRDS-P3-039-insider-transactions"
    priority: "P3_SPECIALIZED"
    project_need: "Insider trading and ownership activity signals."
    quant_use_case: "Insider purchase/sale pressure, governance/sentiment features, event filters, and risk diagnostics."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "tr_insiders"
    wrds_table: "amend"
    wrds_product_or_library: "Refinitiv/Thomson insiders, FactSet insider, TwoIQ if entitled"
    logical_dataset: "insider_transactions"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "event"
    expected_size_class: "large"
    partition_strategy: "year"
    key_columns:
      identifiers: ["cusip", "ticker", "cik", "insider_id"]
      dates: ["effdate", "secdate", "trandate_ar", "tdate", "trade_date"]
      measures: ["transaction type", "shares", "price", "ownership", "amend flags"]
    joins:
      required_link_tables: ["crsp.dsenames", "wrdsapps.boardex_trinsider_link", "wrdsapps.exec_trinsider_link"]
      joins_to_project_data: ["future insider feature store"]
      point_in_time_risks: ["Use SEC filing date/accepted date rather than trade date if modeling investable signals."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High if filing lag ignored."
      restatement: "Medium due to amendments."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms tr_insiders tables and FactSet/TwoIQ metadata; exact production table choice should follow entitlement."

  - requirement_id: "WRDS-P3-040-patents-innovation"
    priority: "P3_SPECIALIZED"
    project_need: "Patent and innovation data for long-horizon feature research."
    quant_use_case: "Innovation intensity, patent quality, intangible asset proxies, and sector-specific growth features."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "contrib_kpss"
    wrds_table: "kpss_patents"
    wrds_product_or_library: "KPSS patents and WRDS patent links"
    logical_dataset: "patent_innovation_features"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "full_history"
    frequency: "event"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["gvkey", "patent_id", "assignee"]
      dates: ["filing_date", "grantdate", "link_bdate"]
      measures: ["citation fields", "patent counts", "technology fields"]
    joins:
      required_link_tables: ["wrdsapps_patents.uspatents_gvkey_linking", "comp.company", "crsp.ccmxpf_linktable"]
      joins_to_project_data: ["future long-horizon feature store"]
      point_in_time_risks: ["Grant dates and citation updates can leak; use filing/grant availability according to feature definition."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High if future citations are used."
      restatement: "Medium."
      delisting: "Low to medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms contrib_kpss.kpss_patents, contrib_patent_firm_link tables, and wrdsapps patent link tables."

  - requirement_id: "WRDS-P3-041-supply-chain-customer-links"
    priority: "P3_SPECIALIZED"
    project_need: "Customer/supplier and segment relationship data."
    quant_use_case: "Supply-chain momentum, customer concentration, peer spillovers, revenue segment exposure, and sector-neutral alternative features."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "comp"
    wrds_table: "wrds_seg_customer"
    wrds_product_or_library: "Compustat segments and FactSet Revere supply chain if entitled"
    logical_dataset: "supply_chain_customer_links"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full available history"
      tier_split: "modern_research"
    frequency: "annual"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["gvkey", "customer_gvkey", "cusip", "companyid"]
      dates: ["datadate", "srcdate", "start_"]
      measures: ["sales", "customer_name", "relationship fields", "segment fields"]
    joins:
      required_link_tables: ["comp.company", "crsp.ccmxpf_linktable", "factset_revere_supply_chain.wrds_relationship if entitled"]
      joins_to_project_data: ["future supply-chain feature store"]
      point_in_time_risks: ["Use disclosure/source dates; customer relationships can be reported long after fiscal periods."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High if fiscal-period data is used before disclosure."
      restatement: "Medium."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms comp.seg_customer, comp.wrds_seg_customer, and FactSet Revere supply-chain families."

  - requirement_id: "WRDS-P3-042-news-events-ravenpack-reprisk"
    priority: "P3_SPECIALIZED"
    project_need: "News/sentiment/event feeds for event-driven and alternative-data extensions."
    quant_use_case: "News sentiment, event study filters, ESG controversy, macro/news regime controls, and post-news drift tests."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "ravenpack_full"
    wrds_table: "rp_equities_standardrpnavariableset"
    wrds_product_or_library: "RavenPack/RepRisk/Dow Jones if entitled"
    logical_dataset: "news_sentiment_events"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available"
      optimal: "full entitled history"
      tier_split: "recent_critical"
    frequency: "event"
    expected_size_class: "huge"
    partition_strategy: "month"
    key_columns:
      identifiers: ["entity_id", "rp_entity_id", "ticker", "cusip", "gvkey"]
      dates: ["timestamp", "news_date", "range_start", "range_end"]
      measures: ["sentiment", "event relevance", "novelty", "category", "source", "controversy score"]
    joins:
      required_link_tables: ["ravenpack_common.rp_entity_mapping if entitled", "comp.company", "crsp.dsenames"]
      joins_to_project_data: ["future event feature store"]
      point_in_time_risks: ["Use exact news timestamp and source availability; entity mapping windows matter."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "Critical if revised/news-classified records are used before timestamp."
      restatement: "Medium for reprocessed sentiment/event classification."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog metadata confirms RavenPack and RepRisk families. Entitlement and exact table access should be verified before planning pulls."

  - requirement_id: "WRDS-P4-043-esg-sustainability-and-climate"
    priority: "P4_LONG_TAIL"
    project_need: "ESG, climate, and sustainability data for specialized overlays."
    quant_use_case: "ESG risk controls, climate risk tilt, controversy filters, and non-alpha research appendices."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "crsp"
    wrds_table: "esg"
    wrds_product_or_library: "CRSP ESG, Audit ESG funds, MSCI/Trucost/RepRisk if entitled"
    logical_dataset: "esg_climate_sustainability"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2018-01-02 to latest available"
      optimal: "full available history"
      tier_split: "recent_critical"
    frequency: "mixed"
    expected_size_class: "medium"
    partition_strategy: "year"
    key_columns:
      identifiers: ["permno", "gvkey", "cik", "ticker"]
      dates: ["date", "event_date", "market_cap_as_of_date", "signature_date"]
      measures: ["ESG scores", "climate fields", "assurance fields", "controversy fields"]
    joins:
      required_link_tables: ["crsp.dsenames", "comp.company", "crsp.ccmxpf_linktable"]
      joins_to_project_data: ["future ESG overlay diagnostics"]
      point_in_time_risks: ["Vendor ESG histories may be backfilled; confirm point-in-time availability before predictive use."]
    bias_risks:
      survivorship: "Medium."
      lookahead: "High for backfilled ESG scores."
      restatement: "High for revised ESG histories."
      delisting: "Medium."
      corporate_actions: "Medium."
    notes: "Catalog confirms crsp.esg, crsp.eod_esg, audit_esg_funds tables, and climate/patent families. Long-tail for this repo unless strategy explicitly shifts."

  - requirement_id: "WRDS-P4-044-international-global-equities"
    priority: "P4_LONG_TAIL"
    project_need: "Non-US/global equity extension once the US WRDS/CRSP pipeline is defensible."
    quant_use_case: "Out-of-market validation, international robustness, regional factor tests, and broader research publication scope."
    wrds_availability: "confirmed_in_catalog"
    wrds_schema: "comp"
    wrds_table: "g_secd"
    wrds_product_or_library: "Compustat Global, Datastream/Worldscope links, international WRDS apps"
    logical_dataset: "global_equity_extension"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2010-01-01 to latest available"
      optimal: "full available global history"
      tier_split: "legacy_backfill"
    frequency: "daily"
    expected_size_class: "huge"
    partition_strategy: "year"
    key_columns:
      identifiers: ["gvkey", "iid", "isin", "sedol", "ticker"]
      dates: ["datadate", "monthend", "date"]
      measures: ["prccd", "cshoc", "cshtrd", "trfd", "div", "split", "gind", "gsubind"]
    joins:
      required_link_tables: ["comp.g_company", "wrdsapps.ds2ws_linktable", "wrdsapps.intl_security_returns"]
      joins_to_project_data: ["future global research branch"]
      point_in_time_risks: ["Global calendars, currencies, local market holidays, and identifier histories must be treated explicitly."]
    bias_risks:
      survivorship: "High without dead/inactive securities and country-specific coverage audits."
      lookahead: "High for accounting and index membership."
      restatement: "Medium to high."
      delisting: "High."
      corporate_actions: "High."
    notes: "Not urgent for the current US CRSP claim. Include only after P0-P2 US evidence work is stable."

  - requirement_id: "WRDS-P4-045-external-fred-treasury-vintages"
    priority: "P4_LONG_TAIL"
    project_need: "Macro and rate vintages if macro timing becomes a predictive feature rather than a descriptive control."
    quant_use_case: "Rate regime, inflation/growth conditions, macro release surprise, and vintage-aware macro robustness."
    wrds_availability: "uncertain_or_external"
    wrds_schema: "external_or_wrds_to_be_verified"
    wrds_table: "fred_treasury_vintages_to_be_verified"
    wrds_product_or_library: "FRED/ALFRED/Treasury or WRDS macro if entitled"
    logical_dataset: "macro_rate_vintages"
    required_for_current_reproduction: false
    required_for_current_claim_validation: false
    useful_for_future_expansion: true
    date_range:
      minimum_required: "2000-01-01 to latest available"
      optimal: "full vintage history"
      tier_split: "legacy_backfill"
    frequency: "mixed"
    expected_size_class: "small"
    partition_strategy: "table"
    key_columns:
      identifiers: ["series_id"]
      dates: ["observation_date", "release_date", "vintage_date"]
      measures: ["value", "yield", "rate", "surprise"]
    joins:
      required_link_tables: []
      joins_to_project_data: ["future macro regime diagnostics"]
      point_in_time_risks: ["Use vintages/release dates; final revised macro series are not safe as predictive features."]
    bias_risks:
      survivorship: "Low."
      lookahead: "Critical for macro releases and revisions."
      restatement: "Critical unless vintage data is used."
      delisting: "Low."
      corporate_actions: "Low."
    notes: "Catalog scan confirmed macrofin factor/uncertainty tables, but did not pin exact FRED/ALFRED/Treasury vintage tables. Treat as external or entitlement-specific."

wrds_catalog_checks_needed:
  - "Verify whether future exports should use legacy CRSP tables (crsp.dsf/msf/dsenames/dsedelist) or CIZ-style tables (crsp.dsf_v2, crsp.stkdlysecuritydata, crsp.stksecurityinfohist, crsp.stkdelists) as the canonical source."
  - "Verify exact coverage and row counts for restored or regenerated wrds_crsp_export_20251221_v1 before claiming reproduction."
  - "Verify whether the current local WRDS vault already has non-raw derived exports compatible with ${WRDS_DATA_ROOT}/crsp/daily_csv, meta, universes, and manifests."
  - "Verify exact yearly OptionMetrics volatility-surface table names for full US coverage; sample names are visible, but production full-history naming should be checked before download."
  - "Verify TAQ schema partition naming for the desired date range; catalog shows taqm_YYYY schemas and daily complete_nbbo/cqm/ctm tables."
  - "Verify exact US short-interest table availability; no exact US short-interest table was pinned in the bounded catalog scan."
  - "Verify securities-lending entitlements and table names for Markit/IHS/S3 or equivalent data; OptionMetrics borrateYYYY is confirmed but may not replace full lending data."
  - "Verify CBOE/VIX-specific table names if volatility-index controls are needed; cboe.eqfactor and cboe.optfactor are confirmed, but VIX table was not pinned."
  - "Verify RavenPack/RepRisk/News entitlement and exact production table access before any news-feature pull."
  - "Verify whether SDC Platinum is entitled and exposed under a schema not surfaced by the bounded scan; Audit Analytics M&A tables are confirmed but not a full SDC substitute."
  - "Verify point-in-time availability dates for Compustat, IBES, 13F, Audit Analytics, governance, ESG, and macro datasets before using them as predictive features."

entitlement_questions:
  - "Do we have active WRDS entitlement for CRSP US Stock/Security including daily, monthly, names, delistings, distributions, indexes, and CIZ-style files?"
  - "Do we have Compustat North America fundamentals, company/security descriptors, and index constituent history?"
  - "Do we have CRSP/Compustat Merged link tables and WRDSApps link libraries for IBES, OptionMetrics, TAQ, Bond, FactSet, and BoardEx?"
  - "Do we have Ken French daily FF5 plus momentum factors through WRDS, or should a licensed local factor export be maintained separately?"
  - "Do we have IBES summary/detail/actuals/recommendations and permission to store derived feature panels in the shared vault?"
  - "Do we have OptionMetrics IvyDB US including option prices, underlying security prices, borrow rates, volatility surfaces, and CRSP links?"
  - "Do we have NYSE TAQ/TAQM access for 2018-present, and what monthly/date partitions are affordable to pull first?"
  - "Do we have Markit/IHS/S3 securities lending or any WRDS-exposed short-sale/borrow availability dataset beyond OptionMetrics borrow rates?"
  - "Do we have Thomson/Refinitiv 13F and mutual fund holdings, plus CRSP mutual fund returns?"
  - "Do we have Audit Analytics, BoardEx, CIQ compensation, insider transactions, RavenPack/RepRisk, FactSet Revere, KPSS patents, TRACE/Bond Return, and ESG/climate datasets?"
  - "Are any of the above restricted from derived-feature sharing, hashing, or inclusion in review bundles?"

highest_priority_download_order:
  - requirement_id: "WRDS-P0-001-current-derived-export-package"
    reason: "Unblocks exact current reproduction and source-artifact recovery without choosing new research data."
  - requirement_id: "WRDS-P0-002-crsp-daily-stock-prices-returns"
    reason: "Core price/return/volume/shares source for current WRDS strategy and all US equity research."
  - requirement_id: "WRDS-P0-003-crsp-security-names-share-exchange-history"
    reason: "Required for point-in-time common-stock/exchange filters and ticker/permno mapping."
  - requirement_id: "WRDS-P0-004-crsp-delisting-returns"
    reason: "Required to avoid survivorship and delisting-return bias."
  - requirement_id: "WRDS-P0-008-pit-flagship-universe-snapshots"
    reason: "Current strategy cannot run defensibly without PIT universe snapshots."
  - requirement_id: "WRDS-P0-007-ccm-link-and-compustat-sector-metadata"
    reason: "Needed for sector metadata, sector caps, and sector-neutral scoring."
  - requirement_id: "WRDS-P0-005-crsp-market-index-returns"
    reason: "Required for a defensible market-proxy baseline."
  - requirement_id: "WRDS-P0-006-ken-french-daily-factors"
    reason: "Required for risk-free cash baseline and FF5+MOM factor diagnostics."
  - requirement_id: "WRDS-P1-009-crsp-monthly-stock-file"
    reason: "Cheap core foundation for universe formation, baselines, and long history."
  - requirement_id: "WRDS-P1-011-crsp-corporate-actions-and-adjustments"
    reason: "Strengthens corporate-action correctness and validates adjusted return construction."
  - requirement_id: "WRDS-P1-012-crsp-ciz-modern-stock-files"
    reason: "Future-proofs the CRSP pipeline and supports fresh post-2019 holdout construction."
  - requirement_id: "WRDS-P2-021-liquidity-diagnostics-taq-derived"
    reason: "Improves slippage/spread realism before expensive full TAQ pulls."
  - requirement_id: "WRDS-P2-026-optionmetrics-borrow-rates"
    reason: "Empirical borrow costs materially improve net-of-costs claim quality."
  - requirement_id: "WRDS-P1-013-compustat-annual-fundamentals"
    reason: "Core feature and factor expansion after price/universe validity is locked."
  - requirement_id: "WRDS-P2-018-ibes-eps-summary-detail-actuals"
    reason: "High-value analyst/revision/surprise features for later research campaigns."
  - requirement_id: "WRDS-P2-022-taq-intraday-trades-quotes-nbbo"
    reason: "Expensive but valuable for execution/cost calibration once narrower diagnostics justify it."

dedupe_keys_for_global_merge:
  - "local_derived.crsp/daily_csv:dataset_id_symbol_date"
  - "local_derived.universes/flagship_sector_neutral.csv:dataset_id_symbol_effective_date"
  - "crsp.dsf:permno_date"
  - "crsp.dsenames:permno_namedt_nameendt"
  - "crsp.dsedelist:permno_dlstdt"
  - "crsp.msf:permno_date"
  - "crsp.msenames:permno_namedt_nameendt"
  - "crsp.msedelist:permno_dlstdt"
  - "crsp.dsi:date"
  - "ff.fivefactors_daily:date"
  - "ff.factors_daily:date"
  - "crsp.ccmxpf_linktable:gvkey_lpermno_linkdt_linkenddt_linkprim_linktype"
  - "comp.company:gvkey"
  - "comp.security:gvkey_iid"
  - "comp.funda:gvkey_datadate_indfmt_consol_popsrc_datafmt"
  - "comp.fundq:gvkey_datadate_fyearq_fqtr_indfmt_consol_popsrc_datafmt"
  - "comp.idxcst_his:gvkeyx_gvkey_iid_from_thru"
  - "wrdsapps.firm_ratio_ccm:gvkey_permno_adate"
  - "ibes.statsum_epsus:ticker_statpers_measure_fiscalp_fpi_fpedats"
  - "ibes.det_epsus:ticker_estimator_analys_anndats_actdats_fpedats_measure_fpi"
  - "ibes.act_epsus:ticker_anndats_actdats_measure_pends"
  - "ibes.recdsum:ticker_statpers"
  - "wrdsapps_link_crsp_ibes.ibcrsphist:permno_ticker_sdate_edate"
  - "contrib_liquidity_taq.bbd:identifier_date"
  - "taqm_YYYY.complete_nbbo_YYYYMMDD:symbol_date_time_exchange"
  - "taqm_YYYY.cqm_YYYYMMDD:symbol_date_time_exchange_sequence"
  - "taqm_YYYY.ctm_YYYYMMDD:symbol_date_time_exchange_sequence"
  - "wrdsapps_link_crsp_taqm.taqmclink:permno_symbol_date"
  - "optionm.secprd:secid_date"
  - "optionm.securd:secid"
  - "optionm.opprcdYYYY:secid_optionid_date"
  - "optionm.borrateYYYY:securityid_date_expirationdate_days"
  - "optionm.vsurfdYYYY:secid_date_days_delta_cp_flag"
  - "wrdsapps_link_crsp_optionm.opcrsphist:secid_permno_sdate_edate"
  - "tfn.s34:mgrno_cusip_fdate_rdate"
  - "tfn.s12:fundno_cusip_fdate_rdate"
  - "crsp_q_mutualfunds.fund_hdr:crsp_fundno"
  - "crsp_q_mutualfunds.monthly_returns:crsp_fundno_caldt"
  - "wrdsapps_bondret.trace_enhanced_clean:cusip_trd_exctn_dt_trade_id"
  - "macrofin.q_factors_daily:date"
  - "audit.feed91_aaer:aaer_event_key"
  - "audit.feed18_merger_acquisition:company_fkey_comm_date_transaction_id"
  - "boardex.na_wrds_company_profile:companyid_annualreportdate"
  - "tr_insiders.amend:company_insider_transaction_effective_date"
  - "contrib_kpss.kpss_patents:patent_id"
  - "comp.wrds_seg_customer:gvkey_customer_datadate_srcdate"
  - "ravenpack_full.rp_equities_standardrpnavariableset:entity_timestamp_story_id"
```

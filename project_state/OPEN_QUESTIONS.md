# Open Questions

- **WRDS rerun completeness** – Latest WRDS artifacts under `artifacts/wrds_flagship/` lack metrics/folds; docs reference pre‑tightening run. When full data is available, what runtime/resources are required to finish a 2005–2024 walk‑forward with the tightened risk caps?
- **Signal→weight contract** – Flagship strategy emits `meta["weight"]`; Portfolio converts to quantity using current equity/price. Should weights reflect gross exposure targets or per‑sleeve budgets? Clarify for new allocators/strategies.
- **Borrow/ADV coverage** – How to handle symbols missing `borrow_fee_annual_bps` or ADV/spread metadata in WRDS exports? Should there be explicit fallbacks per sector/market‑cap bucket rather than global defaults?
- **Queue model realism** – IOC/PO queue fill fraction uses spread/vol/ADV heuristics and optional randomness. Are these calibrated against any empirical data? Should beta tests compare against historical order book data?
- **SPA vs reality check inputs** – SPA currently runs on grid returns after WFV; reality check bootstrap during WFV also penalises data‑snooping. Should we harmonise these tests or drop one to avoid duplicated inference?
- **Factor model choice** – Default FF5+MOM for WRDS; FF3 for sample. Should models align with data frequency (daily vs weekly) and be configurable from YAML?
- **Performance bottlenecks** – Large WFV runs may exceed interactive time; consider profiling (`MICROALPHA_PROFILE`) or chunked fold execution. Are there easy wins (vectorised returns, caching price windows) without violating chronology?
- **Data quality checks** – Should the engine validate monotonicity/positivity of `volume`/`close` on load (esp. WRDS exports) to avoid silent zero‑turnover runs?

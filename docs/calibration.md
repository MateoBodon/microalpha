Execution Cost Calibration

This guide explains how to configure commission and market impact models.

Commission

- commission (per-share): legacy per-share fee preserved for back-compat.
- commission_bps (preferred): basis points of notional. Commission is
  |qty| * fill_price * commission_bps / 10,000.

Examples:
- 1 bps: commission_bps: 1.0
- 0.5 bps: commission_bps: 0.5

Market Impact

Microalpha ships stylized models useful for research hygiene:

- Linear impact (KyleLambda): slippage = λ * qty
- Square-root impact (SquareRootImpact): slippage = k * sqrt(|qty|)
- TWAP splitting to reduce instantaneous participation
- LOB demo (FIFO with latency) for pedagogical scenarios

Square-root Law Defaults

Empirically, instantaneous impact scales sublinearly with participation:

Impact ≈ Y * σ * sqrt(Participation)

Where σ is daily volatility and Participation = Notional / ADV.
For a daily bar backtest, a pragmatic default is:

- Y ≈ 0.5 (dimensionless)
- σ from symbol’s rolling 20–60d daily volatility
- ADV from rolling average daily volume x price

Map to per-share slippage coefficient k used by SquareRootImpact by
approximating qty as a fraction of ADV at the current price.

Suggested Workflow

1. Start with conservative defaults: commission_bps: 1.0, SquareRootImpact with
   price_impact ≈ 1e-3 for liquid names; increase for small caps.
2. Use TWAP (slices: 2–4) to reduce instantaneous impact.
3. Sensitivity test results against a 2× range of costs.

WRDS Calibration (Optional)

- Use scripts/wrds_crsp_prep.py to export symbol CSVs.
- Compute rolling σ and ADV per symbol, and derive a time-varying k per
  cap bucket. Apply via strategy params or execution kwargs.

Note: The LOB model is pedagogical and not intended as a production-grade
microstructure simulator.


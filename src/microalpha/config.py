"""Configuration schemas for microalpha backtests."""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, model_validator


class SlippageCfg(BaseModel):
    type: Literal["volume", "linear", "sqrt", "linear_sqrt", "linear+sqrt"]
    impact: float = Field(
        default=1e-4, description="Generic impact coefficient (legacy support)."
    )
    k_lin: float | None = Field(
        default=None, description="Linear impact coefficient for ADV scaling."
    )
    eta: float | None = Field(
        default=None, description="Square-root impact coefficient."
    )
    default_adv: float = Field(
        default=1_000_000.0,
        description="Fallback ADV when metadata is unavailable.",
    )
    default_spread_bps: float = Field(
        default=5.0,
        description="Fallback bid-ask spread in basis points.",
    )
    spread_floor_multiplier: float = Field(
        default=0.5, description="Floor multiplier applied to spread for impact."
    )

    @model_validator(mode="before")
    @classmethod
    def _normalise_type(cls, values):  # type: ignore[override]
        if not isinstance(values, dict):
            return values
        stype = str(values.get("type", "")).lower()
        if stype in {"linear+sqrt", "linear_plus_sqrt", "linear-sqrt"}:
            values["type"] = "linear_sqrt"
        return values


class ExecModelCfg(BaseModel):
    type: str = "twap"
    # Commission (per-share or per-unit) – replacing legacy 'aln'
    commission: float = 0.1
    # Keep legacy alias for backward-compatibility (deprecated)
    aln: float | None = None
    price_impact: float = 0.0
    lam: float | None = None
    slices: int | None = None
    urgency: float | None = None
    book_levels: int | None = None
    level_size: int | None = None
    mid_price: float | None = None
    tick_size: float | None = None
    latency_ack: float | None = None
    latency_ack_jitter: float | None = None
    latency_fill: float | None = None
    latency_fill_jitter: float | None = None
    # LOB semantics: enforce t+1 fills by default (can be disabled)
    lob_tplus1: bool | None = True
    slippage: Optional[SlippageCfg] = None
    limit_mode: Literal["market", "ioc", "po"] | None = None
    queue_coefficient: float | None = None
    queue_passive_multiplier: float | None = None
    queue_seed: int | None = None
    queue_randomize: bool | None = None
    volatility_lookback: int | None = None
    min_fill_qty: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _normalise_legacy_fields(cls, values):  # type: ignore[override]
        if not isinstance(values, dict):
            return values
        # Map legacy 'aln' to 'commission' if provided
        if "commission" not in values and "aln" in values:
            try:
                values["commission"] = float(values.get("aln"))
            except Exception:
                pass
            warnings.warn(
                "ExecModelCfg.aln is deprecated; use 'commission' instead.",
                DeprecationWarning,
            )
        # Support legacy execution naming variants
        if values.get("type") in {"squareroot", "sqrt"}:
            values["type"] = "sqrt"
        if "limit_mode" in values and values["limit_mode"] is not None:
            values["limit_mode"] = str(values["limit_mode"]).lower()
        return values


class StrategyCfg(BaseModel):
    name: str
    lookback: int | None = None
    z: float | None = None
    params: Dict[str, Any] = Field(default_factory=dict)
    param_grid: Dict[str, Any] | None = None
    allocator: str | None = None
    allocator_params: Dict[str, Any] = Field(default_factory=dict)


class CapitalPolicyCfg(BaseModel):
    type: Literal["volatility_scaled"]
    lookback: int = 20
    target_dollar_vol: float = 10_000.0
    min_qty: int = 1


class BacktestCfg(BaseModel):
    data_path: str
    symbol: str
    cash: float = 1_000_000
    exec: ExecModelCfg = Field(default_factory=ExecModelCfg)
    strategy: StrategyCfg
    seed: int = 42
    max_exposure: float | None = None
    max_drawdown_stop: float | None = None
    turnover_cap: float | None = None
    kelly_fraction: float | None = None
    # Optional risk sizing and constraints
    vol_target_annualized: float | None = None
    vol_lookback: int | None = None
    max_portfolio_heat: float | None = None
    max_positions_per_sector: int | None = None
    sectors: Dict[str, str] | None = None
    capital_policy: CapitalPolicyCfg | None = None
    start_date: str | None = None
    end_date: str | None = None
    metrics_hac_lags: int | None = None
    meta_path: str | None = None

    @property
    def resolved_data_path(self) -> Path:
        expanded = os.path.expandvars(os.path.expanduser(self.data_path))
        return Path(expanded)


def parse_config(raw: Any) -> BacktestCfg:
    try:
        return BacktestCfg.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

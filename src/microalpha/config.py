"""Configuration schemas for microalpha backtests."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, model_validator


class SlippageCfg(BaseModel):
    type: Literal["volume"]
    impact: float = Field(
        default=1e-4, description="Coefficient for volume-based slippage impact."
    )


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
        return values


class StrategyCfg(BaseModel):
    name: str
    lookback: int | None = None
    z: float | None = None
    params: Dict[str, Any] = Field(default_factory=dict)
    param_grid: Dict[str, Any] | None = None


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

    @property
    def resolved_data_path(self) -> Path:
        return Path(self.data_path)


def parse_config(raw: Any) -> BacktestCfg:
    try:
        return BacktestCfg.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

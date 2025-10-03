"""Configuration schemas for microalpha backtests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, Field, ValidationError


class ExecModelCfg(BaseModel):
    type: str = "twap"
    aln: float = 0.1
    price_impact: float = 0.0
    lam: float | None = None
    slices: int | None = None
    book_levels: int | None = None
    level_size: int | None = None
    mid_price: float | None = None
    tick_size: float | None = None
    latency_ack: float | None = None
    latency_ack_jitter: float | None = None
    latency_fill: float | None = None
    latency_fill_jitter: float | None = None


class StrategyCfg(BaseModel):
    name: str
    lookback: int | None = None
    z: float | None = None
    params: Dict[str, Any] = Field(default_factory=dict)
    param_grid: Dict[str, Any] | None = None


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

    @property
    def resolved_data_path(self) -> Path:
        return Path(self.data_path)


def parse_config(raw: Any) -> BacktestCfg:
    try:
        return BacktestCfg.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

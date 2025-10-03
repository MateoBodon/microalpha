"""Configuration schemas for microalpha backtests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError


class ExecModelCfg(BaseModel):
    type: str = "twap"
    aln: float = 0.1
    price_impact: float = 0.0


class StrategyCfg(BaseModel):
    name: str
    lookback: int
    z: float | None = None


class BacktestCfg(BaseModel):
    data_path: str
    symbol: str
    cash: float = 1_000_000
    exec: ExecModelCfg = Field(default_factory=ExecModelCfg)
    strategy: StrategyCfg
    seed: int = 42

    @property
    def resolved_data_path(self) -> Path:
        return Path(self.data_path)


def parse_config(raw: Any) -> BacktestCfg:
    try:
        return BacktestCfg.model_validate(raw)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


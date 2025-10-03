"""Walk-forward validation configuration schemas."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .config import BacktestCfg


class WalkForwardWindow(BaseModel):
    start: str
    end: str
    training_days: int = Field(gt=0)
    testing_days: int = Field(gt=0)


class WFVCfg(BaseModel):
    template: BacktestCfg
    walkforward: WalkForwardWindow
    grid: Dict[str, List[Any]] = Field(default_factory=dict)
    artifacts_dir: str | None = None

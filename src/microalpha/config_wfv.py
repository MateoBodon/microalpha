"""Walk-forward validation configuration schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from .config import BacktestCfg


class WalkForwardWindow(BaseModel):
    start: str
    end: str
    training_days: int = Field(gt=0)
    testing_days: int = Field(gt=0)


class RealityCheckCfg(BaseModel):
    method: Literal["stationary", "circular", "iid"] = "stationary"
    block_length: Optional[int] = None
    samples: int = Field(default=200, gt=1)


class WFVCfg(BaseModel):
    template: BacktestCfg
    walkforward: WalkForwardWindow
    grid: Dict[str, List[Any]] = Field(default_factory=dict)
    artifacts_dir: str | None = None
    reality_check: RealityCheckCfg = Field(default_factory=RealityCheckCfg)

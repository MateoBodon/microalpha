from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_BASE_CFG = Path("configs/wfv_flagship_wrds.yaml")
_SMOKE_CFG = Path("configs/wfv_flagship_wrds_smoke.yaml")


def _extract_risk(template: dict) -> dict:
    strategy = template.get("strategy", {})
    params = strategy.get("params", {})
    capital = template.get("capital_policy", {})
    return {
        "max_exposure": template.get("max_exposure"),
        "max_drawdown_stop": template.get("max_drawdown_stop"),
        "max_portfolio_heat": template.get("max_portfolio_heat"),
        "turnover_cap": template.get("turnover_cap"),
        "max_positions_per_sector": params.get("max_positions_per_sector"),
        "turnover_target_pct_adv": params.get("turnover_target_pct_adv"),
        "min_adv": params.get("min_adv"),
        "min_price": params.get("min_price"),
        "target_dollar_vol": capital.get("target_dollar_vol"),
    }


def test_wrds_flagship_risk_limits_match_spec() -> None:
    raw = yaml.safe_load(_BASE_CFG.read_text(encoding="utf-8"))
    template = raw["template"]
    risk = _extract_risk(template)

    assert pytest.approx(1.25) == risk["max_exposure"]
    assert pytest.approx(0.20) == risk["max_drawdown_stop"]
    assert pytest.approx(1.5) == risk["max_portfolio_heat"]
    assert risk["max_positions_per_sector"] == 8
    assert pytest.approx(0.03) == risk["turnover_target_pct_adv"]
    assert risk["min_adv"] == 50_000_000.0
    assert risk["min_price"] == 12.0
    assert risk["turnover_cap"] == 180_000_000.0
    assert risk["target_dollar_vol"] == 225_000.0


def test_wrds_smoke_config_keeps_same_limits() -> None:
    base = _extract_risk(yaml.safe_load(_BASE_CFG.read_text(encoding="utf-8"))["template"])
    smoke = _extract_risk(yaml.safe_load(_SMOKE_CFG.read_text(encoding="utf-8"))["template"])
    assert base == smoke

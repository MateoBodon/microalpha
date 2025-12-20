"""Utilities for recording reproducibility manifests."""

from __future__ import annotations

import json
import os
import platform
import random
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from typing import Any, Mapping, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class Manifest:
    run_id: str
    git_sha: str
    microalpha_version: str
    python: str
    platform: str
    numpy_version: str
    pandas_version: str
    seed: int
    config_path: str
    config_sha256: str
    config_summary: dict[str, Any] = field(default_factory=dict)


def resolve_git_sha() -> Tuple[str, str]:
    """Return ``(full_sha, short_sha)`` for the current Git HEAD."""

    try:
        sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown", "unknown"

    short = sha[:7] if sha else "unknown"
    return sha, short


def generate_run_id(short_sha: str, timestamp: Optional[datetime] = None) -> str:
    """Create a run identifier using a UTC timestamp and short SHA."""

    current = timestamp or datetime.now(timezone.utc)
    ts = current.strftime("%Y-%m-%dT%H-%M-%SZ")
    suffix = short_sha if short_sha and short_sha != "unknown" else "nogit"
    return f"{ts}-{suffix}"


def _resolve_distribution_version() -> str:
    """Resolve the installed distribution version for microalpha."""

    try:
        return importlib_metadata.version("microalpha")
    except importlib_metadata.PackageNotFoundError:
        packages = importlib_metadata.packages_distributions()
        distributions = packages.get("microalpha") or []
        for dist in distributions:
            try:
                return importlib_metadata.version(dist)
            except importlib_metadata.PackageNotFoundError:
                continue
    return "unknown"


def build(
    seed: Optional[int],
    config_path: str,
    run_id: str,
    config_sha256: str,
    config_summary: Mapping[str, Any] | None = None,
    git_sha: Optional[str] = None,
) -> Manifest:
    """Construct a manifest and synchronise global RNG state."""

    # Normalise seeds and set global RNGs
    norm_seed = int(seed or 0)
    random.seed(norm_seed)
    np.random.seed(norm_seed)

    full_sha = git_sha or resolve_git_sha()[0]
    version = _resolve_distribution_version()

    return Manifest(
        run_id=run_id,
        git_sha=full_sha,
        microalpha_version=version,
        python=sys.version,
        platform=platform.platform(),
        numpy_version=np.__version__,
        pandas_version=pd.__version__,
        seed=norm_seed,
        config_path=os.path.abspath(config_path),
        config_sha256=config_sha256,
        config_summary=dict(config_summary or {}),
    )


def extract_config_summary(raw_config: Mapping[str, Any]) -> dict[str, Any]:
    """Pull key risk/cost parameters from a config mapping for the manifest."""

    def _as_mapping(value: Any) -> Mapping[str, Any]:
        return value if isinstance(value, Mapping) else {}

    template = _as_mapping(raw_config.get("template", raw_config))
    if not template:
        template = _as_mapping(raw_config)

    exec_cfg = _as_mapping(template.get("exec"))
    slippage_cfg = _as_mapping(exec_cfg.get("slippage"))
    strategy_cfg = _as_mapping(template.get("strategy"))
    params_cfg = _as_mapping(strategy_cfg.get("params"))
    borrow_cfg = _as_mapping(template.get("borrow"))

    risk_caps = {
        "max_gross_leverage": template.get("max_gross_leverage")
        if template.get("max_gross_leverage") is not None
        else template.get("max_portfolio_heat"),
        "max_portfolio_heat": template.get("max_portfolio_heat"),
        "max_net_leverage": template.get("max_exposure"),
        "max_single_name_weight": template.get("max_single_name_weight"),
        "max_drawdown_stop": template.get("max_drawdown_stop"),
        "max_positions_per_sector": template.get("max_positions_per_sector"),
    }
    turnover_caps = {
        "turnover_cap": template.get("turnover_cap"),
        "turnover_target_pct_adv": params_cfg.get("turnover_target_pct_adv"),
        "min_adv": params_cfg.get("min_adv"),
    }
    borrow_model = {
        "annual_fee_bps": borrow_cfg.get("annual_fee_bps"),
        "floor_bps": borrow_cfg.get("floor_bps"),
        "multiplier": borrow_cfg.get("multiplier"),
    }
    cost_model = {
        "exec_type": exec_cfg.get("type"),
        "commission": exec_cfg.get("commission") or exec_cfg.get("aln"),
        "price_impact": exec_cfg.get("price_impact"),
        "slippage_type": slippage_cfg.get("type"),
        "k_lin": slippage_cfg.get("k_lin"),
        "eta": slippage_cfg.get("eta"),
        "default_adv": slippage_cfg.get("default_adv"),
        "default_spread_bps": slippage_cfg.get("default_spread_bps"),
        "spread_floor_multiplier": slippage_cfg.get("spread_floor_multiplier"),
    }

    return {
        "risk_caps": risk_caps,
        "turnover_caps": turnover_caps,
        "borrow_model": borrow_model,
        "cost_model": cost_model,
    }


def write(manifest: Manifest, outdir: str) -> None:
    """Write the manifest to ``outdir/manifest.json``."""

    os.makedirs(outdir, exist_ok=True)
    manifest_path = os.path.join(outdir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(asdict(manifest), handle, indent=2)

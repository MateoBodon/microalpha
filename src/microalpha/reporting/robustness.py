"""Reporting helpers for cost sensitivity and metadata coverage."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd
import yaml

from microalpha.market_metadata import SymbolMeta, load_symbol_meta
from microalpha.risk_stats import sharpe_stats

DEFAULT_MULTIPLIERS: tuple[float, ...] = (0.5, 1.0, 2.0)


@dataclass(frozen=True)
class RobustnessArtifacts:
    """Paths to generated robustness artifacts."""

    cost_sensitivity: Path
    metadata_coverage: Path


def write_robustness_artifacts(
    artifact_dir: Path | str, multipliers: Sequence[float] = DEFAULT_MULTIPLIERS
) -> RobustnessArtifacts:
    """Compute and persist robustness artifacts under ``artifact_dir``."""

    artifact_dir = Path(artifact_dir)
    cost = compute_cost_sensitivity(artifact_dir, multipliers=multipliers)
    cov = compute_metadata_coverage(artifact_dir)

    cost_path = artifact_dir / "cost_sensitivity.json"
    cov_path = artifact_dir / "metadata_coverage.json"

    cost_path.write_text(json.dumps(cost, indent=2), encoding="utf-8")
    cov_path.write_text(json.dumps(cov, indent=2), encoding="utf-8")

    return RobustnessArtifacts(cost_sensitivity=cost_path, metadata_coverage=cov_path)


# ---------------------------------------------------------------------------
# Cost sensitivity
# ---------------------------------------------------------------------------

def compute_cost_sensitivity(
    artifact_dir: Path | str,
    *,
    multipliers: Sequence[float] = DEFAULT_MULTIPLIERS,
    periods_per_year: int = 252,
) -> Mapping[str, object]:
    """Ex‑post cost scaling over an existing equity curve and trade log.

    Costs are estimated from recorded commissions and slippage; borrow fees are
    currently unavailable in logs and therefore excluded (noted in output).
    No re-simulation is performed – returns are adjusted by scaling the
    per-period cost fraction.
    """

    artifact_dir = Path(artifact_dir)
    equity_path = artifact_dir / "equity_curve.csv"
    trades_path = _resolve_trades_path(artifact_dir)

    equity_df = pd.read_csv(equity_path)
    if "returns" not in equity_df.columns:
        equity_df["returns"] = equity_df["equity"].pct_change().fillna(0.0)

    returns = equity_df["returns"].astype(float)
    timestamps = pd.to_datetime(equity_df["timestamp"])
    dates = timestamps.dt.normalize()
    prev_equity = equity_df["equity"].shift(1).fillna(equity_df["equity"].iloc[0])

    trades_df = _load_trades(trades_path)
    if trades_df.empty:
        cost_by_day = pd.Series(dtype=float)
        commission_total = 0.0
        slippage_total = 0.0
    else:
        trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"])
        trades_df["date"] = trades_df["timestamp"].dt.normalize()
        trades_df["notional"] = trades_df["price"].abs() * trades_df["qty"].abs()
        trades_df["commission"] = trades_df.get("commission", 0.0).astype(float)
        trades_df["slippage_cost"] = (
            trades_df.get("slippage", 0.0).astype(float).abs() * trades_df["qty"].abs()
        )
        commission_total = float(trades_df["commission"].sum())
        slippage_total = float(trades_df["slippage_cost"].sum())
        cost_by_day = trades_df.groupby("date")[["commission", "slippage_cost"]].sum().sum(axis=1)

    per_day_cost = cost_by_day.reindex(dates).fillna(0.0).to_numpy()
    base_metrics = _metrics_from_returns(returns, periods_per_year=periods_per_year)

    grid = []
    for multiplier in multipliers:
        adjustment = (multiplier - 1.0) * (per_day_cost / prev_equity.to_numpy())
        adjusted_returns = returns - adjustment
        metrics = _metrics_from_returns(adjusted_returns, periods_per_year=periods_per_year)
        cost_drag = (base_metrics["cagr"] - metrics["cagr"]) * 10_000.0
        grid.append(
            {
                "multiplier": float(multiplier),
                "sharpe_ratio": metrics["sharpe_ratio"],
                "max_drawdown": metrics["max_drawdown"],
                "cagr": metrics["cagr"],
                "mar": metrics["mar"],
                "cost_drag_bps_per_year": float(cost_drag),
            }
        )

    return {
        "method": "ex_post_cost_scaling",
        "description": (
            "Scales recorded commissions and slippage; borrow costs are not logged "
            "and are excluded. No re-simulation performed."
        ),
        "multipliers": [float(m) for m in multipliers],
        "baseline": base_metrics,
        "grid": grid,
        "cost_basis": {
            "commission_total": float(commission_total),
            "slippage_total": float(slippage_total),
            "borrow_total": None,
            "total": float(commission_total + slippage_total),
            "currency": "USD",
        },
    }


def _metrics_from_returns(
    returns: pd.Series, *, periods_per_year: int = 252
) -> Mapping[str, float]:
    if returns.empty:
        return {
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "cagr": 0.0,
            "mar": 0.0,
        }

    sharpe_summary = sharpe_stats(returns=returns, periods=periods_per_year, ddof=0)
    sharpe = float(sharpe_summary["sharpe"])

    curve = (1.0 + returns).cumprod()
    running_max = curve.cummax()
    drawdown = (running_max - curve) / running_max
    max_dd = float(drawdown.max() if not drawdown.empty else 0.0)

    years = max(len(returns) / periods_per_year, 1e-9)
    ending_value = float(curve.iloc[-1]) if not curve.empty else 1.0
    cagr = float(ending_value ** (1.0 / years) - 1.0)
    mar = float(cagr / max(max_dd, 1e-9)) if max_dd > 0 else 0.0

    return {
        "sharpe_ratio": sharpe,
        "max_drawdown": max_dd,
        "cagr": cagr,
        "mar": mar,
    }


# ---------------------------------------------------------------------------
# Metadata coverage
# ---------------------------------------------------------------------------

def compute_metadata_coverage(artifact_dir: Path | str) -> Mapping[str, object]:
    """Compute liquidity/financing metadata coverage for executed trades."""

    artifact_dir = Path(artifact_dir)
    config_path = _resolve_config_path(artifact_dir)
    config = _load_config(config_path) if config_path else {}
    meta_path = _resolve_meta_path(config_path, config)

    symbol_meta = {}
    if meta_path and meta_path.exists():
        symbol_meta = load_symbol_meta(meta_path)

    trades_path = _resolve_trades_path(artifact_dir)
    trades_df = _load_trades(trades_path)
    if trades_df.empty:
        return {
            "meta_source": str(meta_path) if meta_path else None,
            "coverage": {},
            "totals": {},
            "fallback_top": [],
            "defaults": _extract_defaults(config),
            "note": "No trades available for coverage calculation.",
        }

    trades_df["notional"] = trades_df["price"].abs() * trades_df["qty"].abs()
    trades_df["short_side"] = trades_df["qty"] < 0

    coverage_records: list[dict[str, object]] = []
    for row in trades_df.itertuples(index=False):
        symbol = str(getattr(row, "symbol")).upper()
        meta = symbol_meta.get(symbol, SymbolMeta())
        coverage_records.append(
            {
                "symbol": symbol,
                "notional": float(getattr(row, "notional")),
                "short_side": bool(getattr(row, "short_side")),
                "has_adv": meta.adv is not None,
                "has_spread": meta.spread_bps is not None,
                "has_borrow": meta.borrow_fee_annual_bps is not None,
            }
        )

    frame = pd.DataFrame(coverage_records)
    total_notional = float(frame["notional"].sum())
    short_notional = float(frame.loc[frame["short_side"], "notional"].sum())

    def _pct(mask: pd.Series) -> float | None:
        denom = total_notional
        if denom <= 0:
            return None
        return float(frame.loc[mask, "notional"].sum() / denom)

    adv_pct = _pct(frame["has_adv"])
    spread_pct = _pct(frame["has_spread"])
    borrow_pct = (
        float(
            frame.loc[frame["short_side"] & frame["has_borrow"], "notional"].sum()
            / max(short_notional, 1e-9)
        )
        if short_notional > 0
        else None
    )

    missing = (
        frame.assign(
            missing_adv=~frame["has_adv"],
            missing_spread=~frame["has_spread"],
            missing_borrow=frame["short_side"] & ~frame["has_borrow"],
        )
        .groupby("symbol")[["notional", "missing_adv", "missing_spread", "missing_borrow"]]
        .agg(
            notional_missing_adv=("missing_adv", "sum"),
            notional_missing_spread=("missing_spread", "sum"),
            notional_missing_borrow=("missing_borrow", "sum"),
            trade_notional=("notional", "sum"),
        )
    )
    missing = missing.sort_values("trade_notional", ascending=False)

    fallback_top = []
    for sym, row in missing.head(10).iterrows():
        fallback_top.append(
            {
                "symbol": sym,
                "missing_adv_trades": int(row["notional_missing_adv"]),
                "missing_spread_trades": int(row["notional_missing_spread"]),
                "missing_borrow_trades": int(row["notional_missing_borrow"]),
            }
        )

    return {
        "meta_source": str(meta_path) if meta_path else None,
        "coverage": {
            "pct_notional_with_adv": adv_pct,
            "pct_notional_with_spread": spread_pct,
            "pct_short_notional_with_borrow_fee": borrow_pct,
        },
        "totals": {
            "total_notional": total_notional,
            "short_notional": short_notional,
            "trades": int(len(frame)),
        },
        "fallback_top": fallback_top,
        "defaults": _extract_defaults(config),
        "note": (
            "Coverage based on metadata CSV (if provided). Missing values imply "
            "default ADV/spread/borrow costs were used by the simulator."
        ),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_trades(trades_path: Path) -> pd.DataFrame:
    if trades_path.suffix == ".jsonl":
        records = []
        with trades_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return pd.DataFrame(records)

    return pd.read_csv(trades_path)


def _resolve_trades_path(artifact_dir: Path) -> Path:
    for candidate in ("trades.jsonl", "trades.csv"):
        path = artifact_dir / candidate
        if path.exists():
            return path
    raise FileNotFoundError(f"No trades log found under {artifact_dir}")


def _resolve_config_path(artifact_dir: Path) -> Path | None:
    # Prefer a YAML copy saved alongside the artifacts.
    yaml_files = list(artifact_dir.glob("*.yaml")) + list(artifact_dir.glob("*.yml"))
    return yaml_files[0] if yaml_files else None


def _load_config(config_path: Path) -> Mapping[str, object]:
    with config_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _resolve_meta_path(config_path: Path | None, config: Mapping[str, object]) -> Path | None:
    meta_value = None
    if isinstance(config, Mapping):
        meta_value = config.get("meta_path") or config.get("meta")
        if meta_value is None:
            template = config.get("template")
            if isinstance(template, Mapping):
                meta_value = template.get("meta_path")
    if meta_value is None:
        return None

    candidate = Path(str(meta_value)).expanduser()
    if candidate.is_absolute() and candidate.exists():
        return candidate

    if config_path is not None:
        rel = (config_path.parent / candidate).resolve()
        if rel.exists():
            return rel

    repo_rel = (Path.cwd() / candidate).resolve()
    if repo_rel.exists():
        return repo_rel
    return candidate


def _extract_defaults(config: Mapping[str, object]) -> Mapping[str, float | None]:
    def _from_exec(key: str, default: float | None = None) -> float | None:
        exec_block = config.get("exec") if isinstance(config, Mapping) else None
        if isinstance(exec_block, Mapping):
            slippage = exec_block.get("slippage")
            if isinstance(slippage, Mapping):
                return float(slippage.get(key)) if slippage.get(key) is not None else default
        return default

    return {
        "default_adv": _from_exec("default_adv"),
        "default_spread_bps": _from_exec("default_spread_bps"),
        "spread_floor_multiplier": _from_exec("spread_floor_multiplier"),
    }

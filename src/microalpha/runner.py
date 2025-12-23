"""High-level execution helpers for single backtests."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Mapping

import numpy as np
import pandas as pd
import yaml

from .broker import SimulatedBroker
from .capital import VolatilityScaledPolicy
from .config import CapitalPolicyCfg, SlippageCfg, parse_config
from .data import CsvDataHandler, MultiCsvDataHandler
from .engine import Engine
from .execution import (
    TWAP,
    VWAP,
    Executor,
    ImplementationShortfall,
    KyleLambda,
    LOBExecution,
)
from .execution import (
    SquareRootImpact as SquareRootImpactExecutor,
)
from .execution_safety import evaluate_execution_safety
from .integrity import evaluate_portfolio_integrity
from .logging import JsonlWriter
from .manifest import (
    build as build_manifest,
)
from .manifest import (
    extract_config_summary,
    generate_run_id,
    resolve_git_sha,
)
from .manifest import (
    write as write_manifest,
)
from .market_metadata import load_symbol_meta
from .metrics import compute_metrics
from .portfolio import Portfolio
from .risk import bootstrap_sharpe_ratio
from .slippage import (
    LinearImpact,
    LinearPlusSqrtImpact,
    VolumeSlippageModel,
)
from .slippage import (
    SquareRootImpact as SquareRootImpactSlippage,
)
from .strategies.breakout import BreakoutStrategy
from .strategies.cs_momentum import CrossSectionalMomentum
from .strategies.flagship_momentum import FlagshipMomentumStrategy
from .strategies.meanrev import MeanReversionStrategy
from .strategies.mm import NaiveMarketMakingStrategy
from .wrds import guard_no_wrds_copy

STRATEGY_MAPPING = {
    "MeanReversionStrategy": MeanReversionStrategy,
    "BreakoutStrategy": BreakoutStrategy,
    "NaiveMarketMakingStrategy": NaiveMarketMakingStrategy,
    "CrossSectionalMomentum": CrossSectionalMomentum,
    "FlagshipMomentumStrategy": FlagshipMomentumStrategy,
}

EXECUTION_MAPPING = {
    "instant": Executor,
    "linear": Executor,
    "twap": TWAP,
    "vwap": VWAP,
    "is": ImplementationShortfall,
    "sqrt": SquareRootImpactExecutor,
    "squareroot": SquareRootImpactExecutor,
    "kyle": KyleLambda,
    "lob": LOBExecution,
}


def run_from_config(
    config_path: str, override_artifacts_dir: str | None = None
) -> Dict[str, Any]:
    """Execute a backtest described by ``config_path``."""

    cfg_path = Path(config_path).expanduser().resolve()
    with cfg_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    cfg = parse_config(config)
    unsafe_execution, unsafe_reasons, exec_alignment = evaluate_execution_safety(
        cfg.exec
    )
    if unsafe_execution and not cfg.allow_unsafe_execution:
        raise ValueError(
            "Unsafe execution mode detected (same-bar fills enabled). "
            "Set allow_unsafe_execution: true to proceed."
        )
    cfg_bytes = yaml.safe_dump(config).encode("utf-8")
    config_hash = hashlib.sha256(cfg_bytes).hexdigest()

    full_sha, short_sha = resolve_git_sha()
    base_run_id = generate_run_id(short_sha)
    # Allow CLI override of artifacts root directory without mutating on-disk config
    if override_artifacts_dir is not None:
        config = dict(config)
        config["artifacts_dir"] = override_artifacts_dir

    run_id, artifacts_dir = prepare_artifacts_dir(cfg_path, config, base_run_id)
    manifest = build_manifest(
        cfg.seed,
        str(cfg_path),
        run_id,
        config_hash,
        config_summary=extract_config_summary(config),
        git_sha=full_sha,
        unsafe_execution=unsafe_execution,
        unsafe_reasons=unsafe_reasons,
        execution_alignment=exec_alignment,
    )
    root_rng = np.random.default_rng(manifest.seed)
    write_manifest(manifest, str(artifacts_dir))
    persist_config(cfg_path, artifacts_dir)

    data_dir = resolve_path(cfg.data_path, cfg_path)

    symbol = cfg.symbol
    initial_cash = cfg.cash

    symbol_meta: Dict[str, Any] = {}
    if getattr(cfg, "meta_path", None):
        meta_resolved = resolve_path(cfg.meta_path, cfg_path)
        symbol_meta = load_symbol_meta(meta_resolved)

    strategy_name = cfg.strategy.name
    strategy_class = STRATEGY_MAPPING.get(strategy_name)
    if strategy_class is None:
        raise ValueError(f"Unknown strategy '{strategy_name}'")

    strategy_params: Dict[str, Any] = dict(cfg.strategy.params)
    if cfg.strategy.lookback is not None:
        strategy_params.setdefault("lookback", cfg.strategy.lookback)
    if cfg.strategy.z is not None:
        strategy_params.setdefault("z_threshold", cfg.strategy.z)
    if cfg.strategy.allocator:
        strategy_params.setdefault("allocator", cfg.strategy.allocator)
    if cfg.strategy.allocator_params:
        strategy_params.setdefault(
            "allocator_kwargs", dict(cfg.strategy.allocator_params)
        )

    # Multi-asset support (if config strategy expects symbols list)
    data_handler: CsvDataHandler | MultiCsvDataHandler
    if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
        if strategy_name == "FlagshipMomentumStrategy":
            universe_path = strategy_params.get("universe_path")
            if universe_path is None:
                raise ValueError(
                    "FlagshipMomentumStrategy requires 'universe_path' in params"
                )
            u_path = resolve_path(str(universe_path), cfg_path)
            if not u_path.exists():
                raise FileNotFoundError(f"Flagship universe file not found: {u_path}")
            strategy_params["universe_path"] = str(u_path)
            universe_df = pd.read_csv(u_path)
            if "symbol" not in universe_df.columns:
                raise ValueError("Universe file must contain 'symbol' column")
            universe_symbols = sorted(
                universe_df["symbol"].astype(str).str.upper().unique()
            )
            strategy_params["symbols"] = universe_symbols
            strategy_params.setdefault("warmup_history", None)
        if strategy_name == "CrossSectionalMomentum" and "symbols" not in strategy_params:
            strategy_params["symbols"] = config.get("symbols") or [symbol]

        symbols = strategy_params.get("symbols") or config.get("symbols") or [symbol]
        symbols = [str(sym).upper() for sym in symbols]
        strategy_params["symbols"] = symbols
        data_handler = MultiCsvDataHandler(csv_dir=data_dir, symbols=symbols)
    else:
        data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    if cfg.start_date or cfg.end_date:
        data_handler.set_date_range(cfg.start_date, cfg.end_date)
    if data_handler.data is None:
        raise FileNotFoundError(
            f"Unable to load data for symbol '{symbol}' from {data_dir}"
        )

    trade_logger = JsonlWriter(str(artifacts_dir / "trades.jsonl"))
    capital_policy = resolve_capital_policy(cfg.capital_policy)

    portfolio = Portfolio(
        data_handler=data_handler,
        initial_cash=initial_cash,
        max_exposure=cfg.max_exposure,
        max_drawdown_stop=cfg.max_drawdown_stop,
        turnover_cap=cfg.turnover_cap,
        kelly_fraction=cfg.kelly_fraction,
        trade_logger=trade_logger,
        vol_target_annualized=cfg.vol_target_annualized,
        vol_lookback=cfg.vol_lookback,
        max_portfolio_heat=cfg.max_portfolio_heat,
        max_gross_leverage=cfg.max_gross_leverage,
        max_single_name_weight=cfg.max_single_name_weight,
        sectors=getattr(cfg, "sectors", None),
        max_positions_per_sector=cfg.max_positions_per_sector,
        capital_policy=capital_policy,
        symbol_meta=symbol_meta,
        borrow_cfg=cfg.borrow,
    )
    exec_type = cfg.exec.type.lower() if cfg.exec.type else "instant"
    executor_cls = EXECUTION_MAPPING.get(exec_type, Executor)
    exec_kwargs: Dict[str, Any] = {
        "price_impact": cfg.exec.price_impact,
        "commission": cfg.exec.commission,
    }
    if executor_cls is KyleLambda:
        exec_kwargs["lam"] = (
            cfg.exec.lam if cfg.exec.lam is not None else cfg.exec.price_impact
        )
    if executor_cls in (TWAP, VWAP, ImplementationShortfall) and cfg.exec.slices:
        exec_kwargs["slices"] = cfg.exec.slices
    if executor_cls is ImplementationShortfall and cfg.exec.urgency is not None:
        exec_kwargs["urgency"] = cfg.exec.urgency
    if executor_cls is LOBExecution:
        from .lob import LatencyModel, LimitOrderBook

        latency_rng = np.random.default_rng(root_rng.integers(2**32))
        latency = LatencyModel(
            ack_fixed=cfg.exec.latency_ack or 0.001,
            ack_jitter=cfg.exec.latency_ack_jitter or 0.0005,
            fill_fixed=cfg.exec.latency_fill or 0.01,
            fill_jitter=cfg.exec.latency_fill_jitter or 0.002,
            rng=latency_rng,
        )
        book = LimitOrderBook(latency_model=latency)
        levels = cfg.exec.book_levels or 3
        level_size = cfg.exec.level_size or 200
        tick = cfg.exec.tick_size or 0.1
        mid_price = cfg.exec.mid_price
        if mid_price is None:
            full_data = getattr(data_handler, "full_data", None)
            if isinstance(full_data, pd.DataFrame) and not full_data.empty:
                mid_price = float(full_data.iloc[0]["close"])
            else:
                mid_price = 100.0
        book.seed_book(mid_price=mid_price, tick=tick, levels=levels, size=level_size)
        exec_kwargs["book"] = book
        if cfg.exec.lob_tplus1 is not None:
            exec_kwargs["lob_tplus1"] = bool(cfg.exec.lob_tplus1)

    slippage_model = resolve_slippage_model(cfg.exec.slippage, symbol_meta)
    if slippage_model is not None:
        exec_kwargs["slippage_model"] = slippage_model
    if symbol_meta:
        exec_kwargs.setdefault("symbol_meta", symbol_meta)
    if cfg.exec.limit_mode and cfg.exec.limit_mode.lower() != "market":
        exec_kwargs["limit_mode"] = cfg.exec.limit_mode.upper()
    if cfg.exec.queue_coefficient is not None:
        exec_kwargs["queue_coefficient"] = float(cfg.exec.queue_coefficient)
    if cfg.exec.queue_passive_multiplier is not None:
        exec_kwargs["queue_passive_multiplier"] = float(
            cfg.exec.queue_passive_multiplier
        )
    if cfg.exec.queue_seed is not None:
        exec_kwargs["queue_seed"] = int(cfg.exec.queue_seed)
    if cfg.exec.queue_randomize is not None:
        exec_kwargs["queue_randomize"] = bool(cfg.exec.queue_randomize)
    if cfg.exec.volatility_lookback is not None:
        exec_kwargs["volatility_lookback"] = int(cfg.exec.volatility_lookback)
    if cfg.exec.min_fill_qty is not None:
        exec_kwargs["min_fill_qty"] = int(cfg.exec.min_fill_qty)

    executor = executor_cls(data_handler=data_handler, **exec_kwargs)
    broker = SimulatedBroker(executor)

    if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
        strategy = strategy_class(**strategy_params)
    else:
        strategy = strategy_class(symbol=symbol, **strategy_params)
    if hasattr(strategy, "sector_map") and strategy.sector_map:
        portfolio.sector_of.update(strategy.sector_map)
    engine_rng = np.random.default_rng(root_rng.integers(2**32))
    # Hint engine where to place profiling outputs for this run
    import os as _os

    _os.environ["MICROALPHA_ARTIFACTS_DIR"] = str(artifacts_dir)

    engine = Engine(data_handler, strategy, portfolio, broker, rng=engine_rng)
    engine.run()

    trade_logger.close()

    commission_total = 0.0
    slippage_total = 0.0
    trades_list = getattr(portfolio, "trades", None) or []
    for trade in trades_list:
        try:
            commission_total += float(trade.get("commission", 0.0) or 0.0)
            slippage_total += abs(float(trade.get("slippage", 0.0) or 0.0)) * abs(
                float(trade.get("qty", 0.0) or 0.0)
            )
        except (TypeError, ValueError):
            continue

    integrity = evaluate_portfolio_integrity(
        portfolio,
        equity_records=portfolio.equity_curve,
        slippage_total=slippage_total,
    )
    integrity_path = _persist_integrity(integrity, artifacts_dir)
    _update_manifest_integrity(
        artifacts_dir,
        integrity_path,
        run_invalid=not integrity.ok,
    )

    run_mode = getattr(cfg, "run_mode", "headline")
    if not integrity.ok and run_mode == "headline":
        reasons = "; ".join(integrity.reasons) or "integrity check failed"
        raise ValueError(f"PnL integrity check failed: {reasons}")

    metrics = compute_metrics(
        portfolio.equity_curve,
        portfolio.total_turnover,
        trades=getattr(portfolio, "trades", None),
        hac_lags=cfg.metrics_hac_lags,
    )
    bootstrap_path, bootstrap_meta = _persist_bootstrap(metrics, artifacts_dir)
    metrics_paths = _persist_metrics(
        metrics,
        artifacts_dir,
        extra_metrics={
            **{
                key: value
                for key, value in bootstrap_meta.items()
                if value is not None or key == "bootstrap_samples"
            },
            "borrow_cost_total": float(getattr(portfolio, "borrow_cost_total", 0.0)),
            "commission_total": float(commission_total),
            "slippage_total": float(slippage_total),
        },
    )
    exposures_path, factor_path = persist_exposures(portfolio, artifacts_dir)
    trades_path = _persist_trades(portfolio, artifacts_dir)

    result: Dict[str, Any] = asdict(manifest)
    result.update(
        {
            "artifacts_dir": str(artifacts_dir),
            "strategy": strategy_name,
            "seed": cfg.seed,
            "metrics": metrics_paths,
            "exposures_path": exposures_path,
            "factor_exposure_path": factor_path,
            "bootstrap_path": bootstrap_path,
            "trades_path": trades_path,
            "integrity_path": integrity_path,
        }
    )
    return result


def prepare_artifacts_dir(
    cfg_path: Path, config: Dict[str, Any], base_run_id: str
) -> tuple[str, Path]:
    root = Path(config.get("artifacts_dir", "artifacts"))
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()

    root.mkdir(parents=True, exist_ok=True)

    candidate_run_id = base_run_id
    candidate = root / candidate_run_id
    suffix = 1
    while candidate.exists():
        candidate_run_id = f"{base_run_id}-{suffix:02d}"
        candidate = root / candidate_run_id
        suffix += 1

    candidate.mkdir()
    return candidate_run_id, candidate


def persist_config(cfg_path: Path, artifacts_dir: Path) -> None:
    destination = artifacts_dir / cfg_path.name
    guard_no_wrds_copy(cfg_path, operation="copy")
    shutil.copy2(cfg_path, destination)


def _persist_metrics(
    metrics: Dict[str, Any],
    artifacts_dir: Path,
    *,
    extra_metrics: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    metrics_copy = dict(metrics)
    df = metrics_copy.pop("equity_df")
    if extra_metrics:
        for key, value in extra_metrics.items():
            metrics_copy[key] = value
    equity_path = artifacts_dir / "equity_curve.csv"
    df.to_csv(equity_path, index=False)

    metrics_path = artifacts_dir / "metrics.json"
    stable_metrics = _stable_metrics(metrics_copy)
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(stable_metrics, handle, indent=2)

    manifest_metrics = stable_metrics.copy()
    manifest_metrics["equity_curve_path"] = str(equity_path)
    manifest_metrics["metrics_path"] = str(metrics_path)
    return manifest_metrics


def _persist_integrity(result, artifacts_dir: Path) -> str:
    payload = {
        "ok": bool(result.ok),
        "reasons": list(result.reasons),
        "details": dict(result.details),
    }
    path = artifacts_dir / "integrity.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return str(path)


def _update_manifest_integrity(
    artifacts_dir: Path, integrity_path: str, *, run_invalid: bool
) -> None:
    manifest_path = artifacts_dir / "manifest.json"
    if not manifest_path.exists():
        return
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["integrity_path"] = integrity_path
    payload["run_invalid"] = bool(run_invalid)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def persist_exposures(
    portfolio: Portfolio,
    artifacts_dir: Path,
    filename: str = "exposures.csv",
    factor_filename: str = "factor_exposure.csv",
) -> tuple[str | None, str | None]:
    equity = portfolio.last_equity or portfolio.initial_cash
    current_ts = portfolio.current_time
    exposures: list[Dict[str, Any]] = []

    for symbol, position in portfolio.positions.items():
        qty = getattr(position, "qty", 0)
        if qty == 0:
            continue
        price = None
        if current_ts is not None:
            price = portfolio.data_handler.get_latest_price(symbol, current_ts)
        if price is None:
            price = portfolio.avg_cost.get(symbol)
        if price is None:
            continue
        market_value = float(qty * price)
        weight = float(market_value / equity) if equity else 0.0
        exposures.append(
            {
                "symbol": symbol,
                "qty": float(qty),
                "price": float(price),
                "market_value": market_value,
                "weight": weight,
                "abs_weight": abs(weight),
            }
        )

    if not exposures:
        return None, None

    df = pd.DataFrame(exposures).sort_values("abs_weight", ascending=False)
    df = df.drop(columns=["abs_weight"])
    path = artifacts_dir / filename
    df.to_csv(path, index=False)

    sectors = []
    for row in exposures:
        symbol = row["symbol"]
        sectors.append(portfolio.sector_of.get(symbol, "UNKNOWN"))
    factor_df = pd.DataFrame(
        {
            "sector": sectors,
            "market_value": [row["market_value"] for row in exposures],
            "weight": [row["weight"] for row in exposures],
        }
    )
    factor_summary = (
        factor_df.groupby("sector", as_index=True)
        .sum(numeric_only=True)
        .assign(abs_weight=lambda x: x["weight"].abs())
        .sort_values("abs_weight", ascending=False)
        .drop(columns=["abs_weight"])
    )
    factor_path = artifacts_dir / factor_filename
    factor_summary.to_csv(factor_path)

    return str(path), str(factor_path)


def _persist_bootstrap(
    metrics: Dict[str, Any],
    artifacts_dir: Path,
    *,
    periods: int = 252,
    simulations: int = 1024,
) -> tuple[str, Dict[str, Any]]:
    bootstrap_path = artifacts_dir / "bootstrap.json"
    samples: list[float] = []
    stats: Dict[str, Any] = {
        "bootstrap_samples": 0,
        "bootstrap_p_value": None,
        "bootstrap_ci_low": None,
        "bootstrap_ci_high": None,
    }

    df = metrics.get("equity_df")
    if isinstance(df, pd.DataFrame) and not df.empty:
        returns = df["returns"].to_numpy()
        bootstrap = bootstrap_sharpe_ratio(
            returns,
            num_simulations=simulations,
            periods=periods,
            rng=np.random.default_rng(0),
        )
        samples = [float(x) for x in bootstrap["sharpe_dist"]]
        stats["bootstrap_samples"] = len(samples)
        stats["bootstrap_p_value"] = float(bootstrap["p_value"])
        ci = bootstrap.get("confidence_interval")
        if ci is not None:
            stats["bootstrap_ci_low"] = float(ci[0])
            stats["bootstrap_ci_high"] = float(ci[1])

    with bootstrap_path.open("w", encoding="utf-8") as handle:
        json.dump(samples, handle, indent=2)
    return str(bootstrap_path), stats


def _stable_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    disallowed = {"run_id", "timestamp", "artifacts_dir", "config_path"}
    return {key: value for key, value in metrics.items() if key not in disallowed}


def _persist_trades(portfolio: Portfolio, artifacts_dir: Path) -> str | None:
    if getattr(portfolio, "trade_log_path", None):
        return str(portfolio.trade_log_path)

    if not getattr(portfolio, "trades", None):
        return None

    trades_df = pd.DataFrame(portfolio.trades)
    trades_path = artifacts_dir / "trades.csv"
    trades_df.to_csv(trades_path, index=False)
    return str(trades_path)


def resolve_path(value: str, cfg_path: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    path = Path(expanded)
    if path.is_absolute():
        return path

    candidate = (cfg_path.parent / path).resolve()
    if candidate.exists():
        return candidate

    return (Path.cwd() / path).resolve()


def resolve_capital_policy(
    cfg: CapitalPolicyCfg | None,
) -> VolatilityScaledPolicy | None:
    if cfg is None:
        return None
    if cfg.type == "volatility_scaled":
        return VolatilityScaledPolicy(
            lookback=cfg.lookback,
            target_dollar_vol=cfg.target_dollar_vol,
            min_qty=cfg.min_qty,
        )
    raise ValueError(f"Unknown capital policy type '{cfg.type}'")


def resolve_slippage_model(
    cfg: SlippageCfg | None,
    symbol_meta: Mapping[str, Any] | None = None,
):
    if cfg is None:
        return None
    stype = cfg.type.lower()
    meta = symbol_meta or {}
    if stype == "volume":
        return VolumeSlippageModel(price_impact=cfg.impact, metadata=meta)
    if stype == "linear":
        return LinearImpact(
            k_lin=cfg.k_lin if cfg.k_lin is not None else cfg.impact,
            metadata=meta,
            default_adv=cfg.default_adv,
            default_spread_bps=cfg.default_spread_bps,
            spread_floor_multiplier=cfg.spread_floor_multiplier,
        )
    if stype in {"sqrt", "squareroot"}:
        return SquareRootImpactSlippage(
            eta=cfg.eta if cfg.eta is not None else cfg.impact,
            metadata=meta,
            default_adv=cfg.default_adv,
            default_spread_bps=cfg.default_spread_bps,
            spread_floor_multiplier=cfg.spread_floor_multiplier,
        )
    if stype in {"linear_sqrt", "linear+sqrt"}:
        return LinearPlusSqrtImpact(
            k_lin=cfg.k_lin if cfg.k_lin is not None else cfg.impact,
            eta=cfg.eta if cfg.eta is not None else cfg.impact,
            metadata=meta,
            default_adv=cfg.default_adv,
            default_spread_bps=cfg.default_spread_bps,
            spread_floor_multiplier=cfg.spread_floor_multiplier,
        )
    raise ValueError(f"Unknown slippage model '{cfg.type}'")

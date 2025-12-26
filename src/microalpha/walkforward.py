"""Walk-forward validation orchestration."""

from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import asdict
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple, cast

import numpy as np
import pandas as pd
import yaml

from .broker import SimulatedBroker
from .config import BacktestCfg, ExecModelCfg
from .config_wfv import NonDegenerateCfg, RealityCheckCfg, WFVCfg
from .data import CsvDataHandler, DataHandler, MultiCsvDataHandler
from .engine import Engine
from .execution import (
    TWAP,
    VWAP,
    Executor,
    ImplementationShortfall,
    KyleLambda,
    LOBExecution,
    SquareRootImpact,
)
from .execution_safety import evaluate_execution_safety
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
from .order_flow import OrderFlowDiagnostics, infer_non_degenerate_reason
from .portfolio import Portfolio
from .integrity import evaluate_portfolio_integrity
from .risk_stats import block_bootstrap
from .runner import (
    persist_config,
    persist_exposures,
    prepare_artifacts_dir,
    resolve_capital_policy,
    resolve_path,
    resolve_slippage_model,
)
from .strategies.breakout import BreakoutStrategy
from .strategies.cs_momentum import CrossSectionalMomentum
from .strategies.flagship_mom import FlagshipMomentumStrategy
from .strategies.meanrev import MeanReversionStrategy
from .strategies.mm import NaiveMarketMakingStrategy

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
    "sqrt": SquareRootImpact,
    "squareroot": SquareRootImpact,
    "kyle": KyleLambda,
    "lob": LOBExecution,
}


def _non_degenerate_active(cfg: NonDegenerateCfg | None) -> bool:
    return bool(cfg and cfg.is_active())


def _non_degenerate_reasons(
    portfolio: Portfolio, cfg: NonDegenerateCfg | None
) -> list[str]:
    if not _non_degenerate_active(cfg):
        return []
    reasons: list[str] = []
    num_trades = len(getattr(portfolio, "trades", None) or [])
    turnover = float(getattr(portfolio, "total_turnover", 0.0) or 0.0)
    if cfg is None:
        return reasons
    if cfg.min_trades is not None and num_trades < cfg.min_trades:
        reasons.append(
            f"num_trades {num_trades} < min_trades {int(cfg.min_trades)}"
        )
    if cfg.min_turnover is not None and turnover < cfg.min_turnover:
        reasons.append(
            f"total_turnover {turnover:.4f} < min_turnover {float(cfg.min_turnover):.4f}"
        )
    return reasons


def load_wfv_cfg(path: str) -> WFVCfg:
    """Load a walk-forward validation configuration."""

    import yaml

    from .config import BacktestCfg, ExecModelCfg, StrategyCfg

    with open(path, "r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    if not isinstance(raw, dict):
        raise ValueError("Walk-forward configuration must be a mapping.")

    if "template" in raw and "walkforward" in raw:
        return WFVCfg(**raw)

    if {"data", "strategy", "walkforward"}.issubset(raw):
        data_cfg = raw["data"]
        strategy_payload = dict(raw["strategy"])
        grid = raw.get("grid") or strategy_payload.pop("param_grid", {}) or {}

        exec_payload = dict(raw.get("broker_settings") or raw.get("exec") or {})
        if "mode" in exec_payload:
            exec_payload["type"] = exec_payload.pop("mode")
        if "commission" in exec_payload:
            exec_payload["aln"] = exec_payload.pop("commission")

        portfolio_cfg = raw.get("portfolio") or {}
        data_path = data_cfg.get("directory") or data_cfg.get("path")
        if data_path is None:
            raise ValueError("Legacy walk-forward config missing data.directory/path")
        symbol = data_cfg.get("symbol")
        if symbol is None:
            raise ValueError("Legacy walk-forward config missing data.symbol")

        cash_value = portfolio_cfg.get("initial_cash", raw.get("cash", 1_000_000))
        try:
            cash = float(cash_value) if cash_value is not None else 1_000_000.0
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid cash value in walk-forward config") from exc

        seed_value = raw.get("random_seed", raw.get("seed", 42))
        try:
            seed = int(seed_value) if seed_value is not None else 42
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid seed value in walk-forward config") from exc

        template = BacktestCfg(
            data_path=data_path,
            symbol=symbol,
            cash=cash,
            exec=ExecModelCfg(**exec_payload),
            strategy=StrategyCfg(**strategy_payload),
            seed=seed,
            max_exposure=portfolio_cfg.get("max_exposure"),
            max_drawdown_stop=portfolio_cfg.get("max_drawdown_stop"),
            turnover_cap=portfolio_cfg.get("turnover_cap"),
            kelly_fraction=portfolio_cfg.get("kelly_fraction"),
            max_portfolio_heat=portfolio_cfg.get("max_portfolio_heat"),
            max_gross_leverage=portfolio_cfg.get("max_gross_leverage"),
            max_single_name_weight=portfolio_cfg.get("max_single_name_weight"),
            borrow=portfolio_cfg.get("borrow"),
        )

        reality_payload = raw.get("reality_check") or {}
        return WFVCfg(
            template=template,
            walkforward=raw["walkforward"],
            holdout=raw.get("holdout"),
            grid=grid,
            artifacts_dir=raw.get("artifacts_dir"),
            reality_check=reality_payload,
            non_degenerate=raw.get("non_degenerate"),
        )

    raise ValueError("Invalid walk-forward configuration schema.")


def run_walk_forward(
    config_path: str,
    override_artifacts_dir: str | None = None,
    reality_check_method: str | None = None,
    reality_check_block_len: int | None = None,
) -> Dict[str, Any]:
    cfg_path = Path(config_path).expanduser().resolve()
    raw_config = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    cfg = load_wfv_cfg(str(cfg_path))
    if reality_check_method or reality_check_block_len is not None:
        rc_update: Dict[str, Any] = {}
        if reality_check_method:
            rc_update["method"] = reality_check_method.lower()
        if reality_check_block_len is not None:
            rc_update["block_length"] = reality_check_block_len
        if rc_update:
            rc_cfg = cfg.reality_check.model_copy(update=rc_update)
            cfg = cfg.model_copy(update={"reality_check": rc_cfg})
    config_hash = hashlib.sha256(yaml.safe_dump(raw_config).encode("utf-8")).hexdigest()
    unsafe_execution, unsafe_reasons, exec_alignment = evaluate_execution_safety(
        cfg.template.exec
    )
    if unsafe_execution and not cfg.template.allow_unsafe_execution:
        raise ValueError(
            "Unsafe execution mode detected (same-bar fills enabled). "
            "Set allow_unsafe_execution: true in the template to proceed."
        )

    full_sha, short_sha = resolve_git_sha()
    base_run_id = generate_run_id(short_sha)
    # Allow CLI override of artifacts root directory without mutating on-disk config
    effective_cfg = dict(raw_config)
    if override_artifacts_dir is not None:
        effective_cfg["artifacts_dir"] = override_artifacts_dir

    run_id, artifacts_dir = prepare_artifacts_dir(cfg_path, effective_cfg, base_run_id)
    manifest = build_manifest(
        cfg.template.seed,
        str(cfg_path),
        run_id,
        config_hash,
        config_summary=extract_config_summary(raw_config),
        git_sha=full_sha,
        unsafe_execution=unsafe_execution,
        unsafe_reasons=unsafe_reasons,
        execution_alignment=exec_alignment,
    )
    write_manifest(manifest, str(artifacts_dir))
    persist_config(cfg_path, artifacts_dir)

    trade_logger = JsonlWriter(str(artifacts_dir / "trades.jsonl"))
    run_mode = getattr(cfg.template, "run_mode", "headline")

    data_dir = resolve_path(cfg.template.data_path, cfg_path)
    symbol = cfg.template.symbol
    base_params = _strategy_params(cfg.template.strategy)
    param_grid: Dict[str, Sequence[Any]] = {
        key: tuple(values) for key, values in cfg.grid.items()
    }
    if not param_grid:
        raise ValueError("Parameter grid is required for walk-forward validation")

    training_days = int(cfg.walkforward.training_days)
    testing_days = int(cfg.walkforward.testing_days)
    start_date = pd.Timestamp(cfg.walkforward.start)
    end_date = pd.Timestamp(cfg.walkforward.end)

    holdout_start: pd.Timestamp | None = None
    holdout_end: pd.Timestamp | None = None
    selection_end = end_date
    if cfg.holdout is not None:
        holdout_start = pd.Timestamp(cfg.holdout.start)
        holdout_end = pd.Timestamp(cfg.holdout.end)
        if holdout_end < holdout_start:
            raise ValueError("Holdout end date must be on or after holdout start date")
        selection_end = min(end_date, holdout_start - pd.Timedelta(days=1))
        if selection_end < start_date:
            raise ValueError("Holdout start date leaves no selection window")

    strategy_name = cfg.template.strategy.name
    data_handler: DataHandler
    cs_symbols: List[str] = []
    if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
        if strategy_name == "CrossSectionalMomentum":
            raw_symbols = list(cfg.template.strategy.params.get("symbols") or [])
            if not raw_symbols:
                raw_symbols = list(getattr(cfg.template, "symbols", []) or [])
            if not raw_symbols:
                raw_symbols = [symbol]
            cs_symbols = [str(sym).upper() for sym in raw_symbols]
            base_params.setdefault("symbols", cs_symbols)
        else:
            universe_path = base_params.get("universe_path") or cfg.template.strategy.params.get(
                "universe_path"
            )
            if universe_path is None:
                raise ValueError(
                    "FlagshipMomentumStrategy requires 'universe_path' defined in template params"
                )
            u_path = resolve_path(str(universe_path), cfg_path)
            if not u_path.exists():
                raise FileNotFoundError(f"Flagship universe file not found: {u_path}")
            base_params["universe_path"] = str(u_path)
            universe_df = pd.read_csv(u_path)
            if "symbol" not in universe_df.columns:
                raise ValueError("Flagship universe file must contain 'symbol' column")
            cs_symbols = sorted(universe_df["symbol"].astype(str).str.upper().unique())
            base_params["symbols"] = cs_symbols
        data_handler = MultiCsvDataHandler(csv_dir=data_dir, symbols=cs_symbols)
    else:
        data_handler = CsvDataHandler(csv_dir=data_dir, symbol=symbol)
    if data_handler.data is None:
        raise FileNotFoundError(
            f"Unable to load data for symbol '{symbol}' from {data_dir}"
        )

    symbol_meta: Dict[str, Any] = {}
    if getattr(cfg.template, "meta_path", None):
        meta_resolved = resolve_path(cfg.template.meta_path, cfg_path)
        symbol_meta = load_symbol_meta(meta_resolved)

    equity_records: List[Dict[str, Any]] = []
    folds: List[Dict[str, Any]] = []
    grid_rows: List[Dict[str, Any]] = []
    selection_grid_summaries: List[List[Dict[str, Any]]] = []
    bootstrap_samples: List[float] = []
    reality_metadata: Dict[str, Any] | None = None
    reality_pvalues: List[float] = []
    fold_exposure_paths: List[str] = []
    fold_factor_paths: List[str] = []
    total_turnover = 0.0
    total_commission = 0.0
    total_slippage = 0.0
    total_borrow_cost = 0.0
    total_num_trades = 0
    total_trade_notional = 0.0
    total_realized_pnl = 0.0
    total_win_trades = 0
    total_loss_trades = 0
    integrity_checks: list[dict[str, Any]] = []
    integrity_ok = True

    current_date = start_date
    master_rng = np.random.default_rng(cfg.template.seed)
    strategy_class = STRATEGY_MAPPING.get(strategy_name)
    if strategy_class is None:
        raise ValueError(f"Unknown strategy '{strategy_name}'")

    try:
        while (
            current_date
            + pd.Timedelta(days=training_days + testing_days + 1)
            <= selection_end
        ):
            train_start = current_date
            train_end = train_start + pd.Timedelta(days=training_days)
            test_start = train_end + pd.Timedelta(days=1)
            test_end = test_start + pd.Timedelta(days=testing_days)

            fold_rng = _spawn_rng(master_rng)
            train_rng = _spawn_rng(fold_rng)

            (
                best_params,
                train_metrics,
                rc_result,
                grid_payload,
                grid_summary,
                grid_exclusions,
            ) = _optimise_parameters(
                data_handler,
                train_start,
                train_end,
                strategy_class,
                param_grid,
                base_params,
                cfg.template,
                train_rng,
                cfg.reality_check,
                non_degenerate=cfg.non_degenerate,
                symbol_meta=symbol_meta,
            )

            if not best_params or not train_metrics:
                folds.append(
                    {
                        "train_start": str(train_start.date()),
                        "train_end": str(train_end.date()),
                        "test_start": str(test_start.date()),
                        "test_end": str(test_end.date()),
                        "best_params": None,
                        "train_metrics": None,
                        "test_metrics": None,
                        "reality_check_pvalue": None,
                        "reality_check": None,
                        "spa_pvalue": None,
                        "grid_summary": [],
                        "grid_exclusions": grid_exclusions,
                        "selection_status": "no_valid_candidates",
                    }
                )
                current_date += pd.Timedelta(days=testing_days)
                continue

            warmup_prices: List[float] | None = None
            warmup_history: Dict[str, List[float]] | None = None
            if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
                assert isinstance(data_handler, MultiCsvDataHandler)
                warmup_history = _collect_cs_warmup_history(
                    data_handler,
                    train_start,
                    train_end,
                    cs_symbols,
                )
            else:
                assert isinstance(data_handler, CsvDataHandler)
                warmup_prices = _collect_warmup_prices(
                    data_handler, train_end, best_params.get("lookback", 0)
                )

            data_handler.set_date_range(test_start, test_end)
            if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
                assert isinstance(data_handler, MultiCsvDataHandler)
                kwargs = _strategy_kwargs(best_params)
                kwargs.pop("warmup_prices", None)
                if warmup_history:
                    kwargs["warmup_history"] = warmup_history
                strategy = strategy_class(**kwargs)
            else:
                strategy = strategy_class(
                    symbol=symbol, **_strategy_kwargs(best_params, warmup_prices)
                )
            order_flow = (
                OrderFlowDiagnostics()
                if cfg.template.order_flow_diagnostics
                else None
            )
            portfolio = _build_portfolio(
                data_handler,
                cfg.template,
                trade_logger=trade_logger,
                symbol_meta=symbol_meta,
                order_flow=order_flow,
            )
            if hasattr(strategy, "sector_map") and strategy.sector_map:
                portfolio.sector_of.update(strategy.sector_map)
            test_rng = _spawn_rng(fold_rng)
            exec_rng = _spawn_rng(test_rng)
            executor = _build_executor(
                data_handler,
                cfg.template.exec,
                exec_rng,
                symbol_meta=symbol_meta,
            )
            broker = SimulatedBroker(executor)
            # Hint engine where to place profiling outputs for this run
            import os as _os

            _os.environ["MICROALPHA_ARTIFACTS_DIR"] = str(artifacts_dir)

            engine = Engine(
                data_handler,
                strategy,
                portfolio,
                broker,
                rng=_spawn_rng(test_rng),
            )
            engine.run()

            filter_diagnostics: Dict[str, Any] | None = None
            if hasattr(strategy, "get_filter_diagnostics"):
                try:
                    filter_diagnostics = strategy.get_filter_diagnostics()
                except Exception as exc:  # pragma: no cover - diagnostics should not fail the run
                    filter_diagnostics = {
                        "error": f"{type(exc).__name__}: {exc}",
                    }
            order_flow_payload = _finalize_order_flow(order_flow, filter_diagnostics)

            if portfolio.equity_curve:
                equity_records.extend(portfolio.equity_curve)
            total_turnover += float(portfolio.total_turnover)
            total_borrow_cost += float(getattr(portfolio, "borrow_cost_total", 0.0))
            trades_list = getattr(portfolio, "trades", None) or []
            total_num_trades += len(trades_list)
            fold_slippage = 0.0
            for trade in trades_list:
                try:
                    commission_val = float(trade.get("commission", 0.0) or 0.0)
                    slippage_val = abs(float(trade.get("slippage", 0.0) or 0.0)) * abs(
                        float(trade.get("qty", 0.0) or 0.0)
                    )
                    total_commission += commission_val
                    total_slippage += slippage_val
                    fold_slippage += slippage_val
                except (TypeError, ValueError):
                    continue
                try:
                    qty = float(trade.get("qty", 0.0) or 0.0)
                    price = float(trade.get("price", 0.0) or 0.0)
                    total_trade_notional += abs(qty) * abs(price)
                except (TypeError, ValueError):
                    pass
                realized = trade.get("realized_pnl")
                if realized is not None:
                    try:
                        realized_val = float(realized)
                    except (TypeError, ValueError):
                        realized_val = None
                    if realized_val is not None:
                        total_realized_pnl += realized_val
                        if realized_val > 0:
                            total_win_trades += 1
                        elif realized_val < 0:
                            total_loss_trades += 1

            fold_index = len(folds)
            fold_integrity = evaluate_portfolio_integrity(
                portfolio,
                equity_records=portfolio.equity_curve,
                slippage_total=fold_slippage,
            )
            integrity_checks.append(
                {
                    "fold": fold_index,
                    "phase": "test",
                    "ok": bool(fold_integrity.ok),
                    "reasons": list(fold_integrity.reasons),
                    "details": dict(fold_integrity.details),
                }
            )
            if not fold_integrity.ok:
                integrity_ok = False
                if run_mode == "headline":
                    integrity_path = _persist_integrity_checks(
                        artifacts_dir, integrity_ok, integrity_checks
                    )
                    _update_manifest_integrity(
                        artifacts_dir,
                        integrity_path,
                        run_invalid=True,
                    )
                    raise ValueError(
                        "PnL integrity check failed in walk-forward fold "
                        f"{fold_index}: {', '.join(fold_integrity.reasons)}"
                    )
            exposure_path, factor_path = persist_exposures(
                portfolio,
                artifacts_dir,
                filename=f"exposures_fold_{fold_index}.csv",
                factor_filename=f"factor_exposure_fold_{fold_index}.csv",
            )
            if exposure_path:
                fold_exposure_paths.append(exposure_path)
            if factor_path:
                fold_factor_paths.append(factor_path)

            test_metrics = compute_metrics(
                portfolio.equity_curve,
                portfolio.total_turnover,
                hac_lags=cfg.template.metrics_hac_lags,
            )

            rc_summary: Dict[str, Any] | None = None
            rc_pvalue = None
            if rc_result:
                rc_pvalue = rc_result.get("p_value")
                best_sharpe_val = rc_result.get("best_sharpe")
                if best_sharpe_val is not None and np.isfinite(best_sharpe_val):
                    best_sharpe_val = float(best_sharpe_val)
                else:
                    best_sharpe_val = None
                rc_summary = {
                    "p_value": float(rc_pvalue) if rc_pvalue is not None else None,
                    "best_sharpe": best_sharpe_val,
                    "method": rc_result.get("method"),
                    "block_length": rc_result.get("block_length"),
                    "num_bootstrap": rc_result.get("num_bootstrap"),
                    "num_models": rc_result.get("num_models"),
                }
                distribution = rc_result.get("distribution", [])
                bootstrap_samples.extend(float(x) for x in distribution)
                reality_metadata = dict(rc_summary)
                if rc_pvalue is not None:
                    reality_pvalues.append(float(rc_pvalue))

            fold_entry = {
                "train_start": str(train_start.date()),
                "train_end": str(train_end.date()),
                "test_start": str(test_start.date()),
                "test_end": str(test_end.date()),
                "best_params": best_params,
                "train_metrics": _metrics_summary(train_metrics),
                "test_metrics": _metrics_summary(test_metrics),
                "filter_diagnostics": filter_diagnostics,
                "order_flow_diagnostics": order_flow_payload,
                "reality_check_pvalue": (
                    None if rc_pvalue is None else float(rc_pvalue)
                ),
                "reality_check": rc_summary,
                "exposures_path": exposure_path,
                "factor_exposure_path": factor_path,
                "spa_pvalue": None,
                "grid_summary": grid_summary,
                "grid_exclusions": grid_exclusions,
            }

            if grid_payload:
                grid_rows.extend(
                    _grid_rows_for_fold(
                        grid_payload,
                        fold_index=fold_index,
                        phase="train",
                    )
                )
            if grid_summary:
                selection_grid_summaries.append(grid_summary)

            folds.append(fold_entry)

            current_date += pd.Timedelta(days=testing_days)
    finally:
        trade_logger.close()

    selection_summary = _aggregate_selection_summary(selection_grid_summaries)
    selection_summary_path: str | None = None
    if selection_summary:
        selection_path = artifacts_dir / "selection_summary.json"
        with selection_path.open("w", encoding="utf-8") as handle:
            json.dump(selection_summary, handle, indent=2)
        selection_summary_path = str(selection_path)

    non_degenerate_cfg = cfg.non_degenerate
    non_degenerate_active = _non_degenerate_active(non_degenerate_cfg)
    total_excluded = sum(len(fold.get("grid_exclusions") or []) for fold in folds)
    non_degenerate_payload: Dict[str, Any] | None = None
    if non_degenerate_active and non_degenerate_cfg is not None:
        non_degenerate_payload = {
            "min_trades": non_degenerate_cfg.min_trades,
            "min_turnover": non_degenerate_cfg.min_turnover,
        }
    selection_failure_reason: str | None = None
    if non_degenerate_active and not selection_summary:
        criteria = []
        if non_degenerate_cfg is not None and non_degenerate_cfg.min_trades is not None:
            criteria.append(f"min_trades={int(non_degenerate_cfg.min_trades)}")
        if (
            non_degenerate_cfg is not None
            and non_degenerate_cfg.min_turnover is not None
        ):
            criteria.append(
                f"min_turnover={float(non_degenerate_cfg.min_turnover)}"
            )
        criteria_text = ", ".join(criteria) if criteria else "unspecified"
        selection_failure_reason = (
            "Non-degenerate constraints rejected all candidates "
            f"({criteria_text}; excluded={total_excluded})."
        )
    if selection_failure_reason:
        integrity_ok = False
        integrity_checks.append(
            {
                "fold": None,
                "phase": "selection",
                "ok": False,
                "reasons": [selection_failure_reason],
                "details": {"excluded_candidates": int(total_excluded)},
            }
        )

    selected_entry = selection_summary[0] if selection_summary else None
    selected_model = selected_entry["model"] if selected_entry else None
    selected_params = (
        dict(selected_entry.get("params") or {}) if selected_entry else None
    )
    selected_params_full: Dict[str, Any] | None = None
    if selected_entry:
        selected_params_full = dict(base_params)
        selected_params_full.update(selected_params or {})

    holdout_metrics: Dict[str, Any] | None = None
    holdout_metrics_path: str | None = None
    holdout_manifest_path: str | None = None
    holdout_equity_path: str | None = None
    holdout_returns_path: str | None = None
    holdout_trades_path: str | None = None
    if holdout_start is not None and holdout_end is not None:
        if selected_params_full is None:
            if not selection_failure_reason:
                raise ValueError("Holdout configured but no selection results found")
        if selected_params_full is not None:

            warmup_end = holdout_start - pd.Timedelta(days=1)
            warmup_prices = None
            warmup_history = None
            if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
                assert isinstance(data_handler, MultiCsvDataHandler)
                warmup_start = warmup_end - pd.Timedelta(days=training_days)
                warmup_history = _collect_cs_warmup_history(
                    data_handler,
                    warmup_start,
                    warmup_end,
                    cs_symbols,
                )
            else:
                assert isinstance(data_handler, CsvDataHandler)
                warmup_prices = _collect_warmup_prices(
                    data_handler, warmup_end, selected_params_full.get("lookback", 0)
                )

            data_handler.set_date_range(holdout_start, holdout_end)
            if strategy_name in {"CrossSectionalMomentum", "FlagshipMomentumStrategy"}:
                assert isinstance(data_handler, MultiCsvDataHandler)
                kwargs = _strategy_kwargs(selected_params_full)
                kwargs.pop("warmup_prices", None)
                if warmup_history:
                    kwargs["warmup_history"] = warmup_history
                holdout_strategy = strategy_class(**kwargs)
            else:
                holdout_strategy = strategy_class(
                    symbol=symbol,
                    **_strategy_kwargs(selected_params_full, warmup_prices),
                )

            holdout_trade_logger = JsonlWriter(
                str(artifacts_dir / "holdout_trades.jsonl")
            )
            holdout_portfolio = _build_portfolio(
                data_handler,
                cfg.template,
                trade_logger=holdout_trade_logger,
                symbol_meta=symbol_meta,
            )
            if hasattr(holdout_strategy, "sector_map") and holdout_strategy.sector_map:
                holdout_portfolio.sector_of.update(holdout_strategy.sector_map)

            holdout_rng = _spawn_rng(master_rng)
            exec_rng = _spawn_rng(holdout_rng)
            holdout_executor = _build_executor(
                data_handler,
                cfg.template.exec,
                exec_rng,
                symbol_meta=symbol_meta,
            )
            holdout_broker = SimulatedBroker(holdout_executor)
            import os as _os

            _os.environ["MICROALPHA_ARTIFACTS_DIR"] = str(artifacts_dir)

            holdout_engine = Engine(
                data_handler,
                holdout_strategy,
                holdout_portfolio,
                holdout_broker,
                rng=_spawn_rng(holdout_rng),
            )
            holdout_engine.run()
            holdout_trade_logger.close()
            holdout_trades_path = holdout_trade_logger.path

            holdout_trades = getattr(holdout_portfolio, "trades", None) or []
            holdout_slippage_total = 0.0
            for trade in holdout_trades:
                try:
                    holdout_slippage_total += abs(
                        float(trade.get("slippage", 0.0) or 0.0)
                    ) * abs(float(trade.get("qty", 0.0) or 0.0))
                except (TypeError, ValueError):
                    continue
            holdout_integrity = evaluate_portfolio_integrity(
                holdout_portfolio,
                equity_records=holdout_portfolio.equity_curve,
                slippage_total=holdout_slippage_total,
            )
            integrity_checks.append(
                {
                    "fold": None,
                    "phase": "holdout",
                    "ok": bool(holdout_integrity.ok),
                    "reasons": list(holdout_integrity.reasons),
                    "details": dict(holdout_integrity.details),
                }
            )
            if not holdout_integrity.ok:
                integrity_ok = False
                if run_mode == "headline":
                    integrity_path = _persist_integrity_checks(
                        artifacts_dir, integrity_ok, integrity_checks
                    )
                    _update_manifest_integrity(
                        artifacts_dir,
                        integrity_path,
                        run_invalid=True,
                    )
                    raise ValueError(
                        "PnL integrity check failed in holdout: "
                        + ", ".join(holdout_integrity.reasons)
                    )

            holdout_metrics_raw = compute_metrics(
                holdout_portfolio.equity_curve,
                holdout_portfolio.total_turnover,
                hac_lags=cfg.template.metrics_hac_lags,
            )
            holdout_metrics_copy = dict(holdout_metrics_raw)
            holdout_df = cast(
                pd.DataFrame, holdout_metrics_copy.pop("equity_df", pd.DataFrame())
            )
            holdout_metrics = _stable_metrics(holdout_metrics_copy)

            holdout_total_commission = 0.0
            holdout_total_slippage = 0.0
            holdout_trades = getattr(holdout_portfolio, "trades", None) or []
            holdout_num_trades = len(holdout_trades)
            holdout_trade_notional = 0.0
            holdout_realized_pnl = 0.0
            holdout_win_trades = 0
            holdout_loss_trades = 0
            for trade in holdout_trades:
                try:
                    holdout_total_commission += float(trade.get("commission", 0.0) or 0.0)
                    holdout_total_slippage += abs(
                        float(trade.get("slippage", 0.0) or 0.0)
                    ) * abs(float(trade.get("qty", 0.0) or 0.0))
                except (TypeError, ValueError):
                    continue
                try:
                    qty = float(trade.get("qty", 0.0) or 0.0)
                    price = float(trade.get("price", 0.0) or 0.0)
                    holdout_trade_notional += abs(qty) * abs(price)
                except (TypeError, ValueError):
                    pass
                realized = trade.get("realized_pnl")
                if realized is not None:
                    try:
                        realized_val = float(realized)
                    except (TypeError, ValueError):
                        realized_val = None
                    if realized_val is not None:
                        holdout_realized_pnl += realized_val
                        if realized_val > 0:
                            holdout_win_trades += 1
                        elif realized_val < 0:
                            holdout_loss_trades += 1
            holdout_win_denom = holdout_win_trades + holdout_loss_trades
            holdout_win_rate = (
                holdout_win_trades / holdout_win_denom if holdout_win_denom > 0 else 0.0
            )
            holdout_avg_trade_notional = (
                holdout_trade_notional / holdout_num_trades if holdout_num_trades > 0 else 0.0
            )
            holdout_metrics.update(
                {
                    "borrow_cost_total": float(
                        getattr(holdout_portfolio, "borrow_cost_total", 0.0)
                    ),
                    "commission_total": float(holdout_total_commission),
                    "slippage_total": float(holdout_total_slippage),
                    "num_trades": holdout_num_trades,
                    "avg_trade_notional": float(holdout_avg_trade_notional),
                    "win_rate": float(holdout_win_rate),
                    "total_realized_pnl": float(holdout_realized_pnl),
                }
            )

            if holdout_df is not None and not holdout_df.empty:
                holdout_equity_path = str(artifacts_dir / "holdout_equity_curve.csv")
                holdout_df.to_csv(holdout_equity_path, index=False)
                if "returns" in holdout_df.columns:
                    holdout_returns_path = str(artifacts_dir / "holdout_returns.csv")
                    holdout_df[["timestamp", "returns"]].to_csv(
                        holdout_returns_path, index=False
                    )

            holdout_metrics_path = str(artifacts_dir / "holdout_metrics.json")
            with Path(holdout_metrics_path).open("w", encoding="utf-8") as handle:
                json.dump(holdout_metrics, handle, indent=2)

            holdout_manifest_payload = {
                "run_id": run_id,
                "config_sha256": config_hash,
                "git_sha": full_sha,
                "unsafe_execution": bool(unsafe_execution),
                "unsafe_reasons": list(unsafe_reasons),
                "execution_alignment": dict(exec_alignment),
                "selection_window_end": str(selection_end.date()),
                "holdout_start": str(holdout_start.date()),
                "holdout_end": str(holdout_end.date()),
                "selected_model": selected_model,
                "selected_params": selected_params,
                "selected_params_full": selected_params_full,
                "selection_metric": (
                    None
                    if selected_entry is None
                    else float(selected_entry.get("mean_sharpe", 0.0) or 0.0)
                ),
                "selection_summary_path": selection_summary_path,
                "holdout_metrics_path": holdout_metrics_path,
                "holdout_equity_curve_path": holdout_equity_path,
                "holdout_returns_path": holdout_returns_path,
                "holdout_trades_path": holdout_trades_path,
            }
            holdout_manifest_path = str(artifacts_dir / "holdout_manifest.json")
            with Path(holdout_manifest_path).open("w", encoding="utf-8") as handle:
                json.dump(holdout_manifest_payload, handle, indent=2)

    exposures_path: str | None = None
    factor_exposure_path: str | None = None
    grid_returns_path: str | None = None
    if fold_exposure_paths:
        final_path = artifacts_dir / "exposures.csv"
        last_df = pd.read_csv(fold_exposure_paths[-1])
        last_df.to_csv(final_path, index=False)
        exposures_path = str(final_path)
    if fold_factor_paths:
        final_factor_path = artifacts_dir / "factor_exposure.csv"
        last_factor_df = pd.read_csv(fold_factor_paths[-1], index_col=0)
        last_factor_df.to_csv(final_factor_path)
        factor_exposure_path = str(final_factor_path)
    if grid_rows:
        grid_df = pd.DataFrame(grid_rows)
        grid_path = artifacts_dir / "grid_returns.csv"
        grid_df.to_csv(grid_path, index=False)
        grid_returns_path = str(grid_path)

    folds_path = artifacts_dir / "folds.json"
    with folds_path.open("w", encoding="utf-8") as handle:
        json.dump(folds, handle, indent=2)

    aggregated_p_value: float | None = (
        float(np.mean(reality_pvalues)) if reality_pvalues else None
    )

    bootstrap_path = artifacts_dir / "bootstrap.json"
    with bootstrap_path.open("w", encoding="utf-8") as handle:
        json.dump([float(x) for x in bootstrap_samples], handle, indent=2)

    reality_check_path: str | None = None
    if reality_metadata:
        rc_payload = dict(reality_metadata)
        if aggregated_p_value is not None:
            rc_payload["p_value_mean"] = aggregated_p_value
        rc_payload["num_samples"] = len(bootstrap_samples)
        rc_path = artifacts_dir / "reality_check.json"
        with rc_path.open("w", encoding="utf-8") as handle:
            json.dump(rc_payload, handle, indent=2)
        reality_check_path = str(rc_path)
    else:
        reality_check_path = None

    total_win_denom = total_win_trades + total_loss_trades
    total_win_rate = total_win_trades / total_win_denom if total_win_denom > 0 else 0.0
    total_avg_trade_notional = (
        total_trade_notional / total_num_trades if total_num_trades > 0 else 0.0
    )
    metrics = _summarise_walkforward(
        equity_records,
        artifacts_dir,
        total_turnover,
        hac_lags=cfg.template.metrics_hac_lags,
        extra_metrics={
            "reality_check_p_value": aggregated_p_value,
            "bootstrap_samples": len(bootstrap_samples),
            "borrow_cost_total": float(total_borrow_cost),
            "commission_total": float(total_commission),
            "slippage_total": float(total_slippage),
            "num_trades": total_num_trades,
            "avg_trade_notional": float(total_avg_trade_notional),
            "win_rate": float(total_win_rate),
            "total_realized_pnl": float(total_realized_pnl),
        },
    )

    integrity_path = _persist_integrity_checks(
        artifacts_dir, integrity_ok, integrity_checks
    )
    _update_manifest_integrity(
        artifacts_dir,
        integrity_path,
        run_invalid=not integrity_ok,
    )

    manifest_payload = asdict(manifest)
    manifest_payload["integrity_path"] = integrity_path
    manifest_payload["run_invalid"] = bool(not integrity_ok)
    manifest_payload["walkforward"] = {
        "selection_window_start": str(start_date.date()),
        "selection_window_end": str(selection_end.date()),
        "holdout_start": None if holdout_start is None else str(holdout_start.date()),
        "holdout_end": None if holdout_end is None else str(holdout_end.date()),
        "selected_model": selected_model,
        "selected_params": selected_params,
        "selected_params_full": selected_params_full,
        "selection_summary_path": selection_summary_path,
        "holdout_metrics_path": holdout_metrics_path,
        "holdout_manifest_path": holdout_manifest_path,
        "non_degenerate": non_degenerate_payload,
        "non_degenerate_excluded": int(total_excluded),
        "non_degenerate_failure_reason": selection_failure_reason,
    }
    manifest_path = artifacts_dir / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest_payload, handle, indent=2)

    if selection_failure_reason:
        raise ValueError(selection_failure_reason)

    result: Dict[str, Any] = dict(manifest_payload)
    result.update(
        {
            "artifacts_dir": str(artifacts_dir),
            "strategy": strategy_name,
            "folds_path": str(folds_path),
            "bootstrap_path": str(bootstrap_path),
            "reality_check_path": reality_check_path,
            "exposures_path": exposures_path,
            "factor_exposure_path": factor_exposure_path,
            "grid_returns_path": grid_returns_path,
            "selection_summary_path": selection_summary_path,
            "holdout_metrics_path": holdout_metrics_path,
            "holdout_manifest_path": holdout_manifest_path,
            "holdout_equity_path": holdout_equity_path,
            "holdout_returns_path": holdout_returns_path,
            "holdout_trades_path": holdout_trades_path,
            "metrics": metrics,
            "holdout_metrics": holdout_metrics,
            "folds": folds,
            "trades_path": str(artifacts_dir / "trades.jsonl"),
            "integrity_path": integrity_path,
        }
    )
    return result


def _optimise_parameters(
    data_handler: DataHandler,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    strategy_class,
    param_grid: Mapping[str, Sequence[Any]],
    base_params: Dict[str, Any],
    cfg: BacktestCfg,
    rng: np.random.Generator,
    reality_cfg: RealityCheckCfg,
    *,
    non_degenerate: NonDegenerateCfg | None = None,
    symbol_meta: Mapping[str, Any] | None = None,
) -> Tuple[
    Dict[str, Any],
    Dict[str, Any] | None,
    Dict[str, Any] | None,
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
]:
    best_entry: Dict[str, Any] | None = None
    results: List[Dict[str, Any]] = []
    exclusions: List[Dict[str, Any]] = []

    keys = list(param_grid.keys())

    for combination in product(*(param_grid[key] for key in keys)):
        params = dict(zip(keys, combination))

        sim_rng = _spawn_rng(rng)

        data_handler.set_date_range(train_start, train_end)
        combined = dict(base_params)
        combined.update(params)
        if strategy_class in (CrossSectionalMomentum, FlagshipMomentumStrategy):
            strategy = strategy_class(**_strategy_kwargs(combined))
        else:
            strategy = strategy_class(symbol=cfg.symbol, **_strategy_kwargs(combined))
        order_flow = OrderFlowDiagnostics() if cfg.order_flow_diagnostics else None
        portfolio = _build_portfolio(
            data_handler,
            cfg,
            symbol_meta=symbol_meta,
            order_flow=order_flow,
        )
        if hasattr(strategy, "sector_map") and strategy.sector_map:
            portfolio.sector_of.update(strategy.sector_map)
        exec_rng = _spawn_rng(sim_rng)
        executor = _build_executor(
            data_handler,
            cfg.exec,
            exec_rng,
            symbol_meta=symbol_meta,
        )
        broker = SimulatedBroker(executor)

        engine = Engine(
            data_handler,
            strategy,
            portfolio,
            broker,
            rng=_spawn_rng(sim_rng),
        )
        engine.run()

        filter_diagnostics: Dict[str, Any] | None = None
        if hasattr(strategy, "get_filter_diagnostics"):
            try:
                filter_diagnostics = strategy.get_filter_diagnostics()
            except Exception as exc:  # pragma: no cover - diagnostics should not fail tuning
                filter_diagnostics = {
                    "error": f"{type(exc).__name__}: {exc}",
                }
        order_flow_payload = _finalize_order_flow(order_flow, filter_diagnostics)

        if not portfolio.equity_curve:
            exclusions.append(
                {
                    "model": _format_param_label(params),
                    "params": dict(params),
                    "num_trades": len(getattr(portfolio, "trades", None) or []),
                    "turnover": float(
                        getattr(portfolio, "total_turnover", 0.0) or 0.0
                    ),
                    "reasons": ["empty_equity_curve"],
                    "filter_diagnostics": filter_diagnostics,
                    "order_flow_diagnostics": order_flow_payload,
                }
            )
            continue

        metrics = compute_metrics(
            portfolio.equity_curve,
            portfolio.total_turnover,
            hac_lags=cfg.metrics_hac_lags,
        )

        exclusion_reasons = _non_degenerate_reasons(portfolio, non_degenerate)
        if exclusion_reasons:
            diagnostic_reason = infer_non_degenerate_reason(order_flow_payload)
            exclusions.append(
                {
                    "model": _format_param_label(params),
                    "params": dict(params),
                    "num_trades": len(getattr(portfolio, "trades", None) or []),
                    "turnover": float(
                        getattr(portfolio, "total_turnover", 0.0) or 0.0
                    ),
                    "reasons": exclusion_reasons,
                    "filter_diagnostics": filter_diagnostics,
                    "order_flow_diagnostics": order_flow_payload,
                    "diagnostic_reason": diagnostic_reason,
                }
            )
            continue

        results.append(
            {
                "params": dict(params),
                "metrics": metrics,
                "returns": metrics.get("equity_df", pd.DataFrame())[
                    "returns"
                ].to_numpy(),
            }
        )

    if not results:
        return {}, None, None, [], [], exclusions

    grid_payload = _build_grid_payload(results)
    grid_summary = _grid_summary_from_payload(grid_payload)

    best_entry = max(
        results, key=lambda item: item["metrics"].get("sharpe_ratio", float("-inf"))
    )
    rc_method = reality_cfg.method.lower()
    rc_block_len = reality_cfg.block_length
    rc_samples = int(reality_cfg.samples)
    reality_result = bootstrap_reality_check(
        results,
        seed=cfg.seed,
        n_bootstrap=rc_samples,
        method=rc_method,
        block_len=rc_block_len,
    )

    params = dict(base_params)
    params.update(best_entry["params"])
    return (
        params,
        best_entry["metrics"],
        reality_result,
        grid_payload,
        grid_summary,
        exclusions,
    )


def _build_portfolio(
    data_handler,
    cfg: BacktestCfg,
    trade_logger: JsonlWriter | None = None,
    symbol_meta: Mapping[str, Any] | None = None,
    order_flow: OrderFlowDiagnostics | None = None,
) -> Portfolio:
    return Portfolio(
        data_handler=data_handler,
        initial_cash=cfg.cash,
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
        capital_policy=resolve_capital_policy(cfg.capital_policy),
        symbol_meta=symbol_meta,
        borrow_cfg=cfg.borrow,
        order_flow=order_flow,
    )


def _build_executor(
    data_handler,
    exec_cfg: ExecModelCfg,
    rng: np.random.Generator,
    symbol_meta: Mapping[str, Any] | None = None,
):
    exec_type = exec_cfg.type.lower() if exec_cfg.type else "twap"
    executor_cls = EXECUTION_MAPPING.get(exec_type, Executor)
    kwargs: Dict[str, Any] = {
        "price_impact": exec_cfg.price_impact,
        "commission": exec_cfg.commission,
    }
    if executor_cls is KyleLambda:
        kwargs["lam"] = (
            exec_cfg.lam if exec_cfg.lam is not None else exec_cfg.price_impact
        )
    if executor_cls in (TWAP, VWAP, ImplementationShortfall) and exec_cfg.slices:
        kwargs["slices"] = exec_cfg.slices
    if executor_cls is ImplementationShortfall and exec_cfg.urgency is not None:
        kwargs["urgency"] = exec_cfg.urgency
    if executor_cls is LOBExecution:
        from .lob import LatencyModel, LimitOrderBook

        latency = LatencyModel(
            ack_fixed=exec_cfg.latency_ack or 0.001,
            ack_jitter=exec_cfg.latency_ack_jitter or 0.0005,
            fill_fixed=exec_cfg.latency_fill or 0.01,
            fill_jitter=exec_cfg.latency_fill_jitter or 0.002,
            rng=rng,
        )
        book = LimitOrderBook(latency_model=latency)
        levels = exec_cfg.book_levels or 3
        level_size = exec_cfg.level_size or 200
        tick = exec_cfg.tick_size or 0.1
        mid_price = exec_cfg.mid_price
        if mid_price is None:
            full_data = getattr(data_handler, "full_data", None)
            if isinstance(full_data, pd.DataFrame) and not full_data.empty:
                mid_price = float(full_data.iloc[0]["close"])
            else:
                mid_price = 100.0
        book.seed_book(mid_price=mid_price, tick=tick, levels=levels, size=level_size)
        kwargs["book"] = book
        if exec_cfg.lob_tplus1 is not None:
            kwargs["lob_tplus1"] = bool(exec_cfg.lob_tplus1)
    slippage_model = resolve_slippage_model(exec_cfg.slippage, symbol_meta)
    if slippage_model is not None:
        kwargs["slippage_model"] = slippage_model
    if symbol_meta:
        kwargs.setdefault("symbol_meta", symbol_meta)
    if exec_cfg.limit_mode and exec_cfg.limit_mode.lower() != "market":
        kwargs["limit_mode"] = exec_cfg.limit_mode.upper()
    if exec_cfg.queue_coefficient is not None:
        kwargs["queue_coefficient"] = float(exec_cfg.queue_coefficient)
    if exec_cfg.queue_passive_multiplier is not None:
        kwargs["queue_passive_multiplier"] = float(
            exec_cfg.queue_passive_multiplier
        )
    if exec_cfg.queue_seed is not None:
        kwargs["queue_seed"] = int(exec_cfg.queue_seed)
    if exec_cfg.queue_randomize is not None:
        kwargs["queue_randomize"] = bool(exec_cfg.queue_randomize)
    if exec_cfg.volatility_lookback is not None:
        kwargs["volatility_lookback"] = int(exec_cfg.volatility_lookback)
    if exec_cfg.min_fill_qty is not None:
        kwargs["min_fill_qty"] = int(exec_cfg.min_fill_qty)

    return executor_cls(data_handler=data_handler, **kwargs)


def _spawn_rng(parent: np.random.Generator) -> np.random.Generator:
    return np.random.default_rng(int(parent.integers(2**32)))


def _collect_warmup_prices(
    data_handler: CsvDataHandler, train_end: pd.Timestamp, lookback: int
) -> List[float]:
    if lookback <= 0:
        return []

    warmup_start = train_end - pd.Timedelta(days=lookback)
    data_handler.set_date_range(warmup_start, train_end)
    return [event.price for event in data_handler.stream()]


def _collect_cs_warmup_history(
    data_handler: MultiCsvDataHandler,
    train_start: pd.Timestamp,
    train_end: pd.Timestamp,
    symbols: Sequence[str],
) -> Dict[str, List[float]]:
    data_handler.set_date_range(train_start, train_end)
    history: Dict[str, List[float]] = {sym: [] for sym in symbols}
    for event in data_handler.stream():
        history.setdefault(event.symbol, []).append(event.price)
    return history


def _summarise_walkforward(
    equity_records: List[Dict[str, Any]],
    artifacts_dir: Path,
    total_turnover: float,
    hac_lags: int | None = None,
    extra_metrics: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    metrics = compute_metrics(
        equity_records,
        total_turnover,
        hac_lags=hac_lags,
    )
    metrics_copy = dict(metrics)
    df = cast(pd.DataFrame, metrics_copy.pop("equity_df"))
    if extra_metrics:
        for key, value in extra_metrics.items():
            if value is not None:
                metrics_copy[key] = value

    equity_path: str | None = None
    oos_returns_path: str | None = None
    if not df.empty:
        path = artifacts_dir / "equity_curve.csv"
        df.to_csv(path, index=False)
        equity_path = str(path)
        if "returns" in df.columns:
            returns_path = artifacts_dir / "oos_returns.csv"
            df[["timestamp", "returns"]].to_csv(returns_path, index=False)
            oos_returns_path = str(returns_path)

    metrics_path = artifacts_dir / "metrics.json"
    stable_metrics = _stable_metrics(metrics_copy)
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(stable_metrics, handle, indent=2)

    manifest_metrics = stable_metrics.copy()
    manifest_metrics["equity_curve_path"] = equity_path
    manifest_metrics["oos_returns_path"] = oos_returns_path
    manifest_metrics["metrics_path"] = str(metrics_path)
    return manifest_metrics


def _stable_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    disallowed = {"run_id", "timestamp", "artifacts_dir", "config_path"}
    return {key: value for key, value in metrics.items() if key not in disallowed}


def _finalize_order_flow(
    order_flow: OrderFlowDiagnostics | None,
    filter_diagnostics: Mapping[str, Any] | None,
) -> Dict[str, Any] | None:
    if order_flow is None:
        return None
    try:
        order_flow.merge_filter_diagnostics(filter_diagnostics)
    except Exception as exc:  # pragma: no cover - diagnostics should not fail run
        order_flow.record_error(
            f"merge_filter_diagnostics_error: {type(exc).__name__}: {exc}"
        )
    return order_flow.payload()


def _persist_integrity_checks(
    artifacts_dir: Path,
    overall_ok: bool,
    checks: Sequence[Mapping[str, Any]],
) -> str:
    payload = {
        "ok": bool(overall_ok),
        "checks": list(checks),
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


def _build_grid_payload(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for entry in entries:
        params = dict(entry.get("params") or {})
        metrics = entry.get("metrics") or {}
        eq_df = metrics.get("equity_df")
        returns: List[float] = []
        timestamps: List[str] = []
        if isinstance(eq_df, pd.DataFrame) and not eq_df.empty:
            if "returns" in eq_df:
                returns = [float(x) for x in eq_df["returns"].astype(float).tolist()]
            ts_series = eq_df.get("timestamp")
            if ts_series is not None:
                timestamps = [_format_ts(val) for val in ts_series]
        else:
            arr = np.asarray(entry.get("returns"), dtype=float)
            if arr.size:
                returns = [float(x) for x in arr.tolist()]
        payload.append(
            {
                "params": params,
                "model": _format_param_label(params),
                "returns": returns,
                "timestamps": timestamps,
                "sharpe_ratio": float(metrics.get("sharpe_ratio", 0.0) or 0.0),
                "cagr": float(metrics.get("cagr", 0.0) or 0.0),
                "ann_vol": float(metrics.get("ann_vol", 0.0) or 0.0),
            }
        )
    return payload


def _grid_summary_from_payload(payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary: List[Dict[str, Any]] = []
    for entry in payload:
        summary.append(
            {
                "model": entry.get("model"),
                "params": entry.get("params", {}),
                "sharpe_ratio": entry.get("sharpe_ratio", 0.0),
                "cagr": entry.get("cagr", 0.0),
                "ann_vol": entry.get("ann_vol", 0.0),
            }
        )
    return summary


def _aggregate_selection_summary(
    grid_summaries: Sequence[List[Dict[str, Any]]],
) -> List[Dict[str, Any]]:
    aggregated: Dict[str, Dict[str, Any]] = {}
    for fold_index, summary in enumerate(grid_summaries):
        for entry in summary:
            model = entry.get("model") or _format_param_label(
                entry.get("params", {})
            )
            params = dict(entry.get("params") or {})
            sharpe = float(entry.get("sharpe_ratio", 0.0) or 0.0)
            cagr = float(entry.get("cagr", 0.0) or 0.0)
            ann_vol = float(entry.get("ann_vol", 0.0) or 0.0)
            record = aggregated.setdefault(
                model,
                {
                    "model": model,
                    "params": params,
                    "sharpes": [],
                    "cagrs": [],
                    "ann_vols": [],
                    "folds": [],
                },
            )
            record["sharpes"].append(sharpe)
            record["cagrs"].append(cagr)
            record["ann_vols"].append(ann_vol)
            record["folds"].append(fold_index)

    summary: List[Dict[str, Any]] = []
    for model, record in aggregated.items():
        sharpe_vals = record["sharpes"]
        cagr_vals = record["cagrs"]
        ann_vol_vals = record["ann_vols"]
        summary.append(
            {
                "model": model,
                "params": record.get("params") or {},
                "mean_sharpe": float(np.mean(sharpe_vals))
                if sharpe_vals
                else float("-inf"),
                "mean_cagr": float(np.mean(cagr_vals)) if cagr_vals else 0.0,
                "mean_ann_vol": float(np.mean(ann_vol_vals)) if ann_vol_vals else 0.0,
                "num_folds": int(len(sharpe_vals)),
                "folds": record.get("folds") or [],
            }
        )

    summary.sort(
        key=lambda item: (
            -float(item.get("mean_sharpe", float("-inf"))),
            -int(item.get("num_folds", 0)),
            str(item.get("model") or ""),
        )
    )
    return summary


def _grid_rows_for_fold(
    payload: List[Dict[str, Any]],
    fold_index: int,
    phase: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for entry in payload:
        returns = entry.get("returns") or []
        timestamps = entry.get("timestamps") or []
        if not timestamps or len(timestamps) != len(returns):
            timestamps = [str(i) for i in range(len(returns))]
        for ts, value in zip(timestamps, returns):
            rows.append(
                {
                    "fold": fold_index,
                    "phase": phase,
                    "model": entry.get("model"),
                    "timestamp": ts,
                    "panel_id": f"{fold_index}:{ts}",
                    "value": float(value),
                }
            )
    return rows


def _format_param_label(params: Mapping[str, Any]) -> str:
    if not params:
        return "default"
    parts: List[str] = []
    for key, value in sorted(params.items()):
        if isinstance(value, float):
            parts.append(f"{key}={value:.4f}")
        else:
            parts.append(f"{key}={value}")
    return "|".join(parts)


def _metrics_summary(metrics: Dict[str, Any]) -> Dict[str, Any]:
    if not metrics:
        return {}

    summary: Dict[str, Any] = {}
    df = metrics.get("equity_df")
    for key, value in metrics.items():
        if key == "equity_df":
            continue
        if isinstance(value, (np.generic,)):
            value = float(value)
        summary[key] = value

    if df is not None and not df.empty:
        summary["observations"] = int(len(df))
        summary["period_start"] = _format_ts(df["timestamp"].iloc[0])
        summary["period_end"] = _format_ts(df["timestamp"].iloc[-1])
    else:
        summary["observations"] = 0

    return summary


def _format_ts(value: Any) -> str:
    try:
        ts = pd.to_datetime(value)
        return str(ts)
    except Exception:
        return str(value)


def _annualised_sharpe(returns: np.ndarray, periods: int = 252) -> float:
    if returns.size == 0:
        return 0.0
    mean = returns.mean()
    std = returns.std(ddof=0)
    if std == 0:
        return 0.0
    return float(np.sqrt(periods) * (mean / std))


def bootstrap_reality_check(
    results: List[Dict[str, Any]],
    seed: int,
    n_bootstrap: int = 200,
    method: str = "stationary",
    block_len: int | None = None,
) -> Dict[str, Any] | None:
    valid = [res for res in results if res["returns"].size > 1]
    if len(valid) < 2:
        return None

    observed_sharpes = [res["metrics"].get("sharpe_ratio", 0.0) for res in valid]
    best_sharpe = max(observed_sharpes)
    if not np.isfinite(best_sharpe):
        return None

    rng = np.random.default_rng(seed)
    method_lower = method.lower()
    use_iid = method_lower == "iid"
    if use_iid:
        warnings.warn(
            "IID resampling for walk-forward reality check is deprecated; "
            "prefer stationary or circular block bootstrap.",
            DeprecationWarning,
            stacklevel=2,
        )

    exceed = 0
    distribution: List[float] = []
    for _ in range(max(1, n_bootstrap)):
        max_sharpe = float("-inf")
        for entry in valid:
            returns = entry["returns"]
            if use_iid:
                sample = rng.choice(returns, size=returns.size, replace=True)
            else:
                sample = next(
                    block_bootstrap(
                        returns,
                        B=1,
                        method=method_lower,  # type: ignore[arg-type]
                        block_len=block_len,
                        rng=rng,
                    )
                )
            sharpe = _annualised_sharpe(sample)
            max_sharpe = max(max_sharpe, sharpe)
        distribution.append(float(max_sharpe))
        if max_sharpe >= best_sharpe:
            exceed += 1

    p_value = (exceed + 1) / (len(distribution) + 1)
    return {
        "p_value": float(p_value),
        "distribution": distribution,
        "best_sharpe": float(best_sharpe),
        "method": method_lower,
        "block_length": block_len,
        "num_models": len(valid),
        "num_bootstrap": len(distribution),
    }


def _strategy_params(strategy_cfg) -> Dict[str, Any]:
    params = dict(strategy_cfg.params)
    if getattr(strategy_cfg, "lookback", None) is not None:
        params.setdefault("lookback", strategy_cfg.lookback)
    if getattr(strategy_cfg, "z", None) is not None:
        params.setdefault("z_threshold", strategy_cfg.z)
    return params


def _strategy_kwargs(params: Dict[str, Any], warmup_prices=None) -> Dict[str, Any]:
    kwargs = dict(params)
    if "z" in kwargs and "z_threshold" not in kwargs:
        kwargs["z_threshold"] = kwargs.pop("z")
    if warmup_prices is not None:
        kwargs["warmup_prices"] = warmup_prices
    return kwargs

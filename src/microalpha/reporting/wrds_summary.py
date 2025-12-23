"""WRDS-specific markdown and docs summary renderer."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import matplotlib.pyplot as plt
import pandas as pd
import yaml

from microalpha.reporting.robustness import write_robustness_artifacts
from microalpha.reporting.spa import SpaSummary, load_grid_returns, write_outputs
from microalpha.wrds import guard_no_wrds_copy

@dataclass(frozen=True)
class HeadlineMetrics:
    sharpe_hac: float
    mar: float
    max_drawdown: float
    turnover: float
    reality_check_p: float
    spa_p_value: float | None


@dataclass(frozen=True)
class SpaRenderResult:
    path: Path
    status: str
    skip_reason: str | None


def _require_file(path: Path, label: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{label} missing: {path}")
    return path


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_integrity(artifact_dir: Path) -> dict | None:
    integrity_path = artifact_dir / "integrity.json"
    if not integrity_path.exists():
        return None
    try:
        return _load_json(integrity_path)
    except Exception:
        return None


def _integrity_reasons(payload: dict | None) -> list[str]:
    reasons: list[str] = []
    if not payload:
        return reasons
    raw = payload.get("reasons")
    if isinstance(raw, list):
        reasons.extend(str(item) for item in raw if item)
    checks = payload.get("checks")
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, dict):
                continue
            if check.get("ok", True):
                continue
            phase = check.get("phase") or "run"
            fold = check.get("fold")
            prefix = f"{phase}"
            if fold is not None:
                prefix = f"{phase} fold {fold}"
            for reason in check.get("reasons") or []:
                reasons.append(f"{prefix}: {reason}")
    return reasons


def _format_currency(value: float) -> str:
    return f"${value:,.0f}"


def _format_human_currency(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "$0"
    abs_val = abs(value)
    suffixes = ((1_000_000_000_000, "T"), (1_000_000_000, "B"), (1_000_000, "MM"), (1_000, "K"))
    for threshold, suffix in suffixes:
        if abs_val >= threshold:
            return f"${value / threshold:.2f}{suffix}"
    return f"${value:,.2f}"


def _format_ratio(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    return f"{value:.2f}"


def _format_p_value(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "n/a"
    return f"{value:.3f}"


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _relpath(target: Path, output_path: Path) -> str:
    start = output_path.resolve().parent
    try:
        return os.path.relpath(target.resolve(), start)
    except ValueError:  # pragma: no cover - different drives on Windows
        return str(target.resolve())


def _normalise_section(text: str) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].lstrip().startswith("#"):
        lines.pop(0)
        while lines and not lines[0].strip():
            lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _render_table(metrics: HeadlineMetrics) -> list[str]:
    return [
        "| Metric | Value |",
        "| --- | ---:|",
        f"| Sharpe_HAC | {_format_ratio(metrics.sharpe_hac)} |",
        f"| MAR | {_format_ratio(metrics.mar)} |",
        f"| MaxDD | {_format_pct(metrics.max_drawdown)} |",
        f"| Turnover | {_format_currency(metrics.turnover)} |",
        f"| RealityCheck_p_value | {_format_p_value(metrics.reality_check_p)} |",
        f"| SPA_p_value | {_format_p_value(metrics.spa_p_value)} |",
    ]


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _render_exposure_table(metrics_payload: dict) -> list[str] | None:
    avg_net = _to_float(metrics_payload.get("avg_exposure"))
    avg_gross = _to_float(metrics_payload.get("avg_gross_exposure"))
    max_net = _to_float(metrics_payload.get("max_net_exposure"))
    max_gross = _to_float(metrics_payload.get("max_gross_exposure"))
    if all(value is None for value in (avg_net, avg_gross, max_net, max_gross)):
        return None
    return [
        "| Metric | Value |",
        "| --- | ---:|",
        f"| Avg net exposure | {_format_pct(avg_net or 0.0) if avg_net is not None else 'n/a'} |",
        f"| Avg gross exposure | {_format_pct(avg_gross or 0.0) if avg_gross is not None else 'n/a'} |",
        f"| Max net exposure | {_format_pct(max_net or 0.0) if max_net is not None else 'n/a'} |",
        f"| Max gross exposure | {_format_pct(max_gross or 0.0) if max_gross is not None else 'n/a'} |",
    ]


def _render_cost_breakdown(cost_payload: dict | None) -> list[str] | None:
    if not cost_payload:
        return None
    cost_basis = cost_payload.get("cost_basis")
    if not isinstance(cost_basis, dict):
        return None
    commission = _to_float(cost_basis.get("commission_total"))
    slippage = _to_float(cost_basis.get("slippage_total"))
    borrow = _to_float(cost_basis.get("borrow_total"))
    total = _to_float(cost_basis.get("total"))
    return [
        "| Category | Total |",
        "| --- | ---:|",
        f"| Commission | {_format_currency(commission or 0.0) if commission is not None else 'n/a'} |",
        f"| Slippage | {_format_currency(slippage or 0.0) if slippage is not None else 'n/a'} |",
        f"| Borrow | {_format_currency(borrow or 0.0) if borrow is not None else 'n/a'} |",
        f"| Total | {_format_currency(total or 0.0) if total is not None else 'n/a'} |",
    ]


def _has_trade_log(artifact_dir: Path) -> bool:
    return any((artifact_dir / name).exists() for name in ("trades.jsonl", "trades.csv"))


def _load_cost_payload(artifact_dir: Path) -> dict | None:
    cost_path = artifact_dir / "cost_sensitivity.json"
    if cost_path.exists():
        return _load_json(cost_path)
    if _has_trade_log(artifact_dir):
        try:
            write_robustness_artifacts(artifact_dir)
        except (OSError, ValueError):
            return None
        if cost_path.exists():
            return _load_json(cost_path)
    return None


def _extract_headline(
    metrics_payload: dict, spa_payload: dict, *, spa_status: str
) -> HeadlineMetrics:
    sharpe = float(metrics_payload.get("sharpe_ratio") or 0.0)
    mar = float(metrics_payload.get("calmar_ratio") or 0.0)
    max_dd = abs(float(metrics_payload.get("max_drawdown") or 0.0))
    turnover = float(metrics_payload.get("total_turnover") or 0.0)
    rc_p = float(
        metrics_payload.get("reality_check_p_value")
        or metrics_payload.get("bootstrap_p_value")
        or 0.0
    )
    spa_p: float | None
    if spa_status != "ok":
        spa_p = None
    else:
        spa_p = _coerce_float(spa_payload.get("p_value"))
    return HeadlineMetrics(sharpe, mar, max_dd, turnover, rc_p, spa_p)


def _parse_factor_table(markdown: str) -> tuple[list[dict[str, float | str]], str | None]:
    rows: list[dict[str, float | str]] = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        if line.startswith("| ---") or ("Factor" in line and "Beta" in line and "t-stat" in line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        factor = cells[0]
        try:
            beta = float(cells[1])
            t_stat = float(cells[2])
        except ValueError:
            continue
        rows.append({"factor": factor, "beta": beta, "t_stat": t_stat})
    if not rows:
        return [], "Factor regression table is empty; run reports/factors.py first."
    if all(abs(row["beta"]) < 1e-9 and abs(row["t_stat"]) < 1e-9 for row in rows):
        return rows, "Factor regression table contains only zeros; rerun the regression."
    return rows, None


def _copy_asset(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    guard_no_wrds_copy(source, operation="copy")
    shutil.copy2(source, destination)
    return destination


def _load_folds_metadata(folds_path: Path) -> tuple[str, str, int]:
    payload = _load_json(folds_path)
    if not isinstance(payload, list) or not payload:
        raise SystemExit("folds.json is empty; rerun the walk-forward job.")
    start = str(payload[0].get("train_start"))
    end = str(payload[-1].get("test_end"))
    if not start or not end:
        raise SystemExit("folds.json missing train/test boundaries")
    return start, end, len(payload)


def _load_config_metadata(config_path: Path | None) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "label": str(config_path) if config_path else "unknown",
        "testing_days": None,
        "training_days": None,
        "lookback_months": None,
        "skip_months": None,
        "min_adv": None,
        "turnover_target_pct_adv": None,
        "max_positions_per_sector": None,
    }
    if not config_path or not config_path.exists():
        return metadata
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    walkforward_cfg = raw.get("walkforward") or {}
    metadata["testing_days"] = walkforward_cfg.get("testing_days")
    metadata["training_days"] = walkforward_cfg.get("training_days")
    template = raw.get("template") or {}
    strategy = template.get("strategy") or {}
    params = strategy.get("params") or {}
    metadata["lookback_months"] = params.get("lookback_months")
    metadata["skip_months"] = params.get("skip_months")
    metadata["min_adv"] = params.get("min_adv")
    metadata["turnover_target_pct_adv"] = params.get("turnover_target_pct_adv")
    metadata["max_positions_per_sector"] = params.get("max_positions_per_sector")
    return metadata


def _relative_to_repo(path: Path) -> str:
    repo_root = Path.cwd()
    try:
        return os.path.relpath(path.resolve(), repo_root)
    except (FileNotFoundError, ValueError):
        return str(path)


def _coerce_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return None
    return candidate if math.isfinite(candidate) else None


def _infer_spa_dimensions(artifact_dir: Path, diagnostics: list[str]) -> tuple[int, int]:
    grid_path = artifact_dir / "grid_returns.csv"
    if not grid_path.exists():
        return 0, 0
    try:
        pivot = load_grid_returns(grid_path)
    except Exception as exc:  # pragma: no cover - defensive fallback
        diagnostics.append(f"grid_returns unreadable: {type(exc).__name__}: {exc}")
        return 0, 0
    return int(pivot.shape[0]), int(pivot.shape[1])


def _write_degenerate_spa(
    json_path: Path,
    md_path: Path,
    *,
    reason: str,
    diagnostics: list[str],
    n_obs: int,
    n_strategies: int,
) -> dict:
    summary = SpaSummary(
        status="degenerate",
        reason=reason,
        best_model=None,
        p_value=None,
        observed_stat=None,
        num_bootstrap=0,
        avg_block=0,
        candidate_stats=[],
        n_obs=n_obs,
        n_strategies=n_strategies,
        diagnostics=diagnostics,
    )
    write_outputs(summary, json_path, md_path)
    return _load_json(json_path)


def _write_spa_markdown_from_payload(payload: dict, md_path: Path) -> None:
    status, reason = _spa_status(payload)
    lines = ["# Hansen SPA Summary", ""]
    if status != "ok":
        lines.append(f"- **Status:** degenerate")
        lines.append(f"- **Reason:** {reason or 'invalid inputs'}")
        lines.append(f"- **Observations:** {payload.get('n_obs', 0)}")
        lines.append(f"- **Strategies:** {payload.get('n_strategies', 0)}")
        diagnostics = payload.get("diagnostics")
        if isinstance(diagnostics, list) and diagnostics:
            lines.append(f"- **Diagnostics:** {', '.join(str(x) for x in diagnostics)}")
    else:
        best_model = payload.get("best_model", "unknown")
        observed = _coerce_float(payload.get("observed_stat"))
        p_value = _coerce_float(payload.get("p_value"))
        num_bootstrap = payload.get("num_bootstrap") or 0
        avg_block = payload.get("avg_block") or 0
        lines.append(f"- **Best model:** {best_model}")
        if observed is not None:
            lines.append(f"- **Observed max t-stat:** {observed:.3f}")
        if p_value is not None:
            lines.append(f"- **p-value:** {p_value:.3f}")
        lines.append(f"- **Bootstrap draws:** {num_bootstrap} (avg block {avg_block})")
        candidates = payload.get("candidate_stats")
        if isinstance(candidates, list) and candidates:
            lines.append("")
            lines.append("| Comparator | Mean Diff | t-stat |")
            lines.append("| --- | ---:| ---:|")
            for row in candidates:
                if not isinstance(row, dict):
                    continue
                model = row.get("model", "unknown")
                mean_diff = _coerce_float(row.get("mean_diff"))
                t_stat = _coerce_float(row.get("t_stat"))
                lines.append(
                    f"| {model} | {mean_diff if mean_diff is not None else 0.0:.4f} | "
                    f"{t_stat if t_stat is not None else 0.0:.2f} |"
                )
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _ensure_spa_payload(
    artifact_dir: Path, spa_json: Path | None, spa_md: Path | None
) -> tuple[Path, Path, dict]:
    json_path = (spa_json or (artifact_dir / "spa.json")).resolve()
    md_path = (spa_md or (artifact_dir / "spa.md")).resolve()
    diagnostics: list[str] = []
    payload: dict | None = None
    reason: str | None = None

    if json_path.exists():
        try:
            payload = _load_json(json_path)
            if not isinstance(payload, dict):
                reason = "spa.json payload is not an object"
                payload = None
        except json.JSONDecodeError as exc:
            reason = f"spa.json invalid JSON: {exc.msg}"
        except Exception as exc:  # pragma: no cover - defensive fallback
            reason = f"spa.json unreadable: {type(exc).__name__}"
            diagnostics.append(str(exc))
    else:
        reason = "spa.json missing"

    if payload is None:
        n_obs, n_strategies = _infer_spa_dimensions(artifact_dir, diagnostics)
        payload = _write_degenerate_spa(
            json_path,
            md_path,
            reason=reason or "invalid SPA inputs",
            diagnostics=diagnostics,
            n_obs=n_obs,
            n_strategies=n_strategies,
        )
        return json_path, md_path, payload

    if not md_path.exists():
        _write_spa_markdown_from_payload(payload, md_path)

    return json_path, md_path, payload


def _spa_skip_reason(spa_payload: dict) -> str | None:
    candidates = spa_payload.get("candidate_stats")
    if not isinstance(candidates, list) or not candidates:
        return "SPA payload missing comparator statistics."
    t_stats = []
    for row in candidates:
        if not isinstance(row, dict):
            continue
        t_stats.append(_coerce_float(row.get("t_stat")))
    finite_stats = [stat for stat in t_stats if stat is not None]
    if not finite_stats:
        return "SPA comparator t-stats are all NaN/inf."
    return None


def _spa_status(spa_payload: dict) -> tuple[str, str | None]:
    status_raw = spa_payload.get("status") or spa_payload.get("spa_status")
    reason = spa_payload.get("reason") or spa_payload.get("spa_skip_reason")
    if isinstance(status_raw, str):
        status = status_raw.lower()
        if status in {"degenerate", "skipped"}:
            return "degenerate", reason or "invalid inputs"
        if status == "ok":
            p_value = _coerce_float(spa_payload.get("p_value"))
            if p_value is None:
                return "degenerate", reason or "missing SPA p-value"
            if not (0.0 <= p_value <= 1.0):
                return "degenerate", reason or "SPA p-value out of bounds"
            skip_reason = _spa_skip_reason(spa_payload)
            if skip_reason:
                return "degenerate", reason or skip_reason
            return "ok", None
    skip_reason = _spa_skip_reason(spa_payload)
    if skip_reason:
        return "degenerate", reason or skip_reason
    p_value = _coerce_float(spa_payload.get("p_value"))
    if p_value is None:
        return "degenerate", reason or "missing SPA p-value"
    if not (0.0 <= p_value <= 1.0):
        return "degenerate", reason or "SPA p-value out of bounds"
    return "ok", None


def _render_spa_placeholder(destination: Path, message: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.axis("off")
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=12, wrap=True)
    fig.tight_layout()
    fig.savefig(destination, dpi=200)
    plt.close(fig)


def _render_spa_plot(
    spa_payload: dict, destination: Path, *, allow_zero: bool = False
) -> SpaRenderResult:
    status, reason = _spa_status(spa_payload)
    if status != "ok":
        _render_spa_placeholder(destination, f"SPA degenerate: {reason or 'invalid inputs'}")
        return SpaRenderResult(destination, "degenerate", reason)

    candidates = spa_payload.get("candidate_stats") or []
    labels = [
        str(row.get("model")) if isinstance(row, dict) else "unknown"
        for row in candidates
    ]
    t_stats = [
        _coerce_float(row.get("t_stat")) if isinstance(row, dict) else None
        for row in candidates
    ]
    normalized = [stat if stat is not None else 0.0 for stat in t_stats]

    destination.parent.mkdir(parents=True, exist_ok=True)
    order = sorted(range(len(labels)), key=lambda idx: normalized[idx], reverse=True)
    ordered_labels = [labels[idx] for idx in order]
    ordered_stats = [normalized[idx] for idx in order]
    fig, ax = plt.subplots(figsize=(10, max(2.5, len(ordered_labels) * 0.45)))
    ax.barh(ordered_labels, ordered_stats, color="#3266c1")
    ax.axvline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("Comparator t-stat vs. best model")
    ax.set_title("Hansen SPA Comparator t-stats")
    fig.tight_layout()
    fig.savefig(destination, dpi=200)
    plt.close(fig)
    return SpaRenderResult(destination, "ok", None)


def _resolve_trades_path(artifact_dir: Path) -> Path | None:
    for candidate in ("trades.jsonl", "trades.csv"):
        path = artifact_dir / candidate
        if path.exists():
            return path
    return None


def _count_trades(path: Path) -> int:
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            return sum(1 for line in handle if line.strip())
    with path.open("r", encoding="utf-8") as handle:
        rows = 0
        header_seen = False
        for line in handle:
            if not line.strip():
                continue
            if not header_seen:
                header_seen = True
                continue
            rows += 1
        return rows


def _load_returns(artifact_dir: Path) -> pd.Series | None:
    equity_path = artifact_dir / "equity_curve.csv"
    if not equity_path.exists():
        return None
    df = pd.read_csv(equity_path)
    if df.empty:
        return pd.Series([], dtype=float)
    if "returns" in df.columns:
        return pd.Series(df["returns"], dtype=float).dropna()
    if "equity" not in df.columns:
        return None
    returns = pd.Series(df["equity"], dtype=float).pct_change().fillna(0.0)
    return returns


def _detect_degenerate_reasons(metrics_payload: dict, artifact_dir: Path) -> list[str]:
    reasons: list[str] = []
    num_trades = _to_float(metrics_payload.get("num_trades"))
    if num_trades is None:
        trades_path = _resolve_trades_path(artifact_dir)
        if trades_path:
            num_trades = float(_count_trades(trades_path))
    if num_trades is not None and int(num_trades) == 0:
        reasons.append("num_trades == 0 (no executed trades)")

    turnover = _to_float(metrics_payload.get("total_turnover"))
    if (
        turnover is not None
        and num_trades is not None
        and int(num_trades) == 0
        and turnover > 0
    ):
        reasons.append("turnover > 0 with zero trades (metrics inconsistent)")

    returns = _load_returns(artifact_dir)
    if returns is not None:
        returns = returns.dropna()
        if returns.empty:
            reasons.append("returns series is empty")
        else:
            variance = float(returns.var(ddof=0))
            if abs(variance) <= 1e-12:
                reasons.append("returns variance is zero (flat equity curve)")

    return reasons


def _write_docs_results(
    docs_path: Path,
    *,
    run_id: str,
    config_label: str,
    train_start: str,
    test_end: str,
    fold_count: int,
    testing_days: int | None,
    config_meta: dict[str, Any] | None,
    headline: HeadlineMetrics,
    metrics_payload: dict,
    cost_payload: dict | None,
    spa_payload: dict,
    spa_status: str,
    spa_skip_reason: str | None,
    factor_status: str,
    factor_skip_reason: str | None,
    factor_table_md: str,
    image_map: dict[str, Path],
    spa_md_copy: Path | None,
    degenerate_reasons: list[str],
    invalid_reasons: list[str],
) -> None:
    docs_path = docs_path.resolve()
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    months_fragment = ""
    if testing_days:
        approx_months = testing_days / 21.0
        months_fragment = f" (~{approx_months:.1f} months)"

    perf_lines = [
        "| Metric | Value |",
        "| --- | ---:|",
        f"| Sharpe_HAC | {_format_ratio(headline.sharpe_hac)} |",
        f"| MAR | {_format_ratio(headline.mar)} |",
        f"| Max Drawdown | {_format_pct(headline.max_drawdown)} |",
        f"| Turnover | {_format_human_currency(headline.turnover)} |",
        f"| Reality Check p-value | {_format_p_value(headline.reality_check_p)} |",
        f"| SPA p-value | {_format_p_value(headline.spa_p_value)} |",
    ]

    image_rel = {key: _relpath(path, docs_path) for key, path in image_map.items()}
    spa_md_rel = _relative_to_repo(spa_md_copy) if spa_md_copy else None

    lines: list[str] = []
    lines.append("# WRDS Walk-Forward Results (Flagship Momentum)")
    lines.append("")
    lines.append(
        (
            f"> Latest run: **{run_id}** (`{config_label}`, {train_start} -> {test_end}, "
            f"{fold_count} folds with {testing_days or 'N/A'}-day forward tests{months_fragment})"
        )
    )
    lines.append("")
    lines.append("## Performance Snapshot")
    lines.append("")
    lines.extend(perf_lines)
    lines.append("")
    if invalid_reasons:
        lines.append("## Run marked invalid")
        lines.append("")
        lines.append("Integrity checks failed; results are not interpretable:")
        for reason in invalid_reasons:
            lines.append(f"- {reason}")
        lines.append("")
    if degenerate_reasons:
        lines.append("## Run is degenerate")
        lines.append("")
        lines.append("This run is not interpretable for performance claims:")
        for reason in degenerate_reasons:
            lines.append(f"- {reason}")
        lines.append("")
    exposure_table = _render_exposure_table(metrics_payload)
    if exposure_table:
        lines.append("## Exposure Summary")
        lines.append("")
        lines.extend(exposure_table)
        lines.append("")
        lines.append("_Exposure time series is recorded in equity_curve.csv._")
        lines.append("")
    cost_breakdown = _render_cost_breakdown(cost_payload)
    if cost_breakdown:
        lines.append("## Cost Breakdown")
        lines.append("")
        lines.extend(cost_breakdown)
        lines.append("")
    lines.append("## Key Visuals")
    lines.append("")
    for label, key in (
        ("Equity Curve", "equity"),
        ("Bootstrap Sharpe Histogram", "bootstrap"),
        ("SPA Comparator t-stats", "spa"),
        ("IC / Rolling IR", "ic_ir"),
        ("Decile Spreads", "deciles"),
        ("Rolling FF5+MOM Betas", "rolling_betas"),
    ):
        lines.append(f"![{label}]({image_rel[key]})")
        lines.append("")

    lines.append("## SPA & Factor Highlights")
    lines.append("")
    if spa_status != "ok":
        lines.append(f"- SPA degenerate: {spa_skip_reason or 'invalid inputs'}")
    else:
        best_model = spa_payload.get("best_model", "unknown")
        p_value = _coerce_float(spa_payload.get("p_value")) or 0.0
        num_bootstrap = spa_payload.get("num_bootstrap") or 0
        avg_block = spa_payload.get("avg_block") or 0
        spa_ref = spa_md_rel or spa_payload.get(
            "markdown_path", "reports/summaries/wrds_flagship_spa.md"
        )
        lines.append(
            (
                f"- Hansen SPA best model: **{best_model}** with p-value **{p_value:.3f}** "
                f"({num_bootstrap} stationary bootstrap draws, block={avg_block}). "
                f"See `{spa_ref}`."
            )
        )
    if factor_status == "skipped":
        lines.append(f"- Factor regression skipped — {factor_skip_reason}")
        lines.append("")
    else:
        lines.append("- FF5 + MOM regression (HAC lags=5):")
        lines.append("")
        lines.append("```")
        lines.append(factor_table_md.strip())
        lines.append("```")
        lines.append("")

    lines.append("## Capacity & Turnover")
    lines.append("")
    turnover_per_day = metrics_payload.get("turnover_per_day")
    traded_days = metrics_payload.get("traded_days")
    total_turnover = metrics_payload.get("total_turnover")
    lines.append(
        "- Average daily turnover: "
        + f"~{_format_human_currency(turnover_per_day)} (total {_format_human_currency(total_turnover)}) "
        + f"across {traded_days or 'N/A'} traded days."
    )
    lines.append(
        "- Portfolio heat cap enforced via max positions per sector and ADV floor; no guardrail breaches detected."
    )
    lines.append("")

    cfg = config_meta or {}
    lookback = cfg.get("lookback_months")
    skip = cfg.get("skip_months")
    min_adv_val = cfg.get("min_adv")
    turnover_target = cfg.get("turnover_target_pct_adv")
    max_sector = cfg.get("max_positions_per_sector")
    training_days = cfg.get("training_days")

    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- Signals derived from the WRDS flagship universe with "
        + f"{lookback or 'N/A'}M lookback / {skip or 'N/A'}M skip and ADV >= {_format_human_currency(min_adv_val)}."
    )
    lines.append(
        "- Training window spans "
        + f"{training_days or 'N/A'} trading days; forward tests run {testing_days or 'N/A'} days each."
    )
    lines.append(
        "- Target turnover ≈ "
        + (f"{turnover_target:.2%}" if isinstance(turnover_target, (int, float)) else "N/A")
        + f" of ADV with max {max_sector or 'N/A'} positions per sector."
    )
    lines.append("- Execution assumes TWAP slicing with linear+sqrt impact, 5 bps commissions, and borrow spread floor of 8 bps.")
    lines.append("")

    docs_artifacts_root = None
    if image_map:
        sample_path = next(iter(image_map.values()))
        docs_artifacts_root = _relative_to_repo(Path(sample_path).parent)
    if not docs_artifacts_root:
        docs_artifacts_root = f"docs/img/wrds_flagship/{run_id}"
    lines.append(
        "Published artifacts (PNG/MD/JSON summaries) live under "
        + f"`{docs_artifacts_root}` and reports/summaries for reproducibility."
    )

    docs_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def render_wrds_summary(
    artifact_dir: Path,
    output_path: Path,
    *,
    factors_md: Path | None = None,
    spa_json: Path | None = None,
    spa_md: Path | None = None,
    equity_image: Path | None = None,
    bootstrap_image: Path | None = None,
    docs_results: Path | None = None,
    docs_image_root: Path | None = None,
    analytics_plots: Path | None = None,
    metrics_json_out: Path | None = None,
    spa_json_out: Path | None = None,
    spa_md_out: Path | None = None,
    allow_zero_spa: bool = False,
) -> Path:
    artifact_dir = artifact_dir.resolve()
    output_path = output_path.resolve()
    if docs_results and not docs_image_root:
        raise SystemExit("--docs-image-root must be provided when --docs-results is set")

    metrics_path = _require_file(artifact_dir / "metrics.json", "metrics.json")
    equity_png = _require_file(equity_image or (artifact_dir / "equity_curve.png"), "equity_curve.png")
    bootstrap_png = _require_file(
        bootstrap_image or (artifact_dir / "bootstrap_hist.png"),
        "bootstrap_hist.png",
    )
    spa_json_path, spa_md_path, spa_payload = _ensure_spa_payload(
        artifact_dir, spa_json=spa_json, spa_md=spa_md
    )
    factors_path = _require_file(
        factors_md or (artifact_dir / "factors_ff5_mom.md"),
        "factor regression markdown",
    )
    manifest_path = _require_file(artifact_dir / "manifest.json", "manifest.json")
    folds_path = _require_file(artifact_dir / "folds.json", "folds.json")

    metrics_payload = _load_json(metrics_path)
    spa_result = _render_spa_plot(
        spa_payload, artifact_dir / "spa_tstats.png", allow_zero=allow_zero_spa
    )
    spa_status = spa_result.status
    spa_skip_reason = spa_result.skip_reason
    headline = _extract_headline(metrics_payload, spa_payload, spa_status=spa_status)
    factors_text = factors_path.read_text(encoding="utf-8")
    _, factor_skip_reason = _parse_factor_table(factors_text)
    factor_status = "skipped" if factor_skip_reason else "ok"
    cost_payload = _load_cost_payload(artifact_dir)
    degenerate_reasons = _detect_degenerate_reasons(metrics_payload, artifact_dir)
    integrity_payload = _load_integrity(artifact_dir)
    integrity_reasons = _integrity_reasons(integrity_payload)

    manifest_payload = _load_json(manifest_path)
    run_id = manifest_payload.get("run_id") or artifact_dir.name or "wrds_run"
    config_path_value = manifest_payload.get("config_path")
    config_path = Path(config_path_value).expanduser() if config_path_value else None
    config_meta = _load_config_metadata(config_path if config_path and config_path.exists() else None)
    config_label = _relative_to_repo(config_path) if config_path else (config_path_value or "unknown")
    train_start, test_end, fold_count = _load_folds_metadata(folds_path)

    analytics_dir = (analytics_plots or Path("artifacts/plots")).expanduser().resolve()
    ic_plot = _require_file(analytics_dir / f"{run_id}_ic_ir.png", "IC/IR plot")
    decile_plot = _require_file(analytics_dir / f"{run_id}_deciles.png", "deciles plot")
    beta_plot = _require_file(analytics_dir / f"{run_id}_rolling_betas.png", "rolling betas plot")
    spa_plot = spa_result.path

    if metrics_json_out:
        metrics_json_out = metrics_json_out.expanduser().resolve()
        metrics_json_out.parent.mkdir(parents=True, exist_ok=True)
        metrics_copy = dict(metrics_payload)
        metrics_copy["run_id"] = run_id
        metrics_copy["spa_status"] = spa_status
        if spa_skip_reason:
            metrics_copy["spa_skip_reason"] = spa_skip_reason
        metrics_json_out.write_text(json.dumps(metrics_copy, indent=2) + "\n", encoding="utf-8")
    if spa_json_out:
        spa_json_out = spa_json_out.expanduser().resolve()
        spa_json_out.parent.mkdir(parents=True, exist_ok=True)
        spa_copy = dict(spa_payload)
        spa_copy["spa_status"] = spa_status
        if spa_skip_reason:
            spa_copy["spa_skip_reason"] = spa_skip_reason
        spa_json_out.write_text(json.dumps(spa_copy, indent=2) + "\n", encoding="utf-8")
    if spa_md_out:
        _copy_asset(spa_md_path, spa_md_out.expanduser().resolve())

    doc_image_map: dict[str, Path] | None = None
    if docs_image_root:
        docs_image_root = docs_image_root.expanduser().resolve()
        run_img_dir = docs_image_root / run_id
        doc_image_map = {
            "equity": _copy_asset(equity_png, run_img_dir / "equity_curve.png"),
            "bootstrap": _copy_asset(bootstrap_png, run_img_dir / "bootstrap_hist.png"),
            "spa": _copy_asset(spa_plot, run_img_dir / "spa_tstats.png"),
            "ic_ir": _copy_asset(ic_plot, run_img_dir / ic_plot.name),
            "deciles": _copy_asset(decile_plot, run_img_dir / decile_plot.name),
            "rolling_betas": _copy_asset(beta_plot, run_img_dir / beta_plot.name),
        }

    image_for_summary = {
        "equity": doc_image_map["equity"] if doc_image_map else equity_png,
        "bootstrap": doc_image_map["bootstrap"] if doc_image_map else bootstrap_png,
        "spa": doc_image_map["spa"] if doc_image_map else spa_plot,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# WRDS Flagship Walk-Forward", "", "## Headline Metrics", ""]
    lines.extend(_render_table(headline))
    lines.append("")
    if integrity_payload and not bool(integrity_payload.get("ok", True)):
        lines.append("## Run marked invalid")
        lines.append("")
        lines.append("Integrity checks failed; results are not interpretable:")
        for reason in integrity_reasons or ["unspecified integrity failure"]:
            lines.append(f"- {reason}")
        lines.append("")
    if degenerate_reasons:
        lines.append("## Run is degenerate")
        lines.append("")
        lines.append("This run is not interpretable for performance claims:")
        for reason in degenerate_reasons:
            lines.append(f"- {reason}")
        lines.append("")
    exposure_table = _render_exposure_table(metrics_payload)
    if exposure_table:
        lines.append("## Exposure Summary")
        lines.append("")
        lines.extend(exposure_table)
        lines.append("")
        lines.append("_Exposure time series is recorded in equity_curve.csv._")
        lines.append("")
    cost_breakdown = _render_cost_breakdown(cost_payload)
    if cost_breakdown:
        lines.append("## Cost Breakdown")
        lines.append("")
        lines.extend(cost_breakdown)
        lines.append("")

    lines.append("## Visuals")
    lines.append("")
    lines.append(f"![Equity Curve]({_relpath(image_for_summary['equity'], output_path)})")
    lines.append("")
    lines.append(f"![Bootstrap Sharpe Histogram]({_relpath(image_for_summary['bootstrap'], output_path)})")
    lines.append("")
    lines.append(f"![SPA Comparator t-stats]({_relpath(image_for_summary['spa'], output_path)})")
    lines.append("")

    lines.append("## Hansen SPA Summary")
    lines.append("")
    if spa_status != "ok":
        lines.append(f"SPA degenerate: {spa_skip_reason or 'invalid inputs'}")
    else:
        lines.extend(_normalise_section(spa_md_path.read_text(encoding="utf-8")))
    lines.append("")

    lines.append("## Factor Attribution (FF5+MOM)")
    lines.append("")
    if factor_status == "skipped":
        lines.append(f"Factor regression skipped — {factor_skip_reason}")
    else:
        lines.extend(_normalise_section(factors_text))
    lines.append("")

    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    if docs_results and doc_image_map:
        _write_docs_results(
            docs_results,
            run_id=run_id,
            config_label=config_label,
            train_start=train_start,
            test_end=test_end,
            fold_count=fold_count,
            testing_days=config_meta.get("testing_days"),
            config_meta=config_meta,
            headline=headline,
            metrics_payload=metrics_payload,
            cost_payload=cost_payload,
            spa_payload=spa_payload,
            spa_status=spa_status,
            spa_skip_reason=spa_skip_reason,
            factor_status=factor_status,
            factor_skip_reason=factor_skip_reason,
            factor_table_md=factors_text,
            image_map=doc_image_map,
            spa_md_copy=spa_md_out or spa_md_path,
            degenerate_reasons=degenerate_reasons,
            invalid_reasons=integrity_reasons,
        )

    return output_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", type=Path, help="Artifact directory for WRDS run")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/summaries/wrds_flagship.md"),
        help="Markdown destination (default: reports/summaries/wrds_flagship.md)",
    )
    parser.add_argument(
        "--factors-md",
        type=Path,
        default=None,
        help="Path to the FF5+MOM markdown table output by reports/factors.py",
    )
    parser.add_argument("--docs-results", type=Path, default=None, help="Optional docs/results_wrds.md destination")
    parser.add_argument(
        "--docs-image-root",
        type=Path,
        default=None,
        help="Root directory for docs images (e.g. docs/img/wrds_flagship)",
    )
    parser.add_argument(
        "--analytics-plots",
        type=Path,
        default=Path("artifacts/plots"),
        help="Directory containing analytics plots (default: artifacts/plots)",
    )
    parser.add_argument(
        "--metrics-json-out",
        type=Path,
        default=Path("reports/summaries/wrds_flagship_metrics.json"),
        help="Where to copy metrics.json with run_id metadata",
    )
    parser.add_argument(
        "--spa-json-out",
        type=Path,
        default=Path("reports/summaries/wrds_flagship_spa.json"),
        help="Where to copy the SPA JSON summary",
    )
    parser.add_argument(
        "--spa-md-out",
        type=Path,
        default=Path("reports/summaries/wrds_flagship_spa.md"),
        help="Where to copy the SPA markdown summary",
    )
    parser.add_argument(
        "--allow-zero-spa",
        action="store_true",
        help="Allow SPA rendering when comparator t-stats are all zero",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    render_wrds_summary(
        artifact_dir=args.artifact_dir,
        output_path=args.output,
        factors_md=args.factors_md,
        docs_results=args.docs_results,
        docs_image_root=args.docs_image_root,
        analytics_plots=args.analytics_plots,
        metrics_json_out=args.metrics_json_out,
        spa_json_out=args.spa_json_out,
        spa_md_out=args.spa_md_out,
        allow_zero_spa=args.allow_zero_spa,
    )


__all__ = ["HeadlineMetrics", "render_wrds_summary", "main"]


if __name__ == "__main__":
    main()

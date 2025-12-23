"""Markdown summary generator for Microalpha artifacts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd

DEFAULT_OUTPUT = Path("reports/summaries/flagship_mom.md")
DEFAULT_TITLE = "Flagship Momentum Case Study"


def _load_json(path: Path) -> Mapping[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_integrity(artifact_dir: Path) -> Mapping[str, object] | None:
    integrity_path = artifact_dir / "integrity.json"
    if not integrity_path.exists():
        return None
    try:
        return _load_json(integrity_path)
    except Exception:
        return None


def _load_manifest(artifact_dir: Path) -> Mapping[str, object] | None:
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        return _load_json(manifest_path)
    except Exception:
        return None


def _unsafe_banner(manifest_payload: Mapping[str, object] | None) -> list[str]:
    if not manifest_payload or not manifest_payload.get("unsafe_execution", False):
        return []
    reasons = manifest_payload.get("unsafe_reasons") or []
    reason_text = ""
    if isinstance(reasons, list) and reasons:
        reason_text = ", ".join(str(reason) for reason in reasons)
    if not reason_text:
        reason_text = "same-bar execution enabled"
    return [
        "## UNSAFE / NOT LEAKAGE-SAFE",
        "",
        f"Results are not leakage-safe ({reason_text}).",
        "",
    ]


def _integrity_reasons(payload: Mapping[str, object]) -> list[str]:
    reasons: list[str] = []
    if not payload:
        return reasons
    if "reasons" in payload:
        raw = payload.get("reasons") or []
        if isinstance(raw, list):
            reasons.extend(str(item) for item in raw if item)
    checks = payload.get("checks")
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, Mapping):
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


def _flatten_bootstrap(path: Path) -> tuple[list[float], float | None]:
    payload = _load_json(path)
    if isinstance(payload, dict):
        dist = payload.get("distribution") or []
        return [float(x) for x in dist], (
            float(payload["p_value"]) if "p_value" in payload else None
        )
    if isinstance(payload, list):
        if payload and isinstance(payload[0], (int, float)):
            return [float(x) for x in payload], None
        samples: list[float] = []
        p_values: list[float] = []
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            dist = entry.get("distribution") or []
            samples.extend(float(x) for x in dist)
            if "p_value" in entry and entry["p_value"] is not None:
                p_values.append(float(entry["p_value"]))
        p_value = sum(p_values) / len(p_values) if p_values else None
        return samples, p_value
    return [], None


def _format_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.2f}%"


def _format_currency(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:,.0f}"


def _render_exposures(exposures_path: Path | None, top_n: int) -> str:
    if exposures_path is None or not exposures_path.exists():
        return "_Exposures unavailable._"
    df = pd.read_csv(exposures_path)
    if df.empty or "weight" not in df.columns:
        return "_Exposures unavailable._"
    df = df.assign(abs_weight=df["weight"].abs())
    df = df.sort_values("abs_weight", ascending=False).head(top_n)
    lines = ["| Symbol | Qty | Market Value | Weight |", "| --- | ---:| ---:| ---:|"]
    for row in df.itertuples(index=False):
        weight = float(getattr(row, "weight"))
        lines.append(
            f"| {getattr(row, 'symbol')} | {getattr(row, 'qty'):.0f} | "
            f"${getattr(row, 'market_value'):,.0f} | {weight * 100:.2f}% |"
        )
    return "\n".join(lines)


def generate_summary(
    artifact_dir: str | Path,
    output_path: str | Path = DEFAULT_OUTPUT,
    *,
    title: str | None = None,
    top_exposures: int = 8,
    equity_image: str | Path | None = None,
    bootstrap_image: str | Path | None = None,
    factor_csv: str | Path | None = Path("data/factors/ff3_sample.csv"),
) -> Path:
    artifact_dir = Path(artifact_dir).resolve()
    if not artifact_dir.exists():
        raise FileNotFoundError(f"Artifact directory not found: {artifact_dir}")

    metrics_path = artifact_dir / "metrics.json"
    bootstrap_path = artifact_dir / "bootstrap.json"
    exposures_path = artifact_dir / "exposures.csv"
    cost_path = artifact_dir / "cost_sensitivity.json"
    coverage_path = artifact_dir / "metadata_coverage.json"

    if not metrics_path.exists():
        raise FileNotFoundError(f"metrics.json not found under {artifact_dir}")

    metrics = _load_json(metrics_path)
    bootstrap_samples: list[float] = []
    bootstrap_pvalue: float | None = None
    if bootstrap_path.exists():
        bootstrap_samples, bootstrap_pvalue = _flatten_bootstrap(bootstrap_path)
    if bootstrap_pvalue is None:
        candidate = metrics.get("reality_check_p_value") or metrics.get(
            "bootstrap_p_value"
        )
        if candidate is not None:
            bootstrap_pvalue = float(candidate)

    degenerate_reasons = _detect_degenerate_reasons(metrics, artifact_dir)

    output_path = Path(output_path)

    lines: list[str] = []
    header = title or DEFAULT_TITLE
    lines.append(f"# {header}")
    lines.append("")

    manifest_payload = _load_manifest(artifact_dir)
    lines.extend(_unsafe_banner(manifest_payload))

    integrity_payload = _load_integrity(artifact_dir)
    integrity_reasons = (
        _integrity_reasons(integrity_payload) if integrity_payload else []
    )
    if integrity_payload and not bool(integrity_payload.get("ok", True)):
        lines.append("## Run marked invalid")
        lines.append("")
        lines.append("Integrity checks failed; results are not interpretable:")
        for reason in integrity_reasons or ["unspecified integrity failure"]:
            lines.append(f"- {reason}")
        lines.append("")

    lines.append("## Performance Snapshot")
    lines.append("")
    lines.extend(_render_metric_table(metrics))
    lines.append("")
    if degenerate_reasons:
        lines.append("## Run is degenerate")
        lines.append("")
        lines.append("This run is not interpretable for performance claims:")
        for reason in degenerate_reasons:
            lines.append(f"- {reason}")
        lines.append("")

    exposure_section = _render_exposure_summary(metrics)
    if exposure_section:
        lines.append("## Exposure Summary")
        lines.append("")
        lines.append(exposure_section)
        lines.append("")

    lines.append("## Visuals")
    lines.append("")
    visuals_rendered = False
    if equity_image and Path(equity_image).exists():
        rel = _relpath(Path(equity_image), output_path)
        lines.append(f"![Equity Curve]({rel})")
        lines.append("")
        visuals_rendered = True
    if bootstrap_image and Path(bootstrap_image).exists():
        rel = _relpath(Path(bootstrap_image), output_path)
        lines.append(f"![Bootstrap Sharpe Histogram]({rel})")
        lines.append("")
        visuals_rendered = True
    if not visuals_rendered:
        lines.append("_No visuals available._")
        lines.append("")

    lines.append("## Bootstrap Reality Check")
    lines.append("")
    if bootstrap_samples:
        sample_series = pd.Series(bootstrap_samples)
        mean = float(sample_series.mean())
        std = float(sample_series.std(ddof=0))
        ci = (
            float(sample_series.quantile(0.025)),
            float(sample_series.quantile(0.975)),
        )
        lines.append(f"- Samples: {len(bootstrap_samples)}")
        lines.append(f"- Mean Sharpe: {mean:.2f}")
        lines.append(f"- Std: {std:.2f}")
        lines.append(f"- 95% CI: [{ci[0]:.2f}, {ci[1]:.2f}]")
        if bootstrap_pvalue is not None:
            lines.append(f"- p-value: {bootstrap_pvalue:.3f}")
    else:
        lines.append("_Bootstrap distribution unavailable._")
    lines.append("")

    lines.append("## Top Exposures")
    lines.append("")
    lines.append(
        _render_exposures(
            exposures_path if exposures_path.exists() else None, top_exposures
        )
    )
    lines.append("")

    factor_section = _render_factor_section(
        artifact_dir=artifact_dir,
        factor_csv=Path(factor_csv) if factor_csv else None,
    )
    if factor_section:
        lines.append(factor_section)
        lines.append("")

    lines.append("## Cost & Metadata Robustness")
    lines.append("")
    cost_section = _render_cost_section(cost_path)
    cost_breakdown = _render_cost_breakdown(cost_path)
    coverage_section = _render_coverage_section(coverage_path)
    if cost_section:
        lines.append(cost_section)
        lines.append("")
    if cost_breakdown:
        lines.append(cost_breakdown)
        lines.append("")
    if coverage_section:
        lines.append(coverage_section)
        lines.append("")
    if not cost_section and not cost_breakdown and not coverage_section:
        lines.append("_Robustness artifacts unavailable._")
        lines.append("")

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return output_path


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", help="Path to an artifacts directory")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Summary output path (default: reports/summaries/flagship_mom.md)",
    )
    parser.add_argument("--title", default=None, help="Optional title override")
    parser.add_argument(
        "--top",
        type=int,
        default=8,
        help="Number of exposures to include in the table (default: 8)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    output_path = generate_summary(
        artifact_dir=args.artifact_dir,
        output_path=args.output,
        title=args.title,
        top_exposures=args.top,
        factor_csv=None,
    )
    print(f"Summary written to {output_path}")


__all__ = ["generate_summary", "main"]


def _render_metric_table(metrics: Mapping[str, object]) -> list[str]:
    entries = {
        "Sharpe_HAC": metrics.get("sharpe_ratio"),
        "MAR": metrics.get("calmar_ratio"),
        "MaxDD": metrics.get("max_drawdown"),
        "Turnover": metrics.get("total_turnover"),
        "RealityCheck_p_value": metrics.get("reality_check_p_value")
        or metrics.get("bootstrap_p_value"),
    }
    lines = ["| Metric | Value |", "| --- | ---:|"]
    for label, value in entries.items():
        lines.append(f"| {label} | {_format_metric(label, value)} |")
    return lines


def _format_metric(label: str, value: object) -> str:
    if value is None:
        return "n/a"
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if label == "MaxDD":
        return f"{numeric * 100:.2f}%"
    if label == "Turnover":
        return f"${numeric:,.0f}"
    if label == "RealityCheck_p_value":
        return f"{numeric:.3f}"
    return f"{numeric:.2f}"


def _render_exposure_summary(metrics: Mapping[str, object]) -> str | None:
    avg_net = metrics.get("avg_exposure")
    avg_gross = metrics.get("avg_gross_exposure")
    max_gross = metrics.get("max_gross_exposure")
    max_net = metrics.get("max_net_exposure")
    if all(val is None for val in (avg_net, avg_gross, max_gross, max_net)):
        return None
    lines = ["| Metric | Value |", "| --- | ---:|"]
    lines.append(f"| Avg net exposure | {_format_pct(_to_float(avg_net))} |")
    lines.append(f"| Avg gross exposure | {_format_pct(_to_float(avg_gross))} |")
    lines.append(f"| Max gross exposure | {_format_pct(_to_float(max_gross))} |")
    lines.append(f"| Max net exposure | {_format_pct(_to_float(max_net))} |")
    lines.append("")
    lines.append("_Exposure time series is recorded in equity_curve.csv._")
    return "\n".join(lines)


def _render_cost_breakdown(cost_path: Path) -> str | None:
    if not cost_path.exists():
        return None
    payload = _load_json(cost_path)
    cost_basis = payload.get("cost_basis") if isinstance(payload, Mapping) else None
    if not cost_basis:
        return None
    commission = _to_float(cost_basis.get("commission_total"))
    slippage = _to_float(cost_basis.get("slippage_total"))
    borrow = _to_float(cost_basis.get("borrow_total"))
    total = _to_float(cost_basis.get("total"))
    lines = ["**Cost breakdown (totals)**", ""]
    lines.append("| Category | Total |")
    lines.append("| --- | ---:|")
    lines.append(f"| Commission | {_format_currency(commission)} |")
    lines.append(f"| Slippage | {_format_currency(slippage)} |")
    lines.append(f"| Borrow | {_format_currency(borrow)} |")
    lines.append(f"| Total | {_format_currency(total)} |")
    return "\n".join(lines)


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _detect_degenerate_reasons(
    metrics: Mapping[str, object], artifact_dir: Path
) -> list[str]:
    reasons: list[str] = []
    num_trades = _to_float(metrics.get("num_trades"))
    if num_trades is None:
        trades_path = _resolve_trades_path(artifact_dir)
        if trades_path:
            num_trades = float(_count_trades(trades_path))
    if num_trades is not None and int(num_trades) == 0:
        reasons.append("num_trades == 0 (no executed trades)")

    turnover = _to_float(metrics.get("total_turnover"))
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


def _relpath(path: Path, output_path: Path) -> str:
    start = output_path.resolve().parent
    try:
        return os.path.relpath(path.resolve(), start)
    except ValueError:
        return str(path.resolve())


def _render_factor_section(
    *,
    artifact_dir: Path | str,
    factor_csv: Path | None,
    hac_lags: int = 5,
) -> str | None:
    if factor_csv is None or not factor_csv.exists():
        return None
    artifact_dir = Path(artifact_dir)
    equity_csv = artifact_dir / "equity_curve.csv"
    if not equity_csv.exists():
        return None

    from .factors import compute_factor_regression

    try:
        results = compute_factor_regression(equity_csv, factor_csv, hac_lags=hac_lags)
    except Exception:  # pragma: no cover - fallback when regression fails
        return None
    if not results:
        return None

    lines = ["## Factor Regression (FF3 sample)", ""]
    lines.append("| Factor | Beta | t-stat |")
    lines.append("| --- | ---:| ---:|")
    for row in results:
        lines.append(f"| {row.name} | {row.beta:.4f} | {row.t_stat:.2f} |")
    lines.append("")
    lines.append(
        "_Computed against `data/factors/ff3_sample.csv` using Newey-West standard errors._"
    )
    return "\n".join(lines)


def _render_cost_section(cost_path: Path) -> str | None:
    if not cost_path.exists():
        return None
    payload = _load_json(cost_path)
    grid = payload.get("grid") if isinstance(payload, Mapping) else None
    if not grid:
        return "_Cost sensitivity unavailable._"

    lines = ["**Cost sensitivity (ex-post scaling of recorded costs)**", ""]
    lines.append(
        "| Multiplier | Sharpe | MaxDD | CAGR | MAR | Cost drag (bps/yr) |"
    )
    lines.append("| --- | ---:| ---:| ---:| ---:| ---:|")
    for row in grid:
        lines.append(
            "| "
            f"{float(row.get('multiplier', 0.0)):.2f} | "
            f"{float(row.get('sharpe_ratio', 0.0)):.2f} | "
            f"{_format_pct(row.get('max_drawdown'))} | "
            f"{_format_pct(row.get('cagr'))} | "
            f"{float(row.get('mar', 0.0)):.2f} | "
            f"{float(row.get('cost_drag_bps_per_year', 0.0)):.1f} |"
        )
    note = payload.get("description")
    if note:
        lines.append("")
        lines.append(f"_{note}_")
    return "\n".join(lines)


def _render_coverage_section(coverage_path: Path) -> str | None:
    if not coverage_path.exists():
        return None
    payload = _load_json(coverage_path)
    coverage = payload.get("coverage") if isinstance(payload, Mapping) else None

    lines = ["**Metadata coverage (liquidity/borrow inputs)**", ""]
    if not coverage:
        lines.append("_Coverage unavailable._")
        note = payload.get("note")
        if note:
            lines.append("")
            lines.append(f"_{note}_")
        return "\n".join(lines)

    rows = [
        ("Notional with ADV", coverage.get("pct_notional_with_adv")),
        ("Notional with spread_bps", coverage.get("pct_notional_with_spread")),
        (
            "Short notional with borrow fee",
            coverage.get("pct_short_notional_with_borrow_fee"),
        ),
    ]
    lines.append("| Metric | Value |")
    lines.append("| --- | ---:|")
    for label, value in rows:
        lines.append(f"| {label} | {_format_pct(value)} |")

    top = payload.get("fallback_top") or []
    if top:
        lines.append("")
        lines.append("Top fallback symbols (trade counts):")
        for entry in top:
            lines.append(
                f"- {entry.get('symbol')}: "
                f"adv_missing={entry.get('missing_adv_trades', 0)}, "
                f"spread_missing={entry.get('missing_spread_trades', 0)}, "
                f"borrow_missing={entry.get('missing_borrow_trades', 0)}"
            )

    note = payload.get("note")
    if note:
        lines.append("")
        lines.append(f"_{note}_")
    return "\n".join(lines)

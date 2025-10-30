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

    output_path = Path(output_path)

    lines: list[str] = []
    header = title or DEFAULT_TITLE
    lines.append(f"# {header}")
    lines.append("")

    lines.append("## Performance Snapshot")
    lines.append("")
    lines.extend(_render_metric_table(metrics))
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

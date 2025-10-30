"""Markdown summary generator for Microalpha artifacts."""

from __future__ import annotations

import argparse
import json
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

    lines: list[str] = []
    header = title or DEFAULT_TITLE
    lines.append(f"# {header}")
    lines.append("")

    lines.append("## Headline Metrics")
    lines.append("")
    sharpe = metrics.get("sharpe_ratio")
    sortino = metrics.get("sortino_ratio")
    cagr = metrics.get("cagr")
    max_dd = metrics.get("max_drawdown")
    turnover = metrics.get("total_turnover")
    hac_lags = metrics.get("sharpe_hac_lags")
    num_trades = metrics.get("num_trades")
    win_rate = metrics.get("win_rate")

    headline = [
        f"- Sharpe: {sharpe:.2f}" if sharpe is not None else "- Sharpe: n/a",
        f"- Sortino: {sortino:.2f}" if sortino is not None else "- Sortino: n/a",
        f"- CAGR: {_format_pct(cagr if isinstance(cagr, (float, int)) else None)}",
        f"- Max Drawdown: {_format_pct(max_dd if isinstance(max_dd, (float, int)) else None)}",
        f"- Turnover: ${turnover:,.0f}" if turnover is not None else "- Turnover: n/a",
    ]
    if hac_lags:
        headline.append(f"- HAC Lags: {int(hac_lags)}")
    if num_trades is not None:
        headline.append(f"- Trades: {int(num_trades)}")
    if win_rate is not None:
        headline.append(f"- Win Rate: {win_rate * 100:.1f}%")
    lines.extend(headline)
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
    )
    print(f"Summary written to {output_path}")


__all__ = ["generate_summary", "main"]

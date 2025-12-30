#!/usr/bin/env python3
"""Convenience wrapper for running FF3 regressions on Microalpha artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from microalpha.reporting.factors import compute_factor_regression


def _format(results, meta) -> str:
    lines = ["| Factor | Beta | t-stat |", "| --- | ---:| ---:|"]
    for row in results:
        lines.append(f"| {row.name} | {row.beta:.4f} | {row.t_stat:.2f} |")
    start = meta.overlap_start.date().isoformat() if meta.overlap_start else "n/a"
    end = meta.overlap_end.date().isoformat() if meta.overlap_end else "n/a"
    resample_note = ""
    if meta.resampled:
        rule = f", rule={meta.resample_rule}" if meta.resample_rule else ""
        resample_note = f" (resampled returns{rule})"
    lines.append("")
    lines.append(
        "_Frequency: "
        f"returns {meta.returns_freq}, factors {meta.factors_freq}; "
        f"overlap {start} to {end}; n_obs={meta.n_obs}{resample_note}._"
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", type=Path, help="Artifact directory with equity_curve.csv")
    parser.add_argument(
        "--factors",
        type=Path,
        default=Path("data/factors/ff3_sample.csv"),
        help="Factor CSV path (default: data/factors/ff3_sample.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional markdown file to write the regression table to",
    )
    parser.add_argument("--hac-lags", type=int, default=5)
    parser.add_argument(
        "--allow-resample",
        action="store_true",
        help="Allow resampling returns to factor frequency (compounded).",
    )
    parser.add_argument(
        "--resample-rule",
        default=None,
        help="Optional pandas resample rule for returns (e.g., 'M', 'W-FRI').",
    )
    args = parser.parse_args()

    equity_csv = args.artifact_dir / "equity_curve.csv"
    if not equity_csv.exists():
        raise SystemExit(f"equity_curve.csv not found in {args.artifact_dir}")
    if not args.factors.exists():
        raise SystemExit(f"Factor CSV not found: {args.factors}")

    output = compute_factor_regression(
        equity_csv,
        args.factors,
        hac_lags=args.hac_lags,
        allow_resample=args.allow_resample,
        resample_rule=args.resample_rule,
    )
    table = _format(output.results, output.meta)
    print(table)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(table + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

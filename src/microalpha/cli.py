"""Command line entrypoints for microalpha."""

from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import platform
import sys
import time
from pathlib import Path

from microalpha.reporting.robustness import write_robustness_artifacts
from microalpha.reporting.summary import generate_summary
from microalpha.reporting.tearsheet import (
    DEFAULT_BOOTSTRAP_NAME,
    DEFAULT_EQUITY_NAME,
    render_tearsheet,
)

from .runner import run_from_config
from .walkforward import run_walk_forward


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("-c", "--config", required=True)
    run_parser.add_argument(
        "--out",
        dest="outdir",
        default=None,
        help="Override artifacts output directory root",
    )
    run_parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable cProfile and write to <artifacts_dir>/profile.pstats",
    )

    wfv_parser = subparsers.add_parser("wfv")
    wfv_parser.add_argument("-c", "--config", required=True)
    wfv_parser.add_argument(
        "--out",
        dest="outdir",
        default=None,
        help="Override artifacts output directory root",
    )
    wfv_parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable cProfile and write to <artifacts_dir>/profile.pstats",
    )
    wfv_parser.add_argument(
        "--reality-check-method",
        choices=["stationary", "circular", "iid"],
        help="Bootstrap method for walk-forward reality check",
    )
    wfv_parser.add_argument(
        "--reality-check-block-len",
        type=int,
        dest="reality_check_block_len",
        help="Override block length for walk-forward bootstrap (default Politis-White)",
    )

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument(
        "--artifact-dir",
        required=True,
        help="Existing artifact directory produced by a run or walk-forward job.",
    )
    report_parser.add_argument(
        "--summary-out",
        default=str(Path("reports/summaries/flagship_mom.md")),
        help="Markdown output path (default: reports/summaries/flagship_mom.md).",
    )
    report_parser.add_argument(
        "--tearsheet-out",
        default=None,
        help=(
            "PNG output path for the equity curve plot "
            f"(default: <artifact>/{DEFAULT_EQUITY_NAME})."
        ),
    )
    report_parser.add_argument(
        "--bootstrap-out",
        default=None,
        help=(
            "PNG output path for the bootstrap histogram "
            f"(default: <artifact>/{DEFAULT_BOOTSTRAP_NAME})."
        ),
    )
    report_parser.add_argument(
        "--title",
        default=None,
        help="Optional title override for both summary and plot.",
    )
    report_parser.add_argument(
        "--top-exposures",
        type=int,
        default=8,
        help="Number of exposures to display in the summary table (default: 8).",
    )

    subparsers.add_parser("info")

    args = parser.parse_args()

    if args.cmd == "info":
        print(json.dumps(_build_info(), indent=2))
        return

    t0 = time.time()

    if args.cmd == "run":
        if getattr(args, "profile", False):
            import os as _os

            _os.environ["MICROALPHA_PROFILE"] = "1"
        if args.outdir:
            manifest = run_from_config(args.config, override_artifacts_dir=args.outdir)
        else:
            manifest = run_from_config(args.config)
    elif args.cmd == "wfv":
        if getattr(args, "profile", False):
            import os as _os

            _os.environ["MICROALPHA_PROFILE"] = "1"
        run_kwargs = {
            "reality_check_method": getattr(args, "reality_check_method", None),
            "reality_check_block_len": getattr(args, "reality_check_block_len", None),
        }
        if args.outdir:
            manifest = run_walk_forward(
                args.config, override_artifacts_dir=args.outdir, **run_kwargs
            )
        else:
            manifest = run_walk_forward(args.config, **run_kwargs)
    elif args.cmd == "report":
        artifact_dir = Path(args.artifact_dir).resolve()
        if not artifact_dir.exists():
            raise SystemExit(f"Artifact directory not found: {artifact_dir}")

        metrics_path = artifact_dir / "metrics.json"
        bootstrap_path = artifact_dir / "bootstrap.json"
        equity_csv = artifact_dir / "equity_curve.csv"
        if not equity_csv.exists():
            raise SystemExit("Artifact directory missing equity_curve.csv")

        equity_plot_path = (
            Path(args.tearsheet_out).resolve()
            if args.tearsheet_out
            else (artifact_dir / DEFAULT_EQUITY_NAME)
        )
        bootstrap_plot_path = (
            Path(args.bootstrap_out).resolve()
            if args.bootstrap_out
            else (
                (equity_plot_path.parent if equity_plot_path.suffix else equity_plot_path)
                / DEFAULT_BOOTSTRAP_NAME
            )
        )

        outputs = render_tearsheet(
            equity_csv=equity_csv,
            bootstrap_json=bootstrap_path if bootstrap_path.exists() else None,
            output_path=equity_plot_path,
            bootstrap_output=bootstrap_plot_path,
            metrics_path=metrics_path if metrics_path.exists() else None,
            title=args.title,
        )

        default_factor_csv = Path("data/factors/ff3_sample.csv")
        factor_csv_arg: Path | None = None
        if default_factor_csv.exists() and "sample_wfv" in str(artifact_dir):
            factor_csv_arg = default_factor_csv

        summary_path = generate_summary(
            artifact_dir=artifact_dir,
            output_path=args.summary_out,
            title=args.title,
            top_exposures=args.top_exposures,
            equity_image=outputs.get("equity_curve"),
            bootstrap_image=outputs.get("bootstrap_hist"),
            factor_csv=factor_csv_arg,
        )

        robustness = write_robustness_artifacts(artifact_dir)

        manifest = {
            "artifact_dir": str(artifact_dir),
            "summary_path": str(summary_path.resolve()),
            "equity_curve_path": str(outputs["equity_curve"]),
            "bootstrap_hist_path": str(outputs["bootstrap_hist"]),
            "cost_sensitivity_path": str(robustness.cost_sensitivity),
            "metadata_coverage_path": str(robustness.metadata_coverage),
        }
    else:
        raise SystemExit(f"Unknown command: {args.cmd}")

    manifest["runtime_sec"] = round(time.time() - t0, 3)
    manifest["version"] = _resolve_version()

    print(json.dumps(manifest, indent=2))


def _build_info() -> dict[str, str]:
    info = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "microalpha": _resolve_version(),
        "executable": sys.executable,
    }
    return info


def _resolve_version() -> str:
    try:
        return md.version("microalpha")
    except md.PackageNotFoundError:
        return "unknown"


if __name__ == "__main__":
    main()

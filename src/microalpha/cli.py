"""Command line entrypoints for microalpha."""

from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import platform
import sys
import time

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
    else:
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

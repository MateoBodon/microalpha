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

    wfv_parser = subparsers.add_parser("wfv")
    wfv_parser.add_argument("-c", "--config", required=True)

    subparsers.add_parser("info")

    args = parser.parse_args()

    if args.cmd == "info":
        print(json.dumps(_build_info(), indent=2))
        return

    t0 = time.time()

    if args.cmd == "run":
        manifest = run_from_config(args.config)
    else:
        manifest = run_walk_forward(args.config)

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

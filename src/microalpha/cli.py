"""Command line entrypoints for microalpha."""

from __future__ import annotations

import argparse
import json
import time
import importlib.metadata as md

from .runner import run_from_config
from .walkforward import run_walk_forward


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("-c", "--config", required=True)

    wfv_parser = subparsers.add_parser("wfv")
    wfv_parser.add_argument("-c", "--config", required=True)

    args = parser.parse_args()
    t0 = time.time()

    if args.cmd == "run":
        manifest = run_from_config(args.config)
    else:
        manifest = run_walk_forward(args.config)

    manifest["runtime_sec"] = round(time.time() - t0, 3)
    try:
        manifest["version"] = md.version("microalpha")
    except md.PackageNotFoundError:
        manifest["version"] = "unknown"

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

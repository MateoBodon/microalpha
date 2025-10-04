"""Compatibility wrapper for invoking ``microalpha wfv`` directly."""

from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import time

from microalpha.walkforward import run_walk_forward


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=True)
    args = parser.parse_args()

    start = time.time()
    manifest = run_walk_forward(args.config)
    manifest["runtime_sec"] = round(time.time() - start, 3)
    try:
        manifest["version"] = md.version("microalpha")
    except md.PackageNotFoundError:
        manifest["version"] = "unknown"

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

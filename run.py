"""Compatibility wrapper for invoking ``microalpha run`` directly."""

from __future__ import annotations

import argparse
import json
import time
import importlib.metadata as md

from microalpha.runner import run_from_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=True)
    args = parser.parse_args()

    start = time.time()
    manifest = run_from_config(args.config)
    manifest["runtime_sec"] = round(time.time() - start, 3)
    try:
        manifest["version"] = md.version("microalpha")
    except md.PackageNotFoundError:
        manifest["version"] = "unknown"

    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

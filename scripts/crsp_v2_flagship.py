#!/usr/bin/env python3
"""Audit or build the predeclared CRSP-v2 flagship research panel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from microalpha.research.crsp_v2 import audit_source_protocol
from microalpha.research.crsp_v2_panel import build_monthly_panel

DEFAULT_PROTOCOL = Path("docs/strategy/MICROALPHA_FLAGSHIP_20260710.yaml")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--protocol", type=Path, default=DEFAULT_PROTOCOL, help="Predeclared YAML"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "audit", help="Verify hashes, manifests, partitions, byte sizes, and headers"
    )

    selection = subparsers.add_parser(
        "build-selection-panel",
        help="Build selection panel without reading holdout outcome rows",
    )
    selection.add_argument("--output", type=Path, required=True)
    selection.add_argument("--memory-limit", default="4GB")
    selection.add_argument("--temp-directory", type=Path, default=None)

    final = subparsers.add_parser(
        "build-final-panel",
        help="Build full panel after validating a protocol-bound frozen model receipt",
    )
    final.add_argument("--output", type=Path, required=True)
    final.add_argument("--frozen-model", type=Path, required=True)
    final.add_argument("--memory-limit", default="4GB")
    final.add_argument("--temp-directory", type=Path, default=None)
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.command == "audit":
        payload = audit_source_protocol(args.protocol)
    elif args.command == "build-selection-panel":
        payload = build_monthly_panel(
            args.protocol,
            args.output,
            stage="selection",
            memory_limit=args.memory_limit,
            temp_directory=args.temp_directory,
        )
    else:
        payload = build_monthly_panel(
            args.protocol,
            args.output,
            stage="final",
            frozen_model_path=args.frozen_model,
            memory_limit=args.memory_limit,
            temp_directory=args.temp_directory,
        )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run the preregistered CRSP-v2 distinct residual-momentum family."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from microalpha.research.crsp_v2_distinct import run_distinct_family


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--base-protocol", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--previous-selection-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_distinct_family(
        args.contract,
        args.base_protocol,
        args.panel,
        args.previous_selection_manifest,
        args.output_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run the preregistered annual QVPI fundamental mechanism."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from microalpha.research.crsp_v2_fundamental import run_fundamental_composite


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_fundamental_composite(args.contract, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

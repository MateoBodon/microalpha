#!/usr/bin/env python3
"""Execute the frozen CRSP-v2 validation selection and baseline suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from microalpha.research.crsp_v2_selection import run_selection


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_selection(args.protocol, args.panel, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

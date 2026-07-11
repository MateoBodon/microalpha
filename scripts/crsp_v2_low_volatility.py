#!/usr/bin/env python3
"""Run the preregistered CRSP-v2 low-volatility mechanism."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from microalpha.research.crsp_v2_low_volatility import run_low_volatility


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--base-protocol", type=Path, required=True)
    parser.add_argument("--panel", type=Path, required=True)
    parser.add_argument("--momentum-result-manifest", type=Path, required=True)
    parser.add_argument("--residual-result-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_low_volatility(
        args.contract,
        args.base_protocol,
        args.panel,
        args.momentum_result_manifest,
        args.residual_result_manifest,
        args.output_dir,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

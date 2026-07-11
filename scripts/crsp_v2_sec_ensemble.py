#!/usr/bin/env python3
"""Run the frozen SEC cash-earnings/classic-momentum ensemble once."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from microalpha.research.crsp_v2 import CRSPV2Error
from microalpha.research.crsp_v2_sec_ensemble import (
    run_sec_cash_classic_momentum_ensemble,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--execute-frozen-development-once",
        action="store_true",
        help="required acknowledgement of the admitted one-shot development run",
    )
    args = parser.parse_args()
    if not args.execute_frozen_development_once:
        raise CRSPV2Error("Frozen ensemble development is locked")
    result = run_sec_cash_classic_momentum_ensemble(
        args.contract, args.output_dir, development_lane_admitted=True
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

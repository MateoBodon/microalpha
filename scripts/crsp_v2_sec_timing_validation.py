#!/usr/bin/env python3
"""Run the frozen 2017-2022 SEC reporting-timeliness validation once."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from microalpha.research.crsp_v2 import CRSPV2Error
from microalpha.research.crsp_v2_sec_timing import (
    run_sec_timing_frozen_validation,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--execute-frozen-2017-2022-validation",
        action="store_true",
        help="required acknowledgement of the separately admitted one-shot run",
    )
    args = parser.parse_args()
    if not args.execute_frozen_2017_2022_validation:
        raise CRSPV2Error(
            "SEC-timing validation is locked; pass the explicit one-shot "
            "validation acknowledgement only inside its admitted lifecycle"
        )
    result = run_sec_timing_frozen_validation(
        args.contract, args.output_dir, validation_lane_admitted=True
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

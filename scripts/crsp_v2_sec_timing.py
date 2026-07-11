#!/usr/bin/env python3
"""Run frozen SEC reporting-timeliness metadata coverage without outcomes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from microalpha.research.crsp_v2 import CRSPV2Error
from microalpha.research.crsp_v2_sec_timing import (
    run_sec_timing_return_free_coverage,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--execute-full-return-free-coverage",
        action="store_true",
        help=(
            "required acknowledgement that the 3,106-CIK metadata extraction "
            "has been separately scheduled within memory capacity"
        ),
    )
    args = parser.parse_args()
    if not args.execute_full_return_free_coverage:
        raise CRSPV2Error(
            "Full SEC-timing coverage is locked; pass "
            "--execute-full-return-free-coverage only after separate memory-lane "
            "admission"
        )
    result = run_sec_timing_return_free_coverage(
        args.contract, args.output_dir, memory_lane_admitted=True
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

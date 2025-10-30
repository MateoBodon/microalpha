#!/usr/bin/env python3
"""Wrapper around microalpha.reporting.summary for backward compatibility."""

from __future__ import annotations

from microalpha.reporting.summary import generate_summary, main

if __name__ == "__main__":
    main()

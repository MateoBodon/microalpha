#!/usr/bin/env python3
"""Wrapper around microalpha.reporting.tearsheet for backward compatibility."""

from __future__ import annotations

from microalpha.reporting.tearsheet import main, render_tearsheet

if __name__ == "__main__":
    main()

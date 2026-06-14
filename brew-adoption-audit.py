#!/usr/bin/env python3
"""Compatibility wrapper for source-tree execution."""

from brew_adoption_audit.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Retired verification lifecycle. Use active-task checks and memory-only closeout."""

import sys


def main():
    print("The old Ending verification/repair lifecycle is retired. Verify inside the active task; use project-memory-skill/scripts/ending_memory.py for memory-only closeout.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

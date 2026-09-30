#!/usr/bin/env python3
"""Validate workflow entry metadata and linked references."""

import argparse
import json
import re
from pathlib import Path


def validate(skill_dir):
    root = Path(skill_dir).resolve().parent
    failures = []
    for name in ("workflow-skill", "verify-skill", "project-memory-skill"):
        entry = root / name / "SKILL.md"
        if not entry.is_file():
            failures.append(f"missing {name} entry")
            continue
        text = entry.read_text(encoding="utf-8")
        if not text.startswith("---\n") or f"name: {name}" not in text or "description:" not in text:
            failures.append(f"invalid {name} metadata")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" not in target and not target.startswith("#") and not (entry.parent / target.split("#")[0]).exists():
                failures.append(f"broken {name} reference: {target}")
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    failures = validate(args.skill_dir)
    print(json.dumps({"status": "fail" if failures else "pass", "failures": failures}))
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())

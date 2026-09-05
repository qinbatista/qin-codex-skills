#!/usr/bin/env python3
"""Validate current workflow structure and execution ownership."""

import argparse
import json
import re
from pathlib import Path


def can_show_main_result(requested_work_done):
    return bool(requested_work_done)


def validate_trace(name, trace, skills_root=None):
    failures = []
    result_seen = False
    for node in trace:
        phase = node.get("phase", "result")
        purpose = node.get("purpose", "")
        if phase == "ending" and purpose not in {"memory", "memory_only", "memory_closeout"}:
            failures.append("Ending may only summarize memory")
        if phase == "ending" and any(node.get(field) for field in ("command", "commands", "checks", "launch_tool", "repair")):
            failures.append("Ending cannot execute checks, commands, or task launches")
        if (purpose == "verify" or node.get("skill") == "verify-skill") and result_seen:
            failures.append("verification belongs before task completion")
        if node.get("skill_governed") or node.get("skill") or node.get("skills") or phase == "ending":
            if not node.get("selected_pair"):
                failures.append("governed work requires the selected model and effort")
            elif f"{node.get('model')}|{node.get('effort')}" != node["selected_pair"]:
                failures.append("governed work changed the selected model or effort")
        if node.get("whole_project") and not node.get("whole_project_requested"):
            failures.append("whole-project verification requires requested scope")
        if node.get("id") == "main-result":
            result_seen = True
    return {"name": name, "status": "fail" if failures else "pass", "failures": failures}


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

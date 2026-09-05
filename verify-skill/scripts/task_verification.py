#!/usr/bin/env python3
"""Choose evidence for the active task; never launch a project or another task."""

import argparse
import json


def verification_plan(change_kind, *, requested=False, whole_project_requested=False):
    scopes = {
        "value": [],
        "logic": ["changed_behavior", "failure_boundary"],
        "structure": ["affected_contract", "direct_consumers"],
        "ui": ["rendered_state", "affected_interaction", "desktop_and_narrow_layout", "containment_and_readability"],
        "presentation": ["rendered_page_or_slide", "intended_reading_size", "containment_and_readability"],
        "data": ["bounded_input_output", "state_readback"],
        "installation": ["managed_target_readback", "preserved_user_content"],
    }
    if change_kind not in scopes:
        raise ValueError("unknown change kind")
    checks = scopes[change_kind] or (["changed_value_readback"] if requested else [])
    return {
        "owner": "active_task",
        "required": bool(checks),
        "checks": checks,
        "scope": "whole_project_authorized" if whole_project_requested else "affected_behavior_only",
        "whole_project_allowed": bool(whole_project_requested),
        "ending_checks": [],
        "skip_reason": "simple_value_only" if not checks else "",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("change_kind", choices=("value", "logic", "structure", "ui", "presentation", "data", "installation"))
    parser.add_argument("--requested", action="store_true")
    parser.add_argument("--whole-project-requested", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verification_plan(args.change_kind, requested=args.requested, whole_project_requested=args.whole_project_requested)))


if __name__ == "__main__":
    main()

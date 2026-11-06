#!/usr/bin/env python3
"""Request one inline closeout continuation for a Codex Stop event."""

import json
import sys


def closeout_decision(event):
    """Use Codex's continuation guard; never create chats or touch project data."""
    if not isinstance(event, dict) or event.get("hook_event_name") != "Stop" or not isinstance(event.get("stop_hook_active"), bool):
        raise ValueError("expected a Codex Stop event with a boolean stop_hook_active")
    if event["stop_hook_active"]:
        return {}
    return {
        "decision": "block",
        "reason": "Before finishing this turn, check the current task's applicable inline closeout instructions. Complete or verify any still-needed project cleanup, scoped Obsidian memory, and AI-index maintenance in this chat. Respect read-only and hold requests, project ownership, and first-index consent; do not invent memory or create an Ending chat. Report concrete pending failures, then finish.",
    }


def main():
    print(json.dumps(closeout_decision(json.load(sys.stdin))))


if __name__ == "__main__":
    main()

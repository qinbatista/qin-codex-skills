#!/usr/bin/env python3
"""Ending memory uses the active selected-model context; no task launcher."""


def resolve_ending_backend(capabilities=None):
    return {"status": "inline", "reason": "memory_only", "selected": {"backend": "active_task", "launch_tool": None}, "terminal_lifecycle": False}

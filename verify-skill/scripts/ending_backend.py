#!/usr/bin/env python3
"""Select an independent Ending backend without weakening projectless lifecycle proof."""

from dataclasses import dataclass


BACKEND_ORDER = ("projectless_host", "standard_subagent", "local_codex_exec")


@dataclass(frozen=True)
class EndingBackend:
    backend_id: str
    terminal_lifecycle: bool
    independent_context: bool
    launch_tool: object

    def launch_plan(self, available):
        return {"backend": self.backend_id, "available": bool(available), "terminal_lifecycle": self.terminal_lifecycle, "independent_context": self.independent_context, "launch_tool": self.launch_tool, "producer_context_reuse": False}


class ProjectlessHostEndingBackend(EndingBackend):
    def __init__(self):
        super().__init__("projectless_host", True, True, "codex_app__create_thread")


class StandardSubagentEndingBackend(EndingBackend):
    def __init__(self):
        super().__init__("standard_subagent", False, True, "standard_subagent")


class LocalCodexExecEndingBackend(EndingBackend):
    def __init__(self):
        super().__init__("local_codex_exec", False, True, "codex_exec")


BACKENDS = {backend.backend_id: backend for backend in (ProjectlessHostEndingBackend(), StandardSubagentEndingBackend(), LocalCodexExecEndingBackend())}


def resolve_ending_backend(capabilities=None):
    """Return the first available backend, preserving terminal-proof semantics."""
    availability = {"projectless_host": True, "standard_subagent": False, "local_codex_exec": False} if capabilities is None else {name: bool(capabilities.get(name, False)) for name in BACKEND_ORDER}
    candidates = [BACKENDS[name].launch_plan(availability[name]) for name in BACKEND_ORDER]
    selected = next((candidate for candidate in candidates if candidate["available"]), None)
    if selected is None:
        return {"status": "blocked", "reason": "no_independent_ending_backend_available", "selected": None, "candidates": candidates, "terminal_lifecycle": False}
    if selected["terminal_lifecycle"]:
        return {"status": "launchable", "reason": "projectless_host_available", "selected": selected, "candidates": candidates, "terminal_lifecycle": True}
    return {"status": "blocked", "reason": "independent_evidence_backend_cannot_acknowledge_global_projectless_lifecycle", "selected": selected, "candidates": candidates, "terminal_lifecycle": False}

#!/usr/bin/env python3
"""Keep skill-governed work on the user's selected model and reasoning effort."""

from collections.abc import Mapping

ROUTING_ONLY_SKILLS = {"task-analyze-skill", "workflow-skill"}
MEMORY_OPERATIONS = {"memory", "memory-update", "memory-summary", "record-memory", "summarize-memory"}
VALID_EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"}


def _value(spec, key, default=None):
    return spec.get(key, default) if isinstance(spec, Mapping) else getattr(spec, key, default)


def governing_skills(spec):
    """The planner supplies actual governing skills, not incidental tool names."""
    values = []
    for key in ("governing_skills", "governing_skill", "required_skills", "skills"):
        value = _value(spec, key, []) or []
        values.extend([value] if isinstance(value, str) else value)
    for key in ("skill", "owning_skill"):
        value = _value(spec, key)
        if value:
            values.append(value)
    return sorted({str(value) for value in values if value and value not in ROUTING_ONLY_SKILLS and value not in {"none", "general"}})


def uses_shared_ui_rules(spec):
    surfaces = {"ui", "visual", "website", "dashboard", "pdf", "report", "presentation", "slides"}
    return bool(_value(spec, "visual_presentation", False) or _value(spec, "task_type") in surfaces or _value(spec, "artifact") in {"pdf", "slides", "presentation", "webpage"})


def uses_selected_model(spec):
    if uses_shared_ui_rules(spec):
        return True
    if _value(spec, "phase") == "ending" or _value(spec, "memory_update", False):
        return True
    if _value(spec, "operation") in MEMORY_OPERATIONS or _value(spec, "task_type") == "memory":
        return True
    # An independence claim cannot override a named governing skill or inherited
    # skill constraint: a shell helper inside UI/code work keeps the same pair.
    if governing_skills(spec) or _value(spec, "skill_governed", False):
        return True
    condition = _value(spec, "routing_condition", {}) or {}
    return bool(governing_skills(condition) or uses_shared_ui_rules(condition))


def selected_pair(model, effort):
    if not isinstance(model, str) or not model.strip() or model == "unknown" or "|" in model:
        raise ValueError("selected_model_required")
    if effort not in VALID_EFFORTS:
        raise ValueError("selected_effort_required")
    return f"{model}|{effort}"


def recommendation(model, effort, baseline=None):
    pair = selected_pair(model, effort)
    result = dict(baseline or {})
    result.update({"selected_pair": pair, "selected_model": model, "selected_effort": effort,
                   "attempt_pair": pair, "entry_pair": pair, "entry_anchor_pair": pair,
                   "active_fallback_pair": None, "trial": False, "attempt_trial": False,
                   "reason": "user_selected_skill_model", "attempt_reason": "user_selected_skill_model",
                   "calibration_state": "user_selected", "attempt_calibration_state": "user_selected",
                   "selection_basis": "user_selected", "switch_direction": "no_switch",
                   "switch_change": "no_switch", "source": "user_selection",
                   "memory_available": False, "specificity": "user_selection",
                   "matched_records": 0, "project_key": None, "model_locked": True})
    return result


def bind_node(node, model, effort):
    """Called before validation and again at execution, including direct run_node."""
    if uses_selected_model(node) and node.get("execution_kind") != "deterministic-source-read":
        selected_pair(model, effort)
        node.update({"model": model, "effort": effort, "selection_basis": "user_selected",
                     "allow_fallback": [], "fallback_policy": "none", "trial": False,
                     "model_locked": True})
        node.pop("priority_producer", None)
    return node


def execution_guidance(spec):
    skills = governing_skills(spec)
    scope = _value(spec, "project_root") or _value(spec, "_project_root") or _value(spec, "routing_project_root")
    prefix = f"Governing skills: {', '.join(skills)}. " if skills else ""
    project = f"Active project: {scope}. " if scope else "Use the active project identity. "
    ui_reference = "For any UI or visual presentation, including websites, PDF reports, documents, and slide presentations, read and apply workflow-skill/references/readable-ui.md from the installed Skills root, even without code changes or when another skill owns rendering. "
    return (prefix + project + ui_reference + "Read only relevant existing project/module memory before work; missing memory is optional and must not block execution. "
            "Do not use another project's memory. Preserve the assigned model and effort for governing skills, including helper scripts. "
            "Run scripts and tests without opening or focusing windows: use portable Python, hidden Windows subprocess options, and application-native headless modes; preserve required platform branches and captured output. "
            "Verify meaningful or complex changes inside this active task with the smallest relevant behavior check; skip verification for simple value-only edits. "
            "Do not start a whole project or full build unless the user requests it. Ending only summarizes durable decisions and changes into scoped memory; it does not verify or repair.")

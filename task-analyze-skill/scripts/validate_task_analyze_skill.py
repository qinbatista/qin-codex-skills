#!/usr/bin/env python3
"""Check the routing package's files, syntax and selected-model contract."""

import argparse
import ast
import importlib.util
import json
import re
from pathlib import Path


def validate(skill_dir, models_cache_path=None, global_agents_path=None, global_skills_root=None, global_hooks_path=None):
    root = Path(skill_dir).resolve()
    failures = []
    for path in root.glob("scripts/*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        except (OSError, SyntaxError) as error:
            failures.append(f"{path.name}: {error}")
    for path in [root / "SKILL.md", root / "assets/global-agents-entry-rule.md", *root.glob("references/*.md")]:
        if not path.is_file():
            failures.append(f"missing {path.name}")
            continue
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            if not (path.parent / target.split("#", 1)[0]).exists():
                failures.append(f"{path.name}: broken link {target}")
    policy_path = root / "scripts/selected_model_policy.py"
    if policy_path.exists():
        spec = importlib.util.spec_from_file_location("validate_selected_policy", policy_path)
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        for model, effort in [("gpt-5.6-luna", "max"), ("gpt-6-astra", "ultra")]:
            node = {"skill": "code-skill", "model": "gpt-5.3-codex-spark", "effort": "low", "allow_fallback": ["gpt-5.6-sol|high"]}
            policy.bind_node(node, model, effort)
            if (node["model"], node["effort"], node["allow_fallback"]) != (model, effort, []):
                failures.append("governed task does not preserve the selected pair")
    else:
        failures.append("missing selected-model enforcement")
    return {"status": "fail" if failures else "pass", "failures": failures, "plans": [], "graduated": []}


def validate_result_model_disclosure(disclosure_text):
    path = Path(__file__).with_name("model_identity_disclosure.py")
    spec = importlib.util.spec_from_file_location("optional_model_disclosure", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_disclosure(disclosure_text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--models-cache", type=Path)
    parser.add_argument("--global-agents", type=Path)
    parser.add_argument("--global-skills-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = validate(args.skill_dir, args.models_cache, args.global_agents, args.global_skills_root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return int(bool(result["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())

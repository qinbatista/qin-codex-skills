#!/usr/bin/env python3
"""Detect high-confidence violations of the Python direct-code rules."""

import argparse
import ast
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qin_rule_guard_common import deduplicate_violations, filter_violations, git_added_lines, violation


def python_call_from_only_statement(function_node):
    if len(function_node.body) != 1:
        return None
    statement = function_node.body[0]
    value = statement.value if isinstance(statement, (ast.Expr, ast.Return)) else None
    if isinstance(value, ast.Await):
        value = value.value
    return value if isinstance(value, ast.Call) else None


def python_is_self_call(call, function_name):
    if isinstance(call.func, ast.Name):
        return call.func.id == function_name
    return isinstance(call.func, ast.Attribute) and call.func.attr == function_name and isinstance(call.func.value, ast.Name) and call.func.value.id in {"self", "cls"}


def python_parameter_names(function_node):
    positional = [*function_node.args.posonlyargs, *function_node.args.args]
    names = [argument.arg for argument in positional if argument.arg not in {"self", "cls"}]
    names.extend(argument.arg for argument in function_node.args.kwonlyargs)
    return names


def python_argument_names(call):
    if call.keywords or any(not isinstance(argument, ast.Name) for argument in call.args):
        return None
    return [argument.id for argument in call.args]


def has_semantic_boundary(lines, line_number):
    start = max(0, line_number - 3)
    return any(re.search(r"^\s*#\s*code-gate:\s*semantic-boundary=\s*\S", line) for line in lines[start:line_number])


def python_violations(text):
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        return [violation("parse-error", error.lineno or 1, "Python source cannot be parsed by the active project interpreter.")]
    lines = text.splitlines()
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "_" and isinstance(node.ctx, ast.Store):
            violations.append(violation("discard-binding", node.lineno, "Do not bind or unpack a produced value into _."))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            call = python_call_from_only_statement(node)
            if call is None:
                continue
            if python_is_self_call(call, node.name):
                violations.append(violation("self-recursion", node.lineno, "A function whose only action calls itself has no visible base case or progress."))
                continue
            if python_argument_names(call) == python_parameter_names(node) and not has_semantic_boundary(lines, node.lineno):
                violations.append(violation("pass-through-wrapper", node.lineno, "Call the real owner directly or mark the actual semantic boundary."))
        if isinstance(node, ast.Call) and getattr(node, "end_lineno", node.lineno) > node.lineno:
            compact = ast.unparse(node)
            if len(compact) <= 200:
                violations.append(violation("avoidable-vertical-call", node.lineno, "This complete call fits clearly on one physical line.", node.end_lineno))
    return violations


def check_text(text, suffix):
    if suffix.lower() != ".py":
        raise ValueError("Python source checks require a .py file.")
    return deduplicate_violations(python_violations(text))


def check_path(path, diff_from=None):
    text = path.read_text(encoding="utf-8")
    included_lines = git_added_lines(path, diff_from) if diff_from else None
    violations = filter_violations(check_text(text, path.suffix), included_lines)
    return {"path": path.as_posix(), "status": "pass" if not violations else "fail", "violations": violations}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Check Python source for direct-code rule violations.")
    parser.add_argument("--diff-from", help="Report only violations intersecting lines added since this Git reference.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args(argv)
    for path in args.paths:
        if path.suffix.lower() != ".py":
            parser.error(f"Expected a .py file: {path}")
    return args


def main(argv=None):
    args = parse_args(argv)
    results = [check_path(path.resolve(), args.diff_from) for path in args.paths]
    payload = {"schema_version": 1, "status": "pass" if all(result["status"] == "pass" for result in results) else "fail", "results": results}
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

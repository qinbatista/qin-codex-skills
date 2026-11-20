#!/usr/bin/env python3
"""Detect high-confidence violations of the Python direct-code rules."""

import argparse
import ast
import json
import re
import subprocess
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options

GIT_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")


def violation(code, line, message, end_line=None):
    return {"code": code, "line": line, "end_line": end_line or line, "message": message}


def deduplicate_violations(violations):
    unique = {}
    for item in violations:
        unique.setdefault((item["code"], item["line"], item["end_line"]), item)
    return list(unique.values())


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


def filter_violations(violations, included_lines):
    if included_lines is None:
        return violations
    return [item for item in violations if any(line in included_lines for line in range(item["line"], item["end_line"] + 1))]


def git_added_lines(path, reference):
    root_process = subprocess.run(["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False, shell=False, **hidden_process_options())
    if root_process.returncode != 0:
        raise ValueError("git_root_unavailable")
    repository_root = Path(root_process.stdout.strip()).resolve()
    relative_path = path.resolve().relative_to(repository_root).as_posix()
    tracked_process = subprocess.run(["git", "-C", str(repository_root), "ls-files", "--error-unmatch", "--", relative_path], capture_output=True, text=True, check=False, shell=False, **hidden_process_options())
    if tracked_process.returncode != 0:
        return set(range(1, len(path.read_text(encoding="utf-8").splitlines()) + 1))
    diff_process = subprocess.run(["git", "-C", str(repository_root), "diff", "--unified=0", reference, "--", relative_path], capture_output=True, text=True, check=False, shell=False, **hidden_process_options())
    if diff_process.returncode != 0:
        raise ValueError("git_diff_unavailable")
    added_lines = set()
    for line in diff_process.stdout.splitlines():
        match = GIT_HUNK.match(line)
        if match is None:
            continue
        start = int(match.group("start"))
        count = int(match.group("count") or "1")
        added_lines.update(range(start, start + count))
    return added_lines


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

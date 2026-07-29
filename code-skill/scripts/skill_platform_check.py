#!/usr/bin/env python3
"""Fail closed on newly introduced unguarded platform-specific Skill helpers."""

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SCHEMA_VERSION = 1
BASELINE_GENERATOR = "skill-platform-check/v1"
RUNTIME_DIRECTORIES = {"scripts", "bin", "tools"}
SUFFIX_LANGUAGES = {".py": "python", ".sh": "shell", ".bash": "shell", ".zsh": "shell", ".ps1": "powershell", ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".ts": "javascript", ".tsx": "javascript"}
PATH_PATTERN = re.compile(r"(?:/(?:Users|Applications|tmp)/|~/(?:Library|Applications)|[A-Za-z]:\\(?:Users|Program Files)\\|\\\\|(?:^|[^:])\\[A-Za-z0-9_.-]+\\)")
COMMAND_PATTERN = re.compile(r"\b(osascript|osacompile|cmd\.exe|powershell(?:\.exe)?|open)\b", re.IGNORECASE)
PLATFORM_GUARDS = {"darwin": ("darwin", "Darwin", "$IsMacOS"), "windows": ("win32", "nt", "Windows", "$IsWindows"), "linux": ("linux", "Linux", "$IsLinux")}
PLATFORM_ONLY_MODULES = {"fcntl", "grp", "msvcrt", "pty", "pwd", "resource", "termios"}
PLATFORM_ONLY_CALLS = {"os.fork", "os.getegid", "os.geteuid", "os.getgid", "os.getpgid", "os.getuid", "os.killpg", "os.setpgid", "os.setsid", "os.startfile"}
SUBPROCESS_CALLS = {"subprocess.call", "subprocess.check_call", "subprocess.check_output", "subprocess.Popen", "subprocess.run"}
PYTHON_COMMANDS = {"py", "python", "python3", "python.exe", "python3.exe"}
EXECUTABLE_LITERAL_CALLS = SUBPROCESS_CALLS | {"os.popen", "os.system", "shutil.which"}
PATH_LITERAL_CALLS = EXECUTABLE_LITERAL_CALLS | {"open", "Path", "pathlib.Path"}


def _relative_path(skills_root, path):
    return path.resolve().relative_to(skills_root.resolve()).as_posix()


def _candidate_files(skills_root, selected_files=None):
    skills_root = Path(skills_root).resolve()
    requested_paths = [(Path(path) if Path(path).is_absolute() else skills_root / path).resolve() for path in selected_files] if selected_files else None
    candidates = []
    for skill_path in sorted(skills_root.iterdir(), key=lambda path: path.name) if skills_root.is_dir() else []:
        if not skill_path.is_dir() or skill_path.name.startswith(".") or not (skill_path / "SKILL.md").is_file():
            continue
        for runtime_name in RUNTIME_DIRECTORIES:
            runtime_path = skill_path / runtime_name
            if not runtime_path.is_dir():
                continue
            for candidate in sorted(runtime_path.rglob("*"), key=lambda path: path.as_posix()):
                if not candidate.is_file() or candidate.is_symlink() or candidate.suffix.lower() not in SUFFIX_LANGUAGES:
                    continue
                relative_parts = candidate.relative_to(skill_path).parts
                if any(part in {"tests", "fixtures", "examples", "references", "assets", "cache", "work", "__pycache__"} or part.startswith(".") for part in relative_parts):
                    continue
                if requested_paths and candidate.resolve() not in requested_paths:
                    continue
                candidates.append(candidate)
    return candidates


def _fingerprint(relative_path, language, rule, marker, ordinal):
    value = "\0".join([str(SCHEMA_VERSION), relative_path, language, rule, marker.strip(), str(ordinal)])
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _finding(relative_path, language, rule, line, column, message, marker, occurrence_counts):
    key = (rule, marker.strip())
    occurrence_counts[key] = occurrence_counts.get(key, 0) + 1
    return {"rule": rule, "language": language, "relative_path": relative_path, "line": line, "column": column, "message": message, "fingerprint": _fingerprint(relative_path, language, rule, marker, occurrence_counts[key])}


def _is_platform_guard(test):
    text = ast.unparse(test) if hasattr(ast, "unparse") else ""
    native_guard = r"(?:sys\.platform\s*==\s*['\"](?:darwin|win32)['\"]|sys\.platform\.startswith\(['\"]linux['\"]\)|os\.name\s*==\s*['\"](?:nt|posix)['\"]|platform\.system\(\)\s*==\s*['\"](?:Darwin|Windows|Linux)['\"])"
    normalized_guard = r"(?:platform_name|host_platform\([^)]*\))\s*==\s*['\"](?:windows|macos|linux)['\"]"
    return bool(re.search(f"(?:{native_guard}|{normalized_guard})", text))


def _has_fallback(node):
    return bool(node.orelse) and any(isinstance(item, (ast.Raise, ast.If, ast.Return)) or (isinstance(item, ast.Expr) and isinstance(item.value, ast.Call) and getattr(item.value.func, "id", "") == "exit") for item in node.orelse)


def _contains_resolver(nodes):
    return any(isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr == "which" and isinstance(item.func.value, ast.Name) and item.func.value.id == "shutil" for node in nodes for item in ast.walk(node))


def _contains_platform_sensitive_literal(nodes):
    return any(isinstance(item, ast.Constant) and isinstance(item.value, str) and (PATH_PATTERN.search(item.value) or COMMAND_PATTERN.search(item.value)) for node in nodes for item in ast.walk(node))


def _qualified_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        owner = _qualified_name(node.value)
        return f"{owner}.{node.attr}" if owner else node.attr
    return ""


def _truthy_keyword(call, name):
    return any(keyword.arg == name and isinstance(keyword.value, ast.Constant) and keyword.value.value is True for keyword in call.keywords)


def _subprocess_command(call):
    if not call.args:
        return ""
    command = call.args[0]
    if isinstance(command, (ast.List, ast.Tuple)) and command.elts:
        command = command.elts[0]
    return command.value.strip().lower() if isinstance(command, ast.Constant) and isinstance(command.value, str) else ""


def _ancestor_call(node, parents):
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.Call):
            return current
    return None


def _literal_used_as_path(node, parents):
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and any(token in node.value for token in ("(?:", "\\b", "\\s")):
        return False
    call = _ancestor_call(node, parents)
    return call is None or _qualified_name(call.func) in PATH_LITERAL_CALLS


def _literal_used_as_command(node, parents):
    call = _ancestor_call(node, parents)
    return call is not None and _qualified_name(call.func) in EXECUTABLE_LITERAL_CALLS


def _python_findings(path, relative_path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        return [{"rule": "SPG900", "language": "python", "relative_path": relative_path, "line": getattr(error, "lineno", 1) or 1, "column": getattr(error, "offset", 1) or 1, "message": f"cannot parse runtime helper: {error}", "fingerprint": ""}]
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    findings, counts = [], {}
    guarded_lines, bad_guard_lines = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and _is_platform_guard(node.test):
            guarded_lines.update(range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1))
            if _contains_platform_sensitive_literal(node.body) and not _has_fallback(node):
                bad_guard_lines.add(node.lineno)
            elif _contains_platform_sensitive_literal(node.body) and not _contains_resolver(node.body):
                bad_guard_lines.add(node.lineno)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        parent = parents.get(node)
        if isinstance(parent, ast.Call) and isinstance(parent.func, ast.Attribute) and parent.func.attr == "compile":
            continue
        marker = node.value
        if PATH_PATTERN.search(marker) and node.lineno not in guarded_lines and _literal_used_as_path(node, parents):
            findings.append(_finding(relative_path, "python", "SPG001", node.lineno, node.col_offset + 1, "platform-rooted or separator-specific path is not guarded", marker, counts))
        if COMMAND_PATTERN.search(marker) and node.lineno not in guarded_lines and _literal_used_as_command(node, parents):
            findings.append(_finding(relative_path, "python", "SPG002", node.lineno, node.col_offset + 1, "platform-only command is not inside an explicit platform guard", marker, counts))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = [alias.name.split(".", 1)[0] for alias in node.names] if isinstance(node, ast.Import) else [str(node.module or "").split(".", 1)[0]]
            for module in modules:
                if module in PLATFORM_ONLY_MODULES and node.lineno not in guarded_lines:
                    findings.append(_finding(relative_path, "python", "SPG004", node.lineno, node.col_offset + 1, "platform-only Python module is not inside an explicit platform guard", module, counts))
        if not isinstance(node, ast.Call):
            continue
        qualified_name = _qualified_name(node.func)
        if qualified_name in PLATFORM_ONLY_CALLS and node.lineno not in guarded_lines:
            findings.append(_finding(relative_path, "python", "SPG004", node.lineno, node.col_offset + 1, "platform-only Python API is not inside an explicit platform guard", qualified_name, counts))
        if qualified_name in SUBPROCESS_CALLS and node.lineno not in guarded_lines and (_truthy_keyword(node, "start_new_session") or any(keyword.arg in {"creationflags", "preexec_fn"} for keyword in node.keywords)):
            findings.append(_finding(relative_path, "python", "SPG004", node.lineno, node.col_offset + 1, "platform-only subprocess option is not inside an explicit platform guard", qualified_name, counts))
        if qualified_name in SUBPROCESS_CALLS and node.lineno not in guarded_lines and _truthy_keyword(node, "shell"):
            findings.append(_finding(relative_path, "python", "SPG005", node.lineno, node.col_offset + 1, "shell=True is not portable shared-process behavior", qualified_name, counts))
        command = _subprocess_command(node) if qualified_name in SUBPROCESS_CALLS else ""
        if command in PYTHON_COMMANDS:
            findings.append(_finding(relative_path, "python", "SPG006", node.lineno, node.col_offset + 1, "child Python process must use sys.executable", command, counts))
    for line in sorted(bad_guard_lines):
        findings.append(_finding(relative_path, "python", "SPG003", line, 1, "platform guard needs an explicit non-target outcome and in-branch executable resolver", "platform-guard", counts))
    return findings


def _line_findings(path, relative_path, language):
    findings, counts, guard_stack = [], {}, []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = raw_line.split("#", 1)[0]
        lower = line.lower()
        guard = any(marker.lower() in lower for markers in PLATFORM_GUARDS.values() for marker in markers) or "process.platform" in lower or "uname" in lower or "ostype" in lower
        if guard:
            guard_stack.append(line_number)
        if re.search(r"\b(else|throw|exit 3)\b", lower) and guard_stack:
            guard_stack.pop()
        guarded = bool(guard_stack)
        if PATH_PATTERN.search(line) and not guarded:
            findings.append(_finding(relative_path, language, "SPG001", line_number, PATH_PATTERN.search(line).start() + 1, "platform-rooted or separator-specific path is not guarded", PATH_PATTERN.search(line).group(0), counts))
        command_match = COMMAND_PATTERN.search(line)
        if command_match and not guarded:
            findings.append(_finding(relative_path, language, "SPG002", line_number, command_match.start() + 1, "platform-only command is not inside a recognized platform guard", command_match.group(0), counts))
    for line_number in guard_stack:
        findings.append(_finding(relative_path, language, "SPG003", line_number, 1, "platform guard lacks an explicit non-target outcome", "platform-guard", counts))
    return findings


def collect_findings(skills_root, selected_files=None):
    root = Path(skills_root)
    findings = []
    for path in _candidate_files(root, selected_files):
        relative_path = _relative_path(root, path)
        language = SUFFIX_LANGUAGES[path.suffix.lower()]
        findings.extend(_python_findings(path, relative_path) if language == "python" else _line_findings(path, relative_path, language))
    return sorted(findings, key=lambda finding: (finding["relative_path"], finding["line"], finding["column"], finding["rule"]))


def load_baseline(baseline_path, skills_root):
    try:
        baseline = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"SPG900: invalid baseline: {error}") from error
    if baseline.get("schema_version") != SCHEMA_VERSION or not isinstance(baseline.get("findings"), list):
        raise ValueError("SPG900: baseline has an unsupported schema")
    fingerprints = []
    for finding in baseline["findings"]:
        if not isinstance(finding, dict) or not isinstance(finding.get("fingerprint"), str) or not isinstance(finding.get("relative_path"), str):
            raise ValueError("SPG900: baseline finding is malformed")
        if len(Path(finding["relative_path"]).parts) < 3 or finding["relative_path"].startswith("/") or ".." in Path(finding["relative_path"]).parts:
            raise ValueError("SPG900: baseline finding is outside the closed surface")
        fingerprints.append(finding["fingerprint"])
    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("SPG900: baseline contains duplicate fingerprints")
    return baseline


def new_findings(findings, baseline):
    fingerprints = {finding["fingerprint"] for finding in baseline["findings"]}
    return [finding for finding in findings if finding["fingerprint"] not in fingerprints]


def format_diagnostic(finding):
    remediation = "use pathlib/environment discovery or an explicit guard with a non-target outcome"
    return f"{finding['relative_path']}:{finding['line']}:{finding['column']}: {finding['rule']}: {finding['message']}; remediation: {remediation}"


def assert_skill_platform_safe(skills_root, baseline_path, selected_files=None):
    baseline = load_baseline(baseline_path, skills_root)
    findings = new_findings(collect_findings(skills_root, selected_files), baseline)
    if findings:
        raise RuntimeError("Skill platform gate failed:\n" + "\n".join(format_diagnostic(finding) for finding in findings))
    return findings


def _write_baseline(output, findings):
    payload = {"schema_version": SCHEMA_VERSION, "generated_by": BASELINE_GENERATOR, "findings": findings}
    Path(output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "inventory", "write-baseline"):
        command = subparsers.add_parser(name)
        command.add_argument("--skills-root", type=Path, required=True)
        command.add_argument("--file", dest="files", type=Path, action="append")
        if name == "check":
            command.add_argument("--baseline", type=Path, required=True)
        if name == "write-baseline":
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.skills_root.is_dir():
        print("SPG900: skills root is unreadable", file=sys.stderr)
        return 3
    try:
        findings = collect_findings(args.skills_root, args.files)
        if args.command == "inventory":
            print(json.dumps(findings, indent=2, sort_keys=True))
            return 0
        if args.command == "write-baseline":
            _write_baseline(args.output, findings)
            return 0
        new_items = new_findings(findings, load_baseline(args.baseline, args.skills_root))
        for finding in new_items:
            print(format_diagnostic(finding), file=sys.stderr)
        return 1 if new_items else 0
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 3
    except Exception as error:
        print(f"SPG900: unexpected checker error: {error}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())

"""Shared result and Git line-scope helpers for the Python and C# source checkers."""

import re
import subprocess
from pathlib import Path

from hidden_process import hidden_process_options


GIT_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")


def violation(code, line, message, end_line=None):
    return {"code": code, "line": line, "end_line": end_line or line, "message": message}


def deduplicate_violations(violations):
    unique = {}
    for item in violations:
        unique.setdefault((item["code"], item["line"], item["end_line"]), item)
    return list(unique.values())


def filter_violations(violations, included_lines):
    if included_lines is None:
        return violations
    return [
        item for item in violations
        if any(line in included_lines for line in range(item["line"], item["end_line"] + 1))
    ]


def run_git(directory, *arguments):
    return subprocess.run(
        ["git", "--literal-pathspecs", "-C", str(directory), *arguments],
        capture_output=True, encoding="utf-8", errors="replace", check=False, **hidden_process_options(),
    )


def git_added_lines(path, reference):
    path = path.resolve()
    root_process = run_git(path.parent, "rev-parse", "--show-toplevel")
    if root_process.returncode != 0:
        raise ValueError("git_root_unavailable")
    repository_root = Path(root_process.stdout.strip()).resolve()
    relative_path = path.relative_to(repository_root).as_posix()
    tracked = run_git(repository_root, "ls-files", "--error-unmatch", "--", relative_path)
    if tracked.returncode != 0:
        return set(range(1, len(path.read_text(encoding="utf-8").splitlines()) + 1))
    diff = run_git(
        repository_root, "diff", "--no-color", "--no-ext-diff", "--no-textconv", "--unified=0",
        reference, "--", relative_path,
    )
    if diff.returncode != 0:
        raise ValueError("git_diff_unavailable")
    added_lines = set()
    for line in diff.stdout.splitlines():
        match = GIT_HUNK.match(line)
        if match:
            start = int(match.group("start"))
            count = int(match.group("count") or "1")
            added_lines.update(range(start, start + count))
    return added_lines

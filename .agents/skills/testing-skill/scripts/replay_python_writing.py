"""Generate fresh Codex answers and run the Python casebook's independent checks."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SOURCE = SKILL.parents[2]
sys.path.insert(0, str(SOURCE / "workflow-skill" / "scripts"))
from task_artifact_paths import task_artifact_environment, task_artifact_scope

sys.path.insert(0, str(SOURCE / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


def read_cases():
    casebook = (SKILL / "references" / "codex-python-writing.md").read_text(encoding="utf-8")
    cases = {}
    for section in casebook.split("\n## ")[1:]:
        name, body = section.split("\n", 1)
        match = re.fullmatch(r"\s*```text\n(.+?)\n```\n\n```python\n(.+?)\n```\s*", body, re.DOTALL)
        if not match or name in cases:
            raise ValueError(f"Invalid writing case: {name}")
        cases[name] = match.groups()
    if not cases:
        raise ValueError("The writing casebook is empty.")
    return cases


def verify_answer(codex, environment, work, name, code, checks):
    (work / "answer.py").write_text(code, encoding="utf-8")
    harness = "import runpy, unittest\nfrom pathlib import Path\ncheck = unittest.TestCase()\nsolution = runpy.run_path('answer.py')\n"
    marker = f"passed {name}"
    (work / "check.py").write_text(harness + checks + f"\nprint({marker!r})\n", encoding="utf-8")
    verified = subprocess.run(
        [codex, "sandbox", "-P", ":workspace", "-C", str(work), "--", sys.executable, "-I", "-B", "check.py"],
        cwd=work, capture_output=True, text=True, encoding="utf-8", env=environment, timeout=30, **hidden_process_options(),
    )
    if verified.returncode or marker not in verified.stdout.splitlines():
        raise RuntimeError(verified.stderr.strip()[-1800:] or f"Checker exited {verified.returncode} without completing its assertions")
    print(marker, flush=True)


def replay(codex, environment, rules, root, name, prompt, checks):
    with tempfile.TemporaryDirectory(prefix=f"writing-{name}-", dir=root) as directory:
        work = Path(directory)
        schema = {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"], "additionalProperties": False}
        (work / "schema.json").write_text(json.dumps(schema), encoding="utf-8")
        instructions = f"Write a complete Python module using only the task and supplied Code rules. Return its source in the code field, without fences or tools.\n\n{rules}\n\nTask\n{prompt}"
        writer = subprocess.run(
            [codex, "exec", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
             "--disable", "shell_tool", "--disable", "unified_exec", "--sandbox", "read-only",
             "-c", "project_doc_max_bytes=0", "--color", "never", "--output-schema", "schema.json", "--output-last-message", "answer.json", "-"],
            cwd=work, input=instructions, capture_output=True, text=True, encoding="utf-8", env=environment, timeout=300, **hidden_process_options(),
        )
        model = re.search(r"^model: (.+)$", writer.stderr, re.MULTILINE)
        print(f"{name} ({model[1] if model else 'model not reported'})", flush=True)
        if writer.returncode:
            raise RuntimeError(writer.stderr.strip()[-1800:] or f"Codex exited {writer.returncode}")
        answer = json.loads((work / "answer.json").read_text(encoding="utf-8"))
        verify_answer(codex, environment, work, name, answer["code"], checks)


def main():
    cases = read_cases()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", nargs="?", choices=cases, help="Run a single case; the default runs all.")
    args = parser.parse_args()
    codex = shutil.which("codex")
    if not codex:
        parser.exit(1, "Codex CLI is required for a writing replay.\n")
    code_skill = SOURCE / "code-skill"
    references = ["SKILL.md", "references/code-writing-philosophy.md", "references/python-rules.md", "references/state-and-side-effects.md"]
    rules = "\n\n".join((code_skill / path).read_text(encoding="utf-8") for path in references)
    task_id = os.environ.get("CODEX_THREAD_ID") or "python-writing-replay"
    failures = 0
    borrowed_root = os.environ.get("CODEX_PROJECT_CACHE_ROOT")
    project = Path.cwd() if borrowed_root else SOURCE
    with task_artifact_scope(project, task_id, borrowed_root=borrowed_root) as run:
        environment = task_artifact_environment(run, create=True)
        for name in ([args.case] if args.case else cases):
            try:
                replay(codex, environment, rules, run, name, *cases[name])
            except (KeyError, OSError, RuntimeError, TypeError, ValueError, subprocess.TimeoutExpired) as error:
                print(f"FAILED {name}: {error}", file=sys.stderr)
                failures += 1
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

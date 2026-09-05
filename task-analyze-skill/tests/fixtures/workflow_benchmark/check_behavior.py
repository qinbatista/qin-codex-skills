"""Independent acceptance checks; no model invocation and no visible processes."""

import argparse
import ast
import contextlib
import importlib.util
import json
import os
import platform as platform_api
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock


EXPECTED_TOTALS = {
    "Atlas": "108.45", "Birch": "0.00", "Cedar": "0.25", "Dune": "0.00", "Elm": "0.00"
}


class StartupInfo:
    def __init__(self):
        self.dwFlags = 0
        self.wShowWindow = 1


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_runner(root):
    spec = importlib.util.spec_from_file_location("benchmark_candidate", root / "process_runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def candidate_platform(runner, platform_name):
    """Change candidate detector bindings without changing the verifier's host OS."""
    os_name = "nt" if platform_name == "win32" else "posix"
    system_name = {"win32": "Windows", "darwin": "Darwin", "linux": "Linux"}[platform_name]
    sys_view = SimpleNamespace(**dict(vars(sys), platform=platform_name))
    os_view = SimpleNamespace(**dict(vars(os), name=os_name))
    platform_view = SimpleNamespace(**dict(vars(platform_api), system=lambda: system_name))
    replacements = {}
    for name, value in vars(runner).items():
        if value is sys:
            replacements[name] = sys_view
        elif value is os:
            replacements[name] = os_view
        elif value is platform_api:
            replacements[name] = platform_view
        elif value is platform_api.system:
            replacements[name] = platform_view.system
    # Handle `from os import name as ...` and `from sys import platform as ...`
    # without rewriting unrelated constants that happen to contain these strings.
    source = ast.parse(Path(runner.__file__).read_text(encoding="utf-8"))
    for node in source.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                binding = alias.asname or alias.name
                if node.module == "os" and alias.name == "name":
                    replacements[binding] = os_name
                elif node.module == "sys" and alias.name == "platform":
                    replacements[binding] = platform_name
    with mock.patch.dict(vars(runner), replacements):
        yield


def contract_check(runner, platform):
    sentinel = subprocess.CompletedProcess(["sentinel"], 7, "output", "error")
    environment = {"EXAMPLE_VALUE": "spaces & punctuation"}
    args = [sys.executable, "worker with spaces.py", "one;two", "$(literal)"]
    constants = {
        "CREATE_NO_WINDOW": 0x08000000,
        "CREATE_NEW_CONSOLE": 0x00000010,
        "DETACHED_PROCESS": 0x00000008,
        "STARTF_USESHOWWINDOW": 1,
        "SW_HIDE": 0,
        "STARTUPINFO": StartupInfo,
    }
    with contextlib.ExitStack() as stack:
        stack.enter_context(candidate_platform(runner, platform))
        for key, value in constants.items():
            stack.enter_context(mock.patch.object(subprocess, key, value, create=True))
        run = stack.enter_context(mock.patch.object(subprocess, "run", return_value=sentinel))
        stack.enter_context(mock.patch.object(subprocess, "Popen", side_effect=AssertionError("Preserve the existing subprocess.run owner")))
        result = runner.run_job(args, cwd="sample folder", env=environment, timeout=0.375, input_text="payload")
        require(run.call_count == 1, "Exactly one owned worker launch is expected")
        positional, options = run.call_args
        passed_args = positional[0] if positional else options.get("args")
        require(passed_args == args, "Argument arrays must remain intact")
        require(options.get("shell", False) is False, "Shell execution must be disabled")
        require(options.get("cwd") == "sample folder", "Working directory must be forwarded")
        require(options.get("env") == environment, "Environment must be forwarded")
        require(options.get("timeout") == 0.375, "Timeout must be forwarded")
        require(options.get("input") == "payload", "Input text must be forwarded")
        require(options.get("text") or options.get("universal_newlines") or options.get("encoding"), "Text capture is required")
        require(options.get("capture_output") or (options.get("stdout") == subprocess.PIPE and options.get("stderr") == subprocess.PIPE), "Capture both stdout and stderr")
        require(not options.get("check", False), "Nonzero exits must remain observable CompletedProcess results")
        require(result is sentinel, "Return the owned subprocess result")
        if platform == "win32":
            flags = options.get("creationflags", 0)
            require(flags & constants["CREATE_NO_WINDOW"], "Windows must use CREATE_NO_WINDOW")
            require(not flags & (constants["CREATE_NEW_CONSOLE"] | constants["DETACHED_PROCESS"]), "Windows must not create or detach a console")
            startup = options.get("startupinfo")
            require(startup is not None, "Windows needs hidden STARTUPINFO")
            require(startup.dwFlags & constants["STARTF_USESHOWWINDOW"], "Windows startup flags must control visibility")
            require(startup.wShowWindow == constants["SW_HIDE"], "Windows startup show state must be hidden")
            require(not options.get("start_new_session"), "POSIX session option must not leak into Windows")
        else:
            require("creationflags" not in options and "startupinfo" not in options, "Windows-only options must be absent on POSIX")
            require(options.get("start_new_session") is True, "Preserve the existing POSIX session boundary")


def real_execution_check(runner, root):
    # Call the candidate only after all three launch-option contracts pass.
    # Temporary support files stay inside this task-owned workspace.
    with tempfile.TemporaryDirectory(prefix="tmp-behavior-", dir=str(root)) as directory:
        directory = Path(directory)
        worker = directory / "worker with spaces.py"
        worker.write_text(
            "import json, os, pathlib, sys\n"
            "console = None\n"
            "if sys.platform == 'win32':\n"
            "    import ctypes\n"
            "    console = bool(ctypes.windll.kernel32.GetConsoleWindow())\n"
            "print(json.dumps({'args': sys.argv[1:], 'cwd': str(pathlib.Path.cwd()), 'env': os.environ.get('BENCHMARK_VALUE'), 'input': sys.stdin.read(), 'console': console}))\n"
            "print('observable error output', file=sys.stderr)\n"
            "raise SystemExit(7)\n",
            encoding="utf-8",
        )
        environment = dict(os.environ, BENCHMARK_VALUE="kept exactly")
        arguments = ["one two", "semi;colon", "$(literal)", "中文"]
        result = runner.run_job(
            [sys.executable, str(worker), *arguments], cwd=str(directory),
            env=environment, timeout=5, input_text="request body\n",
        )
        require(result.returncode == 7, "Preserve actual nonzero exit status")
        output = json.loads(result.stdout)
        require(output["args"] == arguments, "Actual arguments must not be shell-expanded")
        require(Path(output["cwd"]).resolve() == directory.resolve(), "Actual working directory must match")
        require(output["env"] == "kept exactly", "Actual environment must match")
        require(output["input"] == "request body\n", "Actual stdin must match")
        require("observable error output" in result.stderr, "Actual stderr must be captured")
        if sys.platform == "win32":
            require(output["console"] is False, "The native Windows child acquired a console")
        try:
            runner.run_job([sys.executable, "-c", "import time; time.sleep(1)"], timeout=0.05)
        except subprocess.TimeoutExpired:
            pass
        else:
            raise AssertionError("Actual timeout must propagate")
        return {"native_platform": sys.platform, "child_console": output["console"], "exit_code": result.returncode}


def check(root):
    evidence = {"status": "passed", "checks": [], "native_platform": sys.platform}

    def attempt(name, function):
        try:
            detail = function()
            evidence["checks"].append({"name": name, "pass": True, "detail": detail})
            return True
        except Exception as error:
            evidence["checks"].append({"name": name, "pass": False, "error": str(error), "error_type": type(error).__name__})
            evidence["status"] = "failed"
            return False

    def totals_check():
        totals = json.loads((root / "totals.json").read_text(encoding="utf-8"))
        require(totals == EXPECTED_TOTALS, "Totals must match exact deduplicated decimal results")
        require(list(totals) == sorted(EXPECTED_TOTALS), "Project keys must be sorted")
        return {"projects": len(totals)}

    attempt("exact_ledger_totals", totals_check)
    try:
        runner = load_runner(root)
    except Exception as error:
        evidence["checks"].append({"name": "import_runner", "pass": False, "error": str(error)})
        evidence["status"] = "failed"
        return evidence
    contracts = [attempt("launch_contract_" + platform, lambda platform=platform: contract_check(runner, platform)) for platform in ("darwin", "linux", "win32")]
    if all(contracts):
        attempt("native_subprocess_behavior", lambda: real_execution_check(runner, root))
    else:
        evidence["checks"].append({"name": "native_subprocess_behavior", "pass": False, "skipped": "Unsafe launch contracts; candidate was not executed"})
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--output", type=Path)
    options = parser.parse_args()
    evidence = check(options.workspace.resolve())
    encoded = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    if options.output:
        options.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if evidence["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

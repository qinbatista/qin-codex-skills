"""Run frozen behavioral and headless UI checks for one copied benchmark input."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


FIXTURE_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


def run_check(argv, timeout=60):
    completed = subprocess.run(
        argv, capture_output=True, text=True, encoding="utf-8", timeout=timeout,
        check=False, **hidden_process_options(),
    )
    try:
        result = json.loads(completed.stdout)
    except ValueError:
        result = {"status": "fail", "error": "Checker did not return JSON", "stdout": completed.stdout}
    return {"exit_code": completed.returncode, "result": result, "stderr": completed.stderr}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--node", default=os.environ.get("BENCHMARK_NODE") or shutil.which("node"))
    parser.add_argument("--playwright", default=os.environ.get("BENCHMARK_PLAYWRIGHT"))
    parser.add_argument("--browser", default=os.environ.get("BENCHMARK_BROWSER"))
    options = parser.parse_args()
    options.output_dir.mkdir(parents=True, exist_ok=True)
    result = {"status": "fail", "headless": True, "checks": {}}
    try:
        if not options.node or not options.playwright:
            raise ValueError("Provide --node and --playwright runtime paths; this checker never installs dependencies")
        actual = (options.workspace / "ledger.csv").read_bytes()
        expected = (FIXTURE_ROOT / "input" / "ledger.csv").read_bytes()
        result["checks"]["immutable_ledger"] = {
            "pass": actual == expected,
            "sha256": hashlib.sha256(actual).hexdigest(),
        }
        result["checks"]["behavior"] = run_check([
            sys.executable, "-B", str(FIXTURE_ROOT / "check_behavior.py"), str(options.workspace.resolve()),
            "--output", str((options.output_dir / "behavior.json").resolve()),
        ])
        ui_argv = [
            options.node, str(FIXTURE_ROOT / "check_ui.cjs"), str(options.workspace.resolve()),
            str(options.output_dir.resolve()), options.playwright,
        ]
        if options.browser:
            ui_argv.append(options.browser)
        result["checks"]["ui"] = run_check(ui_argv)
        checks = result["checks"]
        if checks["immutable_ledger"]["pass"] and all(checks[name]["exit_code"] == 0 for name in ("behavior", "ui")):
            result["status"] = "pass"
    except Exception as error:
        result["error"] = str(error)
        result["error_type"] = type(error).__name__
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    (options.output_dir / "acceptance.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

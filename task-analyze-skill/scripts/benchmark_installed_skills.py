#!/usr/bin/env python3
"""Compare installed skills with a clean control using actual, isolated Codex runs.

Private provider transcripts stay in the explicit output directory. summary.json
contains only metrics and acceptance flags; it never contains prompts or auth data.
This measures one controller per task, not adaptive routing or an Ending lifecycle.
"""

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOURCE_ROOT / "code-skill" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hidden_process import hidden_process_options
from model_execution_receipt import parse_rollout_allowlist, parse_stdout_events

BOUNDARY = """\n\nBenchmark execution boundary (identical in both conditions):
Complete this disposable task directly in the current workspace using the selected
model and effort. Do not delegate, invoke another model, or start another Codex
session. Use applicable installed skills normally. There is no project memory to
read or update; skip Ending for this disposable trial. The study owner handles its
aggregate memory separately. Keep all programs headless and terminals hidden.
"""
DISABLED_FEATURES = ("multi_agent", "apps", "browser_use", "computer_use",
                     "image_generation", "in_app_browser", "plugins", "skill_search")
TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "uncached_input_tokens",
                "output_tokens", "reasoning_output_tokens", "cache_write_input_tokens", "total_tokens")
CORE_TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "uncached_input_tokens", "output_tokens", "total_tokens")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("frozen_tree_contains_symlink")
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(path.relative_to(root).as_posix().encode() + b"\0")
            digest.update(path.read_bytes())
    return digest.hexdigest()


def stage_fixture(source, workspace):
    shutil.copytree(source, workspace)
    for path in sorted(workspace.rglob("*.in")):
        target = path.with_suffix("")
        if target.exists():
            raise ValueError("fixture_template_target_collision")
        path.rename(target)


def load_installer(source):
    spec = importlib.util.spec_from_file_location(
        "benchmark_skill_materializer", source / "management-skill" / "scripts" / "sync_global_skills.py")
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    return installer


def freeze_source(source, target):
    installer = load_installer(source)
    target.mkdir(mode=0o700)
    for name in sorted(installer.APPROVED_GLOBAL_SKILL_NAMES):
        installer.copy_skill_directory(source / name, target / name)


def trial_order(repeats, condition="both"):
    return [(repeat + 1, arm) for repeat in range(repeats)
            for arm in (("control", "installed") if repeat % 2 == 0 else ("installed", "control"))
            if condition == "both" or arm == condition]


def isolated_environment(codex_home, inherited):
    environment = {key: value for key, value in inherited.items()
                   if not key.startswith("CODEX_") and key not in {
                       "OBSIDIAN_VAULT", "OBSIDIAN_VAULT_PATH", "AI_MEMORY_ROOT"}}
    environment.update(CODEX_HOME=str(codex_home), CODEX_SQLITE_HOME=str(codex_home))
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8:strict"
    return environment


def materialize_home(codex_home, source, installed, auth_path):
    codex_home.mkdir(mode=0o700, parents=True)
    if auth_path.is_file():
        # Only create/remove the link. Never read, copy, serialize or chmod auth.
        try:
            (codex_home / "auth.json").symlink_to(auth_path)
        except OSError as error:
            if os.name != "nt" or getattr(error, "winerror", None) != 1314:
                raise
            os.link(auth_path, codex_home / "auth.json")
    config = '[features]\n' + ''.join(f'{name} = false\n' for name in DISABLED_FEATURES)
    (codex_home / "config.toml").write_text(config, encoding="utf-8")
    if installed:
        installer = load_installer(source)
        skills = codex_home / "skills"
        skills.mkdir()
        for name in sorted(installer.APPROVED_GLOBAL_SKILL_NAMES):
            installer.copy_skill_directory(source / name, skills / name)
        (codex_home / "AGENTS.md").write_text(installer.materialized_global_agents_text(source), encoding="utf-8")


def run_captured(command, *, cwd, environment, timeout, input_text=None):
    started = time.perf_counter()
    process = None
    stdout = stderr = ""
    failure = None
    try:
        process = subprocess.Popen(command, cwd=cwd, env=environment, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                   encoding="utf-8", errors="strict",
                                   shell=False, start_new_session=os.name != "nt",
                                   **hidden_process_options())
        try:
            stdout, stderr = process.communicate(input_text, timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            failure = "cancelled" if isinstance(error, KeyboardInterrupt) else "timeout"
            stop_owned_process(process)
            stdout, stderr = process.communicate()
    except OSError as error:
        failure = type(error).__name__
    return {"exit_code": process.returncode if process else None,
            "elapsed_seconds": round(time.perf_counter() - started, 6),
            "failure": failure, "stdout": stdout, "stderr": stderr}


def stop_owned_process(process):
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, check=False, shell=False, timeout=30,
                           **hidden_process_options())
        finally:
            if process.poll() is None:
                process.kill()
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def codex_command(executable, model, effort, sandbox="workspace-write"):
    prefix = [sys.executable, executable] if executable.endswith(".py") else [executable]
    return [*prefix, "exec", "--model", model, "-c", f'model_reasoning_effort="{effort}"',
            "-c", 'approval_policy="never"', "--sandbox", sandbox, "--json", "-"]


def validated_usage(usage):
    """Validate components before deriving totals; optional counters stay unknown."""
    usage = usage if isinstance(usage, dict) else {}
    counts = {name: usage.get(name) for name in TOKEN_FIELDS}
    errors = []
    for name, value in counts.items():
        if value is not None and (type(value) is not int or value < 0):
            errors.append(f"invalid_{name}")
    if any(counts[name] is None for name in ("input_tokens", "cached_input_tokens", "output_tokens")):
        errors.append("missing_required_counts")
    if not errors:
        if counts["cached_input_tokens"] > counts["input_tokens"]:
            errors.append("cached_exceeds_input")
        derived = {"uncached_input_tokens": counts["input_tokens"] - counts["cached_input_tokens"],
                   "total_tokens": counts["input_tokens"] + counts["output_tokens"]}
        for name, value in derived.items():
            if counts[name] is not None and counts[name] != value:
                errors.append(f"inconsistent_{name}")
            counts[name] = value
    return {"counts": counts, "valid": not errors, "errors": errors}


def sum_token_maps(maps):
    return {name: sum(value[name] for value in maps) if maps and all(value[name] is not None for value in maps) else None
            for name in TOKEN_FIELDS}


def pair_history(path, requested_pair):
    expected_model, expected_effort = requested_pair.split("|", 1)
    pairs, valid = set(), True
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            payload = event.get("payload", {})
            if event.get("type") == "turn_context":
                pair = f'{payload.get("model")}|{payload.get("effort")}'
                pairs.add(pair)
                valid = valid and pair == requested_pair
            if event.get("type") == "event_msg" and payload.get("type") == "model_reroute":
                for direction in ("from", "to"):
                    model = payload.get(f"{direction}_model")
                    effort = payload.get(f"{direction}_effort", expected_effort)
                    pairs.add(f"{model}|{effort}")
                    valid = valid and model == expected_model and effort == expected_effort
    return {"pairs": sorted(pairs), "valid": bool(pairs) and valid}


def evidence_from_sessions(codex_home, stdout, requested_pair):
    events = parse_stdout_events(stdout)
    sessions = []
    for path in sorted((codex_home / "sessions").glob("**/*.jsonl")):
        try:
            with path.open(encoding="utf-8") as handle:
                meta = json.loads(handle.readline()).get("payload", {})
        except (OSError, ValueError):
            continue
        observed = parse_rollout_allowlist(path)
        context = observed.get("turn_context") or {}
        reroutes = observed.get("reroutes") or []
        model = reroutes[-1].get("to_model") if reroutes else context.get("model")
        pair = f'{model}|{context.get("effort")}'
        history = pair_history(path, requested_pair)
        usage = validated_usage(observed.get("usage"))
        sessions.append({"id": meta.get("id"), "pair": pair,
                         "cli_version": meta.get("cli_version"),
                         "provider": meta.get("model_provider"),
                         "tokens": usage["counts"], "tokens_valid": usage["valid"],
                         "token_errors": usage["errors"], "history": history,
                         "completed": bool(observed.get("task_complete")),
                         "pair_match": pair == requested_pair and history["valid"]})
    roots = [session for session in sessions if session["id"] == events["thread_id"]]
    complete = bool(sessions) and all(session["tokens_valid"] for session in sessions)
    totals = sum_token_maps([session["tokens"] for session in sessions]) if complete else {key: None for key in TOKEN_FIELDS}
    # Preserve event usage as an explicit lower bound when a failed run did not
    # persist a complete rollout. Never substitute it as complete accounting.
    event_usage = validated_usage(events.get("usage"))
    lower_bound = event_usage["counts"] if event_usage["valid"] else None
    reconciled = bool(len(roots) == 1 and event_usage["valid"] and roots[0]["tokens_valid"]
                      and all(roots[0]["tokens"][key] == event_usage["counts"][key] for key in CORE_TOKEN_FIELDS)
                      and all(roots[0]["tokens"][key] == event_usage["counts"][key] for key in TOKEN_FIELDS
                              if roots[0]["tokens"][key] is not None and event_usage["counts"][key] is not None))
    runtime_pass = (len(sessions) == 1 and len(roots) == 1 and roots[0]["pair_match"]
                    and roots[0]["completed"] and complete and reconciled and totals["total_tokens"] > 0
                    and events["turn_completed"] and not events["turn_failed"]
                    and not events["invalid_json_event_count"])
    return {"runtime_pass": bool(runtime_pass), "session_count": len(sessions),
            "actual_pairs": sorted({pair for session in sessions for pair in session["history"]["pairs"]}),
            "cli_versions": sorted({session["cli_version"] for session in sessions if session["cli_version"]}),
            "providers": sorted({session["provider"] for session in sessions if session["provider"]}),
            "tokens": totals, "tokens_complete": complete, "stdout_usage_reconciled": reconciled,
            "token_validation_errors": sorted({error for session in sessions for error in session["token_errors"]} | set(event_usage["errors"])),
            "event_token_lower_bound": lower_bound, "failure_signals": events["failure_signals"]}


def shell_header_parts(command):
    """Split unquoted shell operators, preserving an attached heredoc body."""
    header, newline, body = command.partition("\n")
    parts, start, quote, escaped = [], 0, None, False
    for index, character in enumerate(header):
        if escaped:
            escaped = False
        elif character == "\\" and quote != "'":
            escaped = True
        elif quote:
            if character == quote:
                quote = None
        elif character in "'\"`":
            quote = character
        elif character in ";&|":
            if header[start:index].strip():
                parts.append(header[start:index].strip())
            start = index + 1
    tail = header[start:].strip()
    if tail:
        parts.append(tail + newline + body)
    return parts


def content_read_commands(command):
    """Return actual read segments, excluding listings and echoed references."""
    try:
        words = shlex.split(command)
    except ValueError:
        return []
    if not words:
        return []
    first = re.match(r'''\s*(?:"([^"]+)"|'([^']+)'|([^\s;&|]+))''', command)
    if first is None:
        return []
    executable = next(value for value in first.groups() if value is not None).replace("\\", "/").rsplit("/", 1)[-1].lower()
    if executable in {"bash", "zsh", "sh", "fish"}:
        for index, word in enumerate(words[1:], 1):
            if word in {"-c", "-lc"} and index + 1 < len(words):
                return content_read_commands(words[index + 1])
    if executable in {"powershell", "powershell.exe", "pwsh", "pwsh.exe"}:
        for index, word in enumerate(words[1:], 1):
            if word.lower() in {"-command", "-c"} and index + 1 < len(words):
                body = " ".join(words[index + 1:]).lstrip()
                if body.startswith("& "):
                    body = body[2:].lstrip()
                return content_read_commands(body)
        return []
    parts = shell_header_parts(command)
    if len(parts) > 1:
        return [read for part in parts for read in content_read_commands(part)]
    if executable in {"cat", "sed", "head", "tail", "get-content"}:
        return [command]
    if executable == "rg":
        listing = any(word in {"--files", "--files-with-matches", "--files-without-match", "--count", "--count-matches", "--quiet"}
                      or (word.startswith("-") and not word.startswith("--") and any(flag in word[1:] for flag in "lcq"))
                      for word in words[1:])
        return [] if listing else [command]
    if re.fullmatch(r"python(?:\d+(?:\.\d+)*)?(?:\.exe)?", executable):
        if "-c" in words:
            index = words.index("-c") + 1
            source = words[index] if index < len(words) else ""
        elif "<<" in command and "\n" in command:
            lines = command.splitlines()[1:]
            source = "\n".join(lines[:-1])
        else:
            return []
        try:
            reading = any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                          and node.func.attr in {"read_text", "read_bytes", "read", "readline", "readlines"}
                          for node in ast.walk(ast.parse(source)))
            return [command] if reading else []
        except SyntaxError:
            return []
    return []


def content_read_command(command):
    return bool(content_read_commands(command))


def skill_read_evidence(stdout, required):
    commands = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        item = event.get("item", {})
        if event.get("type") == "item.completed" and item.get("type") == "command_execution" and item.get("exit_code") == 0 and item.get("aggregated_output", "").strip():
            commands.extend(command.replace("\\", "/") for command in content_read_commands(item.get("command", "")))
    return {name: any(name.replace("\\", "/") in command for command in commands) for name in required}


def copy_regular_tree(source, destination):
    """Retain outputs without following model-created or credential symlinks."""
    destination.mkdir(parents=True, exist_ok=True)
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if ".git" in relative.parts or path.is_symlink() or any((source / Path(*relative.parts[:index])).is_symlink() for index in range(1, len(relative.parts))):
            continue
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def frozen_inputs_unchanged(args):
    return (tree_digest(args.fixture) == args.fixture_sha256
            and tree_digest(args.source) == args.source_sha256
            and (args.check_root is None or tree_digest(args.check_root) == args.check_sha256)
            and all(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest
                    for path, digest in args.check_dependency_hashes))


def prepare_frozen_inputs(args):
    original_source = args.source
    args.source = args.output_dir / "private-source"
    freeze_source(original_source, args.source)
    # Source-relative immutable checkers retain their repository-relative imports,
    # including hidden_process.py. Neither arm imports a changing live checker.
    def frozen_path(path):
        try:
            return args.source / path.relative_to(original_source)
        except ValueError:
            return path
    args.fixture = frozen_path(args.fixture)
    args.check_root = frozen_path(args.check_root) if args.check_root else None
    args.check_command = [part.replace(str(original_source), str(args.source)) for part in args.check_command]
    dependencies = [args.source / "code-skill" / "scripts" / "hidden_process.py", *map(frozen_path, args.check_dependency)]
    args.check_dependency_hashes = [(path, hashlib.sha256(path.read_bytes()).hexdigest()) for path in dict.fromkeys(dependencies)]
    args.source_sha256 = tree_digest(args.source)
    args.fixture_sha256 = tree_digest(args.fixture)
    args.check_sha256 = tree_digest(args.check_root) if args.check_root else None
    prompt = args.prompt_file.read_text(encoding="utf-8").replace(str(original_source), str(args.source))
    prompt += f"\nAssigned model and effort: {args.model}|{args.effort} (task assignment; runtime proof is collected by the study owner).\n" + BOUNDARY
    write_json(args.output_dir / "frozen-inputs.json", {
        "source_sha256": args.source_sha256, "fixture_sha256": args.fixture_sha256,
        "check_sha256": args.check_sha256,
        "check_dependency_sha256": [digest for _, digest in args.check_dependency_hashes],
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "sandbox": args.sandbox, "requested_pair": f"{args.model}|{args.effort}"})
    return prompt


def run_trial(args, repeat, arm, prompt):
    trial = args.output_dir / f"repeat-{repeat}-{arm}"
    trial.mkdir(mode=0o700)
    private = trial / "private"
    private.mkdir(mode=0o700)
    started = time.perf_counter()
    record = {"repeat": repeat, "condition": arm, "status": "fail",
              "requested_pair": f"{args.model}|{args.effort}", "sandbox": args.sandbox}
    # An independent OS temporary ancestry prevents the source project's AGENTS
    # from leaking into control. All durable evidence is copied to explicit Cache.
    with tempfile.TemporaryDirectory(prefix="qin-skill-benchmark-") as sandbox:
        root = Path(sandbox).resolve()
        workspace, codex_home = root / "workspace", root / "codex-home"
        try:
            if not frozen_inputs_unchanged(args):
                raise RuntimeError("frozen_inputs_changed_before_trial")
            stage_fixture(args.fixture, workspace)
            record["initial_workspace_sha256"] = tree_digest(workspace)
            environment = isolated_environment(codex_home, os.environ)
            if not (args.auth_home / "auth.json").is_file() and not environment.get("OPENAI_API_KEY"):
                raise RuntimeError("noninteractive_credentials_unavailable")
            materialize_home(codex_home, args.source, arm == "installed", args.auth_home / "auth.json")
            git = run_captured(["git", "init", "--quiet"], cwd=workspace, environment=environment, timeout=30)
            if git["exit_code"] != 0:
                raise RuntimeError("isolated_git_init_failed")
            provider = run_captured(codex_command(args.codex_bin, args.model, args.effort, args.sandbox),
                                    cwd=workspace, environment=environment, timeout=args.timeout,
                                    input_text=prompt)
            for stream in ("stdout", "stderr"):
                (private / f"provider-{stream}.txt").write_text(provider[stream], encoding="utf-8")
            record.update(evidence_from_sessions(codex_home, provider["stdout"], record["requested_pair"]))
            record.update(provider_seconds=provider["elapsed_seconds"], provider_exit_code=provider["exit_code"],
                          provider_failure=provider["failure"])
            if provider["failure"] == "cancelled":
                raise KeyboardInterrupt()
            record["skill_reads"] = skill_read_evidence(provider["stdout"], args.required_skill_read)
            managed_patterns = [f"{name}/{surface}" for name in load_installer(args.source).APPROVED_GLOBAL_SKILL_NAMES
                                for surface in ("SKILL.md", "references/", "scripts/")]
            record["control_managed_skill_reads"] = arm == "control" and any(skill_read_evidence(provider["stdout"], managed_patterns).values())
            forbidden_memory = [str(args.auth_home / "memories"), str(args.auth_home / "project-change-memory")]
            forbidden_memory.extend(value for key, value in os.environ.items() if "OBSIDIAN" in key and value)
            record["unrelated_memory_read"] = any(skill_read_evidence(provider["stdout"], forbidden_memory).values())
            record["frozen_inputs_unchanged"] = frozen_inputs_unchanged(args)
            if not record["frozen_inputs_unchanged"]:
                raise RuntimeError("frozen_inputs_changed_before_check")
            replacements = {"python": sys.executable, "workspace": str(workspace), "evidence": str(private)}
            command = []
            for part in args.check_command:
                for key, value in replacements.items():
                    part = part.replace("{" + key + "}", value)
                command.append(part)
            check = run_captured(command, cwd=workspace, environment=environment, timeout=args.check_timeout)
            for stream in ("stdout", "stderr"):
                (private / f"check-{stream}.txt").write_text(check[stream], encoding="utf-8")
            try:
                acceptance = json.loads(check["stdout"])
            except ValueError:
                acceptance = {}
            record.update(check_seconds=check["elapsed_seconds"], check_exit_code=check["exit_code"],
                          check_failure=check["failure"],
                          quality_pass=check["exit_code"] == 0 and acceptance.get("status") == "pass")
            if check["failure"] == "cancelled":
                raise KeyboardInterrupt()
            record["frozen_inputs_unchanged"] = record["frozen_inputs_unchanged"] and frozen_inputs_unchanged(args)
            record["skill_application_pass"] = arm != "installed" or all(record["skill_reads"].values())
            record["status"] = "pass" if (record["runtime_pass"] and record["quality_pass"]
                                            and record["skill_application_pass"] and provider["exit_code"] == 0
                                            and provider["failure"] is None and record["frozen_inputs_unchanged"]
                                            and not record["control_managed_skill_reads"]
                                            and not record["unrelated_memory_read"]) else "fail"
        except KeyboardInterrupt:
            record.update(failure="cancelled", cancelled=True)
        except Exception as error:
            record["failure"] = type(error).__name__
            (private / "failure.txt").write_text(str(error), encoding="utf-8")
        finally:
            # Always unlink before retaining evidence or deleting the sandbox.
            auth_link = codex_home / "auth.json"
            if auth_link.is_symlink() or auth_link.is_file():
                auth_link.unlink()
            if (codex_home / "sessions").is_dir():
                copy_regular_tree(codex_home / "sessions", private / "sessions")
            if workspace.is_dir():
                copy_regular_tree(workspace, trial / "artifacts")
    record["total_seconds"] = round(time.perf_counter() - started, 6)
    write_json(trial / "metrics.json", record)
    return record


def summarize(records, repeats, condition="both"):
    arms = {}
    for arm in ("control", "installed"):
        trials = [record for record in records if record["condition"] == arm]
        complete = len(trials) == repeats and all(record.get("tokens_complete") for record in trials)
        arms[arm] = {"trials": len(trials), "passed": sum(record["status"] == "pass" for record in trials),
                     "total_seconds": round(sum(record["total_seconds"] for record in trials), 6),
                     "median_seconds": statistics.median(record["total_seconds"] for record in trials) if trials else None,
                     "tokens_complete": complete,
                     "tokens": sum_token_maps([record["tokens"] for record in trials]) if complete else {key: None for key in TOKEN_FIELDS}}
    comparable = all(arms[arm]["passed"] == repeats and arms[arm]["tokens_complete"] for arm in arms)
    control, installed = arms["control"], arms["installed"]
    win = comparable and installed["total_seconds"] < control["total_seconds"] and installed["tokens"]["total_tokens"] < control["tokens"]["total_tokens"]
    return {"schema_version": 1, "comparison": "same-selected-pair-direct-controller",
            "repeats": repeats, "condition": condition,
            "order": [{"repeat": repeat, "condition": arm} for repeat, arm in trial_order(repeats, condition)],
            "arms": arms, "all_acceptance_passed": comparable, "installed_wins_time_and_tokens": bool(win),
            "time_saving_percent": round(100 * (1 - installed["total_seconds"] / control["total_seconds"]), 2) if comparable else None,
            "token_saving_percent": round(100 * (1 - installed["tokens"]["total_tokens"] / control["tokens"]["total_tokens"]), 2) if comparable else None,
            "limitations": ["Small task-specific sample; provider cache and latency may vary.",
                            "Includes setup, actual model execution, focused acceptance, evidence retention and cleanup.",
                            "Every attempted trial is retained; quality failures disqualify a performance win.",
                            "No nested model sessions or personal memory; aggregate Ending is outside this direct-controller comparison.",
                            "Local runtime metadata is operational evidence, not backend attestation."]}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--check-command", required=True, type=json.loads, help="JSON argv; placeholders: {python}, {workspace}, {evidence}")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--auth-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--codex-bin", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--condition", choices=("both", "control", "installed"), default="both",
                        help="Single-condition pilots never establish a comparative win")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--check-timeout", type=int, default=120)
    parser.add_argument("--check-root", type=Path, help="Immutable checker tree; content hash must remain unchanged")
    parser.add_argument("--check-dependency", action="append", type=Path, default=[],
                        help="Additional immutable checker dependency; hash before and after every trial")
    parser.add_argument("--sandbox", choices=("read-only", "workspace-write", "danger-full-access"), default="workspace-write")
    parser.add_argument("--required-skill-read", action="append", default=[])
    args = parser.parse_args(argv)
    if args.repeats < 1 or args.timeout < 1 or args.check_timeout < 1:
        parser.error("repeats and timeouts must be positive")
    if not isinstance(args.check_command, list) or not args.check_command or not all(isinstance(part, str) for part in args.check_command):
        parser.error("check-command must be a nonempty JSON string array")
    for name in ("fixture", "prompt_file", "output_dir", "source", "auth_home"):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    if not args.fixture.is_dir() or not args.prompt_file.is_file():
        parser.error("fixture directory and prompt file must exist")
    if any(path.is_symlink() for path in args.fixture.rglob("*")) or (args.fixture / ".git").exists():
        parser.error("fixture must not contain symlinks or a Git repository")
    if args.output_dir.exists():
        parser.error("output-dir must be new; never overwrite previous attempts")
    if args.check_root is not None:
        args.check_root = args.check_root.expanduser().resolve()
        if not args.check_root.is_dir():
            parser.error("check-root must be a directory")
    args.check_dependency = [path.expanduser().resolve() for path in args.check_dependency]
    if any(not path.is_file() for path in args.check_dependency):
        parser.error("check-dependency must name existing files")
    return args


def main():
    args = parse_args()
    args.output_dir.mkdir(mode=0o700, parents=True)
    prompt = prepare_frozen_inputs(args)
    private_prompt = args.output_dir / "prompt.txt"
    private_prompt.write_text(prompt, encoding="utf-8")
    records = []
    for repeat, arm in trial_order(args.repeats, args.condition):
        print(json.dumps({"event": "trial_started", "repeat": repeat, "condition": arm}), flush=True)
        records.append(run_trial(args, repeat, arm, prompt))
        write_json(args.output_dir / "trials.json", records)
        print(json.dumps({"event": "trial_finished", **records[-1]}), flush=True)
        if records[-1].get("cancelled"):
            break
    summary = summarize(records, args.repeats, args.condition)
    summary.update(requested_pair=f"{args.model}|{args.effort}",
                   prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                   required_skill_reads=args.required_skill_read,
                   source_sha256=args.source_sha256, source_final_sha256=tree_digest(args.source),
                   fixture_sha256=args.fixture_sha256, check_sha256=args.check_sha256,
                   check_dependency_sha256=[digest for _, digest in args.check_dependency_hashes],
                   sandbox=args.sandbox,
                   common_external_skill_names=sorted(path.name for path in (Path.home() / ".agents" / "skills").glob("*") if path.is_dir()))
    write_json(args.output_dir / "summary.json", summary)
    print(json.dumps({"event": "benchmark_complete", **summary}), flush=True)
    return 130 if any(record.get("cancelled") for record in records) else 0 if records and all(record["status"] == "pass" for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())

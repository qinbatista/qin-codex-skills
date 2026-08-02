#!/usr/bin/env python3
"""Deterministically bridge a frozen benchmark workload into the adaptive runner."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROMPT_PATH_ENV = "CODEX_AUTO_BENCHMARK_PROMPT_PATH"
PROMPT_SHA256_ENV = "CODEX_AUTO_BENCHMARK_WORKLOAD_SHA256"
CODEX_BIN_ENV = "CODEX_AUTO_BENCHMARK_CODEX_BIN"
CHILD_TIMEOUT_ENV = "CODEX_AUTO_BENCHMARK_CHILD_TIMEOUT"
CACHE_ROOT_ENV = "CODEX_AUTO_BENCHMARK_CACHE_ROOT"
PYTHON_ENV = "CODEX_AUTO_BENCHMARK_PYTHON"
LAUNCH_CLAIM_NAME = "adaptive-entry-launch.json"


def sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def strict_json_object(payload):
    document = json.loads(payload)
    if not isinstance(document, dict):
        raise ValueError("benchmark result must be one JSON object")
    return document


def source_tree_sha256(root):
    resolved_root = root.expanduser().resolve(strict=True)
    digest = hashlib.sha256()
    for source_path in sorted(path for path in resolved_root.rglob("*") if path.is_file()):
        if source_path.is_symlink():
            raise ValueError("benchmark source tree cannot contain symlinks")
        relative_path = source_path.relative_to(resolved_root).as_posix().encode("utf-8")
        source_bytes = source_path.read_bytes()
        digest.update(len(relative_path).to_bytes(8, "big"))
        digest.update(relative_path)
        digest.update(len(source_bytes).to_bytes(8, "big"))
        digest.update(source_bytes)
    return digest.hexdigest()


def benchmark_complexity_score(prompt_text):
    matches = re.findall(r"(?im)\bcomplexity score:\s*(\d{1,3})\b", prompt_text)
    if len(matches) != 1:
        raise ValueError("benchmark prompt must bind one complexity score")
    score = int(matches[0])
    if not 0 <= score <= 100:
        raise ValueError("benchmark complexity score is invalid")
    return score


def claim_adaptive_launch(cache_root, workload_sha256):
    cache_root = cache_root.expanduser().resolve()
    cache_root.mkdir(parents=True, exist_ok=True)
    claim_path = cache_root / LAUNCH_CLAIM_NAME
    payload = json.dumps(
        {"schema_version": 1, "workload_sha256": workload_sha256},
        ensure_ascii=False,
        separators=(",", ":"),
    ) + "\n"
    try:
        descriptor = os.open(claim_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise ValueError("benchmark adaptive producer was already launched")
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(payload)
    return claim_path


def prepare_read_only_workspace(source_root, cache_root):
    source_root = source_root.expanduser().resolve(strict=True)
    cache_root = cache_root.expanduser().resolve()
    try:
        cache_root.relative_to(source_root)
    except ValueError:
        pass
    else:
        raise ValueError("benchmark cache root must be outside the frozen source tree")
    cache_root.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="source-copy-", dir=cache_root))
    shutil.copytree(source_root, workspace, dirs_exist_ok=True, copy_function=shutil.copy2)
    if source_tree_sha256(source_root) != source_tree_sha256(workspace):
        raise ValueError("benchmark source copy does not match the frozen source tree")
    return workspace


def extract_result_document(result_text):
    text = str(result_text or "").lstrip("\ufeff")
    if text.startswith("Complexity:"):
        paragraph_end = text.find("\n\n")
        if paragraph_end < 0:
            raise ValueError("adaptive result disclosure has no result payload")
        text = text[paragraph_end + 2:]
    return strict_json_object(text)


def validated_prompt(prompt_file):
    registered_path = os.environ.get(PROMPT_PATH_ENV)
    expected_sha256 = os.environ.get(PROMPT_SHA256_ENV)
    if not registered_path or not expected_sha256:
        raise ValueError("benchmark prompt binding is unavailable")
    resolved_prompt = prompt_file.expanduser().resolve(strict=True)
    if resolved_prompt != Path(registered_path).expanduser().resolve(strict=True) or not resolved_prompt.is_file():
        raise ValueError("benchmark prompt path does not match its binding")
    prompt_bytes = resolved_prompt.read_bytes()
    if sha256_bytes(prompt_bytes) != expected_sha256:
        raise ValueError("benchmark prompt hash does not match its binding")
    prompt_text = prompt_bytes.decode("utf-8")
    if not prompt_text.strip():
        raise ValueError("benchmark prompt is empty")
    return prompt_text


def run_bridge(args):
    prompt_text = validated_prompt(args.prompt_file)
    complexity_score = benchmark_complexity_score(prompt_text)
    configured_python = Path(os.environ[PYTHON_ENV]).expanduser().resolve(strict=True)
    if configured_python != Path(sys.executable).resolve(strict=True):
        raise ValueError("benchmark bridge interpreter does not match its binding")
    codex_home = Path(os.environ["CODEX_HOME"]).expanduser().resolve(strict=True)
    adaptive_runner = codex_home / "skills" / "task-analyze-skill" / "scripts" / "obsidian_adaptive_model_runner.py"
    if not adaptive_runner.is_file():
        raise ValueError("adaptive runner is unavailable")
    codex_bin = os.environ.get(CODEX_BIN_ENV, "codex")
    timeout = int(os.environ.get(CHILD_TIMEOUT_ENV, "720"))
    cache_root = os.environ.get(CACHE_ROOT_ENV)
    if timeout <= 0:
        raise ValueError("adaptive child timeout is invalid")
    if not cache_root:
        raise ValueError("benchmark cache root binding is unavailable")
    source_root = args.workdir.expanduser().resolve(strict=True)
    cache_root = Path(cache_root)
    claim_adaptive_launch(cache_root, sha256_bytes(prompt_text.encode("utf-8")))
    workspace = prepare_read_only_workspace(source_root, cache_root)
    runtime_cache_root = workspace / "Cache" / "task-analyze"
    output_root = runtime_cache_root / "bridge-output"
    workload_id = f"benchmark-{sha256_bytes(prompt_text.encode('utf-8'))[:16]}"
    command = [sys.executable, str(adaptive_runner), "--entry-model", "gpt-5.6-luna", "--entry-effort", "max", "--sandbox", "read-only", "--project-root", str(source_root), "--task-type", "code", "--module", source_root.name, "--complexity-score", str(complexity_score), "--workload-id", workload_id, "--receipt-output", str(output_root / "receipt.json"), "--result-output", str(output_root / "result.json"), "--workdir", str(workspace), "--cache-root", str(runtime_cache_root), "--codex-bin", codex_bin, "--timeout", str(timeout), "--emit-result"]
    process = subprocess.run(command, input=prompt_text, text=True, capture_output=True, cwd=workspace, env=os.environ.copy(), shell=False, timeout=timeout + 30, check=False)
    if process.returncode != 0:
        raise RuntimeError("adaptive runner failed")
    summaries = []
    for raw_line in process.stdout.splitlines():
        try:
            summary = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(summary, dict) and "status" in summary:
            summaries.append(summary)
    if len(summaries) != 1 or summaries[0].get("status") != "pass" or not isinstance(summaries[0].get("result"), str):
        raise RuntimeError("adaptive runner did not return one passing result")
    return extract_result_document(summaries[0]["result"])


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bridge one frozen Auto benchmark workload into adaptive routing.")
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None):
    try:
        document = run_bridge(parse_args(argv))
    except (KeyError, OSError, UnicodeError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"benchmark auto bridge failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(document, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

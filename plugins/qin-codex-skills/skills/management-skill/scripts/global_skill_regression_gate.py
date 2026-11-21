#!/usr/bin/env python3
"""Run and report the retained-capability regression gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager, nullcontext
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "workflow-skill" / "scripts"))
from task_artifact_paths import resolve_task_artifact_root, task_artifact_scope, validate_task_directory, verify_cache_git


CATALOG_RELATIVE_PATH = Path("management-skill/assets/global-skill-capability-catalog.json")
PROJECT_TESTING_SKILL_RELATIVE_PATH = Path(".agents/skills/testing-skill")
PROJECT_AI_INDEX_SKILL_RELATIVE_PATH = Path("skills/ai-index")
PLUGIN_RELEASE_INPUTS = (
    Path("plugins/qin-codex-skills"),
    Path(".github/actions/publish-plugin"),
    Path(".github/workflows/publish-plugin.yml"),
)
DEFAULT_REPORT_RELATIVE_PATH = Path("global-skill-regression/latest.json")
DEFAULT_HISTORY_RELATIVE_PATH = Path("global-skill-regression/history.jsonl")
EXCLUDED_PARTS = {".git", "__pycache__", "cache", "Cache", "outputs", "work", "local", ".venv", "venv", "node_modules", "dist", "build", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}
CHECKOUT_NEUTRAL_TEXT_SUFFIXES = {".json", ".md", ".py", ".svg", ".yaml", ".yml"}
REQUIRED_PLUGIN_CONTRACTS = (("chrome", "control-chrome"), ("sites", "sites-building"), ("muse-ai-plugin", "muse-ai-dev-skill"))
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkout_neutral_file_bytes(path: Path) -> bytes:
    """Normalize CRLF only for known text files materialized by Git checkout."""
    contents = path.read_bytes()
    if path.suffix.lower() not in CHECKOUT_NEUTRAL_TEXT_SUFFIXES and path.name != ".gitignore":
        return contents
    try:
        return contents.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
    except UnicodeDecodeError:
        return contents


def attestation_watched_file_sha256(path: Path) -> str:
    """Hash watched source semantics independently of checkout line endings."""
    return hashlib.sha256(checkout_neutral_file_bytes(path)).hexdigest()


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog(project_root: Path) -> dict[str, object]:
    catalog_path = project_root / CATALOG_RELATIVE_PATH
    catalog = load_json(catalog_path)
    if catalog.get("schema_version") != 1:
        raise RuntimeError("global Skill capability catalog schema_version must be 1")
    checks = catalog.get("checks")
    capabilities = catalog.get("capabilities")
    if not isinstance(checks, list) or not isinstance(capabilities, list):
        raise RuntimeError("global Skill capability catalog must define checks and capabilities")
    check_ids = [str(check.get("id")) for check in checks]
    capability_ids = [str(capability.get("id")) for capability in capabilities]
    if len(check_ids) != len(set(check_ids)) or len(capability_ids) != len(set(capability_ids)):
        raise RuntimeError("global Skill capability and check IDs must be unique")
    known_checks = set(check_ids)
    for capability in capabilities:
        required = capability.get("checks")
        if not isinstance(required, list) or not required or not set(map(str, required)).issubset(known_checks):
            raise RuntimeError(f"capability has missing or unknown checks: {capability.get('id')}")
    return catalog


def included_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts) or path.suffix in EXCLUDED_SUFFIXES:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in included_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(checkout_neutral_file_bytes(path))
        digest.update(b"\0")
    return digest.hexdigest()


def managed_digest(root: Path, managed_skills: list[str]) -> str:
    digest = hashlib.sha256()
    for skill_name in managed_skills:
        skill_root = root / skill_name
        digest.update(skill_name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(tree_digest(skill_root).encode("ascii") if skill_root.is_dir() else b"missing")
        digest.update(b"\0")
    return digest.hexdigest()


def copy_candidate(source_root: Path, candidate_root: Path, managed_skills: list[str], global_agents: str, structural_agents: str) -> None:
    candidate_root.mkdir(parents=True)
    for skill_name in managed_skills:
        source = source_root / skill_name
        if not source.is_dir():
            continue
        shutil.copytree(
            source,
            candidate_root / skill_name,
            ignore=shutil.ignore_patterns(*EXCLUDED_PARTS, "*.pyc", "*.pyo", "*.log"),
        )
    (candidate_root.parent / "AGENTS.md").write_text(global_agents, encoding="utf-8")
    (candidate_root / "AGENTS.md").write_text(structural_agents, encoding="utf-8")


def copy_required_plugin_contracts(plugin_cache: Path, candidate_cache: Path) -> None:
    """Populate only candidate-time plugin contracts needed by structural checks.

    A release gate running in GitHub has no access to a user's installed plugin
    cache.  Its validators need discoverability of the two externally owned
    skills, but never execute their implementation.  Use a clearly marked
    ephemeral contract fixture only in that isolated candidate when a real
    cache is unavailable; runtime/deployment still resolves the real plugin.
    """
    for plugin_id, skill_name in REQUIRED_PLUGIN_CONTRACTS:
        matches = sorted(plugin_cache.glob(f"*/{plugin_id}/*/skills/{skill_name}/SKILL.md")) if plugin_cache.is_dir() else []
        if not matches:
            fixture = candidate_cache / "ci-contract-fixture" / plugin_id / "0.0.0" / "skills" / skill_name / "SKILL.md"
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(
                f"# Candidate-only contract fixture for {plugin_id}:{skill_name}\n\n"
                "This file exists only while structural release validation runs. "
                "It is not an installed runtime plugin.\n",
                encoding="utf-8",
            )
        else:
            source = matches[-1].parent
            target = candidate_cache / source.relative_to(plugin_cache)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, target)


def project_task_cache_root(project_root: Path, cache_root: Path) -> Path:
    path = validate_task_directory(cache_root, project_root)
    verify_cache_git(project_root, path)
    return path


@contextmanager
def candidate_layouts(project_root: Path, deployed_root: Path, managed_skills: list[str], *,
                      layout_run_root: Path | None = None, layout_owner_project: Path | None = None):
    asset = project_root / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
    directive = "This template is written only by the explicit `install-global-agents` command; deploy, pull, and sync preserve user AGENTS.md files.\n\n"
    text = asset.read_text(encoding="utf-8")
    if not text.startswith(directive):
        raise RuntimeError("global AGENTS asset is missing its explicit-install directive")
    configured_cache_root = os.environ.get("CODEX_PROJECT_CACHE_ROOT")
    structural_agents_path = project_root / "AGENTS.md"
    structural_agents = structural_agents_path.read_text(encoding="utf-8") if structural_agents_path.is_file() else "# qin-codex-skills\n"
    if layout_run_root is None:
        layout_scope = task_artifact_scope(project_root, "global-skill-regression-candidates", borrowed_root=configured_cache_root)
    else:
        if layout_owner_project is None:
            raise ValueError("shallow candidate layout requires its exact project owner")
        owner = layout_owner_project.resolve(strict=True)
        borrowed = validate_task_directory(layout_run_root, owner)
        if not project_root.is_relative_to(borrowed) or not deployed_root.is_relative_to(borrowed):
            raise ValueError("shallow candidate layout must remain inside its publication run")
        layout_scope = nullcontext(borrowed)
    with layout_scope as cache_root:
        verify_cache_git(project_root if layout_run_root is None else layout_owner_project, cache_root)
        with tempfile.TemporaryDirectory(prefix="c-", dir=cache_root) as temporary:
            workspace = Path(temporary)
            source_candidate = workspace / "s" / "k"
            deployed_candidate = workspace / "d" / "k"
            copy_candidate(project_root, source_candidate, managed_skills, text[len(directive):], structural_agents)
            copy_candidate(deployed_root, deployed_candidate, managed_skills, text[len(directive):], structural_agents)
            # Both isolated project roots need the real Cache ignore boundary.
            # On Windows, their enclosing publication clone can be a Git repo.
            ignore_rules = (project_root / ".gitignore").read_bytes()
            for root in (source_candidate, deployed_candidate):
                (root / ".gitignore").write_bytes(ignore_rules)
            for name in ("README.md", "README.zh.md"):
                if (project_root / name).is_file():
                    shutil.copy2(project_root / name, source_candidate / name)
            source_inputs = (
                PROJECT_TESTING_SKILL_RELATIVE_PATH,
                PROJECT_AI_INDEX_SKILL_RELATIVE_PATH,
                Path(".github/workflows/ci.yml"),
                *PLUGIN_RELEASE_INPUTS,
            )
            for relative in source_inputs:
                source = project_root / relative
                target = source_candidate / relative
                if source.is_dir():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(source, target, ignore=shutil.ignore_patterns(*EXCLUDED_PARTS, "*.pyc", "*.pyo", "*.log"))
                elif source.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
            plugin_cache = deployed_root.resolve().parent / "plugins" / "cache"
            copy_required_plugin_contracts(plugin_cache, source_candidate.parent / "plugins" / "cache")
            copy_required_plugin_contracts(plugin_cache, deployed_candidate.parent / "plugins" / "cache")
            previous_fixture_root = os.environ.get("QIN_SKILL_GATE_FIXTURE_ROOT")
            if os.name == "nt":
                os.environ["QIN_SKILL_GATE_FIXTURE_ROOT"] = str(cache_root)
            try:
                yield {"source": source_candidate, "deployed": deployed_candidate}
            finally:
                if os.name == "nt":
                    if previous_fixture_root is None:
                        os.environ.pop("QIN_SKILL_GATE_FIXTURE_ROOT", None)
                    else:
                        os.environ["QIN_SKILL_GATE_FIXTURE_ROOT"] = previous_fixture_root


def parse_test_count(output: str) -> int:
    matches = re.findall(r"Ran\s+(\d+)\s+tests?", output)
    if matches:
        return sum(int(value) for value in matches)
    for line in reversed(output.splitlines()):
        stripped = line.strip()
        if not stripped.startswith("{"):
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        for key in ("checks", "test_count", "trial_count"):
            value = payload.get(key)
            if isinstance(value, int) and value > 0:
                return value
    return 1


def sanitized_tail(text: str, replacements: dict[str, str]) -> str:
    value = text[-4000:]
    for original, replacement in replacements.items():
        value = value.replace(original, replacement)
    return value


def command_result(check_id: str, target: str, command: list[str], root: Path, timeout_seconds: int, replacements: dict[str, str]) -> dict[str, object]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if os.name == "nt":
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
    with task_artifact_scope(root, f"global-skill-check:{target}:{check_id}") as cache_root:
        verify_cache_git(root, cache_root)
        temporary_cache = cache_root / "tmp"
        temporary_cache.mkdir()
        environment["CODEX_PROJECT_CACHE_ROOT"] = str(cache_root)
        for variable in ("TMP", "TEMP", "TMPDIR"):
            environment[variable] = str(temporary_cache)
        environment.pop("YOFA_TASK_ARTIFACT_ROOT", None)
        for variable in ("ENDING_MEMORY_TEST_CACHE", "ENDING_CONCURRENCY_TEST_CACHE", "ENDING_LAUNCH_TEST_CACHE", "PROJECT_CHANGE_MEMORY_TEST_CACHE", "PROJECT_KNOWLEDGE_TEST_CACHE", "TASK_RESOURCE_LEDGER_TEST_CACHE", "ENDING_RESOURCE_AUDIT_TEST_CACHE"):
            environment[variable] = str(temporary_cache)
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout_seconds, check=False, env=environment, **hidden_process_options())
    combined = completed.stdout + "\n" + completed.stderr
    count = parse_test_count(combined)
    passed = completed.returncode == 0 and count > 0
    return {
        "check_id": check_id,
        "target": target,
        "kind": "command",
        "status": "pass" if passed else "fail",
        "exit_code": completed.returncode,
        "test_count": count,
        "passed_count": count if passed else 0,
        "command": ["<python>" if value == sys.executable else sanitized_tail(value, replacements) for value in command],
        "stdout_tail": "" if passed else sanitized_tail(completed.stdout, replacements),
        "stderr_tail": "" if passed else sanitized_tail(completed.stderr, replacements),
    }


def public_skill_set_result(check_id: str, target: str, root: Path, managed_skills: list[str]) -> dict[str, object]:
    discovered = sorted(path.parent.name for path in root.glob("*/SKILL.md"))
    expected = sorted(managed_skills)
    passed = discovered == expected if target == "source" else set(expected).issubset(discovered)
    return {
        "check_id": check_id,
        "target": target,
        "kind": "builtin",
        "status": "pass" if passed else "fail",
        "test_count": 1,
        "passed_count": 1 if passed else 0,
        "expected": expected,
        "discovered": discovered,
    }


def deployment_parity_result(check_id: str, project_root: Path, deployed_root: Path, managed_skills: list[str]) -> dict[str, object]:
    differences = []
    for skill_name in managed_skills:
        source = project_root / skill_name
        deployed = deployed_root / skill_name
        if not source.is_dir() or not deployed.is_dir() or tree_digest(source) != tree_digest(deployed):
            differences.append(skill_name)
    passed = not differences
    return {
        "check_id": check_id,
        "target": "cross",
        "kind": "builtin",
        "status": "pass" if passed else "fail",
        "test_count": len(managed_skills),
        "passed_count": len(managed_skills) - len(differences),
        "differences": differences,
    }


def global_agents_parity_result(check_id: str, project_root: Path, deployed_root: Path) -> dict[str, object]:
    source_asset = project_root / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
    deployed_asset = deployed_root / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
    directive = "This template is written only by the explicit `install-global-agents` command; deploy, pull, and sync preserve user AGENTS.md files.\n\n"
    source_text = source_asset.read_text(encoding="utf-8") if source_asset.is_file() else ""
    deployed_text = deployed_asset.read_text(encoding="utf-8") if deployed_asset.is_file() else ""
    source_template = source_text[len(directive):] if source_text.startswith(directive) else ""
    deployed_template = deployed_text[len(directive):] if deployed_text.startswith(directive) else ""
    failures = []
    if not source_template:
        failures.append(str(source_asset))
    if source_template != deployed_template:
        failures.append(str(deployed_asset))
    passed = not failures
    return {
        "check_id": check_id,
        "target": "cross",
        "kind": "builtin",
        "status": "pass" if passed else "fail",
        "test_count": 1,
        "passed_count": 1 if passed else 0,
        "failed_targets": failures,
    }


def attestation_result(check: dict[str, object], project_root: Path) -> dict[str, object]:
    check_id = str(check["id"])
    path = project_root / str(check["path"])
    errors: list[str] = []
    payload: dict[str, object] = {}
    evidence_payload: dict[str, object] = {}
    evidence_path = project_root / str(check.get("evidence", ""))
    if not path.is_file():
        errors.append("attestation is missing")
    else:
        try:
            payload = load_json(path)
            evidence_payload = load_json(evidence_path) if check.get("bind_evidence") is True and evidence_path.is_file() else {}
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"attestation or bound evidence is unreadable: {error}")
    if payload and (payload.get("schema_version") != 1 or payload.get("status") != "pass" or payload.get("check_id") != check_id):
        errors.append("attestation identity or status is invalid")
    if check.get("bind_evidence") is True:
        if not evidence_path.is_file():
            errors.append("attestation evidence is missing")
        elif payload.get("evidence_sha256") != sha256_file(evidence_path):
            errors.append("attestation evidence digest is stale")
    expected_files = list(map(str, check.get("watched_files", [])))
    watched = payload.get("watched_files", {}) if payload else {}
    if not isinstance(watched, dict) or sorted(watched) != sorted(expected_files):
        errors.append("attestation watched-file set is incomplete")
    else:
        for relative in expected_files:
            source = project_root / relative
            if not source.is_file() or watched.get(relative) != attestation_watched_file_sha256(source):
                errors.append(f"stale watched file: {relative}")
    total = payload.get("trial_count", 1) if payload else 1
    passed_count = payload.get("passed_trials", 0) if payload else 0
    if not isinstance(total, int) or total < 1 or not isinstance(passed_count, int) or passed_count != total:
        errors.append("attestation trial counts are not a complete pass")
        total = 1
        passed_count = 0
    return {
        "check_id": check_id,
        "target": "source",
        "kind": "attestation",
        "status": "pass" if not errors else "fail",
        "test_count": total,
        "passed_count": passed_count if not errors else 0,
        "errors": errors,
        "attestation": str(check["path"]),
    }


def selected_targets(mode: str, declared: list[str]) -> list[str]:
    if mode == "source":
        return [target for target in declared if target == "source"]
    if mode == "deployed":
        return [target for target in declared if target in {"deployed", "cross"}]
    return list(declared)


def run_check(check: dict[str, object], target: str, project_root: Path, deployed_root: Path, execution_roots: dict[str, Path], managed_skills: list[str]) -> dict[str, object]:
    check_id = str(check["id"])
    kind = str(check["kind"])
    if kind == "attestation":
        return attestation_result(check, project_root)
    if kind == "builtin":
        if check_id == "public-skill-set":
            return public_skill_set_result(check_id, target, project_root if target == "source" else deployed_root, managed_skills)
        if check_id == "deployment-parity":
            return deployment_parity_result(check_id, project_root, deployed_root, managed_skills)
        if check_id == "global-agents-parity":
            return global_agents_parity_result(check_id, project_root, deployed_root)
        raise RuntimeError(f"unknown builtin gate check: {check_id}")
    root = project_root if check_id == "git-diff-check" else execution_roots[target]
    command = [
        str(value)
        .replace("{python}", sys.executable)
        .replace("{global_agents}", str(root.parent / "AGENTS.md"))
        .replace("{root}", str(root))
        for value in check.get("command", [])
    ]
    replacements = {
        str(project_root): "<source-root>",
        str(deployed_root): "<deployed-root>",
        str(execution_roots["source"]): "<source-candidate>",
        str(execution_roots["deployed"]): "<deployed-candidate>",
        str(Path.home()): "<home>",
    }
    return command_result(check_id, target, command, root, int(check.get("timeout_seconds", 300)), replacements)


def capability_results(catalog: dict[str, object], results: list[dict[str, object]]) -> list[dict[str, object]]:
    by_check: dict[str, list[dict[str, object]]] = {}
    for result in results:
        by_check.setdefault(str(result["check_id"]), []).append(result)
    summaries = []
    for capability in catalog["capabilities"]:
        matched = [result for check_id in capability["checks"] for result in by_check.get(str(check_id), [])]
        runs = len(matched)
        passed_runs = sum(result["status"] == "pass" for result in matched)
        tests = sum(int(result.get("test_count", 0)) for result in matched)
        passed_tests = sum(int(result.get("passed_count", 0)) for result in matched)
        status = "pass" if runs and passed_runs == runs and tests == passed_tests else "fail"
        summaries.append({
            "id": capability["id"],
            "owner_skill": capability["owner_skill"],
            "name": capability["name"],
            "function": capability["function"],
            "test_runs": runs,
            "passed_runs": passed_runs,
            "test_count": tests,
            "passed_count": passed_tests,
            "status": status,
        })
    return summaries


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


def append_history(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    compact = {key: report[key] for key in ("schema_version", "run_id", "created_at", "mode", "status", "source_digest", "deployed_digest", "summary")}
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(compact, ensure_ascii=False, separators=(",", ":")) + "\n")


def run_gate(project_root: Path, deployed_root: Path, mode: str, *,
             layout_run_root: Path | None = None, layout_owner_project: Path | None = None) -> dict[str, object]:
    catalog = load_catalog(project_root)
    managed_skills = list(map(str, catalog["managed_skills"]))
    results = []
    with candidate_layouts(project_root, deployed_root, managed_skills,
                           layout_run_root=layout_run_root, layout_owner_project=layout_owner_project) as execution_roots:
        for check in catalog["checks"]:
            for target in selected_targets(mode, list(map(str, check["targets"]))):
                try:
                    results.append(run_check(check, target, project_root, deployed_root, execution_roots, managed_skills))
                except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
                    results.append({
                        "check_id": check["id"],
                        "target": target,
                        "kind": check["kind"],
                        "status": "fail",
                        "test_count": 1,
                        "passed_count": 0,
                        "errors": [str(error).replace(str(project_root), "<source-root>").replace(str(deployed_root), "<deployed-root>").replace(str(Path.home()), "<home>")],
                    })
    capabilities = capability_results(catalog, results)
    passed_checks = sum(result["status"] == "pass" for result in results)
    total_tests = sum(int(result.get("test_count", 0)) for result in results)
    passed_tests = sum(int(result.get("passed_count", 0)) for result in results)
    status = "pass" if passed_checks == len(results) and all(item["status"] == "pass" for item in capabilities) else "fail"
    source_digest = managed_digest(project_root, managed_skills)
    deployed_digest = ""
    if deployed_root.is_dir():
        deployed_digest = managed_digest(deployed_root, managed_skills)
    return {
        "schema_version": 1,
        "run_id": hashlib.sha256(f"{utc_now()}:{mode}:{source_digest}".encode("utf-8")).hexdigest()[:16],
        "created_at": utc_now(),
        "mode": mode,
        "status": status,
        "source_digest": source_digest,
        "deployed_digest": deployed_digest,
        "summary": {
            "check_runs": len(results),
            "passed_check_runs": passed_checks,
            "test_count": total_tests,
            "passed_count": passed_tests,
            "capability_count": len(capabilities),
            "passed_capabilities": sum(item["status"] == "pass" for item in capabilities),
        },
        "capabilities": capabilities,
        "checks": results,
        "retired_architectures": catalog["retired_architectures"],
    }


def validate_code_samples(evidence: dict[str, object]) -> tuple[int, int]:
    projects = evidence.get("projects", [])
    passed = evidence.get("overall_verdict") == "PASS" and isinstance(projects, list) and len(projects) == 3 and all(project.get("verdict") == "PASS" for project in projects)
    return len(projects) if isinstance(projects, list) else 0, len(projects) if passed else 0


def create_attestation(project_root: Path, check_id: str) -> dict[str, object]:
    catalog = load_catalog(project_root)
    check = next((item for item in catalog["checks"] if item.get("id") == check_id), None)
    if check is None or check.get("kind") != "attestation":
        raise RuntimeError(f"unknown attestation check: {check_id}")
    evidence_path = project_root / str(check["evidence"])
    if not evidence_path.is_file():
        raise RuntimeError(f"attestation evidence is missing: {check['evidence']}")
    evidence = load_json(evidence_path)
    if check_id == "code-sample-attestation":
        trial_count, passed_trials = validate_code_samples(evidence)
    else:
        raise RuntimeError(f"no evidence validator for attestation: {check_id}")
    if trial_count < 1 or passed_trials != trial_count:
        raise RuntimeError(f"real evidence did not pass for attestation: {check_id}")
    payload = {
        "schema_version": 1,
        "check_id": check_id,
        "status": "pass",
        "created_at": utc_now(),
        "trial_count": trial_count,
        "passed_trials": passed_trials,
        "watched_files": {relative: attestation_watched_file_sha256(project_root / relative) for relative in check["watched_files"]},
    }
    if check.get("bind_evidence") is True:
        payload["evidence_sha256"] = sha256_file(evidence_path)
    output = project_root / str(check["path"])
    write_report(output, payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the retained global Skill regression release gate.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    check_parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".agents" / "skills")
    check_parser.add_argument("--mode", choices=("source", "deployed", "release"), required=True)
    check_parser.add_argument("--layout-run-root", type=Path)
    check_parser.add_argument("--layout-owner-project", type=Path)
    check_parser.add_argument("--output", type=Path)
    check_parser.add_argument("--history", type=Path)
    attest_parser = subparsers.add_parser("attest")
    attest_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    attest_parser.add_argument("--check-id", choices=("code-sample-attestation", "memory-execution-consistency-attestation"), required=True)
    args = parser.parse_args()
    project_root = args.project_root.expanduser().resolve()
    if args.command == "attest":
        print(json.dumps(create_attestation(project_root, args.check_id), ensure_ascii=False, indent=2))
        return 0
    layout_options = ({"layout_run_root": args.layout_run_root, "layout_owner_project": args.layout_owner_project}
                      if args.layout_run_root is not None else {})
    report = run_gate(project_root, args.skills_dir.expanduser().resolve(), args.mode, **layout_options)
    configured_cache_root = os.environ.get("CODEX_PROJECT_CACHE_ROOT")
    if configured_cache_root:
        task_cache = project_task_cache_root(project_root, Path(configured_cache_root))
        default_output = task_cache / "global-skill-regression" / "latest.json"
        default_history = task_cache / "global-skill-regression" / "history.jsonl"
    else:
        task_cache = resolve_task_artifact_root(project_root, "global-skill-regression-reports")
        default_output = task_cache / DEFAULT_REPORT_RELATIVE_PATH
        default_history = task_cache / DEFAULT_HISTORY_RELATIVE_PATH
    output = args.output if args.output else default_output
    history = args.history if args.history else default_history
    validate_task_directory(output.parent, project_root)
    validate_task_directory(history.parent, project_root)
    write_report(output, report)
    append_history(history, report)
    print(json.dumps({"status": report["status"], **report["summary"], "report": str(output)}, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

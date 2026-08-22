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
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


CATALOG_RELATIVE_PATH = Path("management-skill/assets/global-skill-capability-catalog.json")
DEFAULT_REPORT_RELATIVE_PATH = Path("Cache/remote-test/global-skill-regression/latest.json")
DEFAULT_HISTORY_RELATIVE_PATH = Path("Cache/remote-test/global-skill-regression/history.jsonl")
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


@contextmanager
def candidate_layouts(project_root: Path, deployed_root: Path, managed_skills: list[str]):
    asset = project_root / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
    directive = "Merge this section into `~/.codex/AGENTS.md` and `~/AGENTS.md`.\n\n"
    text = asset.read_text(encoding="utf-8")
    if not text.startswith(directive):
        raise RuntimeError("global AGENTS asset is missing its merge directive")
    configured_cache_root = os.environ.get("CODEX_PROJECT_CACHE_ROOT")
    temporary_cache_root = tempfile.TemporaryDirectory(prefix="codex-skill-candidates-") if os.name == "nt" and not configured_cache_root else None
    cache_root = Path(configured_cache_root).expanduser() if configured_cache_root else Path(temporary_cache_root.name) if temporary_cache_root is not None else project_root / "Cache" / "remote-test" / "global-skill-regression"
    cache_root.mkdir(parents=True, exist_ok=True)
    structural_agents_path = project_root / "AGENTS.md"
    structural_agents = structural_agents_path.read_text(encoding="utf-8") if structural_agents_path.is_file() else "# qin-codex-skills\n"
    try:
        with tempfile.TemporaryDirectory(prefix="candidate-", dir=cache_root) as temporary:
            workspace = Path(temporary)
            source_candidate = workspace / "source" / "skills"
            deployed_candidate = workspace / "deployed" / "skills"
            copy_candidate(project_root, source_candidate, managed_skills, text[len(directive):], structural_agents)
            copy_candidate(deployed_root, deployed_candidate, managed_skills, text[len(directive):], structural_agents)
            plugin_cache = deployed_root.resolve().parent / "plugins" / "cache"
            copy_required_plugin_contracts(plugin_cache, source_candidate.parent / "plugins" / "cache")
            copy_required_plugin_contracts(plugin_cache, deployed_candidate.parent / "plugins" / "cache")
            yield {"source": source_candidate, "deployed": deployed_candidate}
    finally:
        if temporary_cache_root is not None:
            temporary_cache_root.cleanup()


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
    temporary_cache = None
    if os.name == "nt":
        environment["PYTHONUTF8"] = "1"
        environment["PYTHONIOENCODING"] = "utf-8"
        temporary_cache = tempfile.mkdtemp(prefix="codex-skill-gate-")
        environment["CODEX_PROJECT_CACHE_ROOT"] = temporary_cache
    try:
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=timeout_seconds, check=False, env=environment)
    finally:
        if temporary_cache is not None:
            shutil.rmtree(temporary_cache, ignore_errors=True)
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
    asset = project_root / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
    directive = "Merge this section into `~/.codex/AGENTS.md` and `~/AGENTS.md`.\n\n"
    text = asset.read_text(encoding="utf-8") if asset.is_file() else ""
    expected = text[len(directive):] if text.startswith(directive) else ""
    codex_root = deployed_root.resolve().parent
    targets = [codex_root / "AGENTS.md"]
    if codex_root.name == ".codex":
        targets.append(codex_root.parent / "AGENTS.md")
    failures = [str(path) for path in targets if not path.is_file() or path.read_text(encoding="utf-8") != expected]
    passed = bool(expected) and not failures
    return {
        "check_id": check_id,
        "target": "cross",
        "kind": "builtin",
        "status": "pass" if passed else "fail",
        "test_count": len(targets),
        "passed_count": len(targets) - len(failures),
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
        elif check_id == "memory-execution-consistency-attestation" and validate_memory_execution_consistency(evidence_payload) != (7, 7):
            errors.append("memory-execution consistency evidence is not a complete real pass")
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


def run_gate(project_root: Path, deployed_root: Path, mode: str) -> dict[str, object]:
    catalog = load_catalog(project_root)
    managed_skills = list(map(str, catalog["managed_skills"]))
    results = []
    with candidate_layouts(project_root, deployed_root, managed_skills) as execution_roots:
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


def validate_unity_trials(evidence: dict[str, object]) -> tuple[int, int]:
    trials = evidence.get("trials", [])
    passed = evidence.get("status") == "pass" and evidence.get("trial_count") == 5 and evidence.get("passed_trials") == 5 and evidence.get("source_hashes_unchanged") is True and evidence.get("project_agents_unchanged") is True and evidence.get("all_work_copies_deleted") is True and evidence.get("unity_compile_requested") is True
    if passed and isinstance(trials, list):
        passed = len(trials) == 5 and all(trial.get("status") == "pass" and trial.get("unity_compile", {}).get("status") == "pass" and trial.get("unity_compile", {}).get("exit_code") == 0 and trial.get("work_copy_deleted") is True for trial in trials)
    return len(trials) if isinstance(trials, list) else 0, len(trials) if passed else 0


def validate_memory_execution_consistency(evidence: dict[str, object]) -> tuple[int, int]:
    required_ids = {"memory-record-correction", "memory-projection-reconcile", "skill-contract-defect", "execution-drift", "next-task-effective-recall", "invalid-result-integrity", "coverage-authority-integrity"}
    scenarios = evidence.get("scenarios", {})
    if not isinstance(scenarios, dict):
        return 0, 0
    record_correction = scenarios.get("memory-record-correction", {})
    projection_reconcile = scenarios.get("memory-projection-reconcile", {})
    skill_defect = scenarios.get("skill-contract-defect", {})
    execution_drift = scenarios.get("execution-drift", {})
    next_recall = scenarios.get("next-task-effective-recall", {})
    invalid_result_integrity = scenarios.get("invalid-result-integrity", {})
    coverage_authority_integrity = scenarios.get("coverage-authority-integrity", {})
    all_scenarios_pass = set(scenarios) == required_ids and all(isinstance(scenario, dict) and scenario.get("status") == "pass" for scenario in scenarios.values())
    record_correction_pass = record_correction.get("classification") == "memory_record_defect" and record_correction.get("correction_written") is True and record_correction.get("source_unchanged") is True
    projection_reconcile_pass = projection_reconcile.get("classification") == "memory_projection_defect" and projection_reconcile.get("reconciled") is True
    producer_defects_pass = skill_defect.get("classification") == "skill_contract_defect" and skill_defect.get("memory_write") is False and skill_defect.get("return_to_origin") is True and execution_drift.get("classification") == "execution_drift" and execution_drift.get("memory_write") is False and execution_drift.get("return_to_origin") is True
    next_recall_pass = next_recall.get("effective_only") is True and next_recall.get("superseded_hidden") is True
    invalid_result_pass = invalid_result_integrity.get("placeholder_rejected") is True and invalid_result_integrity.get("disposable_store_and_vault") is True and invalid_result_integrity.get("canonical_owner_readback") is True and invalid_result_integrity.get("exact_id_tombstone") is True and invalid_result_integrity.get("reconcile_blocked") is True
    coverage_authority_pass = coverage_authority_integrity.get("vault_parent_store_absent") is True and coverage_authority_integrity.get("canonical_store_used") is True and coverage_authority_integrity.get("two_model_stores_shared_authority") is True and coverage_authority_integrity.get("concurrent_projection_preserved") is True and coverage_authority_integrity.get("rogue_store_merge_verified") is True
    passed = evidence.get("schema_version") == 1 and evidence.get("check_id") == "memory-execution-consistency-attestation" and evidence.get("status") == "pass" and all_scenarios_pass and record_correction_pass and projection_reconcile_pass and producer_defects_pass and next_recall_pass and invalid_result_pass and coverage_authority_pass
    return len(scenarios), len(scenarios) if passed else 0


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
    elif check_id == "unity-five-attestation":
        trial_count, passed_trials = validate_unity_trials(evidence)
    elif check_id == "memory-execution-consistency-attestation":
        trial_count, passed_trials = validate_memory_execution_consistency(evidence)
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
    check_parser.add_argument("--skills-dir", type=Path, default=Path.home() / ".codex" / "skills")
    check_parser.add_argument("--mode", choices=("source", "deployed", "release"), required=True)
    check_parser.add_argument("--output", type=Path)
    check_parser.add_argument("--history", type=Path)
    attest_parser = subparsers.add_parser("attest")
    attest_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    attest_parser.add_argument("--check-id", choices=("code-sample-attestation", "unity-five-attestation", "memory-execution-consistency-attestation"), required=True)
    args = parser.parse_args()
    project_root = args.project_root.expanduser().resolve()
    if args.command == "attest":
        print(json.dumps(create_attestation(project_root, args.check_id), ensure_ascii=False, indent=2))
        return 0
    report = run_gate(project_root, args.skills_dir.expanduser().resolve(), args.mode)
    output = args.output.expanduser().resolve() if args.output else project_root / DEFAULT_REPORT_RELATIVE_PATH
    history = args.history.expanduser().resolve() if args.history else project_root / DEFAULT_HISTORY_RELATIVE_PATH
    write_report(output, report)
    append_history(history, report)
    print(json.dumps({"status": report["status"], **report["summary"], "report": str(output)}, ensure_ascii=False))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

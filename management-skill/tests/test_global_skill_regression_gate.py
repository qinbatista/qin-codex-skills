import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "global_skill_regression_gate.py"
MODULE_SPEC = importlib.util.spec_from_file_location("global_skill_regression_gate", MODULE_PATH)
GATE = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(GATE)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class GlobalSkillRegressionGateTests(unittest.TestCase):
    def _memory_consistency_evidence(self):
        return {
            "schema_version": 1,
            "check_id": "memory-execution-consistency-attestation",
            "status": "pass",
            "trial_count": 7,
            "passed_trials": 7,
            "execution": {
                "current_platform": "test",
                "host_boundary": "portable-python",
                "disposable_runtime_removed": True,
            },
            "scenarios": {
                "memory-record-correction": {"status": "pass", "classification": "memory_record_defect", "correction_written": True, "source_unchanged": True},
                "memory-projection-reconcile": {"status": "pass", "classification": "memory_projection_defect", "reconciled": True},
                "skill-contract-defect": {"status": "pass", "classification": "skill_contract_defect", "memory_write": False, "return_to_origin": True},
                "execution-drift": {"status": "pass", "classification": "execution_drift", "memory_write": False, "return_to_origin": True},
                "next-task-effective-recall": {"status": "pass", "effective_only": True, "superseded_hidden": True},
                "invalid-result-integrity": {"status": "pass", "placeholder_rejected": True, "disposable_store_and_vault": True, "canonical_owner_readback": True, "exact_id_tombstone": True, "reconcile_blocked": True},
                "coverage-authority-integrity": {"status": "pass", "vault_parent_store_absent": True, "canonical_store_used": True, "two_model_stores_shared_authority": True, "concurrent_projection_preserved": True, "rogue_store_merge_verified": True},
            },
        }

    def test_catalog_has_stable_unique_retained_capabilities_and_referenced_checks(self):
        catalog = GATE.load_catalog(PROJECT_ROOT)
        capability_ids = [item["id"] for item in catalog["capabilities"]]
        check_ids = {item["id"] for item in catalog["checks"]}
        referenced = {check_id for item in catalog["capabilities"] for check_id in item["checks"]}
        self.assertEqual(len(capability_ids), 36)
        self.assertEqual(len(capability_ids), len(set(capability_ids)))
        self.assertEqual(check_ids, referenced)
        projectless_ending = next(item for item in catalog["capabilities"] if item["id"] == "GSR-014")
        self.assertIn("绝对 origin project root", projectless_ending["function"])
        self.assertIn("projectless cwd", projectless_ending["function"])
        self.assertIn("plan、evidence、receipt", projectless_ending["function"])
        fast_ending = next(item for item in catalog["capabilities"] if item["id"] == "GSR-026")
        self.assertIn("gpt-5.3-codex-spark|xhigh", fast_ending["function"])
        self.assertIn("Luna-low", fast_ending["function"])
        consistency = next(item for item in catalog["capabilities"] if item["id"] == "GSR-027")
        self.assertIn("effective", consistency["function"])
        self.assertIn("memory-execution-consistency-attestation", consistency["checks"])
        consistency_check = next(item for item in catalog["checks"] if item["id"] == "memory-execution-consistency-attestation")
        self.assertTrue(consistency_check["bind_evidence"])
        self.assertTrue({"AGENTS.md", "project-memory-skill/scripts/project_change_memory.py", "project-memory-skill/scripts/memory_coverage.py", "project-memory-skill/scripts/obsidian_model_memory.py", "project-memory-skill/tests/test_project_change_memory.py", "project-memory-skill/tests/test_memory_coverage.py", "project-memory-skill/tests/test_obsidian_model_memory.py", "verify-skill/scripts/ending_verification_plan.py", "verify-skill/scripts/ending_task_ledger.py", "workflow-skill/SKILL.md", "management-skill/scripts/global_skill_regression_gate.py"}.issubset(consistency_check["watched_files"]))
        integrity = next(item for item in catalog["capabilities"] if item["id"] == "GSR-028")
        self.assertIn("exact-ID", integrity["function"])
        coverage_integrity = next(item for item in catalog["capabilities"] if item["id"] == "GSR-029")
        self.assertIn("canonical local store", coverage_integrity["function"])
        ui_experience = next(item for item in catalog["capabilities"] if item["id"] == "GSR-030")
        self.assertEqual(ui_experience["owner_skill"], "code-skill")
        self.assertEqual(ui_experience["checks"], ["code-units", "code-sample-attestation"])
        self.assertIn("真实状态反馈", ui_experience["function"])
        self.assertIn("不得伪称完成", ui_experience["function"])
        self.assertIn("图标、emoji、图片、状态样式或图示", ui_experience["function"])
        check_workers = next(item for item in catalog["capabilities"] if item["id"] == "GSR-031")
        self.assertEqual(check_workers["owner_skill"], "verify-skill")
        self.assertIn("ENDING_CHECK_WORKER", check_workers["function"])
        self.assertIn("Terra/Sol", check_workers["function"])
        session_outcomes = next(item for item in catalog["capabilities"] if item["id"] == "GSR-032")
        self.assertEqual(session_outcomes["owner_skill"], "task-analyze-skill")
        self.assertIn("route event", session_outcomes["function"])
        self.assertIn("runtime receipt", session_outcomes["function"])
        self.assertIn("PASS", session_outcomes["function"])
        self.assertIn("Spark fast path", session_outcomes["function"])
        multi_stage = next(item for item in catalog["capabilities"] if item["id"] == "GSR-007")
        self.assertIn("中英文意图", multi_stage["function"])
        self.assertIn("route-required", multi_stage["function"])
        self.assertIn("调用一次 dispatcher", multi_stage["function"])
        code_gate = next(item for item in catalog["capabilities"] if item["id"] == "GSR-033")
        self.assertEqual(code_gate["owner_skill"], "task-analyze-skill")
        self.assertIn("意图优先于", code_gate["function"])
        self.assertIn("问句外壳", code_gate["function"])
        self.assertIn("code-rule-notice", code_gate["function"])
        self.assertIn("统一代码哲学", code_gate["function"])
        self.assertIn("其他业务 Skill", code_gate["function"])
        benchmark = next(item for item in catalog["capabilities"] if item["id"] == "GSR-023")
        self.assertIn("result-ready/运行后 DB 与匹配 rollout 差集恢复基线", benchmark["function"])
        lifecycle = next(item for item in catalog["capabilities"] if item["id"] == "GSR-034")
        self.assertEqual(lifecycle["owner_skill"], "task-analyze-skill")
        self.assertIn("execution-lifecycle-notice", lifecycle["function"])
        self.assertIn("plan+dependency graph", lifecycle["function"])
        self.assertIn("模型启动前硬切", lifecycle["function"])
        self.assertIn("route-required", lifecycle["function"])
        self.assertIn("operational failure 保持质量中立", lifecycle["function"])
        self.assertIn("零 token 并行 capture", lifecycle["function"])
        self.assertIn("精简 runtime view", lifecycle["function"])
        self.assertIn("Windows/链接不可用安全回退", lifecycle["function"])
        self.assertIn("lifecycle-trigger-matrix", lifecycle["checks"])
        consumer_install = next(item for item in catalog["capabilities"] if item["id"] == "GSR-035")
        self.assertEqual(consumer_install["owner_skill"], "management-skill")
        self.assertIn("cross-process target lock", consumer_install["function"])
        self.assertIn("fsynced transaction manifest", consumer_install["function"])
        self.assertIn("源字节物化", consumer_install["function"])
        self.assertIn("recoverable opaque backup", consumer_install["function"])
        self.assertIn("每次都无条件替换八个 managed Skill", consumer_install["function"])
        self.assertIn("用户 AGENTS 不属于普通替换集合", consumer_install["function"])
        self.assertIn("file、symlink、junction", consumer_install["function"])
        self.assertIn("task-analyze-skill/local 不透明保留", consumer_install["function"])
        self.assertIn("deploy/pull/legacy sync 绝不运行", consumer_install["function"])
        self.assertIn("whole-tree hash", consumer_install["function"])
        self.assertIn("发布者在 push 前单独运行一次完整门禁", consumer_install["function"])
        resource_lifecycle = next(item for item in catalog["capabilities"] if item["id"] == "GSR-036")
        self.assertEqual(resource_lifecycle["owner_skill"], "workflow-skill")
        self.assertEqual(resource_lifecycle["checks"], ["workflow-units", "workflow-validator", "platform-check", "cache-layout-units"])
        for required in ("自身创建的精确", "最后 consumer", "反向依赖顺序", "deferred", "Ending 先保存证据", "不得消息、打断、终止、归档、删除或控制其他 task、thread、session 或 Ending"):
            self.assertIn(required, resource_lifecycle["function"])
        workflow_units = next(item for item in catalog["checks"] if item["id"] == "workflow-units")
        self.assertEqual(workflow_units["targets"], ["source", "deployed"])
        self.assertEqual(workflow_units["command"], ["{python}", "-m", "unittest", "discover", "-s", "workflow-skill/tests", "-p", "test_*.py"])
        self.assertIn("禁止编辑、修复、路由或创建生命周期", check_workers["function"])
        retired = {item["id"]: item["replacement"] for item in catalog["retired_architectures"]}
        self.assertEqual(retired["RET-011"], "GSR-026")
        self.assertEqual(retired["RET-012"], "GSR-014")
        self.assertEqual(retired["RET-013"], "GSR-012")
        self.assertEqual(retired["RET-014"], "GSR-031")
        self.assertEqual(retired["RET-015"], "GSR-020")
        self.assertEqual(retired["RET-016"], "GSR-034")
        self.assertEqual(retired["RET-017"], "GSR-035")
        self.assertEqual(retired["RET-018"], "GSR-035")
        self.assertFalse(catalog["policy"]["local_deployment_completion_requires_pass"])
        self.assertNotIn("local_deployment_requires_pass", catalog["policy"])
        self.assertFalse(catalog["policy"]["local_install_write_requires_pass"])
        self.assertFalse(catalog["policy"]["local_install_semantic_precheck_allowed"])
        self.assertTrue(catalog["policy"]["local_install_always_replaces_managed_skills"])
        self.assertTrue(catalog["policy"]["local_install_preserves_user_global_agents"])
        self.assertTrue(catalog["policy"]["local_install_backup_and_safe_write_prerequisites_only"])
        self.assertFalse(catalog["policy"]["local_installation_completion_requires_pass"])
        self.assertFalse(catalog["policy"]["consumer_install_runs_semantic_validation"])
        self.assertFalse(catalog["policy"]["agent_owns_install_test_repair"])
        self.assertTrue(catalog["policy"]["maintainer_publication_owns_release_validation"])
        self.assertTrue(catalog["policy"]["github_publication_requires_pass"])

    def test_capability_counters_report_runs_and_assertions_separately(self):
        catalog = {
            "capabilities": [
                {"id": "GSR-001", "owner_skill": "test", "name": "one", "function": "one", "checks": ["a", "b"]},
                {"id": "GSR-002", "owner_skill": "test", "name": "two", "function": "two", "checks": ["b"]},
            ]
        }
        results = [
            {"check_id": "a", "status": "pass", "test_count": 3, "passed_count": 3},
            {"check_id": "b", "status": "pass", "test_count": 5, "passed_count": 5},
        ]
        summaries = GATE.capability_results(catalog, results)
        self.assertEqual((summaries[0]["test_runs"], summaries[0]["passed_runs"]), (2, 2))
        self.assertEqual((summaries[0]["test_count"], summaries[0]["passed_count"]), (8, 8))
        self.assertEqual(summaries[0]["status"], "pass")
        self.assertEqual((summaries[1]["test_runs"], summaries[1]["passed_runs"]), (1, 1))

    def test_capability_fails_when_any_mapped_check_fails(self):
        catalog = {"capabilities": [{"id": "GSR-001", "owner_skill": "test", "name": "one", "function": "one", "checks": ["a"]}]}
        summary = GATE.capability_results(catalog, [{"check_id": "a", "status": "fail", "test_count": 4, "passed_count": 3}])[0]
        self.assertEqual(summary["status"], "fail")
        self.assertEqual((summary["test_count"], summary["passed_count"]), (4, 3))

    def test_zero_test_command_is_a_failure_even_with_exit_zero(self):
        completed = subprocess.CompletedProcess(["test"], 0, stdout="Ran 0 tests\nOK\n", stderr="")
        with mock.patch.object(GATE.subprocess, "run", return_value=completed):
            result = GATE.command_result("zero", "source", ["test"], PROJECT_ROOT, 1, {})
        self.assertEqual(result["status"], "fail")
        self.assertEqual((result["test_count"], result["passed_count"]), (0, 0))

    def test_attestation_rejects_a_stale_watched_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            watched = root / "code-skill" / "SKILL.md"
            watched.parent.mkdir(parents=True)
            watched.write_text("before", encoding="utf-8")
            attestation = root / "management-skill" / "assets" / "attestation.json"
            attestation.parent.mkdir(parents=True)
            attestation.write_text(json.dumps({
                "schema_version": 1,
                "check_id": "sample",
                "status": "pass",
                "trial_count": 3,
                "passed_trials": 3,
                "watched_files": {"code-skill/SKILL.md": GATE.attestation_watched_file_sha256(watched)},
            }), encoding="utf-8")
            check = {"id": "sample", "kind": "attestation", "path": "management-skill/assets/attestation.json", "watched_files": ["code-skill/SKILL.md"]}
            self.assertEqual(GATE.attestation_result(check, root)["status"], "pass")
            watched.write_text("after", encoding="utf-8")
            result = GATE.attestation_result(check, root)
            self.assertEqual(result["status"], "fail")
            self.assertIn("stale watched file", result["errors"][0])

    def test_attestation_normalizes_watched_text_but_not_bound_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            watched = root / "code-skill" / "SKILL.md"
            evidence = root / "Cache" / "remote-test" / "evidence.json"
            attestation = root / "management-skill" / "assets" / "attestation.json"
            watched.parent.mkdir(parents=True)
            evidence.parent.mkdir(parents=True)
            attestation.parent.mkdir(parents=True)
            watched.write_bytes(b"line one\nline two\n")
            evidence.write_bytes(b'{"line":"one"}\n')
            payload = {"schema_version": 1, "check_id": "sample", "status": "pass", "trial_count": 1, "passed_trials": 1, "evidence_sha256": GATE.sha256_file(evidence), "watched_files": {"code-skill/SKILL.md": GATE.attestation_watched_file_sha256(watched)}}
            attestation.write_text(json.dumps(payload), encoding="utf-8")
            check = {"id": "sample", "kind": "attestation", "path": "management-skill/assets/attestation.json", "evidence": "Cache/remote-test/evidence.json", "bind_evidence": True, "watched_files": ["code-skill/SKILL.md"]}
            watched.write_bytes(b"line one\r\nline two\r\n")
            self.assertEqual(GATE.attestation_result(check, root)["status"], "pass")
            evidence.write_bytes(b'{"line":"one"}\r\n')
            result = GATE.attestation_result(check, root)
            self.assertEqual(result["status"], "fail")
            self.assertIn("attestation evidence digest is stale", result["errors"])
            watched.write_bytes(b"line one\r\nchanged\r\n")
            result = GATE.attestation_result(check, root)
            self.assertEqual(result["status"], "fail")
            self.assertIn("stale watched file: code-skill/SKILL.md", result["errors"])

    def test_deployment_parity_normalizes_known_text_but_keeps_binary_bytes_exact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "source"
            deployed = Path(temp_dir) / "deployed"
            source_skill = root / "code-skill"
            deployed_skill = deployed / "code-skill"
            source_skill.mkdir(parents=True)
            deployed_skill.mkdir(parents=True)
            (source_skill / "SKILL.md").write_bytes(b"line one\nline two\n")
            (deployed_skill / "SKILL.md").write_bytes(b"line one\r\nline two\r\n")
            (source_skill / "fixture.bin").write_bytes(b"same\n")
            (deployed_skill / "fixture.bin").write_bytes(b"same\n")
            self.assertEqual(GATE.deployment_parity_result("deployment-parity", root, deployed, ["code-skill"])["status"], "pass")
            (deployed_skill / "fixture.bin").write_bytes(b"same\r\n")
            result = GATE.deployment_parity_result("deployment-parity", root, deployed, ["code-skill"])
            self.assertEqual(result["status"], "fail")
            self.assertEqual(result["differences"], ["code-skill"])

    def test_global_agents_parity_compares_templates_without_reading_user_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "source"
            deployed = Path(temp_dir) / "deployed"
            source_asset = root / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
            deployed_asset = deployed / "task-analyze-skill" / "assets" / "global-agents-entry-rule.md"
            directive = "This template is written only by the explicit `install-global-agents` command; deploy, pull, and sync preserve user AGENTS.md files.\n\n"
            source_asset.parent.mkdir(parents=True)
            deployed_asset.parent.mkdir(parents=True)
            source_asset.write_text(directive + "# lifecycle\n", encoding="utf-8")
            deployed_asset.write_text(directive + "# lifecycle\n", encoding="utf-8")
            (deployed.parent / "AGENTS.md").write_text("# personal instructions\n", encoding="utf-8")

            matching = GATE.global_agents_parity_result("global-agents-parity", root, deployed)

            self.assertEqual(matching["status"], "pass")
            deployed_asset.write_text(directive + "# changed lifecycle\n", encoding="utf-8")
            drifted = GATE.global_agents_parity_result("global-agents-parity", root, deployed)
            self.assertEqual(drifted["status"], "fail")
            self.assertEqual(drifted["failed_targets"], [str(deployed_asset)])

    def test_memory_execution_consistency_evidence_requires_all_positive_and_negative_scenarios(self):
        evidence = self._memory_consistency_evidence()
        self.assertEqual(GATE.validate_memory_execution_consistency(evidence), (7, 7))
        evidence["scenarios"]["skill-contract-defect"]["memory_write"] = True
        self.assertEqual(GATE.validate_memory_execution_consistency(evidence), (7, 0))
        evidence["scenarios"]["skill-contract-defect"]["memory_write"] = False
        evidence["scenarios"]["next-task-effective-recall"]["superseded_hidden"] = False
        self.assertEqual(GATE.validate_memory_execution_consistency(evidence), (7, 0))
        evidence["scenarios"]["next-task-effective-recall"]["superseded_hidden"] = True
        evidence["scenarios"]["invalid-result-integrity"]["reconcile_blocked"] = False
        self.assertEqual(GATE.validate_memory_execution_consistency(evidence), (7, 0))
        evidence["scenarios"]["invalid-result-integrity"]["reconcile_blocked"] = True
        evidence["scenarios"]["coverage-authority-integrity"]["concurrent_projection_preserved"] = False
        self.assertEqual(GATE.validate_memory_execution_consistency(evidence), (7, 0))
        evidence = self._memory_consistency_evidence()
        evidence["trial_count"] = 6
        self.assertEqual(GATE.validate_memory_execution_consistency(evidence), (7, 0))
        evidence = self._memory_consistency_evidence()
        evidence["passed_trials"] = 6
        self.assertEqual(GATE.validate_memory_execution_consistency(evidence), (7, 0))
        evidence = self._memory_consistency_evidence()
        evidence["execution"]["disposable_runtime_removed"] = False
        self.assertEqual(GATE.validate_memory_execution_consistency(evidence), (7, 0))

    def test_bound_attestation_rejects_changed_real_evidence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            watched = root / "workflow-skill" / "SKILL.md"
            evidence = root / "Cache" / "remote-test" / "memory-execution-consistency" / "result.json"
            attestation = root / "management-skill" / "assets" / "attestation.json"
            watched.parent.mkdir(parents=True)
            evidence.parent.mkdir(parents=True)
            attestation.parent.mkdir(parents=True)
            watched.write_text("contract", encoding="utf-8")
            evidence_payload = self._memory_consistency_evidence()
            evidence.write_text(json.dumps(evidence_payload), encoding="utf-8")
            payload = {"schema_version": 1, "check_id": "memory-execution-consistency-attestation", "status": "pass", "trial_count": 7, "passed_trials": 7, "evidence_sha256": GATE.sha256_file(evidence), "watched_files": {"workflow-skill/SKILL.md": GATE.attestation_watched_file_sha256(watched)}}
            attestation.write_text(json.dumps(payload), encoding="utf-8")
            check = {"id": "memory-execution-consistency-attestation", "kind": "attestation", "path": "management-skill/assets/attestation.json", "evidence": "Cache/remote-test/memory-execution-consistency/result.json", "bind_evidence": True, "watched_files": ["workflow-skill/SKILL.md"]}
            self.assertEqual(GATE.attestation_result(check, root)["status"], "pass")
            evidence.write_text('{"changed":true}', encoding="utf-8")
            result = GATE.attestation_result(check, root)
            self.assertEqual(result["status"], "fail")
            self.assertIn("attestation evidence digest is stale", result["errors"])
            payload["evidence_sha256"] = GATE.sha256_file(evidence)
            attestation.write_text(json.dumps(payload), encoding="utf-8")
            result = GATE.attestation_result(check, root)
            self.assertEqual(result["status"], "fail")
            self.assertIn("memory-execution consistency evidence is not a complete real pass", result["errors"])

    def test_candidate_layout_installs_global_agents_and_excludes_private_local_state(self):
        catalog = GATE.load_catalog(PROJECT_ROOT)
        with tempfile.TemporaryDirectory() as temp_dir:
            deployed = Path(temp_dir) / "deployed"
            deployed.mkdir()
            for skill_name in catalog["managed_skills"]:
                source = PROJECT_ROOT / skill_name
                target = deployed / skill_name
                GATE.shutil.copytree(source, target)
            private = deployed / "task-analyze-skill" / "local" / "events.jsonl"
            private.parent.mkdir(parents=True)
            private.write_text("private", encoding="utf-8")
            for plugin_id, skill_name in (("chrome", "control-chrome"), ("sites", "sites-building")):
                plugin_skill = deployed.parent / "plugins" / "cache" / "openai-bundled" / plugin_id / "1.0.0" / "skills" / skill_name / "SKILL.md"
                plugin_skill.parent.mkdir(parents=True)
                plugin_skill.write_text(f"{plugin_id}:{skill_name}\n", encoding="utf-8")
            with GATE.candidate_layouts(PROJECT_ROOT, deployed, catalog["managed_skills"]) as roots:
                self.assertTrue((roots["source"].parent / "AGENTS.md").is_file())
                self.assertTrue((roots["deployed"].parent / "AGENTS.md").is_file())
                self.assertFalse((roots["deployed"] / "task-analyze-skill" / "local").exists())
                for root in roots.values():
                    candidate_cache = root.parent / "plugins" / "cache"
                    self.assertTrue(any(candidate_cache.glob("*/*/*/skills/control-chrome/SKILL.md")))
                    self.assertTrue(any(candidate_cache.glob("*/*/*/skills/sites-building/SKILL.md")))
                    for relative in (
                        "workflow-skill/references/task-resource-lifecycle.md",
                        "workflow-skill/scripts/task_resource_ledger.py",
                        "workflow-skill/tests/test_task_resource_ledger.py",
                    ):
                        self.assertTrue((root / relative).is_file(), relative)

    def test_candidate_layout_uses_ephemeral_contract_fixtures_without_plugin_cache(self):
        catalog = GATE.load_catalog(PROJECT_ROOT)
        with tempfile.TemporaryDirectory() as temp_dir:
            deployed = Path(temp_dir) / "deployed"
            deployed.mkdir()
            for skill_name in catalog["managed_skills"]:
                GATE.shutil.copytree(PROJECT_ROOT / skill_name, deployed / skill_name)
            with GATE.candidate_layouts(PROJECT_ROOT, deployed, catalog["managed_skills"]) as roots:
                for root in roots.values():
                    candidate_cache = root.parent / "plugins" / "cache"
                    for plugin_id, skill_name in GATE.REQUIRED_PLUGIN_CONTRACTS:
                        fixture = candidate_cache / "ci-contract-fixture" / plugin_id / "0.0.0" / "skills" / skill_name / "SKILL.md"
                        self.assertTrue(fixture.is_file())
                        self.assertIn("Candidate-only contract fixture", fixture.read_text(encoding="utf-8"))

    def test_runner_uses_argument_arrays_without_shell_execution(self):
        text = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("shell=True", text)
        self.assertIn("sys.executable", text)
        self.assertIn("subprocess.run(command", text)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import importlib.util
import json
from copy import deepcopy
import shutil
import tempfile
import unittest
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_task_analyze_skill.py"
MODULE_SPEC = importlib.util.spec_from_file_location("validate_task_analyze_skill", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)
APPROVED = {"task-analyze-skill", "workflow-skill", "code-skill", "verify-skill", "optimization-skill", "management-skill"}


class ValidateTaskAnalyzeSkillTests(unittest.TestCase):
    @contextmanager
    def _with_rust_domain(self, owner="code-skill", spark_first=True, language_alias="rust"):
        original_domains = deepcopy(module.EXECUTION_DOMAINS)
        with tempfile.TemporaryDirectory(prefix="task-analyze-synthetic-skills-") as temporary:
            synthetic_skills_root = Path(temporary)
            try:
                module.EXECUTION_DOMAINS["rust"] = {
                    "display_name": "Rust",
                    "kind": "code",
                    "language_aliases": [language_alias],
                    "owner_skill": owner,
                    "owner_enforced": True,
                    "spark_first": spark_first,
                    "reference_path": "code-skill/references/rust-small-code.md",
                    "active": True,
                    "history_only": False,
                }
                for metadata in module.EXECUTION_DOMAINS.values():
                    owner_skill = metadata["owner_skill"]
                    skill_dir = synthetic_skills_root / owner_skill
                    skill_dir.mkdir(parents=True, exist_ok=True)
                    (skill_dir / "SKILL.md").write_text(f"{owner_skill} skill\n", encoding="utf-8")
                    reference = synthetic_skills_root / metadata["reference_path"]
                    reference.parent.mkdir(parents=True, exist_ok=True)
                    reference.write_text(f"reference: {metadata['reference_path']}\n", encoding="utf-8")
                yield synthetic_skills_root
            finally:
                module.EXECUTION_DOMAINS.clear()
                module.EXECUTION_DOMAINS.update(original_domains)
            # cleanup via TemporaryDirectory context

    def test_plan_rejects_rust_domain_wrong_owner(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        impl = next(node for node in plan["nodes"] if node.get("purpose") == "implement")
        impl["execution_domain"] = "rust"
        impl["skill"] = "workflow-skill"
        with self._with_rust_domain(owner="code-skill") as synthetic_skills_root:
            failures = module.validate_plan(plan, APPROVED, synthetic_skills_root)
        self.assertTrue(any("bypasses code-skill" in failure for failure in failures))

    def test_plan_accepts_complex_terra_code_domain(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        impl = next(node for node in plan["nodes"] if node.get("purpose") == "implement")
        impl["execution_domain"] = "rust"
        impl["skill"] = "code-skill"
        impl["model"] = "gpt-5.6-luna"
        with self._with_rust_domain() as synthetic_skills_root:
            failures = module.validate_plan(plan, APPROVED, synthetic_skills_root)
        self.assertEqual(failures, [])

    def test_plan_rejects_complex_spark_code_domain(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        impl = next(node for node in plan["nodes"] if node.get("purpose") == "implement")
        impl["execution_domain"] = "rust"
        impl["skill"] = "code-skill"
        impl["model"] = "gpt-5.3-codex-spark"
        with self._with_rust_domain() as synthetic_skills_root:
            failures = module.validate_plan(plan, APPROVED, synthetic_skills_root)
        self.assertTrue(any("Spark is valid only" in failure for failure in failures))
    def make_validation_inputs(self):
        source = Path(__file__).resolve().parents[1]
        temp_dir = Path(tempfile.mkdtemp(prefix="task-analyze-validate-"))
        for relative in module.REQUIRED_FILES:
            destination = temp_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text((source / relative).read_text(encoding="utf-8"), encoding="utf-8")
        models_cache = temp_dir / "models_cache.json"
        models_cache.write_text(json.dumps({"models": []}) + "\n", encoding="utf-8")
        global_agents = temp_dir / "AGENTS.md"
        global_agents.write_text("\n".join(["Global Codex Task Entry Rule", "100% task-start contract", "hookless", "exact visible shape", "LOCKED_ROUTE_NODE", "task_route_dispatcher.py run-plan", "same task through `workflow-skill`", "adaptive-routing"]) + "\n", encoding="utf-8")
        global_skills = temp_dir / "skills"
        for skill_name in APPROVED:
            skill_dir = global_skills / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"{skill_name}\n", encoding="utf-8")
        for relative in ("task-analyze-skill/references/model-selection.md", "code-skill/references/python-rules.md", "code-skill/references/csharp-rules.md", "code-skill/references/unity-csharp-rules.md", "code-skill/references/spark-small-code.md"):
            reference = global_skills / relative
            reference.parent.mkdir(parents=True, exist_ok=True)
            reference.write_text(f"reference: {relative}\n", encoding="utf-8")
        for plugin_id, skill_name in (("chrome", "control-chrome"), ("build-web-apps", "frontend-app-builder")):
            plugin_skill = temp_dir / "plugins" / "cache" / "openai-curated-remote" / plugin_id / "1.0.0" / "skills" / skill_name
            plugin_skill.mkdir(parents=True)
            (plugin_skill / "SKILL.md").write_text(f"{plugin_id}:{skill_name}\n", encoding="utf-8")
        return temp_dir, models_cache, global_agents, global_skills

    def test_current_contract_passes(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertTrue(result["valid"], result["failures"])
            self.assertEqual(sum(plan["status"] == "pass" for plan in result["plans"]), len(module.sample_plans()))
            self.assertEqual(len(module.sample_plans()), sum(len(efforts) for efforts in module.MODEL_EFFORTS.values()) * 2)
        finally:
            shutil.rmtree(temp_dir)

    def test_sample_plans_cover_all_supported_entry_pairs(self):
        sample_plans = module.sample_plans()
        expected_plan_count = sum(len(efforts) for efforts in module.MODEL_EFFORTS.values()) * 2
        entry_pairs = {(plan["nodes"][0]["model"], plan["nodes"][0]["effort"]) for plan in sample_plans.values()}
        self.assertEqual(len(sample_plans), expected_plan_count)
        self.assertEqual(len(entry_pairs), sum(len(efforts) for efforts in module.MODEL_EFFORTS.values()))

    def test_downstream_pairs_may_equal_entry_pair(self):
        sample_plans = module.sample_plans()
        plan = json.loads(json.dumps(sample_plans["easy-gpt-5.6-luna-low"]))
        failures = module.validate_plan(plan, APPROVED)
        self.assertEqual(failures, [])

    def test_fixed_sol_entry_contract_is_rejected(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            skill_path = temp_dir / "SKILL.md"
            skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nRun Task Analyze with `GPT-5.6-Sol`.\n", encoding="utf-8")
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertFalse(result["valid"])
            self.assertTrue(any("obsolete text" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)

    def test_complex_route_without_mermaid_is_rejected(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            route_path = temp_dir / "references" / "route-contract.md"
            route_path.write_text(route_path.read_text(encoding="utf-8").replace("## Complex Task: Mermaid Route", "## Complex Task").replace("```mermaid", "```text"), encoding="utf-8")
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertFalse(result["valid"])
            self.assertTrue(any("Mermaid" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)

    def test_hook_or_chat_machine_plan_contract_is_rejected(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            skill_path = temp_dir / "SKILL.md"
            skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nRequire the user-level Codex hook and TASK_ANALYZE_PLAN_JSON output.\n", encoding="utf-8")
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertFalse(result["valid"])
            self.assertTrue(any("obsolete text" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)

    def test_plan_rejects_python_node_without_code_skill(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        plan["nodes"][2]["skill"] = "workflow-skill"
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("bypasses code-skill" in failure for failure in failures))

    def test_plan_rejects_unknown_execution_domain_cleanly(self):
        easy_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "easy")
        plan = json.loads(json.dumps(easy_plan))
        plan["nodes"][0]["execution_domain"] = "rust_lang"
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("execution_domain is unknown" in failure for failure in failures))
        self.assertFalse(any("expected owner" in failure or "has no fallback reason" in failure for failure in failures))

    def test_plan_rejects_unity_csharp_node_without_code_skill(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        plan["nodes"][2]["language"] = "unity_csharp"
        plan["nodes"][2]["skill"] = "workflow-skill"
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("bypasses code-skill" in failure for failure in failures))

    def test_plan_accepts_complex_unity_csharp_with_terra(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        plan["nodes"][2]["language"] = "unity_csharp"
        plan["nodes"][2]["skill"] = "code-skill"
        plan["nodes"][2]["model"] = "gpt-5.6-terra"
        failures = module.validate_plan(plan, APPROVED)
        self.assertEqual(failures, [])

    def test_plan_rejects_real_verify_before_main_result(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        main = next(node for node in plan["nodes"] if node["id"] == "main-result")
        main["dependencies"].append("real-verify")
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("must not depend on Ending Task" in failure for failure in failures))

    def test_stale_model_snapshot_is_rejected(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            snapshot = temp_dir / "references" / "model-capabilities.md"
            snapshot.write_text(snapshot.read_text(encoding="utf-8") + "stale", encoding="utf-8")
            invalid_status = {"valid": False, "status": "stale", "missing_cache_models": []}
            with patch.object(module.sync_model_capabilities, "check_snapshot", return_value=invalid_status):
                result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertFalse(result["valid"])
            self.assertTrue(any("capability check" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)

    def test_related_memory_contract_is_required_and_hookless(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertTrue(result["valid"])
            skill_path = temp_dir / "SKILL.md"
            skill_path.write_text(skill_path.read_text(encoding="utf-8").replace("quick bounded related-memory lookup", "broad mandatory memory dump"), encoding="utf-8")
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertFalse(result["valid"])
            self.assertTrue(any("quick bounded related-memory lookup" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_task_analyze_skill.py"
MODULE_SPEC = importlib.util.spec_from_file_location("validate_task_analyze_skill", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)
APPROVED = {"task-analyze-skill", "workflow-skill", "code-skill", "verify-skill", "optimization-skill", "management-skill"}


class ValidateTaskAnalyzeSkillTests(unittest.TestCase):
    def make_skill_copy(self):
        source = Path(__file__).resolve().parents[1]
        temp_dir = Path(tempfile.mkdtemp(prefix="task-analyze-validate-"))
        for relative in module.REQUIRED_FILES:
            destination = temp_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text((source / relative).read_text(encoding="utf-8"), encoding="utf-8")
        models_cache = temp_dir / "models_cache.json"
        models_cache.write_text((Path.home() / ".codex" / "models_cache.json").read_text(encoding="utf-8"), encoding="utf-8")
        return temp_dir, models_cache

    def test_current_contract_passes(self):
        temp_dir, models_cache = self.make_skill_copy()
        try:
            with patch.object(module, "installed_skills", return_value=APPROVED):
                result = module.validate(temp_dir, models_cache)
            self.assertTrue(result["valid"], result["failures"])
            self.assertEqual(sum(plan["status"] == "pass" for plan in result["plans"]), len(module.sample_plans()))
        finally:
            shutil.rmtree(temp_dir)

    def test_fixed_sol_entry_contract_is_rejected(self):
        temp_dir, models_cache = self.make_skill_copy()
        try:
            skill_path = temp_dir / "SKILL.md"
            skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nRun Task Analyze with `GPT-5.6-Sol`.\n", encoding="utf-8")
            with patch.object(module, "installed_skills", return_value=APPROVED):
                result = module.validate(temp_dir, models_cache)
            self.assertFalse(result["valid"])
            self.assertTrue(any("obsolete text" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)

    def test_complex_route_without_mermaid_is_rejected(self):
        temp_dir, models_cache = self.make_skill_copy()
        try:
            route_path = temp_dir / "references" / "route-contract.md"
            route_path.write_text(route_path.read_text(encoding="utf-8").replace("## Complex Task: Mermaid Route", "## Complex Task").replace("```mermaid", "```text"), encoding="utf-8")
            with patch.object(module, "installed_skills", return_value=APPROVED):
                result = module.validate(temp_dir, models_cache)
            self.assertFalse(result["valid"])
            self.assertTrue(any("Mermaid" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)

    def test_hook_or_chat_machine_plan_contract_is_rejected(self):
        temp_dir, models_cache = self.make_skill_copy()
        try:
            skill_path = temp_dir / "SKILL.md"
            skill_path.write_text(skill_path.read_text(encoding="utf-8") + "\nRequire the user-level Codex hook and TASK_ANALYZE_PLAN_JSON output.\n", encoding="utf-8")
            with patch.object(module, "installed_skills", return_value=APPROVED):
                result = module.validate(temp_dir, models_cache)
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

    def test_plan_rejects_real_verify_before_main_result(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        main = next(node for node in plan["nodes"] if node["id"] == "main-result")
        main["dependencies"].append("real-verify")
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("must not depend on Ending Task" in failure for failure in failures))

    def test_stale_model_snapshot_is_rejected(self):
        temp_dir, models_cache = self.make_skill_copy()
        try:
            snapshot = temp_dir / "references" / "model-capabilities.md"
            snapshot.write_text(snapshot.read_text(encoding="utf-8") + "stale", encoding="utf-8")
            invalid_status = {"valid": False, "status": "stale", "missing_cache_models": []}
            with patch.object(module, "installed_skills", return_value=APPROVED), patch.object(module.sync_model_capabilities, "check_snapshot", return_value=invalid_status):
                result = module.validate(temp_dir, models_cache)
            self.assertFalse(result["valid"])
            self.assertTrue(any("capability check" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()

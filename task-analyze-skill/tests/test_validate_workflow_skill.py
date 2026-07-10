#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from copy import deepcopy
from contextlib import contextmanager
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "workflow-skill" / "scripts" / "validate_workflow_skill.py"
MODULE_SPEC = importlib.util.spec_from_file_location("validate_workflow_skill", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


class ValidateWorkflowSkillTests(unittest.TestCase):
    @contextmanager
    def _with_rust_domain(self, trace, owner="code-skill", spark_first=True, language_alias="rust"):
        original_domains = deepcopy(module.EXECUTION_DOMAINS)
        with tempfile.TemporaryDirectory(prefix="workflow-synthetic-skills-") as temporary:
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
                for skill_id in {node["skill"] for node in trace if isinstance(node, dict) and isinstance(node.get("skill"), str)}:
                    if ":" in skill_id:
                        continue
                    skill_dir = synthetic_skills_root / skill_id
                    skill_dir.mkdir(parents=True, exist_ok=True)
                    (skill_dir / "SKILL.md").write_text(f"{skill_id} skill\n", encoding="utf-8")
                yield synthetic_skills_root
            finally:
                module.EXECUTION_DOMAINS.clear()
                module.EXECUTION_DOMAINS.update(original_domains)

    def test_validate_trace_rejects_rust_wrong_owner(self):
        trace = [
            {"id": "task-analyze", "model": "gpt-5.6-luna", "effort": "low", "skill": "task-analyze-skill", "execution_domain": "general"},
            {"id": "implement", "model": "gpt-5.3-codex-spark", "effort": "low", "skill": "workflow-skill", "execution_domain": "rust", "language": "rust"},
            {"id": "mini-verify", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill", "execution_domain": "general"},
            {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
            {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
        ]
        with self._with_rust_domain(trace) as synthetic_skills_root:
            result = module.validate_trace("synthetic-rust-wrong-owner", trace, synthetic_skills_root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("bypasses code-skill" in failure for failure in result["failures"]))

    def test_validate_trace_rejects_rust_non_spark(self):
        trace = [
            {"id": "task-analyze", "model": "gpt-5.6-luna", "effort": "low", "skill": "task-analyze-skill", "execution_domain": "general"},
            {"id": "implement", "model": "gpt-5.6-luna", "effort": "low", "skill": "code-skill", "execution_domain": "rust", "language": "rust"},
            {"id": "mini-verify", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill", "execution_domain": "general"},
            {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
            {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
        ]
        with self._with_rust_domain(trace) as synthetic_skills_root:
            result = module.validate_trace("synthetic-rust-nonspark", trace, synthetic_skills_root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("is not Spark-first" in failure for failure in result["failures"]))

    def test_validate_trace_accepts_rust_spark_with_code_skill(self):
        trace = [
            {"id": "task-analyze", "model": "gpt-5.6-luna", "effort": "low", "skill": "task-analyze-skill", "execution_domain": "general"},
            {"id": "implement", "model": "gpt-5.3-codex-spark", "effort": "low", "skill": "code-skill", "execution_domain": "rust", "language": "rust"},
            {"id": "mini-verify", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill", "execution_domain": "general"},
            {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
            {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
        ]
        with self._with_rust_domain(trace) as synthetic_skills_root:
            result = module.validate_trace("synthetic-rust-spark", trace, synthetic_skills_root)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["failures"], [])

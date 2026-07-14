#!/usr/bin/env python3
import importlib.util
import json
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
            {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
            {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
        ]
        with self._with_rust_domain(trace) as synthetic_skills_root:
            result = module.validate_trace("synthetic-rust-wrong-owner", trace, synthetic_skills_root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("bypasses code-skill" in failure for failure in result["failures"]))

    def test_validate_trace_rejects_renamed_foreground_verifier_without_user_request_flag(self):
        trace = [
            {"id": "task-analyze", "model": "gpt-5.6-luna", "effort": "low", "skill": "task-analyze-skill"},
            {"id": "quick-check", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill"},
            {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"},
            {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"},
            {"id": "real-verify", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill"},
        ]
        rejected = module.validate_trace("renamed-foreground-verifier", trace)
        trace[1]["user_requested_verification_result"] = True
        accepted = module.validate_trace("user-requested-verification-result", trace)
        self.assertEqual(rejected["status"], "fail")
        self.assertTrue(any("foreground verify-skill requires" in failure for failure in rejected["failures"]))
        self.assertEqual(accepted["status"], "pass")

    def test_validate_trace_rejects_user_request_flag_on_non_verifier(self):
        trace = [
            {"id": "task-analyze", "model": "gpt-5.6-luna", "effort": "low", "skill": "task-analyze-skill"},
            {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "user_requested_verification_result": True},
            {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill"},
            {"id": "real-verify", "model": "gpt-5.6-luna", "effort": "low", "skill": "verify-skill"},
        ]
        result = module.validate_trace("misplaced-user-verification-flag", trace)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("user_requested_verification_result is valid only" in failure for failure in result["failures"]))

    def test_validate_trace_accepts_complex_terra(self):
        trace = [
            {"id": "task-analyze", "model": "gpt-5.6-luna", "effort": "low", "skill": "task-analyze-skill", "execution_domain": "general"},
            {"id": "implement", "model": "gpt-5.6-terra", "effort": "low", "skill": "code-skill", "execution_domain": "rust", "language": "rust", "task_family": "code", "modality": "text", "risk": "medium", "complexity": "complex", "ambiguity": "medium"},
            {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
            {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
        ]
        with self._with_rust_domain(trace) as synthetic_skills_root:
            result = module.validate_trace("synthetic-rust-nonspark", trace, synthetic_skills_root)
        self.assertEqual(result["status"], "pass")

    def test_validate_trace_rejects_complex_spark(self):
        trace = [
            {"id": "task-analyze", "model": "gpt-5.6-luna", "effort": "low", "skill": "task-analyze-skill", "execution_domain": "general"},
            {"id": "implement", "model": "gpt-5.3-codex-spark", "effort": "low", "skill": "code-skill", "execution_domain": "rust", "language": "rust", "task_family": "code", "modality": "text", "risk": "medium", "complexity": "complex", "ambiguity": "medium"},
            {"id": "main-result", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
            {"id": "ending-dispatch", "model": "gpt-5.6-luna", "effort": "low", "skill": "workflow-skill", "execution_domain": "general"},
        ]
        with self._with_rust_domain(trace) as synthetic_skills_root:
            result = module.validate_trace("synthetic-rust-spark", trace, synthetic_skills_root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("Spark is injected only as a result-producer attempt" in failure for failure in result["failures"]))

    def test_validate_trace_rejects_model_outside_shared_gpt56_ladder(self):
        trace = json.loads(json.dumps(module.sample_traces()["admitted-single-luna-entry"]))
        trace[1]["model"] = "gpt-4.1"
        result = module.validate_trace("outside-shared-ladder", trace)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("outside the active shared GPT-5.6 ladder" in failure for failure in result["failures"]))

    def test_workflow_contract_keeps_ordinary_tasks_inline(self):
        workflow_path = Path(__file__).resolve().parents[2] / "workflow-skill" / "SKILL.md"
        text = workflow_path.read_text(encoding="utf-8")
        self.assertIn("Ineligible ordinary work remains inline", text)
        self.assertIn("complete Global foreground path includes entry/controller plus child costs", text)
        self.assertIn("End-to-end performance admission remains separate", text)
        self.assertIn("frozen, receipt-backed, Real-passing, and `trial=false`", text)
        self.assertNotIn("observable entry model and effort belong only to Task Analyze", text)

    def test_global_entry_required_terms_match_compact_contract(self):
        required = module.REQUIRED_ENTRY
        self.assertIn("Eligible text/code producers read shared ladder", required)
        self.assertIn("local JSON stays read-only", required)
        self.assertIn("Spark first: easy=low, complex=high", required)
        self.assertIn("Zero-result operational failure uses current 5.6 pair", required)
        self.assertIn("publish, then return", required)
        self.assertIn("Exact read-only uses one bounded rg per authoritative file, anchored to exact members", required)
        self.assertIn("resolve aliases", required)
        self.assertIn("no subagent/route/plan, guesses, unrelated skills, broad search, reread, full-file read, or pre-result check", required)
        self.assertNotIn("Try Spark first: easy=low, complex=high", required)
        self.assertNotIn("no route, plan, guessed names, unrelated skills, broad search, reread, full-file read, or pre-result check", required)

    def test_routing_matrix_separates_ordinary_inline_from_admitted_routes(self):
        matrix_path = Path(__file__).resolve().parents[2] / "workflow-skill" / "references" / "routing-matrix.md"
        routes = module.parse_routes(matrix_path.read_text(encoding="utf-8"))
        for name in ("open-chrome", "open-youtube", "search-cctv-on-youtube", "design-youtube-like-website"):
            self.assertEqual(routes[name][0], "inline-current-model")
            self.assertNotIn("workflow-skill", routes[name])
        self.assertEqual(routes["admitted-single"][:2], ["task-analyze-skill", "workflow-skill"])
        self.assertEqual(routes["admitted-complex"][:2], ["task-analyze-skill", "workflow-skill"])

    def test_executor_skills_support_inline_and_admitted_modes(self):
        skills_root = Path(__file__).resolve().parents[2]
        code_text = (skills_root / "code-skill" / "SKILL.md").read_text(encoding="utf-8")
        verify_text = (skills_root / "verify-skill" / "SKILL.md").read_text(encoding="utf-8")
        optimization_text = (skills_root / "optimization-skill" / "SKILL.md").read_text(encoding="utf-8")
        management_text = (skills_root / "management-skill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Ordinary implementation may run inline or as one Obsidian-context Spark-first producer with a selected 5.6 fallback", code_text)
        self.assertIn("bounded read-only lookup or audit stays on the bootstrap", code_text)
        self.assertIn("Ordinary inline Real Verify uses the current user-selected model and needs no fabricated child receipt", verify_text)
        self.assertIn("Inline optimization uses the current model and no foreground verifier, Workflow, or child receipt", optimization_text)
        self.assertIn("Do not load this skill for ordinary exact-scoped read-only work or Direct/Global benchmark worker arms", management_text)
        self.assertIn("positively admitted", code_text)
        self.assertIn("An admitted verification node preserves the locked model", verify_text)
        self.assertIn("positively admitted", optimization_text)
        self.assertIn("admitted a delegated route", management_text)
        self.assertIn("optimizer never verifies its own behavior", optimization_text)

    def test_executor_descriptions_and_loader_prompts_begin_with_negative_preselection_boundary(self):
        skills_root = Path(__file__).resolve().parents[2]
        cases = {"code-skill": ("code", "Do not use for an exact-scoped read-only lookup, audit, transform, or workflow reconstruction"), "verify-skill": ("verify", "Use only for explicitly requested verification as the task itself, or for post-result Ending Task Real Verify"), "optimization-skill": ("optimization", "Do not infer optimization from repeated benchmark arms or exact-scoped read-only work"), "management-skill": ("management", "Do not use for ordinary exact-scoped read-only work or Direct/Global benchmark worker arms")}
        for skill_name, (label, description_prefix) in cases.items():
            skill_text = (skills_root / skill_name / "SKILL.md").read_text(encoding="utf-8")
            agent_text = (skills_root / skill_name / "agents" / "openai.yaml").read_text(encoding="utf-8")
            self.assertTrue(module.parse_frontmatter(skill_text)["description"].startswith(description_prefix), skill_name)
            self.assertTrue(module.folded_prompt_text(agent_text).startswith(module.NEGATIVE_AGENT_PREFIXES[f"{label}_agent"]), skill_name)
            self.assertLessEqual(module.folded_prompt_length(agent_text), 1024, skill_name)

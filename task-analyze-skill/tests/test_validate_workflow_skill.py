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
QUALITY_MODEL = module.ACTIVE_MODEL_ORDER[0]
QUALITY_EFFORT = module.ACTIVE_MODEL_EFFORTS[QUALITY_MODEL][0]
COMPLEX_MODEL, COMPLEX_EFFORT = module.MODEL_REGISTRY["role_pairs"]["balanced_complex"].split("|", 1)
PRIORITY_MODEL = module.PRIORITY_PRODUCER_MODEL
PRIORITY_EFFORT = module.PRIORITY_PRODUCER["effort_by_complexity"]["easy"] if module.PRIORITY_PRODUCER else None


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
            {"id": "task-analyze", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "task-analyze-skill", "execution_domain": "general"},
            {"id": "implement", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill", "execution_domain": "rust", "language": "rust"},
            {"id": "main-result", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill", "execution_domain": "general"},
            {"id": "ending-dispatch", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill", "execution_domain": "general"},
        ]
        with self._with_rust_domain(trace) as synthetic_skills_root:
            result = module.validate_trace("synthetic-rust-wrong-owner", trace, synthetic_skills_root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("bypasses code-skill" in failure for failure in result["failures"]))

    def test_validate_trace_rejects_renamed_foreground_verifier_without_user_request_flag(self):
        trace = [
            {"id": "task-analyze", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "task-analyze-skill"},
            {"id": "quick-check", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "verify-skill"},
            {"id": "main-result", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill"},
            {"id": "ending-dispatch", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill"},
            {"id": "real-verify", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "verify-skill"},
        ]
        rejected = module.validate_trace("renamed-foreground-verifier", trace)
        trace[1]["user_requested_verification_result"] = True
        accepted = module.validate_trace("user-requested-verification-result", trace)
        self.assertEqual(rejected["status"], "fail")
        self.assertTrue(any("foreground verify-skill requires" in failure for failure in rejected["failures"]))
        self.assertEqual(accepted["status"], "pass")

    def test_validate_trace_rejects_user_request_flag_on_non_verifier(self):
        trace = [
            {"id": "task-analyze", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "task-analyze-skill"},
            {"id": "main-result", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill", "user_requested_verification_result": True},
            {"id": "ending-dispatch", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill"},
            {"id": "real-verify", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "verify-skill"},
        ]
        result = module.validate_trace("misplaced-user-verification-flag", trace)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("user_requested_verification_result is valid only" in failure for failure in result["failures"]))

    def test_validate_trace_accepts_complex_quality_model(self):
        trace = [
            {"id": "task-analyze", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "task-analyze-skill", "execution_domain": "general"},
            {"id": "implement", "model": COMPLEX_MODEL, "effort": COMPLEX_EFFORT, "skill": "code-skill", "execution_domain": "rust", "language": "rust", "task_family": "code", "modality": "text", "risk": "medium", "complexity": "complex", "ambiguity": "medium"},
            {"id": "main-result", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill", "execution_domain": "general"},
            {"id": "ending-dispatch", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill", "execution_domain": "general"},
        ]
        with self._with_rust_domain(trace) as synthetic_skills_root:
            result = module.validate_trace("synthetic-rust-nonspark", trace, synthetic_skills_root)
        self.assertEqual(result["status"], "pass")

    @unittest.skipIf(PRIORITY_MODEL is None, "catalog has no optional priority producer")
    def test_validate_trace_rejects_priority_producer_as_plan_node(self):
        trace = [
            {"id": "task-analyze", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "task-analyze-skill", "execution_domain": "general"},
            {"id": "implement", "model": PRIORITY_MODEL, "effort": PRIORITY_EFFORT, "skill": "code-skill", "execution_domain": "rust", "language": "rust", "task_family": "code", "modality": "text", "risk": "medium", "complexity": "complex", "ambiguity": "medium"},
            {"id": "main-result", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill", "execution_domain": "general"},
            {"id": "ending-dispatch", "model": QUALITY_MODEL, "effort": QUALITY_EFFORT, "skill": "workflow-skill", "execution_domain": "general"},
        ]
        with self._with_rust_domain(trace) as synthetic_skills_root:
            result = module.validate_trace("synthetic-rust-spark", trace, synthetic_skills_root)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("priority producer is injected only as a result-producer attempt" in failure for failure in result["failures"]))

    def test_validate_trace_rejects_model_outside_catalog_quality_ladder(self):
        trace = json.loads(json.dumps(next(iter(module.sample_traces().values()))))
        trace[1]["model"] = "gpt-4.1"
        result = module.validate_trace("outside-shared-ladder", trace)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(any("outside the active catalog-generated quality ladder" in failure for failure in result["failures"]))

    def test_workflow_validator_uses_highest_numeric_family_registry_and_optional_priority_producer(self):
        payload = module.MODEL_REGISTRY
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(tuple(model["id"] for model in payload["models"]), module.ACTIVE_MODEL_ORDER)
        active_family = payload["active_family"]["id"]
        self.assertEqual(payload["active_family"]["selection"], "highest_numeric_gpt_family")
        self.assertTrue(all(model["id"].startswith(f"{active_family}-") or model["id"] == active_family for model in payload["models"]))
        self.assertEqual(len(payload["source"]["catalog_sha256"]), 64)
        if module.PRIORITY_PRODUCER_MODEL is not None:
            self.assertNotIn(module.PRIORITY_PRODUCER_MODEL, module.ACTIVE_MODEL_ORDER)

    def test_workflow_contract_keeps_ordinary_tasks_inline(self):
        workflow_path = Path(__file__).resolve().parents[2] / "workflow-skill" / "SKILL.md"
        text = workflow_path.read_text(encoding="utf-8")
        self.assertIn("Ineligible ordinary work remains inline", text)
        self.assertIn("complete Global foreground path includes entry/controller plus child costs", text)
        self.assertIn("End-to-end performance admission remains separate", text)
        self.assertIn("frozen, receipt-backed, Real-passing, and `trial=false`", text)
        self.assertNotIn("observable entry model and effort belong only to Task Analyze", text)

    def test_workflow_contract_refreshes_models_only_on_explicit_local_update(self):
        workflow_path = Path(__file__).resolve().parents[2] / "workflow-skill" / "SKILL.md"
        text = workflow_path.read_text(encoding="utf-8")
        self.assertIn("reads the saved shared contract unchanged", text)
        self.assertIn("Ordinary tasks do not scan or refresh the local model cache", text)
        self.assertIn("Only an explicit user model-update request", text)
        self.assertIn("never fetch models over the network", text)
        self.assertIn("preserve the saved contract when the local cache is unavailable", text)
        self.assertNotIn("auto-refreshed shared contract", text)

    def test_global_entry_required_terms_match_compact_contract(self):
        required = module.REQUIRED_ENTRY
        self.assertIn("Eligible text/code MUST run adaptive producer", required)
        self.assertIn("Saved highest-family ladder", required)
        self.assertIn("only explicit user model-update", required)
        self.assertIn("never fetch", required)
        self.assertIn("no hierarchy notes or local JSON authority", required)
        self.assertIn("Priority: easy=low, complex=high", required)
        self.assertIn("zero-result uses contextual quality pair", required)
        self.assertIn("publish then return", required)
        self.assertIn("Exact read-only: one bounded rg/file at exact members/aliases", required)
        self.assertIn("no subagent/route/plan, guesses, broad/reread/full read/pre-result check", required)
        self.assertNotIn("Spark first: easy=low, complex=high", required)
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
        self.assertIn("Every eligible implementation runs as one Obsidian-context priority-first producer with a catalog-derived quality fallback", code_text)
        self.assertIn("highest registered numeric GPT family", code_text)
        self.assertIn("bounded read-only lookup or audit stays on the bootstrap", code_text)
        self.assertIn("Ordinary inline Real Verify uses the current user-selected model and needs no fabricated child receipt", verify_text)
        self.assertIn("Eligible text/code optimization uses the catalog-derived adaptive producer; ineligible tool-only work stays inline", optimization_text)
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

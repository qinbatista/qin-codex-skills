#!/usr/bin/env python3
import importlib.util
import json
from copy import deepcopy
import shutil
import tempfile
import unittest
from pathlib import Path
from contextlib import contextmanager


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_task_analyze_skill.py"
MODULE_SPEC = importlib.util.spec_from_file_location("validate_task_analyze_skill", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)
APPROVED = {"task-analyze-skill", "workflow-skill", "prompt-skill", "code-skill", "verify-skill", "optimization-skill", "management-skill", "project-memory-skill"}


class ValidateTaskAnalyzeSkillTests(unittest.TestCase):
    def test_new_profile_presets_use_post_result_real_verification(self):
        self.assertTrue(module.PROFILE_PRESETS)
        self.assertEqual({preset["verification_shape"] for preset in module.PROFILE_PRESETS.values()}, {"real"})

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
        self.assertTrue(any("Spark is injected only as a result-producer attempt" in failure for failure in failures))

    def test_plan_rejects_spark_entry(self):
        plan = json.loads(json.dumps(next(iter(module.sample_plans().values()))))
        plan["entry"] = {"model": module.LEGACY_SPARK_MODEL, "effort": "low"}
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("entry Spark is a result-producer priority attempt only" in failure for failure in failures))

    def make_validation_inputs(self):
        source = Path(__file__).resolve().parents[1]
        temp_dir = Path(tempfile.mkdtemp(prefix="task-analyze-validate-"))
        for relative in module.REQUIRED_FILES:
            destination = temp_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text((source / relative).read_text(encoding="utf-8"), encoding="utf-8")
        models_cache = temp_dir / "models_cache.json"
        ladder = json.loads((source / "assets" / "model-capability-ladder.json").read_text(encoding="utf-8"))
        cache_models = [{"slug": model["id"], "supported_reasoning_levels": [{"effort": effort} for effort in model["codex_efforts"]]} for model in ladder["models"]]
        models_cache.write_text(json.dumps({"models": cache_models}) + "\n", encoding="utf-8")
        global_agents = temp_dir / "AGENTS.md"
        entry_asset_text = (source / "assets" / "global-agents-entry-rule.md").read_text(encoding="utf-8")
        global_agents.write_text(entry_asset_text.replace("Merge this section into `~/.codex/AGENTS.md`.\n\n", ""), encoding="utf-8")
        global_skills = temp_dir / "skills"
        for skill_name in APPROVED:
            skill_dir = global_skills / skill_name
            if skill_name == "prompt-skill":
                skill_dir.mkdir(parents=True)
                (skill_dir / "agents").mkdir()
                (skill_dir / "SKILL.md").write_text((source.parent / "prompt-skill" / "SKILL.md").read_text(encoding="utf-8"), encoding="utf-8")
                (skill_dir / "agents" / "openai.yaml").write_text((source.parent / "prompt-skill" / "agents" / "openai.yaml").read_text(encoding="utf-8"), encoding="utf-8")
            elif skill_name == "project-memory-skill":
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text("project-memory-skill\n", encoding="utf-8")
                (skill_dir / "scripts").mkdir()
                (skill_dir / "scripts" / "obsidian_model_memory.py").write_text((source.parent / "project-memory-skill" / "scripts" / "obsidian_model_memory.py").read_text(encoding="utf-8"), encoding="utf-8")
            else:
                skill_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(f"{skill_name}\n", encoding="utf-8")
        for relative in ("task-analyze-skill/references/model-selection.md", "code-skill/references/python-rules.md", "code-skill/references/csharp-rules.md", "code-skill/references/unity-csharp-rules.md", "code-skill/references/spark-small-code.md"):
            reference = global_skills / relative
            reference.parent.mkdir(parents=True, exist_ok=True)
            source_reference = source.parent / relative
            reference.write_text(source_reference.read_text(encoding="utf-8") if source_reference.exists() else f"reference: {relative}\n", encoding="utf-8")
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
            self.assertEqual(len(module.sample_plans()), sum(len(efforts) for efforts in module.ACTIVE_MODEL_EFFORTS.values()) * 2)
        finally:
            shutil.rmtree(temp_dir)

    def test_code_domain_references_keep_checks_after_first_presentation(self):
        skills_root = Path(__file__).resolve().parents[2]
        python_text = (skills_root / "code-skill" / "references" / "python-rules.md").read_text(encoding="utf-8")
        csharp_text = (skills_root / "code-skill" / "references" / "csharp-rules.md").read_text(encoding="utf-8")
        unity_text = (skills_root / "code-skill" / "references" / "unity-csharp-rules.md").read_text(encoding="utf-8")
        self.assertIn("Present the completed Python edit immediately", python_text)
        self.assertIn("After that first presentation, Ending Task", python_text)
        self.assertIn("present the completed edit immediately", csharp_text)
        self.assertIn("afterward in Ending Task Real Verify", csharp_text)
        self.assertNotIn("check before the main result", csharp_text.lower())
        self.assertIn("uses this file plus", unity_text)

    def test_sample_plans_cover_all_supported_entry_pairs(self):
        sample_plans = module.sample_plans()
        expected_plan_count = sum(len(efforts) for efforts in module.ACTIVE_MODEL_EFFORTS.values()) * 2
        entry_pairs = {(plan["entry"]["model"], plan["entry"]["effort"]) for plan in sample_plans.values()}
        self.assertEqual(len(sample_plans), expected_plan_count)
        self.assertEqual(len(entry_pairs), sum(len(efforts) for efforts in module.ACTIVE_MODEL_EFFORTS.values()))
        self.assertNotIn(module.LEGACY_SPARK_MODEL, {model for model, _ in entry_pairs})

    def test_adaptive_contract_uses_shared_ladder_and_obsidian_authority(self):
        self.assertIn("assets/model-capability-ladder.json", module.REQUIRED_FILES)
        self.assertIn("scripts/obsidian_adaptive_model_runner.py", module.REQUIRED_FILES)
        self.assertNotIn("scripts/adaptive_model_runner.py", module.REQUIRED_FILES)
        self.assertIn("Obsidian `Projects/<project-key>/ModelExperience`", module.REQUIRED_ADAPTIVE_TEXT)
        self.assertIn("Old local `model_experience.json` is legacy read-only only", module.REQUIRED_ADAPTIVE_TEXT)
        self.assertEqual(tuple(module.ACTIVE_MODEL_EFFORTS), module.ACTIVE_MODEL_ORDER)

    def test_shared_ladder_rejects_active_spark(self):
        source = Path(__file__).resolve().parents[1] / "assets" / "model-capability-ladder.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        payload["models"].append({"id": module.LEGACY_SPARK_MODEL, "codex_efforts": ["low"]})
        failures = module.validate_shared_ladder(json.dumps(payload))
        self.assertTrue(any("Spark" in failure or "Luna, Terra, and Sol" in failure for failure in failures))

    def test_sample_plans_are_schema_two_result_then_ending(self):
        for name, plan in module.sample_plans().items():
            with self.subTest(name=name):
                self.assertEqual(plan["schema_version"], 2)
                self.assertEqual({node["phase"] for node in plan["nodes"]}, {"result", "ending"})
                self.assertNotIn("mini_verify_node", plan)
                main_result_node = plan["main_result_node"]
                main = next(node for node in plan["nodes"] if node["id"] == main_result_node)
                self.assertEqual(main["phase"], "result")
                for ending in (node for node in plan["nodes"] if node["phase"] == "ending"):
                    self.assertIn(main_result_node, ending["dependencies"])

    def test_plan_rejects_legacy_foreground_mini_phase(self):
        plan = json.loads(json.dumps(next(iter(module.sample_plans().values()))))
        main_result_node = plan["main_result_node"]
        plan["nodes"].insert(
            1,
            {
                "id": "legacy-mini",
                "phase": "mini",
                "skill": "verify-skill",
                "model": "gpt-5.6-luna",
                "effort": "low",
                "dependencies": [main_result_node],
                "execution_domain": "general",
            },
        )
        plan["mini_verify_node"] = "legacy-mini"
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("phase must be result or ending" in failure for failure in failures))
        self.assertIn("mini_verify_node is not valid in schema 2", failures)

    def test_plan_rejects_renamed_foreground_verifier_without_user_request_flag(self):
        plan = json.loads(json.dumps(next(iter(module.sample_plans().values()))))
        old_main_id = plan["main_result_node"]
        main = next(node for node in plan["nodes"] if node["id"] == old_main_id)
        main.update({"id": "quick-check", "skill": "verify-skill"})
        plan["main_result_node"] = "quick-check"
        for ending in (node for node in plan["nodes"] if node.get("phase") == "ending"):
            ending["dependencies"] = ["quick-check" if dependency == old_main_id else dependency for dependency in ending.get("dependencies", [])]
        failures = module.validate_plan(plan, APPROVED)
        main["user_requested_verification_result"] = True
        authorized_failures = module.validate_plan(plan, APPROVED)
        self.assertIn("quick-check verify-skill result nodes require user_requested_verification_result=true", failures)
        self.assertFalse(any("user_requested_verification_result" in failure for failure in authorized_failures))

    def test_plan_requires_post_result_real_verifier(self):
        plan = json.loads(json.dumps(next(iter(module.sample_plans().values()))))
        plan["nodes"] = [node for node in plan["nodes"] if node["skill"] != "verify-skill"]
        failures = module.validate_plan(plan, APPROVED)
        self.assertIn("plan must contain exactly one post-result Real verifier for the main result", failures)

    def test_downstream_pairs_may_equal_entry_pair(self):
        sample_plans = module.sample_plans()
        plan = json.loads(json.dumps(sample_plans["admitted-single-gpt-5.6-luna-low"]))
        failures = module.validate_plan(plan, APPROVED)
        self.assertEqual(failures, [])

    def test_full_route_plan_requires_explicit_admission_scope(self):
        plan = json.loads(json.dumps(next(iter(module.sample_plans().values()))))
        plan.pop("route_scope")
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("explicitly admitted" in failure for failure in failures))

    def test_route_contract_keeps_ordinary_complex_work_inline(self):
        route_text = (Path(__file__).resolve().parents[1] / "references" / "route-contract.md").read_text(encoding="utf-8")
        self.assertIn("current model performs the task directly regardless of apparent complexity", route_text)
        self.assertIn("Apparent complexity alone does not create a dispatcher", route_text)
        self.assertIn("If admission is absent, execute inline with no route display", route_text)

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
            route_path.write_text(route_path.read_text(encoding="utf-8").replace("## Admitted Complex Graph: Mermaid Route", "## Admitted Complex Graph").replace("```mermaid", "```text"), encoding="utf-8")
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
        next(node for node in plan["nodes"] if node.get("purpose") == "implement")["skill"] = "workflow-skill"
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
        implementation = next(node for node in plan["nodes"] if node.get("purpose") == "implement")
        implementation["language"] = "unity_csharp"
        implementation["skill"] = "workflow-skill"
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("bypasses code-skill" in failure for failure in failures))

    def test_plan_accepts_complex_unity_csharp_with_terra(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        implementation = next(node for node in plan["nodes"] if node.get("purpose") == "implement")
        implementation["language"] = "unity_csharp"
        implementation["skill"] = "code-skill"
        implementation["model"] = "gpt-5.6-terra"
        failures = module.validate_plan(plan, APPROVED)
        self.assertEqual(failures, [])

    def test_plan_rejects_real_verify_before_main_result(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        main = next(node for node in plan["nodes"] if node["id"] == plan["main_result_node"])
        main["dependencies"].append("ending-real")
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("must not depend on Ending work" in failure for failure in failures))

    def test_stale_model_snapshot_is_rejected(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            cache = json.loads(models_cache.read_text(encoding="utf-8"))
            cache["models"] = [model for model in cache["models"] if model["slug"] != "gpt-5.6-terra"]
            models_cache.write_text(json.dumps(cache) + "\n", encoding="utf-8")
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertFalse(result["valid"])
            self.assertTrue(any("shared model-capability ladder failed local cache check" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)

    def test_inline_bootstrap_contract_requires_no_hook(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            original_text = global_agents.read_text(encoding="utf-8")
            for required_term in module.REQUIRED_GLOBAL_BOOTSTRAP_TEXT:
                with self.subTest(required_term=required_term):
                    self.assertIn(required_term, original_text)
                    global_agents.write_text(original_text.replace(required_term, "removed production bootstrap term", 1), encoding="utf-8")
                    validation = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
                    self.assertFalse(validation["valid"])
                    self.assertTrue(any(f"global AGENTS missing required contract: {required_term}" == failure for failure in validation["failures"]))
            global_agents.write_text(original_text, encoding="utf-8")
        finally:
            shutil.rmtree(temp_dir)

    def test_inline_bootstrap_is_compact_and_matches_the_entry_asset_exactly(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            global_agents_text = global_agents.read_text(encoding="utf-8")
            entry_asset_text = (temp_dir / "assets" / "global-agents-entry-rule.md").read_text(encoding="utf-8")
            self.assertLessEqual(len(global_agents_text.encode("utf-8")), module.MAX_GLOBAL_BOOTSTRAP_BYTES)
            self.assertEqual(entry_asset_text.replace(module.GLOBAL_ENTRY_ASSET_DIRECTIVE, "", 1), global_agents_text)
        finally:
            shutil.rmtree(temp_dir)

    def test_inline_bootstrap_requires_universal_post_result_ending_and_no_pre_result_verify(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            bootstrap_text = global_agents.read_text(encoding="utf-8")
            self.assertIn("Eligible text/code producers read the shared ladder", bootstrap_text)
            self.assertIn("Obsidian `Projects/<key>/ModelExperience`", bootstrap_text)
            self.assertIn("local model JSON stays read-only", bootstrap_text)
            self.assertIn("Try Spark first: easy=low, complex=high", bootstrap_text)
            self.assertIn("zero-result operational failure uses the current 5.6 pair", bootstrap_text)
            self.assertIn("published output returns now", bootstrap_text)
            self.assertIn("Prompt/AI-instruction work loads `prompt-skill`", bootstrap_text)
            self.assertIn("durable edits load `project-memory-skill`", bootstrap_text)
            self.assertIn("Every non-ENDING_TASK_WORKER task", bootstrap_text)
            self.assertIn("Ending start receipt", bootstrap_text)
            self.assertIn("independent Ending subagent", bootstrap_text)
            self.assertIn("Ending Real writes the receipt-backed outcome to Obsidian", bootstrap_text)
            self.assertIn("Parallelize isolated logs/docs", bootstrap_text)
            self.assertIn("Final requires PASS or BLOCKED", bootstrap_text)
            self.assertIn("log failed project/module/file state before a new 5.6 repair lifecycle", bootstrap_text)
            self.assertIn("re-present and use a different verifier", bootstrap_text)
            self.assertIn("use a different verifier", bootstrap_text)
            self.assertIn("No hook", bootstrap_text)
            self.assertIn("Exact read-only uses one bounded rg per authoritative file", bootstrap_text)
            self.assertIn("anchored to members", bootstrap_text)
            self.assertNotIn("Mini Verify", bootstrap_text)
            global_agents.write_text(bootstrap_text.replace("one bounded rg", "one search", 1), encoding="utf-8")
            validation = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertFalse(validation["valid"])
            self.assertTrue(any("bounded rg" in failure.lower() for failure in validation["failures"]))
        finally:
            shutil.rmtree(temp_dir)

    def test_inline_bootstrap_rejects_size_growth_and_asset_drift(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            global_agents.write_text(global_agents.read_text(encoding="utf-8") + "x" * module.MAX_GLOBAL_BOOTSTRAP_BYTES, encoding="utf-8")
            oversized = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertTrue(any("exceeds compact bootstrap limit" in failure for failure in oversized["failures"]))
            global_agents.write_text((temp_dir / "assets" / "global-agents-entry-rule.md").read_text(encoding="utf-8").replace(module.GLOBAL_ENTRY_ASSET_DIRECTIVE, "", 1), encoding="utf-8")
            entry_asset = temp_dir / "assets" / "global-agents-entry-rule.md"
            entry_asset.write_text(entry_asset.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")
            drifted = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertTrue(any("does not exactly match global AGENTS" in failure for failure in drifted["failures"]))
        finally:
            shutil.rmtree(temp_dir)

    def test_global_entry_asset_requires_same_production_bootstrap(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            entry_asset = temp_dir / "assets" / "global-agents-entry-rule.md"
            original_text = entry_asset.read_text(encoding="utf-8")
            for required_term in module.REQUIRED_GLOBAL_ENTRY_ASSET_TEXT:
                with self.subTest(required_term=required_term):
                    self.assertIn(required_term, original_text)
                    entry_asset.write_text(original_text.replace(required_term, "removed production bootstrap term", 1), encoding="utf-8")
                    validation = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
                    self.assertFalse(validation["valid"])
                    self.assertTrue(any(f"global entry asset missing required contract: {required_term}" == failure for failure in validation["failures"]))
            entry_asset.write_text(original_text, encoding="utf-8")
        finally:
            shutil.rmtree(temp_dir)

    def test_global_bootstrap_rejects_hook_and_machine_plan_markers(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            entry_asset = temp_dir / "assets" / "global-agents-entry-rule.md"
            for label, path in (("global AGENTS", global_agents), ("global entry asset", entry_asset)):
                original_text = path.read_text(encoding="utf-8")
                for forbidden_term in module.FORBIDDEN_GLOBAL_BOOTSTRAP_TEXT:
                    with self.subTest(label=label, forbidden_term=forbidden_term):
                        path.write_text(original_text + f"\n{forbidden_term}\n", encoding="utf-8")
                        validation = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
                        self.assertFalse(validation["valid"])
                        self.assertTrue(any(f"{label} contains forbidden hook or machine-plan contract: {forbidden_term}" == failure for failure in validation["failures"]))
                path.write_text(original_text, encoding="utf-8")
        finally:
            shutil.rmtree(temp_dir)

    def test_global_bootstrap_does_not_require_benchmark_fixture_shapes(self):
        benchmark_fixture_terms = ["Symbol lookup: first call searches the target plus all assignment lines", "One-file audit: first call reads the whole bounded file; no locator/extractor", "Exact multi-file graph: first call batches the allowlist", "After the final read, emit the requested output immediately; no separate reasoning/self-review", "Mini once", "Route only for proven total token+time wins"]
        for benchmark_fixture_term in benchmark_fixture_terms:
            self.assertNotIn(benchmark_fixture_term, module.REQUIRED_GLOBAL_BOOTSTRAP_TEXT)
            self.assertNotIn(benchmark_fixture_term, module.REQUIRED_GLOBAL_ENTRY_ASSET_TEXT)

    def test_agent_prompt_requires_ordinary_result_inline_contract(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            agent_path = temp_dir / "agents" / "openai.yaml"
            required_term = "trying Spark first"
            agent_path.write_text(agent_path.read_text(encoding="utf-8").replace(required_term, "removed priority attempt"), encoding="utf-8")
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertFalse(result["valid"])
            self.assertIn(f"agents/openai.yaml missing required contract: {required_term}", result["failures"])
        finally:
            shutil.rmtree(temp_dir)

    def test_entry_context_guard_implementation_is_required(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            receipt_path = temp_dir / "scripts" / "model_execution_receipt.py"
            receipt_path.write_text(receipt_path.read_text(encoding="utf-8").replace("entry_context_adaptive_runner_required", "removed_guard_code"), encoding="utf-8")
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertFalse(result["valid"])
            self.assertTrue(any("receipt entry guard" in failure for failure in result["failures"]))
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()

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
QUALITY_MODEL = module.ACTIVE_MODEL_ORDER[0]
QUALITY_EFFORT = module.ACTIVE_MODEL_EFFORTS[QUALITY_MODEL][0]
BALANCED_MODEL, BALANCED_EFFORT = module._complex_followup_node_pair()
COMPLEX_MODEL, COMPLEX_EFFORT = module._complex_followup_implementation_pair()
PRIORITY_MODEL = module.PRIORITY_PRODUCER_MODEL
PRIORITY_EFFORT = module.PRIORITY_PRODUCER["effort_by_complexity"]["easy"] if module.PRIORITY_PRODUCER else None


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

    def test_plan_accepts_complex_quality_code_domain(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        impl = next(node for node in plan["nodes"] if node.get("purpose") == "implement")
        impl["execution_domain"] = "rust"
        impl["skill"] = "code-skill"
        impl["model"] = QUALITY_MODEL
        impl["effort"] = QUALITY_EFFORT
        with self._with_rust_domain() as synthetic_skills_root:
            failures = module.validate_plan(plan, APPROVED, synthetic_skills_root)
        self.assertEqual(failures, [])

    @unittest.skipIf(PRIORITY_MODEL is None, "catalog has no optional priority producer")
    def test_plan_rejects_priority_producer_as_code_plan_node(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        impl = next(node for node in plan["nodes"] if node.get("purpose") == "implement")
        impl["execution_domain"] = "rust"
        impl["skill"] = "code-skill"
        impl["model"] = PRIORITY_MODEL
        impl["effort"] = PRIORITY_EFFORT
        with self._with_rust_domain() as synthetic_skills_root:
            failures = module.validate_plan(plan, APPROVED, synthetic_skills_root)
        self.assertTrue(any("schedule producer is valid only for a disjoint source branch" in failure for failure in failures))

    @unittest.skipIf(PRIORITY_MODEL is None, "catalog has no optional priority producer")
    def test_plan_rejects_priority_producer_entry(self):
        plan = json.loads(json.dumps(next(iter(module.sample_plans().values()))))
        plan["entry"] = {"model": PRIORITY_MODEL, "effort": PRIORITY_EFFORT}
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("entry schedule producer is valid only for a disjoint source branch" in failure for failure in failures))

    def make_validation_inputs(self):
        source = Path(__file__).resolve().parents[1]
        temp_dir = Path(tempfile.mkdtemp(prefix="task-analyze-validate-"))
        for relative in module.REQUIRED_FILES:
            destination = temp_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text((source / relative).read_text(encoding="utf-8"), encoding="utf-8")
        models_cache = temp_dir / "models_cache.json"
        ladder = json.loads((source / "assets" / "model-capability-ladder.json").read_text(encoding="utf-8"))
        registry_rows = list(ladder["models"])
        if ladder.get("priority_producer"):
            registry_rows.append(ladder["priority_producer"])
        cache_models = []
        for row in registry_rows:
            efforts = row["codex_efforts"]
            cache_models.append({"slug": row["id"], "display_name": row.get("display_name", row["id"]), "description": row.get("provider_positioning", ""), "visibility": "list", "priority": row["provider_priority"], "supported_reasoning_levels": [{"effort": effort} for effort in efforts], "default_reasoning_level": row.get("default_effort", efforts[0]), "supported_in_api": row.get("supported_in_api", False), "input_modalities": row.get("input_modalities", ["text"]), "context_window": row.get("context_window"), "additional_speed_tiers": row.get("additional_speed_tiers", [])})
        models_cache.write_text(json.dumps({"client_version": "validator-test", "fetched_at": "2026-07-15T00:00:00Z", "models": cache_models}, indent=2) + "\n", encoding="utf-8")
        catalog, catalog_sha256 = module.load_catalog(models_cache)
        generated_ladder = module.build_registry(catalog, catalog_sha256)
        (temp_dir / "assets" / "model-capability-ladder.json").write_text(json.dumps(generated_ladder, indent=2) + "\n", encoding="utf-8")
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
        self.assertIn("Before presenting a light/local Python edit", python_text)
        self.assertIn("separate persistent Codex thread and return without waiting", python_text)
        self.assertIn("Before presentation, run the smallest safe local smoke", csharp_text)
        self.assertIn("separate `End Task-{concise related task name}` thread", csharp_text)
        self.assertNotIn("check before the main result", csharp_text.lower())
        self.assertIn("uses this file plus", unity_text)

    def test_sample_plans_cover_all_supported_entry_pairs(self):
        sample_plans = module.sample_plans()
        expected_plan_count = sum(len(efforts) for efforts in module.ACTIVE_MODEL_EFFORTS.values()) * 2
        entry_pairs = {(plan["entry"]["model"], plan["entry"]["effort"]) for plan in sample_plans.values()}
        self.assertEqual(len(sample_plans), expected_plan_count)
        self.assertEqual(len(entry_pairs), sum(len(efforts) for efforts in module.ACTIVE_MODEL_EFFORTS.values()))
        if module.PRIORITY_PRODUCER_MODEL is not None:
            self.assertNotIn(module.PRIORITY_PRODUCER_MODEL, {model for model, _ in entry_pairs})

    def test_adaptive_contract_uses_shared_ladder_and_obsidian_authority(self):
        self.assertIn("assets/model-capability-ladder.json", module.REQUIRED_FILES)
        self.assertIn("scripts/model_registry.py", module.REQUIRED_FILES)
        self.assertIn("scripts/sync_model_capabilities.py", module.REQUIRED_FILES)
        self.assertIn("scripts/obsidian_adaptive_model_runner.py", module.REQUIRED_FILES)
        self.assertNotIn("scripts/adaptive_model_runner.py", module.REQUIRED_FILES)
        self.assertIn("Obsidian broad `Model Switch.md`", module.REQUIRED_ADAPTIVE_TEXT)
        self.assertIn("sole active private authority", module.REQUIRED_ADAPTIVE_TEXT)
        self.assertEqual(tuple(module.ACTIVE_MODEL_EFFORTS), module.ACTIVE_MODEL_ORDER)

    def test_shared_registry_contains_only_the_highest_numeric_gpt_family_and_source_digest(self):
        payload = json.loads((Path(__file__).resolve().parents[1] / "assets" / "model-capability-ladder.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(tuple(model["id"] for model in payload["models"]), module.ACTIVE_MODEL_ORDER)
        active_family = payload["active_family"]["id"]
        self.assertEqual(payload["active_family"]["selection"], "highest_numeric_gpt_family")
        self.assertTrue(active_family.startswith("gpt-"))
        self.assertTrue(all(model["id"].startswith(f"{active_family}-") or model["id"] == active_family for model in payload["models"]))
        self.assertEqual(payload["active_family"]["model_count"], len(payload["models"]))
        self.assertEqual(len(payload["source"]["catalog_sha256"]), 64)
        if payload.get("priority_producer"):
            self.assertNotIn(payload["priority_producer"]["id"], module.ACTIVE_MODEL_ORDER)

    def test_explicit_check_detects_a_higher_synthetic_numeric_family_without_version_assumption(self):
        temp_dir, models_cache, _, _ = self.make_validation_inputs()
        try:
            cache = json.loads(models_cache.read_text(encoding="utf-8"))
            synthetic_models = [{"slug": "gpt-99-test-weak", "display_name": "Synthetic Weak", "description": "Fast synthetic coding model.", "visibility": "list", "priority": 3, "supported_reasoning_levels": [{"effort": "low"}, {"effort": "medium"}, {"effort": "high"}], "default_reasoning_level": "medium", "supported_in_api": True, "input_modalities": ["text", "image"], "context_window": 272000, "additional_speed_tiers": []}, {"slug": "gpt-99-test-balanced", "display_name": "Synthetic Balanced", "description": "Balanced synthetic coding model for everyday work.", "visibility": "list", "priority": 2, "supported_reasoning_levels": [{"effort": "low"}, {"effort": "medium"}, {"effort": "high"}], "default_reasoning_level": "medium", "supported_in_api": True, "input_modalities": ["text", "image"], "context_window": 272000, "additional_speed_tiers": []}, {"slug": "gpt-99-test-frontier", "display_name": "Synthetic Frontier", "description": "Frontier synthetic coding model.", "visibility": "list", "priority": 1, "supported_reasoning_levels": [{"effort": "low"}, {"effort": "medium"}, {"effort": "high"}], "default_reasoning_level": "high", "supported_in_api": True, "input_modalities": ["text", "image"], "context_window": 272000, "additional_speed_tiers": []}]
            cache["models"].extend(synthetic_models)
            models_cache.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
            catalog, catalog_sha256 = module.load_catalog(models_cache)
            expected_registry = module.build_registry(catalog, catalog_sha256)
            self.assertEqual(expected_registry["active_family"]["id"], "gpt-99")
            self.assertEqual([model["id"] for model in expected_registry["models"]], ["gpt-99-test-weak", "gpt-99-test-balanced", "gpt-99-test-frontier"])
            self.assertFalse(any(model["id"] in module.ACTIVE_MODEL_ORDER for model in expected_registry["models"]))
            if module.PRIORITY_PRODUCER_MODEL is not None:
                self.assertEqual(expected_registry["priority_producer"]["id"], module.PRIORITY_PRODUCER_MODEL)
            ladder_text = (temp_dir / "assets" / "model-capability-ladder.json").read_text(encoding="utf-8")
            status = module.check_model_cache_ladder(models_cache, ladder_text)
            self.assertFalse(status["valid"])
            self.assertEqual(status["status"], "stale")
            self.assertNotEqual(status["expected_catalog_sha256"], status["observed_catalog_sha256"])
        finally:
            shutil.rmtree(temp_dir)

    def test_catalog_fetch_timestamp_only_does_not_mark_registry_stale(self):
        temp_dir, models_cache, _, _ = self.make_validation_inputs()
        try:
            cache = json.loads(models_cache.read_text(encoding="utf-8"))
            cache["fetched_at"] = "2099-01-01T00:00:00Z"
            models_cache.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
            ladder_text = (temp_dir / "assets" / "model-capability-ladder.json").read_text(encoding="utf-8")
            status = module.check_model_cache_ladder(models_cache, ladder_text)
            self.assertTrue(status["valid"])
            self.assertEqual(status["status"], "pass")
            self.assertEqual(status["expected_catalog_sha256"], status["observed_catalog_sha256"])
        finally:
            shutil.rmtree(temp_dir)

    @unittest.skipIf(PRIORITY_MODEL is None, "catalog has no optional priority producer")
    def test_shared_ladder_rejects_priority_producer_as_quality_rung(self):
        source = Path(__file__).resolve().parents[1] / "assets" / "model-capability-ladder.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        duplicate = dict(payload["models"][-1])
        duplicate["id"] = PRIORITY_MODEL
        duplicate["capability_rank"] = len(payload["models"]) + 1
        duplicate["provider_priority"] = payload["models"][-1]["provider_priority"] - 1
        payload["models"].append(duplicate)
        failures = module.validate_shared_ladder(json.dumps(payload))
        self.assertTrue(any("invalid" in failure or "priority producer" in failure for failure in failures))

    def test_shared_ladder_rejects_private_learning_hierarchy_contract_drift(self):
        source = Path(__file__).resolve().parents[1] / "assets" / "model-capability-ladder.json"
        payload = json.loads(source.read_text(encoding="utf-8"))
        payload["private_learning_contract"]["hierarchy_notes"] = True
        failures = module.validate_shared_ladder(json.dumps(payload))
        self.assertTrue(any("private learning contract" in failure or "invalid" in failure for failure in failures))

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
                "model": QUALITY_MODEL,
                "effort": QUALITY_EFFORT,
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
        plan = json.loads(json.dumps(next(plan for plan in sample_plans.values() if plan["complexity"] == "easy")))
        failures = module.validate_plan(plan, APPROVED)
        self.assertEqual(failures, [])

    def test_full_route_plan_requires_explicit_admission_scope(self):
        plan = json.loads(json.dumps(next(iter(module.sample_plans().values()))))
        plan.pop("route_scope")
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("explicitly admitted" in failure for failure in failures))

    def test_route_contract_routes_eligible_production_and_keeps_exact_read_only_inline(self):
        route_text = (Path(__file__).resolve().parents[1] / "references" / "route-contract.md").read_text(encoding="utf-8")
        self.assertIn("Eligible text/code production calls `obsidian_adaptive_model_runner.py` exactly once even on cold start", route_text)
        self.assertIn("Other exact read-only work stays inline", route_text)
        self.assertIn("Apparent complexity alone does not create a dispatcher", route_text)
        self.assertIn("An open-ended multi-node foreground exists only after comparable end-to-end evidence positively admits it", route_text)

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

    def test_plan_accepts_complex_unity_csharp_with_quality_model(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        implementation = next(node for node in plan["nodes"] if node.get("purpose") == "implement")
        implementation["language"] = "unity_csharp"
        implementation["skill"] = "code-skill"
        implementation["model"] = COMPLEX_MODEL
        implementation["effort"] = COMPLEX_EFFORT
        failures = module.validate_plan(plan, APPROVED)
        self.assertEqual(failures, [])

    def test_plan_rejects_real_verify_before_main_result(self):
        complex_plan = next(plan for plan in module.sample_plans().values() if plan["complexity"] == "complex")
        plan = json.loads(json.dumps(complex_plan))
        main = next(node for node in plan["nodes"] if node["id"] == plan["main_result_node"])
        main["dependencies"].append("ending-real")
        failures = module.validate_plan(plan, APPROVED)
        self.assertTrue(any("must not depend on Ending work" in failure for failure in failures))

    def test_saved_model_snapshot_is_not_passively_compared_to_local_cache(self):
        temp_dir, models_cache, global_agents, global_skills = self.make_validation_inputs()
        try:
            cache = json.loads(models_cache.read_text(encoding="utf-8"))
            cache["models"] = [model for model in cache["models"] if model["slug"] != QUALITY_MODEL]
            models_cache.write_text(json.dumps(cache) + "\n", encoding="utf-8")
            result = module.validate(temp_dir, models_cache, global_agents, global_skills, temp_dir / "hooks.json")
            self.assertTrue(result["valid"])
            self.assertEqual(result["capability_status"]["status"], "saved")
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
            for required_term in module.REQUIRED_GLOBAL_BOOTSTRAP_TEXT:
                self.assertIn(required_term, bootstrap_text)
            self.assertIn("Producer owns files/skills/Mini Test", bootstrap_text)
            self.assertIn("create/link `End Task-{task name}` if available", bootstrap_text)
            self.assertIn("never subtask/emulate/wait/self-verify", bootstrap_text)
            self.assertIn("Ending <=60s evidence-only", bootstrap_text)
            self.assertIn("never gates", bootstrap_text)
            self.assertIn("`gpt-5.6-sol|ultra`", bootstrap_text)
            self.assertIn("before skills/memory/files", bootstrap_text)
            self.assertIn("NEVER spawn/read", bootstrap_text)
            self.assertIn("task vs task+Ending", bootstrap_text)
            self.assertIn("no reread/full read/precheck", bootstrap_text)
            self.assertNotIn("Mini Verify", bootstrap_text)
            global_agents.write_text(bootstrap_text.replace("one bounded rg/file", "one search/file", 1), encoding="utf-8")
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
            required_term = "before skills, memory, or files"
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

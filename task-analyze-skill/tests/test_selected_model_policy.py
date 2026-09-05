import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location("selected_tests_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


policy = load("selected_model_policy")
runner = load("obsidian_adaptive_model_runner")
receipt = load("model_execution_receipt")
disclosure = load("model_identity_disclosure")


class SelectedModelPolicyTests(unittest.TestCase):
    def test_exact_user_pair_preserved_for_each_governing_surface(self):
        for model, effort in [("gpt-5.6-luna", "max"), ("gpt-6-astra", "ultra")]:
            for skill in ["code-skill", "emil-design-eng", "prompt-skill", "project-memory-skill"]:
                with self.subTest(model=model, skill=skill):
                    node = {"skill": skill, "model": "gpt-5.3-codex-spark", "effort": "low", "priority_producer": True, "allow_fallback": ["gpt-5.6-sol|high"]}
                    policy.bind_node(node, model, effort)
                    self.assertEqual((node["model"], node["effort"]), (model, effort))
                    self.assertEqual(node["allow_fallback"], [])
                    self.assertNotIn("priority_producer", node)

    def test_incidental_shell_inherits_governing_constraint(self):
        node = {"skill_governed": True, "operation": "execute", "complexity_score": 1, "model": "gpt-5.3-codex-spark", "effort": "low"}
        policy.bind_node(node, "gpt-6-astra", "ultra")
        self.assertEqual(node["model"], "gpt-6-astra")

    def test_independence_claim_cannot_erase_named_skill(self):
        self.assertTrue(policy.uses_selected_model({"skill_independent": True, "governing_skills": ["code-skill"]}))
        self.assertTrue(policy.uses_selected_model({"skill_governed": False, "routing_condition": {"owning_skill": "emil-design-eng"}}))

    def test_routing_machinery_alone_does_not_lock_an_independent_task(self):
        node = {"skill": "workflow-skill", "model": "gpt-5.6-luna", "effort": "low"}
        self.assertFalse(policy.uses_selected_model(node))
        policy.bind_node(node, "gpt-6-astra", "ultra")
        self.assertEqual(node["model"], "gpt-5.6-luna")

    def test_memory_summary_always_preserves_user_pair(self):
        for scope in ({"phase": "ending"}, {"task_type": "memory"}, {"memory_update": True}, {"operation": "memory-summary"}):
            self.assertTrue(policy.uses_selected_model(scope))

    def test_unknown_selected_identity_is_not_silently_downgraded(self):
        with self.assertRaisesRegex(ValueError, "selected_model_required"):
            policy.bind_node({"skill": "code-skill"}, "unknown", "unknown")

    def test_selected_recommendation_never_reads_adaptive_history(self):
        args = SimpleNamespace(governing_skills=["code-skill"], resolved_entry_model="gpt-6-astra", resolved_entry_effort="ultra")
        with patch.object(runner.obsidian_model_memory, "recommend_model", side_effect=AssertionError("history must not select governed work")):
            recommendation = runner._recommend(args, "edit a value")
        self.assertEqual(recommendation["selected_pair"], "gpt-6-astra|ultra")
        self.assertIsNone(recommendation["active_fallback_pair"])

    def test_exact_output_guard_cannot_upgrade_governed_work(self):
        recommendation = policy.recommendation("gpt-5.6-luna", "max")
        with patch.object(runner, "_is_exact_expression_contract", return_value=True):
            self.assertEqual(runner._exact_contract_recommendation("exact expression", recommendation)["selected_pair"], "gpt-5.6-luna|max")

    def test_selected_pair_rejects_automatic_fallback_even_if_caller_supplies_one(self):
        args = SimpleNamespace(allow_fallback=["gpt-5.6-sol|high"])
        with patch.object(runner.obsidian_model_memory, "load_shared_ladder", side_effect=AssertionError("not adaptive")):
            self.assertEqual(runner._attempt_pairs(args, policy.recommendation("gpt-6-astra", "ultra")), ["gpt-6-astra|ultra"])

    def test_default_code_cli_carries_governing_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            args = runner.resolve_fast_path_args(runner.parse_args(["--workdir", temp, "--task-type", "code"]), "change the function")
        self.assertEqual(args.governing_skills, ["code-skill"])

    def test_independent_cli_requires_explicit_classification_for_code_helper(self):
        with tempfile.TemporaryDirectory() as temp:
            args = runner.resolve_fast_path_args(runner.parse_args(["--workdir", temp, "--task-type", "code", "--skill-independent"]), "run a simple standalone extraction script")
        self.assertFalse(policy.uses_selected_model(args))

    def test_keyword_counts_do_not_force_a_graph(self):
        with tempfile.TemporaryDirectory() as temp:
            args = runner.resolve_fast_path_args(runner.parse_args(["--workdir", temp]), "inspect fix and test this function")
        self.assertFalse(args.graph_required)

    def test_verification_stays_in_task_and_test_only_does_not_require_memory(self):
        result = runner.result_lifecycle_policy(True, "question", 65, "low", operation="verify", real_test=True, material_update_kind="none")
        self.assertFalse(result["ending_required"])
        self.assertEqual(result["verification_owner"], "active_task")
        self.assertEqual(result["deferred_verification_owner"], "none")

    def test_simple_value_change_skips_verification(self):
        result = runner.result_lifecycle_policy(True, "code", 8, "low", material_update_kind="trivial_value_only")
        self.assertEqual(result["producer_check_scope"], "skip_simple_value_change")
        self.assertFalse(result["ending_required"])

    def test_material_change_only_requests_memory_closeout(self):
        result = runner.result_lifecycle_policy(True, "code", 70, "low", material_update_kind="structural")
        self.assertTrue(result["ending_required"])
        self.assertEqual(result["ending_purpose"], "memory_only")
        self.assertEqual(result["ending_model_policy"], "user_selected")

    def test_old_ending_check_worker_cannot_run(self):
        with self.assertRaisesRegex(ValueError, "retired"):
            receipt.route_node_lifecycle_boundary("ENDING_CHECK_WORKER")

    def test_receipt_prompt_allows_in_task_ui_check_and_prohibits_unrequested_full_build(self):
        text = receipt.route_node_lifecycle_boundary("LOCKED_ROUTE_NODE", {})
        self.assertIn("inside this active task", text)
        self.assertIn("unless requested", text)
        self.assertNotIn("exactly one", text)

    def test_memory_event_does_not_launch_a_task(self):
        output = io.StringIO()
        with redirect_stdout(output):
            runner._emit_ending_required({"entry_pair": "gpt-6-astra|ultra"})
        event = json.loads(output.getvalue())
        self.assertEqual(event["stage"], "memory-closeout-required")
        self.assertNotIn("thread_target", event)
        self.assertEqual(event["selected_pair"], "gpt-6-astra|ultra")

    def test_new_selected_model_can_be_disclosed_without_old_catalog_gate(self):
        identity = disclosure.resolve_disclosure_identity(entry_resolution={"status": "verified", "model": "gpt-6-astra", "effort": "ultra"})
        self.assertEqual(identity["effective_pair"], "gpt-6-astra|ultra")


if __name__ == "__main__":
    unittest.main()

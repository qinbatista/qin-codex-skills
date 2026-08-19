#!/usr/bin/env python3
import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "session_effort.py"
SPEC = importlib.util.spec_from_file_location("session_effort", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class SessionEffortTests(unittest.TestCase):
    def turn_key(self, turn_id):
        return hashlib.sha256(turn_id.encode("utf-8")).hexdigest()[:24]

    def write_session(self, root, session_id, project, turns=None):
        session_path = root / "2026" / "08" / "03" / f"rollout-{session_id}.jsonl"
        session_path.parent.mkdir(parents=True)
        turns = turns or [("turn-1", "gpt-5.6-luna", "max", "implement the SVG corner trace."), ("turn-2", "gpt-5.6-luna", "max", "still wrong, fix the SVG corner line."), ("turn-3", "gpt-5.6-terra", "max", "again, fix the SVG corner line.")]
        events = [{"type": "session_meta", "payload": {"session_id": session_id, "cwd": str(project)}}]
        for turn_id, model, effort, message in turns:
            events.extend([{"type": "turn_context", "payload": {"turn_id": turn_id, "model": model, "effort": effort}}, {"type": "event_msg", "payload": {"type": "user_message", "message": f"My request for Codex: {message}"}}])
        session_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    def write_terminal_outcome(self, store, session_id, module_name, turn_id, pair, real_status, failure_class=None):
        session_key = module.session_key(session_id)
        task_scope = module.task_scope_key("demo", "code", module_name, module_name)
        session_scope = module.session_task_scope_key(session_key, task_scope)
        route_event_id = f"route-{turn_id}"
        failure_class = failure_class or ("none" if real_status == "pass" else "quality")
        route_record = {"session_memory_schema": 2, "event_id": route_event_id, "recorded_at": "2026-08-19T00:00:00Z", "session_key": session_key, "codex_session_key": session_key, "session_task_scope_key": session_scope, "turn_key": self.turn_key(turn_id), "project_key": "demo", "task_type": "code", "module": module_name, "selected_pair": pair}
        result_record = {"model_experience_schema": 1, "event_id": f"result-{turn_id}", "recorded_at": "2026-08-19T00:01:00Z", "session_key": session_key, "codex_session_key": session_key, "session_task_scope_key": session_scope, "project_key": "demo", "task_type": "code", "module": module_name, "session_event_id": route_event_id, "completed_pair": pair, "model_evidence": "runtime_receipt", "receipt_status": "pass", "turn_completed": True, "model_match": True, "effort_match": True, "real_status": real_status, "failure_class": failure_class}
        envelopes = [{"local_model_memory_schema": 2, "event": "session-effort", "record": route_record}, {"local_model_memory_schema": 1, "event": "model-result", "record": result_record}]
        store.write_text("".join(json.dumps(envelope) + "\n" for envelope in envelopes), encoding="utf-8")

    def test_repeated_failure_escalates_and_records_user_effort(self):
        session_id = "019fc8e5-87da-7082-90b9-6d505404d229"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            self.write_session(root / "sessions", session_id, project)
            store = root / "events.jsonl"
            prompt = "Still wrong, fix the SVG corner line."
            summary = module.assess_session(prompt, project, project_key="demo", task_type="code", module="svg-repair", operation="fix", modality="mixed", complexity_score=65, task_summary=prompt, session_id=session_id, sessions_root=root / "sessions", local_store=store)
            self.assertTrue(summary["failure_recorded"])
            self.assertEqual(summary["state"], "repeated_failure")
            self.assertEqual(summary["last_model_pair"], "gpt-5.6-luna|max")
            self.assertEqual(summary["route_class"], "core_solving_short_difficult")
            self.assertEqual(summary["preferred_solving_pair"], "gpt-5.6-terra|low")
            self.assertEqual(module.next_escalation_pair(summary["last_model_pair"], ["gpt-5.6-luna|max", "gpt-5.6-terra|max", "gpt-5.6-sol|max", "gpt-5.6-sol|ultra"]), "gpt-5.6-terra|max")
            written = module.record_session_effort(summary, project_key="demo", task_type="code", module="svg-repair", complexity_score=65, complexity_band="complex", selected_pair="gpt-5.6-terra|max", requested_pair="gpt-5.6-luna|max", local_store=store)
            self.assertEqual(written["status"], "written")
            next_summary = module.assess_session("Again, fix the SVG corner line.", project, project_key="demo", task_type="code", module="svg-repair", operation="fix", modality="mixed", complexity_score=65, task_summary="Again, fix the SVG corner line.", session_id=session_id, sessions_root=root / "sessions", local_store=store)
            self.assertEqual(next_summary["last_model_pair"], "gpt-5.6-terra|max")

    def test_transformed_current_tail_is_not_counted_as_prior_work(self):
        session_id = "019fc8e5-87da-7082-90b9-6d505404d229"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            self.write_session(root / "sessions", session_id, project, [("turn-1", "gpt-5.6-luna", "max", "implement the session history model route.")])
            summary = module.assess_session("Can you implement the model routing session history?", project, project_key="demo", task_type="code", module="routing", operation="implement", modality="text", complexity_score=40, task_summary="Can you implement the model routing session history?", session_id=session_id, sessions_root=root / "sessions", local_store=root / "events.jsonl")
        self.assertEqual(summary["current_turn_match"], "semantic_tail")
        self.assertEqual(summary["same_task_turns"], 0)
        self.assertFalse(summary["failure_recorded"])
        self.assertEqual(summary["state"], "solved_or_new_topic")

    def test_verified_pass_resets_session_escalation_until_feedback_is_corrective(self):
        session_id = "019fc8e5-87da-7082-90b9-6d505404d229"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            store = root / "events.jsonl"
            self.write_session(root / "sessions", session_id, project, [("turn-1", "gpt-5.6-luna", "max", "implement the session history model route."), ("turn-2", "gpt-5.6-luna", "max", "continue the session history model route.")])
            self.write_terminal_outcome(store, session_id, "routing", "turn-1", "gpt-5.6-luna|max", "pass")
            summary = module.assess_session("Continue the session history model route.", project, project_key="demo", task_type="code", module="routing", operation="implement", modality="text", complexity_score=65, task_summary="Continue the session history model route.", session_id=session_id, sessions_root=root / "sessions", local_store=store)
        self.assertEqual(summary["resolution_state"], "verified_pass")
        self.assertEqual(summary["last_model_source"], "verified_terminal")
        self.assertEqual(summary["last_model_pair"], "gpt-5.6-luna|max")
        self.assertFalse(summary["failure_recorded"])

    def test_corrective_feedback_escalates_from_verified_terminal_pair(self):
        session_id = "019fc8e5-87da-7082-90b9-6d505404d229"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            store = root / "events.jsonl"
            self.write_session(root / "sessions", session_id, project, [("turn-1", "gpt-5.6-luna", "max", "implement the session history model route."), ("turn-2", "gpt-5.6-luna", "max", "still wrong, repair the session history model route.")])
            self.write_terminal_outcome(store, session_id, "routing", "turn-1", "gpt-5.6-luna|max", "pass")
            summary = module.assess_session("Still wrong, repair the session history model route.", project, project_key="demo", task_type="code", module="routing", operation="fix", modality="text", complexity_score=65, task_summary="Still wrong, repair the session history model route.", session_id=session_id, sessions_root=root / "sessions", local_store=store)
        self.assertTrue(summary["failure_recorded"])
        self.assertEqual(summary["resolution_state"], "feedback_unresolved")
        self.assertEqual(summary["last_model_source"], "verified_terminal")
        self.assertEqual(module.solve_route_pair(summary, summary["last_model_pair"], ["gpt-5.6-luna|max", "gpt-5.6-terra|low", "gpt-5.6-sol|low"])["pair"], "gpt-5.6-terra|low")

    def test_verified_terminal_failure_marks_same_topic_unresolved_without_feedback_words(self):
        session_id = "019fc8e5-87da-7082-90b9-6d505404d229"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            store = root / "events.jsonl"
            self.write_session(root / "sessions", session_id, project, [("turn-1", "gpt-5.6-luna", "max", "implement the session history model route."), ("turn-2", "gpt-5.6-luna", "max", "continue the session history model route.")])
            self.write_terminal_outcome(store, session_id, "routing", "turn-1", "gpt-5.6-luna|max", "fail")
            summary = module.assess_session("Continue the session history model route.", project, project_key="demo", task_type="code", module="routing", operation="implement", modality="text", complexity_score=65, task_summary="Continue the session history model route.", session_id=session_id, sessions_root=root / "sessions", local_store=store)
        self.assertTrue(summary["failure_recorded"])
        self.assertEqual(summary["resolution_state"], "verified_failure")
        self.assertEqual(summary["latest_terminal_outcome"], "verified_fail")

    def test_operational_terminal_failure_does_not_upgrade_the_model(self):
        session_id = "019fc8e5-87da-7082-90b9-6d505404d229"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            store = root / "events.jsonl"
            self.write_session(root / "sessions", session_id, project, [("turn-1", "gpt-5.6-luna", "max", "implement the session history model route."), ("turn-2", "gpt-5.6-luna", "max", "continue the session history model route.")])
            self.write_terminal_outcome(store, session_id, "routing", "turn-1", "gpt-5.6-luna|max", "fail", "execution")
            summary = module.assess_session("Continue the session history model route.", project, project_key="demo", task_type="code", module="routing", operation="implement", modality="text", complexity_score=65, task_summary="Continue the session history model route.", session_id=session_id, sessions_root=root / "sessions", local_store=store)
        self.assertFalse(summary["failure_recorded"])
        self.assertEqual(summary["latest_terminal_outcome"], "operational_failure")
        self.assertEqual(summary["resolution_state"], "unverified_continuation")

    def test_new_topic_does_not_inherit_failure(self):
        session_id = "019fc8e5-87da-7082-90b9-6d505404d229"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            self.write_session(root / "sessions", session_id, project)
            summary = module.assess_session("Implement the database migration for invoices.", project, project_key="demo", task_type="code", module="billing", session_id=session_id, sessions_root=root / "sessions", local_store=root / "events.jsonl")
        self.assertFalse(summary["failure_recorded"])
        self.assertEqual(summary["state"], "solved_or_new_topic")
        self.assertEqual(summary["same_task_turns"], 0)

    def test_response_item_history_detects_one_unresolved_task_and_escalates(self):
        session_id = "019fc8e5-87da-7082-90b9-6d505404d229"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / "project"
            project.mkdir()
            session_path = root / "sessions" / "2026" / "08" / "03" / f"rollout-{session_id}.jsonl"
            session_path.parent.mkdir(parents=True)
            events = [
                {"type": "session_meta", "payload": {"session_id": session_id, "cwd": str(project)}},
                {"type": "response_item", "payload": {"role": "user", "type": "message", "content": [{"type": "input_text", "text": "Injected context, not a task turn."}]}},
                {"type": "turn_context", "payload": {"turn_id": "turn-1", "model": "gpt-5.6-luna", "effort": "max"}},
                {"type": "response_item", "payload": {"role": "user", "type": "message", "content": [{"type": "input_text", "text": "Implement the session history model route."}]}},
                {"type": "event_msg", "payload": {"type": "user_message", "message": "Implement the session history model route."}},
                {"type": "turn_context", "payload": {"turn_id": "turn-2", "model": "gpt-5.6-luna", "effort": "max"}},
                {"type": "response_item", "payload": {"role": "user", "type": "message", "content": [{"type": "input_text", "text": "Still wrong, fix the session history model route."}]}},
                {"type": "event_msg", "payload": {"type": "user_message", "message": "Still wrong, fix the session history model route."}},
            ]
            session_path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
            prompt = "Still wrong, fix the session history model route."
            summary = module.assess_session(prompt, project, project_key="demo", task_type="code", module="routing", operation="fix", modality="text", complexity_score=65, task_summary=prompt, session_id=session_id, sessions_root=root / "sessions", local_store=root / "events.jsonl")
        self.assertTrue(summary["failure_recorded"])
        self.assertEqual(summary["turn_count"], 2)
        self.assertEqual(summary["same_task_turns"], 1)
        self.assertEqual(summary["last_model_pair"], "gpt-5.6-luna|max")
        self.assertEqual(module.solve_route_pair(summary, summary["last_model_pair"], ["gpt-5.6-luna|max", "gpt-5.6-terra|low", "gpt-5.6-sol|low"])["pair"], "gpt-5.6-terra|low")

    def test_session_and_explicit_task_scope_are_hashed_and_isolated(self):
        first_session = module.session_key("019fc8e5-87da-7082-90b9-6d505404d229")
        second_session = module.session_key("019fc8e5-87da-7082-90b9-6d505404d230")
        first_task = module.task_scope_key("demo", "code", "pipeline", "step-one")
        second_task = module.task_scope_key("demo", "code", "pipeline", "step-two")
        self.assertNotEqual(first_session, second_session)
        self.assertNotEqual(first_task, second_task)
        self.assertTrue(module.scope_matches({"codex_session_key": first_session, "task_scope_key": first_task}, session_key_value=first_session, task_scope=first_task))
        related = module.scope_relation({"codex_session_key": first_session, "task_scope_key": first_task}, session_key_value=second_session, task_scope=first_task)
        self.assertTrue(related["matched"])
        self.assertEqual(related["reason"], "related_task_scope")
        self.assertFalse(module.scope_matches({"codex_session_key": first_session, "task_scope_key": first_task}, session_key_value=first_session, task_scope=second_task))
        self.assertFalse(module.scope_matches({"codex_session_key": first_session, "task_scope_key": first_task}, session_key_value=second_session, task_scope=second_task))
        self.assertFalse(module.scope_matches({"session_key": "", "task_scope_key": ""}, session_key_value=first_session))

    def test_related_task_group_crosses_sessions_only_with_explicit_group_evidence(self):
        first_session = module.session_key("019fc8e5-87da-7082-90b9-6d505404d229")
        second_session = module.session_key("019fc8e5-87da-7082-90b9-6d505404d230")
        group = module.task_group_key("demo", "shared-route", "related-step")
        relation = module.scope_relation({"codex_session_key": first_session, "task_name": "related-step", "task_group": "shared-route", "task_group_key": group}, session_key_value=second_session, task_group_key_value=group)
        self.assertTrue(relation["matched"])
        self.assertEqual(relation["reason"], "related_task_group")
        isolated = module.scope_relation({"codex_session_key": first_session, "task_group_key": module.task_group_key("demo", "other-route", "other-step")}, session_key_value=second_session, task_group_key_value=group)
        self.assertFalse(isolated["matched"])
        self.assertEqual(isolated["reason"], "unrelated_session")

    def test_escalation_stops_at_sol_ultra(self):
        pairs = ["gpt-5.6-luna|max", "gpt-5.6-terra|max", "gpt-5.6-sol|max", "gpt-5.6-sol|ultra"]
        self.assertEqual(module.next_escalation_pair("gpt-5.6-luna|max", pairs), "gpt-5.6-terra|max")
        self.assertEqual(module.next_escalation_pair("gpt-5.6-terra|max", pairs), "gpt-5.6-sol|max")
        self.assertEqual(module.next_escalation_pair("gpt-5.6-sol|max", pairs), "gpt-5.6-sol|ultra")
        self.assertIsNone(module.next_escalation_pair("gpt-5.6-sol|ultra", pairs))

    def test_task_class_selects_cheaper_image_and_max_long_solving_routes(self):
        image = module.classify_task("Read the image and compare the sleeve shape.", operation="inspect", modality="image", complexity_score=20)
        medium_task = module.classify_task("Read the design, compare all corners, and fix the SVG.", operation="fix", modality="mixed", complexity_score=55)
        long_task = module.classify_task("Trace all outlines first, then inspect every intersection, update multiple files, run tests, and export the final result.", operation="fix", modality="mixed", complexity_score=65)
        frontier_task = module.classify_task("Comprehensively read and understand massive information from many sources, synthesize tradeoffs, choose an architecture, and write the final plan.", operation="analyze", modality="text", complexity_score=70)
        explicit_entry = module.classify_task("Use gpt-5.6-luna|max as the entry model, then fix this difficult SVG.", operation="fix", modality="mixed", complexity_score=65)
        generic_code = module.classify_task("Implement the database migration and run tests.", task_type="code", operation="implement", modality="text", complexity_score=55)
        simple_prose = module.classify_task("Write a short email confirming the meeting.", task_type="general", operation="write", modality="text", complexity_score=10)
        self.assertEqual(image["solving_surface"], "image_inspection")
        self.assertEqual(image["preferred_solving_pair"], "gpt-5.6-luna|low")
        self.assertEqual(medium_task["estimated_effort"], "medium")
        self.assertEqual(medium_task["preferred_solving_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(long_task["task_length"], "long")
        self.assertEqual(long_task["preferred_solving_pair"], "gpt-5.6-terra|max")
        self.assertEqual(frontier_task["model_family"], "gpt-5.6-sol")
        self.assertEqual(frontier_task["estimated_effort"], "max")
        self.assertEqual(frontier_task["preferred_solving_pair"], "gpt-5.6-sol|max")
        self.assertEqual(explicit_entry["explicit_route_hint"], "gpt-5.6-luna|max")
        self.assertEqual(explicit_entry["preferred_solving_pair"], "gpt-5.6-terra|low")
        self.assertEqual(generic_code["preferred_solving_pair"], "gpt-5.6-terra|medium")
        self.assertEqual(simple_prose["preferred_solving_pair"], "gpt-5.6-luna|low")

    def test_solving_route_keeps_effort_class_when_model_strengthens(self):
        pairs = ["gpt-5.6-luna|low", "gpt-5.6-luna|max", "gpt-5.6-terra|low", "gpt-5.6-terra|max", "gpt-5.6-sol|low", "gpt-5.6-sol|max"]
        short_core = {"preferred_solving_pair": "gpt-5.6-terra|low", "route_reason": "short_difficult_core_solving_light_route", "last_model_source": "context"}
        long_core = {"preferred_solving_pair": "gpt-5.6-terra|max", "route_reason": "long_core_solving_max_route", "last_model_source": "context"}
        image = {"preferred_solving_pair": "gpt-5.6-luna|low", "route_reason": "cheaper_image_inspection_route", "last_model_source": "context"}
        self.assertEqual(module.solve_route_pair(short_core, "gpt-5.6-luna|max", pairs)["pair"], "gpt-5.6-terra|low")
        self.assertEqual(module.solve_route_pair(short_core, "gpt-5.6-terra|low", pairs)["pair"], "gpt-5.6-sol|low")
        self.assertEqual(module.solve_route_pair(long_core, "gpt-5.6-luna|max", pairs)["pair"], "gpt-5.6-terra|max")
        self.assertEqual(module.solve_route_pair(image, "gpt-5.6-luna|max", pairs)["pair"], "gpt-5.6-luna|low")
        self.assertEqual(module.solve_route_pair(short_core, "gpt-5.6-luna|max", ["gpt-5.6-luna|max"])["pair"], "gpt-5.6-terra|low")


if __name__ == "__main__":
    unittest.main()

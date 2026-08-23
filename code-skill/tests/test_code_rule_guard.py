import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "code_rule_guard.py"
MODULE_SPEC = importlib.util.spec_from_file_location("code_rule_guard", SCRIPT_PATH)
module = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(module)


class CodeRuleGuardTests(unittest.TestCase):
    def codes(self, source, suffix):
        return {item["code"] for item in module.check_text(source, suffix)}

    def test_python_rejects_discard_pass_through_self_recursion_and_vertical_call(self):
        discard = "def run(value):\n    _, kept = value\n    return kept\n"
        wrapper = "def save_data(value):\n    return provider.save_data(value)\n"
        recursion = "def save_data():\n    return save_data()\n"
        vertical = "value = call(\n    first,\n    second,\n)\n"
        self.assertIn("discard-binding", self.codes(discard, ".py"))
        self.assertIn("pass-through-wrapper", self.codes(wrapper, ".py"))
        self.assertIn("self-recursion", self.codes(recursion, ".py"))
        self.assertIn("avoidable-vertical-call", self.codes(vertical, ".py"))

    def test_pattern_wildcard_and_real_semantic_boundary_are_allowed(self):
        boundary = "# code-gate: semantic-boundary=public validation\ndef save_data(value):\n    return provider.save_data(value)\n"
        self.assertNotIn("pass-through-wrapper", self.codes(boundary, ".py"))
        self.assertEqual(self.codes("case _:\n    break;\n", ".cs"), set())

    def test_empty_semantic_boundary_reason_does_not_bypass_wrapper_rule(self):
        boundary = "# code-gate: semantic-boundary=\ndef save_data(value):\n    return provider.save_data(value)\n"
        self.assertIn("pass-through-wrapper", self.codes(boundary, ".py"))

    def test_semantic_boundary_text_inside_a_string_does_not_bypass_wrapper_rule(self):
        boundary = "marker = 'code-gate: semantic-boundary=fake'\ndef save_data(value):\n    return provider.save_data(value)\n"
        self.assertIn("pass-through-wrapper", self.codes(boundary, ".py"))

    def test_python_parse_failure_is_reported_without_a_traceback(self):
        self.assertEqual(self.codes("def broken(:\n", ".py"), {"parse-error"})

    def test_python_awaitable_name_is_not_misread_as_a_call(self):
        source = "async def wait_for_owner(pending):\n    await pending\n"
        self.assertEqual(self.codes(source, ".py"), set())

    def test_unity_csharp_rejects_named_pitfalls(self):
        source = "\n".join(["_ = SaveDataAsync();", "var controller = new PlayerController();", "void SaveData() { SaveData(); }", "public bool SaveData(Data value) => _provider.SaveData(value);", "SaveData(", "    value);", "Widget widget = new Widget(", "    first,", "    second);"])
        self.assertTrue({"discard-assignment", "obvious-var", "self-recursion", "pass-through-wrapper", "avoidable-vertical-call"}.issubset(self.codes(source, ".cs")))

    def test_unity_csharp_rejects_multiline_self_recursion_and_pass_through_wrapper(self):
        source = "\n".join(["void SaveData()", "{", "    SaveData();", "}", "", "public bool PersistData(Data value)", "{", "    return _provider.PersistData(value);", "}"])
        self.assertTrue({"self-recursion", "pass-through-wrapper"}.issubset(self.codes(source, ".cs")))

    def test_duplicate_discard_bindings_on_one_line_emit_one_actionable_violation(self):
        violations = module.check_text("first, _, _, second = values\n", ".py")
        self.assertEqual([(item["code"], item["line"]) for item in violations], [("discard-binding", 1)])

    def test_unity_csharp_allows_direct_call_explicit_type_and_marked_facade(self):
        source = "\n".join(["await SaveDataAsync();", "PlayerController controller = new PlayerController();", "// code-gate: semantic-boundary=public validation", "public bool SaveData(Data value) => _provider.SaveData(value);"])
        self.assertEqual(self.codes(source, ".cs"), set())

    def test_changed_line_filter_does_not_fail_for_legacy_violation_outside_patch(self):
        violations = [module.violation("legacy", 2, "old"), module.violation("new", 7, "new", 9)]
        self.assertEqual([item["code"] for item in module.filter_violations(violations, {8})], ["new"])


if __name__ == "__main__":
    unittest.main()

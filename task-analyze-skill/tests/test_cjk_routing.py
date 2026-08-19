#!/usr/bin/env python3
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "obsidian_adaptive_model_runner.py"
SPEC = importlib.util.spec_from_file_location("cjk_routing_runner", SCRIPT)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class CjkRoutingTests(unittest.TestCase):
    def resolve(self, prompt):
        with tempfile.TemporaryDirectory() as temporary:
            return RUNNER.resolve_fast_path_args(RUNNER.parse_args(["--workdir", temporary]), prompt)

    def test_fullwidth_and_ascii_cjk_questions_are_questions(self):
        prompts = ("这个函数是干什么的？", "这个函数有什么作用?", "为什么这里会报错？", "这个架构有什么问题？", "请解释一下这段代码。", "帮我分析一下这段代码。")
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                arguments = self.resolve(prompt)
                self.assertEqual(arguments.task_type, "question")
                self.assertEqual(arguments.operation, "answer")
                self.assertLessEqual(arguments.complexity_score, 24)
                self.assertTrue(arguments.fast_path_eligible)

    def test_simple_cjk_edits_use_small_fast_path_and_priority_tier(self):
        cases = (("把这个变量从5改成6", "edit"), ("修复这个拼写错误", "fix"), ("删除这一行日志", "delete"), ("给这个函数改个名字", "rename"), ("修改 PlayerController.cs，把 jumpHeight 从 5 改成 6", "edit"))
        for prompt, operation in cases:
            with self.subTest(prompt=prompt):
                arguments = self.resolve(prompt)
                self.assertEqual(arguments.task_type, "code")
                self.assertEqual(arguments.operation, operation)
                self.assertLessEqual(arguments.complexity_score, 24)
                self.assertTrue(arguments.fast_path_eligible)
                selected = RUNNER.routing_policy.priority_first_pair(arguments.task_type, arguments.modality, arguments.operation, arguments.complexity, arguments.complexity_score)
                self.assertEqual(selected, ("gpt-5.3-codex-spark", "low"))
                self.assertTrue(RUNNER.result_lifecycle_policy(True, arguments.task_type, arguments.complexity_score, arguments.risk)["ending_required"])

    def test_cjk_medium_requests_leave_fast_path(self):
        prompts = ("重构这个类，拆成两个组件并补测试", "修改玩家存档系统，同时保持旧存档兼容", "优化这个 Unity UI 页面性能", "重构 SaveManager，把同步保存改成异步，同时保持旧存档兼容并增加测试")
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                arguments = self.resolve(prompt)
                self.assertEqual(arguments.task_type, "code")
                self.assertGreater(arguments.complexity_score, 24)
                self.assertFalse(arguments.fast_path_eligible)
                self.assertTrue(RUNNER.result_lifecycle_policy(True, arguments.task_type, arguments.complexity_score, arguments.risk)["ending_required"])

    def test_cjk_complex_question_is_not_demoted_for_being_a_question(self):
        prompt = "请分析整个项目的架构、数据库迁移、并发风险、回滚方案和完整测试策略？"
        arguments = self.resolve(prompt)
        self.assertEqual(arguments.task_type, "question")
        self.assertEqual(arguments.operation, "answer")
        self.assertGreaterEqual(arguments.complexity_score, 70)
        self.assertFalse(arguments.fast_path_eligible)
        self.assertTrue(arguments.routing_reasons)

    def test_cjk_complex_unity_refactor_reaches_advanced_band(self):
        arguments = self.resolve("重构整个 Unity 项目的存档系统，涉及多个文件、并发、数据库迁移、回滚、测试和性能验证")
        self.assertEqual(arguments.task_type, "code")
        self.assertGreaterEqual(arguments.complexity_score, 75)
        self.assertEqual(arguments.complexity_band, "advanced")
        self.assertFalse(arguments.fast_path_eligible)

    def test_concept_explanation_does_not_inflate_from_technical_terms(self):
        arguments = self.resolve("请解释“数据库迁移、并发、架构、性能”这些词是什么意思？")
        self.assertEqual(arguments.task_type, "question")
        self.assertLessEqual(arguments.complexity_score, 24)
        self.assertTrue(arguments.fast_path_eligible)

    def test_mixed_language_prompt_and_risk_override(self):
        arguments = self.resolve("帮我 refactor SaveManager.cs，把保存改成 async，并补 integration test")
        self.assertEqual(arguments.task_type, "code")
        self.assertEqual(arguments.operation, "refactor")
        self.assertGreater(arguments.complexity_score, 24)
        self.assertFalse(arguments.fast_path_eligible)
        risky = self.resolve("修改 production config 里的一个值")
        self.assertGreater(risky.complexity_score, 24)
        self.assertFalse(risky.fast_path_eligible)

    def test_unknown_intent_is_not_silently_code(self):
        self.assertEqual(RUNNER.infer_task_type("今天天气怎么样"), "question")
        self.assertEqual(RUNNER.infer_task_type("蓝色的云"), "unknown")


if __name__ == "__main__":
    unittest.main()

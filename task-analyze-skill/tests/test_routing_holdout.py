#!/usr/bin/env python3
"""Non-benchmark routing regressions that remain disjoint from the frozen corpus."""

import importlib.util
import json
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = SKILL_ROOT / "scripts" / "routing_policy.py"
SPEC = importlib.util.spec_from_file_location("routing_holdout_policy", POLICY_PATH)
POLICY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(POLICY)


HOLDOUT_CASES = (
    ("请解释 SQLite WAL 是什么？", "question", "answer", 0, 24, True),
    ("把 PlayerInput 的 moveSpeed 从4改成5", "code", "edit", 0, 24, True),
    ("重构网络客户端和服务器同步，处理并发、回滚和集成测试", "code", "refactor", 50, 100, False),
    ("分析跨模块存档迁移和 Addressables 序列化兼容策略", "analysis", "analyze", 50, 100, False),
    ("删除全部旧存档", "code", "delete", 25, 100, False),
    ("帮我 rename Prefab serialization field，然后补 test", "code", "rename", 25, 100, False),
)


class RoutingHoldoutTests(unittest.TestCase):
    def test_holdout_cases_remain_outside_the_frozen_benchmark_corpus(self):
        corpus = json.loads((SKILL_ROOT / "assets" / "routing-benchmark-cases.json").read_text(encoding="utf-8"))
        corpus_prompts = {case["prompt"] for case in corpus["cases"]}
        self.assertTrue(all(prompt not in corpus_prompts for prompt, *_ in HOLDOUT_CASES))

    def test_holdout_classification_contract(self):
        for prompt, task_type, operation, minimum, maximum, fast_path in HOLDOUT_CASES:
            with self.subTest(prompt=prompt):
                observed = POLICY.analyze_prompt_routing(prompt)
                self.assertEqual(observed["task_type"], task_type)
                self.assertEqual(observed["operation"], operation)
                self.assertGreaterEqual(observed["complexity_score"], minimum)
                self.assertLessEqual(observed["complexity_score"], maximum)
                self.assertEqual(observed["fast_path_eligible"], fast_path)


if __name__ == "__main__":
    unittest.main()

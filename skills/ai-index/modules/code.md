# Code

Start at [SKILL.md](../../../code-skill/SKILL.md) and the selected philosophy, state, or platform reference. [code_rule_guard.py](../../../code-skill/scripts/code_rule_guard.py) checks Python source for high-confidence findings. [hidden_process.py](../../../code-skill/scripts/hidden_process.py) owns quiet subprocess options and [skill_platform_check.py](../../../code-skill/scripts/skill_platform_check.py) checks compatibility against the maintained [baseline](../../../code-skill/assets/skill-platform-baseline.json).

For every local edit, including tests and scripts, use Management’s [code navigation](../../../management-skill/references/project-ai-index.md#code-navigation) and [method-boundary philosophy](../../../code-skill/references/code-writing-philosophy.md#choose-method-boundaries-deliberately): keep a cohesive operation together, parameterize shared flows, extract only a justified independent contract, and propose unrelated structural refactors before performing them.

Code owns general writing, structure, lifecycle and side-effect contracts and the Python profile. Prompt owns reusable prompt design. Select the matching language or product Skill for specialized requirements through the Code entry. Preserve supported platform behavior and quiet execution. Use the real affected case for behavior evidence.

Tests live in `code-skill/tests/` and the [project registry](../../../.agents/skills/testing-skill/SKILL.md). Verify owns acceptance; Workflow owns disposable tool output and process cleanup.

[qin_rule_guard_common.py](../../../code-skill/scripts/qin_rule_guard_common.py) owns Git scopes and findings for source checkers. A forwarding or recursion finding spans the declaration and affected body so a change to the call is included. `test_code_work_explains_steps_and_uses_optional_scoped_memory` in [test_code_writing_philosophy.py](../../../code-skill/tests/test_code_writing_philosophy.py) protects startup routing and scoped memory.

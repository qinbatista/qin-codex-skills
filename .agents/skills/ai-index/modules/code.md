# Code

Start at [SKILL.md](../../../../code-skill/SKILL.md) and the selected philosophy/state/platform reference. [code_rule_guard.py](../../../../code-skill/scripts/code_rule_guard.py) checks high-confidence rule violations; [hidden_process.py](../../../../code-skill/scripts/hidden_process.py) owns quiet subprocess options; [skill_platform_check.py](../../../../code-skill/scripts/skill_platform_check.py) checks compatibility against the maintained [baseline](../../../../code-skill/assets/skill-platform-baseline.json).

For every local edit, including tests and scripts, use Management’s [code navigation](../../../../management-skill/references/project-ai-index.md#code-navigation) and [method-boundary philosophy](../../../../code-skill/references/code-writing-philosophy.md#choose-method-boundaries-deliberately): keep a cohesive operation together, parameterize shared flows, extract only a justified independent contract, and propose unrelated structural refactors before performing them.

Code owns writing, structure, lifecycle and side-effect contracts, including Python/Unity-specific references when relevant. Domain APIs remain with their product Skills. A mechanical lookup does not require reading every design reference. Preserve supported platform behavior and quiet execution; checks do not replace real affected-case evidence.

Tests live in `code-skill/tests/` and the [project registry](../../testing-skill/SKILL.md). Verify owns acceptance; Workflow owns disposable tool output and process cleanup.

# Prompt

Start at [SKILL.md](../../../../prompt-skill/SKILL.md). This owner defines reusable prompts and durable AI instructions: objective, input authority, missing-value behavior, constraints and output/acceptance contracts. It has no dedicated runtime script. Ordinary prose is outside its automatic scope.

Keep one authoritative rule per behavior, separate stable policy from per-run data, and preserve external/public names and quoted user content. Prompt logic belongs in the actual owning source; project-specific prompts stay in project Skills/code rather than this global owner.

The maintained contract test is [test_prompt_contract.py](../../../../prompt-skill/tests/test_prompt_contract.py), tracked by the [testing Skill](../../testing-skill/SKILL.md). Read Management only for Skill authoring/ownership changes; read Verify for meaningful affected-case acceptance.

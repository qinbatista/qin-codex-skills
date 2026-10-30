# Project Memory

Start at [SKILL.md](../../../../project-memory-skill/SKILL.md) and [memory/Ending rules](../rules/memory.md). Entry helpers are [obsidian_vault_setup.py](../../../../project-memory-skill/scripts/obsidian_vault_setup.py) for the real vault, [project_knowledge.py](../../../../project-memory-skill/scripts/project_knowledge.py) for filtered current knowledge, [ending_memory.py](../../../../project-memory-skill/scripts/ending_memory.py) for memory-only writes, [ending_memory_launch.py](../../../../project-memory-skill/scripts/ending_memory_launch.py) for handoff/readbacks, and [ending_conversation.py](../../../../project-memory-skill/scripts/ending_conversation.py) for native removal.

For this repository, recall uses `obsidian_vault_setup.py --existing-only`; missing memory is a nonblocking skip, never permission for external directory creation. The setup and CLI targets enforce the no-create path; its real CLI regression checks parent absence.

Keep durable memory solely in the verified vault and exact owner. A hash or source readback is not runtime proof. The parent ends after acknowledged Ending creation; Ending owns its recovery and removal and must never bring cleanup back to the parent. Guidance data is separate from memory payloads.

Recall follows project → task → underlying logic. `project_knowledge.py logic` traverses explicit `applies-logic` links to shared `logic.*` principles and bounded case pointers. It never imports foreign implementation facts; selected references retain exact owners, applicability, differences and dated proof. This uses the existing relation/index store, not keyword-based automatic generalization.

Tests stay in `project-memory-skill/tests/`, tracked by the [testing Skill](../../testing-skill/SKILL.md). Workflow owns resource audit mechanics; Management owns residual project AI-index updates. Neither dependency authorizes product tests, builds or publication by Ending.

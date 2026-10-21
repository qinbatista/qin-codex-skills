# Workflow

Start at [SKILL.md](../../../../workflow-skill/SKILL.md) and select the relevant reference. Entry helpers are [task_artifact_paths.py](../../../../workflow-skill/scripts/task_artifact_paths.py) for external run allocation, [task_cache_cleanup.py](../../../../workflow-skill/scripts/task_cache_cleanup.py) for identity-bound checkpoints, [task_resource_ledger.py](../../../../workflow-skill/scripts/task_resource_ledger.py) for multi-consumer ownership, and [ending_resource_audit.py](../../../../workflow-skill/scripts/ending_resource_audit.py) for residual audits.

Workflow owns readiness, bounded waits, Git branch/delivery rules, browser surfaces and resource cleanup. Keep memory contents with Project Memory and verification acceptance with Verify. Review [execution rules](../rules/execution.md) for mandatory external/quiet/cleanup boundaries. Native ownership and fresh consumer checks govern deletion; an active chat alone does not retain completed scratch.

Tests remain in `workflow-skill/tests/`, registered by the [testing Skill](../../testing-skill/SKILL.md). Read Code's platform helper only for subprocess/portability changes; read Project Memory for Ending handoff/deletion, not ordinary scratch allocation.

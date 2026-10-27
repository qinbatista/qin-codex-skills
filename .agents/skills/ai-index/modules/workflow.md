# Workflow

Start at [SKILL.md](../../../../workflow-skill/SKILL.md) and select the relevant reference. Entry helpers are [task_artifact_paths.py](../../../../workflow-skill/scripts/task_artifact_paths.py) for external run allocation, [task_cache_cleanup.py](../../../../workflow-skill/scripts/task_cache_cleanup.py) for identity-bound checkpoints, [task_resource_ledger.py](../../../../workflow-skill/scripts/task_resource_ledger.py) for multi-consumer ownership, and [ending_resource_audit.py](../../../../workflow-skill/scripts/ending_resource_audit.py) for residual audits.

Workflow owns readiness, bounded waits, Git branch/delivery rules, browser surfaces and resource cleanup. Its [bounded text and log reading](../../../../workflow-skill/references/text-and-log-reading.md) starts machine diagnostics at the latest page, then follows keyword matches and necessary context; Code and Verify route to this owner. Keep memory contents with Project Memory and verification acceptance with Verify. Review [execution rules](../rules/execution.md) for mandatory external/quiet/cleanup boundaries. Native ownership and fresh consumer checks govern deletion; an active chat alone does not retain completed scratch.

The Cache helper owns reasoned retention with due owner review, identity-bound explicit release, and fresh native consumer inventories. Source snapshot producers apply Workflow's external artifact policy and their source allowlist; nested project Cache/build trees are not source inputs.

Tests remain in `workflow-skill/tests/`, registered by the [testing Skill](../../testing-skill/SKILL.md). Read Code's platform helper only for subprocess/portability changes; read Project Memory for Ending handoff/deletion, not ordinary scratch allocation.

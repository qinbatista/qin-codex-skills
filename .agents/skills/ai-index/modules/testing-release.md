# Project testing and release

Start at the [project testing Skill](../../testing-skill/SKILL.md), [test registry](../../testing-skill/references/test-registry.json) and [audit_registry.py](../../testing-skill/scripts/audit_registry.py). They own stable test purpose, goal, level, relative path, runner and Skill ownership; results remain in the current project Cache run.

Each global Skill's clean-clone tests stay in that Skill's `tests/`. Project-only tests stay under the project testing Skill. Consolidate by purpose before adding cases; retain distinct compatibility and release coverage. Apply [verification rules](../rules/verification.md).

Release acceptance is executed by Management's [global_skill_regression_gate.py](../../../../management-skill/scripts/global_skill_regression_gate.py) against its [capability catalog](../../../../management-skill/assets/global-skill-capability-catalog.json). The [release contract](../../../../management-skill/references/global-skill-release-gate.md) distinguishes candidate verification from consumer installation. The publisher validates its selected source and isolated installation before source/index/commit/remote mutation; do not invent attestations or replace real behavior with a mock.

This project-only registry/index is source guidance, not an installable global Skill. Management owns authorized publication and exact candidate selection; Verify owns evidence interpretation.

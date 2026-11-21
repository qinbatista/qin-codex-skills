# Project testing and release

Start at the [project testing Skill](../../../.agents/skills/testing-skill/SKILL.md), [test registry](../../../.agents/skills/testing-skill/references/test-registry.json) and [audit_registry.py](../../../.agents/skills/testing-skill/scripts/audit_registry.py). They own stable test purpose, goal, level, relative path, runner and Skill ownership; results remain in the current project Cache run.

The project testing Skill owns the opt-in [Codex Python writing cases](../../../.agents/skills/testing-skill/references/codex-python-writing.md) and [replay command](../../../.agents/skills/testing-skill/scripts/replay_python_writing.py). Each case checks an independent answer against actual files or database state.

The [resource ledger tests](../../../workflow-skill/tests/test_task_resource_ledger.py) replace an ownership marker with a distinct file carrying the original bytes and timestamp.

Each global Skill's clean-clone tests stay in that Skill's `tests/`. Project-only tests stay under the project testing Skill. Consolidate by purpose before adding cases; retain distinct compatibility and release coverage. Apply [verification rules](../rules/verification.md).

The [GitHub Actions validation matrix](../../../.github/workflows/ci.yml) tests Python 3.10 and 3.11 on `ubuntu-latest`. Python 3.10 covers the existing syntax floor for the host scripts, including structural pattern matching in platform dispatch. `candidate_layouts` includes the workflow in the isolated source layout so the project AI index can validate its ownership and links.

Release acceptance is executed by Management's [global_skill_regression_gate.py](../../../management-skill/scripts/global_skill_regression_gate.py) against its [capability catalog](../../../management-skill/assets/global-skill-capability-catalog.json). The [release contract](../../../management-skill/references/global-skill-release-gate.md) distinguishes candidate verification from consumer installation. The publisher validates its selected source and isolated installation before source/index/commit/remote mutation; do not invent attestations or replace real behavior with a mock.

This project-only registry/index is source guidance, not an installable global Skill. Management owns authorized publication and exact candidate selection; Verify owns evidence interpretation.

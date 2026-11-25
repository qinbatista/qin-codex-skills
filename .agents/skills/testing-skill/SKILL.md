---
name: testing-skill
description: Maintain this project's test purposes and scripts; use before adding Python tests or planning extended project verification.
---

# Project testing

Read [the test registry](references/test-registry.json) before adding a maintained Python test or running an extended test campaign. Find an existing script with the same goal first. Update or combine useful cases, remove obsolete exact duplicates after updating their runners and references, and add a script only for an uncovered behavior or compatibility boundary. The registry records each script's purpose, goal, level, repository-relative path, runner, and owning Skill. Update it whenever a script moves, changes purpose, or is retired.

For a requested Level 2 check of Codex-written Python, run the [writing cases](references/codex-python-writing.md). Each independent answer faces real CSV, pagination or SQLite failure cases.

Replay the [Git closeout case](references/git-closeout.md) to check account scope, worktree base, branch deletion and same-named tag retention with local remotes.

Use Verify's [ordinary-task cleanup examples](../../../verify-skill/references/task-cleanup-examples.md) for an end-to-end trial with a fresh worker and a separate observer.

To test [per-step browser cleanup](../../../workflow-skill/references/task-resource-lifecycle.md#clean-up-each-step), list the initial built-in browser tab IDs. Open a hidden control tab, then open two hidden research tabs with identical URLs. Close the research tabs by their returned handles and verify both IDs are absent while the control and pre-existing tabs remain. Close the control and verify all three test IDs are absent. Release test handles on failure too. Record a provider limitation if the built-in browser or its close/readback operation is unavailable.

For compute cleanup, run a bounded workload in an isolated worker, touch its memory allocation, then wait for verified exit and check its process identity. For a GPU check, submit a small device operation, verify its output and completion, release the buffer and compare the runtime's allocation counter with its baseline. Record the hardware, runtime and measured scope. Close all probe handles and remove its registered scratch.

Choose the smallest level that proves the task's claim:

| Level | Evidence |
| --- | --- |
| 1 | Focused function and syntax/code-error checks; insufficient alone for consequential runtime behavior. |
| 2 | Real execution of the affected case; the usual choice. |
| 3 | Real checks across related code when a structural change can affect multiple paths. |
| 4 | Full environment or release validation when explicitly requested or required by the release contract. |

Prefer new maintained project-only tests in this Skill's non-runtime `tests/`. This repository's eight managed global Skills must carry their own `tests/` into the clean-clone release gate, so leave those files in their native Skill folders and register them here. For other toolchains, keep tests where the actual runner requires them and record their repository-relative paths here; never duplicate a test just to place a copy in this Skill. Temporary fixtures, logs, results, bytecode and runner caches follow the [project Cache artifact policy](../../../workflow-skill/references/project-cache-artifact-policy.md) from their first write. Bind the child temporary environment and cache/output options before running; project-local ignored caches belong inside the exact task run.

Run [the registry auditor](scripts/audit_registry.py) after changing test files or entries. It checks the registry against all managed Skill test files and this Skill's own tests, including missing files and duplicate purposes. A nonzero exit means the inventory needs repair. Use the host's Python 3 interpreter:

```text
macOS/Linux: python3 .agents/skills/testing-skill/scripts/audit_registry.py --project-root .
Windows PowerShell: py -3 .agents\skills\testing-skill\scripts\audit_registry.py --project-root .
```

Registry runner `unittest` means `python -m unittest discover -s <path parent> -p <path name>` with the host's Python 3 interpreter. Run only the affected script or smallest real case for routine level 2 verification; run the broader release gate when level 4 is required for publication. Report the actual runtime and any untested platform or provider boundary.

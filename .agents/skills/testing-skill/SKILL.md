---
name: testing-skill
description: Maintain this project's test purposes and scripts; use before adding Python tests or planning extended project verification.
---

# Project testing

Read [the test registry](references/test-registry.json) before adding a maintained Python test or running an extended test campaign. Find an existing script with the same goal first. Update or combine useful cases, remove obsolete exact duplicates after updating their runners and references, and add a script only for an uncovered behavior or compatibility boundary. The registry records each script's purpose, goal, level, repository-relative path, runner, and owning Skill. Update it whenever a script moves, changes purpose, or is retired.

Choose the smallest level that proves the task's claim:

| Level | Evidence |
| --- | --- |
| 1 | Focused function and syntax/code-error checks; insufficient alone for consequential runtime behavior. |
| 2 | Real execution of the affected case; the usual choice. |
| 3 | Real checks across related code when a structural change can affect multiple paths. |
| 4 | Full environment or release validation when explicitly requested or required by the release contract. |

Prefer new maintained project-only tests in this Skill's non-runtime `tests/`. This repository's eight managed global Skills must carry their own `tests/` into the clean-clone release gate, so leave those files in their native Skill folders and register them here. For other toolchains, keep tests where the actual runner requires them and record their repository-relative paths here; never duplicate a test just to place a copy in this Skill. Temporary fixtures, logs, results, bytecode and runner caches follow the [external artifact policy](../../../workflow-skill/references/project-cache-artifact-policy.md) from their first write. Bind the child temporary environment and cache/output options before running; project-local ignored caches are still misplaced task support.

Run [the registry auditor](scripts/audit_registry.py) after changing test files or entries. It checks the registry against all managed Skill test files and this Skill's own tests, including missing files and duplicate purposes. A nonzero exit means the inventory needs repair. Use the host's Python 3 interpreter:

```text
macOS/Linux: python3 .agents/skills/testing-skill/scripts/audit_registry.py --project-root .
Windows PowerShell: py -3 .agents\skills\testing-skill\scripts\audit_registry.py --project-root .
```

Registry runner `unittest` means `python -m unittest discover -s <path parent> -p <path name>` with the host's Python 3 interpreter. Run only the affected script or smallest real case for routine level 2 verification; run the broader release gate when level 4 is required for publication. Report the actual runtime and any untested platform or provider boundary.

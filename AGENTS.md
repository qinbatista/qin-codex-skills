# qin-codex-skills

## Scope and ownership

- This repository is the source for public Codex global Skills and lifecycle contracts.
- Each top-level Skill owns its `SKILL.md`, metadata, references, scripts, and focused tests.
- `management-skill` owns publication and runtime mirror deployment; do not treat a source edit as deployment.
- `task-analyze-skill` owns routing and receipts; `project-memory-skill` owns durable, sanitized project-change records.

## Stable entry points and constraints

- Route admitted work with `task-analyze-skill/scripts/obsidian_adaptive_model_runner.py`.
- Publish only through `management-skill/scripts/sync_global_skills.py` when authorized.
- Treat `management-skill/assets/global-skill-capability-catalog.json` as the retained global behavior authority; `management-skill/scripts/global_skill_regression_gate.py` must PASS before local deployment or GitHub publication.
- Every durable code change returns after one smallest local Quick Check and requires one detached global projectless Ending. Its `create_thread` target is exactly `{"type":"projectless"}` with no project/current-task attachment, and `list_threads` readback must show `projectId=null` or absent before acknowledgement; any project/current-task/same-task-subtask placement is BLOCKED. Only an eligible low-risk, single-result small non-code task may explicitly skip it. Spark-xhigh remains the sole Ending controller, while capability-routed Terra/Sol `ENDING_CHECK_WORKER` nodes may perform saved semantic runtime, code-quality, prompt, UI, or visual checks without owning lifecycle or repair.
- Before durable work, compare the active Skill/AGENTS process contract, current execution evidence, and effective scoped project-result memory. Ending may append a superseding memory correction or reconcile its projection only for a proven memory defect; Skill or execution defects return to the immutable origin task.
- Keep support artifacts under `Cache/`; never embed machine-specific paths, secrets, or task history in Skill source.
- Keep `AGENTS.md` structural: ownership, entry points, hard constraints, conventions, and definition of done only.
- Important Cache: `Cache/tests/unity-game-code-structure-design/` is the untracked portable structural-trial harness for the Unity game-code ownership reference; owner: `code-skill`; retain for focused local checks.
- Important Cache: `Cache/tests/global-skill-regression/` is the untracked current/cumulative release-gate report store; owner: `management-skill`; retain for non-regression audit history.

## Definition of done

- Preserve every retained capability, add focused regression coverage for durable behavior changes, and require the full source/deployed release gate before deployment or publication.

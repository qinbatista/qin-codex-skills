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
- Ending is a real-evidence lifecycle, not a default confirmation step. Start one detached global projectless Ending only when the released result exposes at least one observable `real_test`, `information_update`, or `memory_update` surface; code changes normally expose `real_test` through the one smallest local Quick Check. A result with no such surface records `intentionally_skipped_simple_task` with `ending_skip_reason=no_real_test_or_information_or_memory_update`, regardless of score, band, risk, or stage count. When required, launch only from the final aggregate producer receipt after every result node/subprocess has settled; a child receipt never starts an Ending. Its `create_thread` target is exactly `{"type":"projectless"}` with no project/current-task attachment, and `list_threads` readback must show `projectId=null` or absent before acknowledgement; any project/current-task/same-task-subtask placement is BLOCKED. The same End Task continues one saved bounded check or closeout action at a time. Spark-xhigh remains the sole Ending controller, while capability-routed Terra/Sol `ENDING_CHECK_WORKER` nodes may perform saved semantic runtime, code-quality, prompt, UI, or visual checks without owning lifecycle or repair.
- Host execution is non-interactive and terminal-local: use the current `exec_command`/Python execution surface and never open Terminal.app, Computer Use, or a second terminal just to click Allow. Nested `codex exec` commands must set `approval_policy="never"` explicitly while retaining their declared sandbox. If a host UI still asks for Allow, stop the retry/relaunch loop and report a host-permission BLOCKED state; do not click or emulate the approval.
- Before durable work, compare the active Skill/AGENTS process contract, current execution evidence, and effective scoped project-result memory. Ending may append a superseding memory correction or reconcile its projection only for a proven memory defect; Skill or execution defects return to the immutable origin task.
- Keep support artifacts under `Cache/`; never embed machine-specific paths, secrets, or task history in Skill source.
- Keep `AGENTS.md` structural: ownership, entry points, hard constraints, conventions, and definition of done only.
- Cache top-level directories use only `tmp-<name>`, `remote-<name>`, or `<YYYYMMDD>`; ordinary task artifacts default to `tmp-<name>` or `<YYYYMMDD>`. Use `remote-<name>` only when the user explicitly asks to retain/save the artifact or this project contract explicitly marks it as retained. `Cache/cache_path.json` is the reserved AI-only registry file. Tests/evidence use `Cache/remote-test/` only when explicitly retained by the user or project contract; ordinary test scratch uses `tmp-*` or `<YYYYMMDD>` and must not be scattered through the repository.
- Important Cache: `Cache/remote-test/unity-game-code-structure-design/` is the untracked portable structural-trial harness for the Unity game-code ownership reference; owner: `code-skill`; retain for focused local checks.
- Important Cache: `Cache/remote-test/global-skill-regression/` is the untracked current/cumulative release-gate report store; owner: `management-skill`; retain for non-regression audit history.

## Definition of done

- Preserve every retained capability, add focused regression coverage for durable behavior changes, and require the full source/deployed release gate before deployment or publication.

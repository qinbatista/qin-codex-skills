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
- Every new task closes in one projectless Ending using fixed Spark-xhigh, with score used only for check scope and a registry-floor fallback allowed only for explicit Spark availability/capability failure.
- Keep support artifacts under `Cache/`; never embed machine-specific paths, secrets, or task history in Skill source.
- Keep `AGENTS.md` structural: ownership, entry points, hard constraints, conventions, and definition of done only.
- Important Cache: `Cache/tests/unity-game-code-structure-design/` is the untracked portable structural-trial harness for the Unity game-code ownership reference; owner: `code-skill`; retain for focused local checks.
- Important Cache: `Cache/tests/global-skill-regression/` is the untracked current/cumulative release-gate report store; owner: `management-skill`; retain for non-regression audit history.

## Definition of done

- Preserve every retained capability, add focused regression coverage for durable behavior changes, and require the full source/deployed release gate before deployment or publication.

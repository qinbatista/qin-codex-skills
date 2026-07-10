---
name: management-skill
description: "Management executor selected by the locked task-analyze-skill plan. Use for local adaptive-routing performance records, Codex auth/profile inspection or confirmed switching, and privacy-safe global skill mirror status, pull, snapshot, sync, or push. Personal routing history stays under task-analyze-skill/local and is excluded from every mirror. The approved public mirror contains the six workflow skills; unrelated local skills are preserved."
---

# Management Skill

Use this executor after `task-analyze-skill` and `workflow-skill` route a management node. It owns local Codex profile operations and the approved global-skill GitHub mirror. It does not choose the workflow model or effort and never inherits the entry model silently.

## Internal Route Selection

Select only what the locked plan requires:

- **Routing performance route**: record or inspect sanitized receipt-backed model/effort accuracy, verification, token, and timing evidence through `../task-analyze-skill/scripts/model_routing_history.py`.
- **Profile route**: inspect saved profiles, refresh login state, import/backup a profile, show sanitized status, or switch the active profile after explicit confirmation.
- **Global skill mirror route**: inspect authoritative local skills, generate a privacy-safe snapshot, compare local/remote state, pull, or explicitly sync/push.
- Use multiple routes only when the locked plan requires them.

## Personal Routing Performance

Task Analyze owns selection and storage. Management records the original result-producer attempt after receipt-backed Mini and updates that same attempt after Real Verify; direct non-dispatch model routes invoke the same recorder, while tool-only routes never record adaptive producer samples.

- Store only the generated local `task-analyze-skill/local/adaptive-routing/model_experience.json` ledger; never mirror it.
- Record controlled task-profile enums, a generalized privacy-filtered task summary, requested/resolved/effective producer model and effort, Mini/Real status, explicit success/failed model ranges, failure class, prompt-free workload hash, tokens, and timing only.
- Never store raw prompts, raw results, paths, thread/session IDs, account data, receipt bodies, secrets, or private task content.
- Categories/model roles are cold-start hints only. Every non-tiny model route carries the exact full Luna-low→Sol-ultra ladder without Spark; an eligible tiny route carries exactly Spark-low plus that full normal fallback. Search only while calibration trial is open, moving effort before model, then reuse the frozen pair with `trial=false`. Ending Real updates the same producer receipt/run and returns `routing_learning`; verified quality failure or profile/policy drift reopens it, while operational failures stay neutral.
- Correctness/quality is the eligibility gate. Rank tokens, then process time, then weaker rung only across complete Real-passing pairs in the same exact `workload_prompt_sha256` cohort. Cross-workload or incomplete evidence falls back to the verified quality boundary and cannot support a savings claim. Deterministic controller recording does not require a decorative Luna model call.
- Static safety, authority, modality, project, code-style, and skill floors always win.
- Never push, sync, snapshot, hash, or overwrite `task-analyze-skill/local/`. Pull must preserve it byte-for-byte.

## Approved Six-Skill Mirror

The public mirror set and order are exactly:

1. `task-analyze-skill`
2. `workflow-skill`
3. `code-skill`
4. `verify-skill`
5. `optimization-skill`
6. `management-skill`

The local global skill directory may contain unrelated skills such as `chronicle`. Mirror selection, hashing, status, pull, and deletion logic must ignore and preserve those unrelated local folders. The remote mirror itself must contain exactly the approved six.

## Privacy And Authorization

- Never reveal or publish tokens, auth files, cookies, profile IDs, private keys, private logs, state databases, receipts with raw prompts, or temporary artifacts.
- Never switch active `auth.json` without explicit confirmation at action time.
- Never push/sync/publish unless the user explicitly requested publishing in the current task.
- Run public-safety checks before any authorized push.
- Preserve unrelated local skills and user files during pull/snapshot operations.

## README Generation

The durable English README source is `assets/readme/github-readme-template.md`. Its 12 local SVG assets (six desktop/mobile diagram pairs) explain the six-skill system, lifecycle, model router, model-experience learning, verification topology, runtime receipts, and private adaptive routing. The README must explain that the portable Task Analyze entry rule is hookless, the selected entrance pair runs Task Analyze only, and personal routing history is never mirrored. `scripts/sync_global_skills.py` reads that template when generating root `README.md`.

The public README must name the First Result Principle, the direct-action boundary, the weak-to-strong complete `model|effort` ladder, the receipt-backed adaptive goal, graduated routing scenarios, the code-domain extension recipe, reasonable response-time/token use, exactly six public skills, and the exclusion of local `model_experience.json`.

For README changes:

1. Edit the durable template and adjacent SVGs.
2. Generate a local repository snapshot only.
3. Verify internal links, SVG parsing/accessibility, desktop/narrow rendering, and six-skill selection.
4. Do not publish without a separate explicit request.

## Main Result And Ending Task

For management work, Mini Verify confirms sanitized scope/state before the first result. After the result, Ending Task may run deeper local/remote comparison, hash/no-diff proof, reports, logs, docs, or memory. A background mismatch/failure notifies and reopens the task.

## Commands

Use the maintained scripts instead of ad hoc profile or mirror logic:

- `scripts/manage_auth_profiles.py`
- `scripts/show_all_auth_status.py`
- `scripts/sync_global_skills.py`

Use snapshot/dry-run/status modes for testing. Do not call `sync` or `push` in a task that was authorized only to edit/test local skills.

## Generated File Placement

Put local snapshots, diffs, test repositories, logs, and status evidence in the active task `cache/` or `work/` area. Never place private auth/profile artifacts in a public snapshot or user-facing output.

# Optional Related Memory

## Purpose

Use a quick memory lookup to improve one task with related past requirements, verified failures, retry lessons, project facts, and model-switch experience. Memory is advisory context, never a reason to delay or replace source inspection.

## Task-Start Search

Run `scripts/obsidian_memory_bridge.py search --query <generalized task summary>` during bounded read-only Task Analyze preflight when a vault is available. The bridge searches `TaskModelExperience/` and structured skill/project/taste/knowledge folders before DailyLog and generic wiki pages, returns only a bounded digest, and never returns raw transcripts or secrets.

- Use only matches that materially affect the current task.
- Prefer exact project, skill, failure, requirement, and verification nouns.
- Pass the concise digest only to nodes that need it.
- Recheck live source when memory may be stale.
- If the bridge returns `unavailable` or `no_matches`, continue normally without warning, setup work, or a blocked route.

The private `local/adaptive-routing/model_experience.json` ledger remains the only machine authority for exact model/effort selection. Obsidian `TaskModelExperience/` is a sanitized human-readable reference for Task Analyze and other skills.

## Obsidian Vault Routing

Use `/Users/qin/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyAILLM` only when the task depends on connected-project history, a repeated failure, a durable user rule, visual/UI verification, project routing, global skills, or a past-work lesson.

- Read vault `AGENTS.md`, root `instruction.md`, `DailyLog/index.md`, today's log when present, `wiki/index.md`, and recent `wiki/log.md` only as needed.
- Before a structured folder, read its `instruction.md`. Main folders are `DailyLog/`, `Skills/`, `AestheticTaste/`, `Projects/`, and `KnowledgeAreas/`.
- Global-skill or workflow failures use `Skills/instruction.md`, `Skills/index.md`, `Skills/Failure Learning.md`, and `Skills/Update Protocol.md`.
- Before a project skill, read `Skills/Skill Ownership Map.md` and `Skills/ProjectSkills/index.md`; keep project skills within their owner unless the user asks to port them.
- Visual, UI, artwork, image, Unity preview, shader/VFX/animation, PDF/report-style, or visual-handoff work uses `AestheticTaste/instruction.md` and `AestheticTaste/index.md`.
- Project work uses `Projects/instruction.md` plus the matching project `instruction.md` and `index.md`. Known pages include MuseAI, ThisIsMyOregon, AIAnimation2D, AIShaderGraphic2D, AIVFX2D, Destiny, Mokozoo, TaggingAPILandingPage, AgentImageEditor, and UnityCodexTest.
- Confirm the live project root before edits; avoid stale backups and temporary worktrees unless selected by the user.
- Done means verified. UI, visual, Unity, shader, generation, browser, backup/recovery, automation, and deployment work needs concrete evidence such as command output, screenshot, generated path, preview, test, or diff.

For Mac Notes sync, read `KnowledgeAreas/Mac Notes Sync.md` and `raw/MacNotes/sync-state.md`. The default direction is Mac Notes to Obsidian and only the Apple Notes `ThisIsMyOregon` tree is retained under `Projects/ThisIsMyOregon/MacNotes/`; do not import general notes or create Apple Notes mirror folders unless asked.

## Ending Update

After the completed result is shown, Ending Task may update only memory related to the work. Write model-switch experience only after Real Verify has produced a durable `pass` or `fail` verdict. Use `scripts/obsidian_memory_bridge.py record-model` with controlled profile fields, producer pair, Real status, boundary state, switch reason, and comparable metrics when available. New records never accept or write a Mini status; legacy Mini fields remain searchable only as migration history.

For meaningful completed work, append a concise entry to today's DailyLog. Reusable lessons, corrections, failure/retry patterns, workarounds, verified results, project/global-skill conflicts, and durable preferences go to the matching structured folder; append `wiki/log.md` for major durable updates.

Never store raw prompts, results, absolute paths, thread/session IDs, receipt bodies, credentials, secrets, or unrelated task history. Missing Obsidian remains a successful no-op.

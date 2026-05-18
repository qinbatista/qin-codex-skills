# qin-codex-skills

Public mirror of Qin's user global Codex skills from `~/.codex/skills`.

This repository stores global skill source files only. Do not copy the repository `.git` directory into `~/.codex/skills`.

## Skills

### [`qin-codex-auth-swithc`](./qin-codex-auth-swithc/)

Inspect and switch saved Codex ChatGPT auth profiles under `~/.codex`. Use when the user wants to find `auth*.json` files, identify which account each file belongs to, review the latest locally observed Codex usage or rate-limit snapshot for each account, and switch the active profile by copying one saved auth file onto `auth.json` without deleting anything.

### [`qin-codex-skills-github-sync`](./qin-codex-skills-github-sync/)

Sync Qin's user global Codex skills with the GitHub repository qin-codex-skills. Use before reading, using, creating, editing, or updating global skills under ~/.codex/skills, and after any global-skill edit so the saved skill code is pushed to GitHub without placing .git metadata inside ~/.codex/skills.

### [`qin-done-means-tested`](./qin-done-means-tested/)

Mandatory final verification skill. Use for any coding, website, UI, script, automation, refactor, bug fix, content update, or file-edit task before claiming the work is done. Always run the most relevant test, preview, build, lint, screenshot, or validation step available, and clearly report what was tested or what could not be tested.

### [`qin-easy-code-spark`](./qin-easy-code-spark/)

Prefer GPT-5.3-Codex-Spark for obvious, bounded, low-risk coding work when Codex has a model-selection or allowed delegation surface available. Use when the expected implementation, review, cleanup, or verification path is clear from the request or nearby code, even if the task is more than a tiny edit; avoid using it for unclear debugging, architecture, multi-system changes, high-risk migrations, or tasks that require deeper reasoning.

### [`qin-image-editing-workflow`](./qin-image-editing-workflow/)

Global image workflow rule. Use whenever a task needs to edit, generate, composite, regenerate, replace content inside, or otherwise modify an image, and whenever a repo or user rule says image-related work must route through the image editor workflow.

### [`qin-karpathy-guidelines`](./qin-karpathy-guidelines/)

Behavioral coding guardrails to reduce wrong assumptions, overcomplication, and unrelated edits. Use for non-trivial coding, debugging, refactoring, implementation, and review work across languages before making changes so Codex surfaces assumptions, prefers the simplest viable solution, keeps edits surgical, and defines verifiable success criteria.

### [`qin-prompt-creating`](./qin-prompt-creating/)

Create and optimize purpose-specific Python f-string prompts for AI tasks using a consistent Purpose + Rules structure. Use automatically when the user needs a prompt created, rewritten, improved, standardized, shortened, or reviewed, even if they do not name this skill. Especially use for direct function prompts for extraction, coordinates, transformation, checking, fixing structured data, and human-reading content prompts for factories, doctors, customers, reviewers, or other audiences where purpose and return JSON format must be clear.

### [`qin-python-code-checker`](./qin-python-code-checker/)

Use for Python writing and formatting tasks across projects when Codex generates, writes, formats, rewrites, refactors, cleans up, optimizes, or otherwise edits Python modules, classes, functions, scripts, or tests. Enforce a minimal Python formatting and refactoring guide so output stays concise, production-ready, behavior-preserving by default, aligned with single-line signatures and calls, descriptive naming, top-level imports, limited try/except usage, trusted function contracts without repeated type or value checks, no unnecessary guards, preserved manual formatting, no auto-formatters unless explicitly requested, the exact required logging pattern, and code-only output when the user wants raw Python.

### [`qin-skill-optimization`](./qin-skill-optimization/)

Optimize an existing Codex skill or prompt-driven instruction layer from concrete failure evidence, pre-use review, or finalization checks. Use when a skill, retry/check prompt, agent instruction block, or other instruction-driven workflow mostly works but should be tightened without changing the underlying job. Scan peer skills first when relevant, merge duplicate requirements into one clear rule, prefer the smallest prompt-first fix when the issue lives in the instruction layer, and verify behavior after the change.

### [`qin-test-pdf-report`](./qin-test-pdf-report/)

Generate a visual PDF report for testing, QA, validation, verification, checks, regressions, audits, review evidence, and reviewable result reporting. Use when the user asks for testing, asks to see a PDF report, wants a visual report, wants a report artifact, wants QA or validation evidence, wants proof with screenshots or tables, or when a project requires result reporting in a clearer form than plain text. Prefer screenshots, images, tables, metrics, and concise status blocks over text-heavy summaries, and return the PDF path instead of a long text report.

### [`qin-ui-review`](./qin-ui-review/)

Cross-project UI review and optimization baseline for browser, app, Unity Editor, and tool surfaces. Use whenever Codex is asked to create, update, optimize, redesign, polish, review, QA, or fix UI/UX for pages, apps, Unity inspectors, custom editor tools, panels, cards, split layouts, dashboards, forms, buttons, typography, labels, visual hierarchy, responsive layout, or user-reported UI problems. Before UI changes, search the UI problem index for related prior issues and apply matching solutions; when a reusable UI correction or rule appears, update the global index in the same turn.

### [`qin-unity-csharp-minimal-style`](./qin-unity-csharp-minimal-style/)

Primary global Unity C# skill for this user's projects. Use for Unity C# tasks across projects whenever Codex creates, edits, refactors, formats, reviews, debugs, explains, or optimizes MonoBehaviours, ScriptableObjects, managers, gameplay systems, or other runtime C# code. This is the shared default Unity C# style unless a tighter repo or user instruction overrides it.

---
name: management-skill
description: Unified management skill for local Codex account/profile operations and global skill GitHub synchronization. Use when the user asks to manage Codex auth profiles, switch local accounts, inspect profile state, sync global skills, commit or push skill changes, compare local and remote skill state, or run management workflows that should route through codex-switch or github-sync without exposing private data.
---

# Management Skill

Use this as the single management entry point. It keeps management tasks aligned with the rest of the skill map and routes to the correct existing management support skill.

## Generated File Placement

Put intermediate files, temporary inputs, cache clones, generated scratch data, logs, previews, and non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Final deliverables go only to the user-requested path or the active workspace `outputs/` directory.

## What This Skill Contains

`management-skill` contains two management routes. Choose only the route required by the current request.

- **Codex profile route**: use `codex-switch` for local Codex auth profile inspection, saved profile listing, usage snapshot review, refresh/login backup, importing auth files, saving the current auth profile, or switching `auth.json` after explicit confirmation.
- **Skill GitHub route**: use `github-sync` for global skill preuse checks, status previews, public-safety scans, local/remote comparison, pulling remote skill changes, committing, pushing, and publishing public-safe skill updates to `qinbatista/qin-codex-skills`.

## Trigger

Use this skill for management work:

- local Codex account/profile management or switching
- Codex auth profile backup, import, refresh, or usage inspection
- global skill synchronization, publishing, commit, push, pull, or status checks
- comparing local `~/.codex/skills` against the GitHub mirror
- mixed management tasks that involve both local profiles and global skill publishing

Do not use this skill for ordinary coding, UI verification, testing, optimization, or pure prose unless the request also includes a management action.

## Workflow

1. Classify the request as `codex-switch`, `github-sync`, or mixed management.
2. Read and follow only the selected support skill:
   - `codex-switch/SKILL.md` for profile/auth tasks.
   - `github-sync/SKILL.md` for global skill GitHub mirror tasks.
3. For mixed management, run the profile route first only when account/profile state affects the sync operation; otherwise keep the routes separate.
4. Record concrete evidence: local command input, command/tool used, output state, remote hash or profile result, and privacy constraints.
5. For skill edits that should be pushed, let `github-sync` run before editing when state is unclear and after verification when the user asked to publish.
6. Route reports or proof through `test-skill` and `verify-skill` when the workflow changed files, pushed to GitHub, or the user asked for validation.

## Guardrails

- Do not run both management routes just because both exist.
- Do not print, expose, commit, or upload tokens, auth files, cookies, profile IDs, raw account logs, private keys, `.env` files, cache contents, or temporary generated artifacts.
- Do not switch the active `auth.json` profile without explicit user confirmation at action time.
- Do not push skill changes until public-safety checks pass.
- Do not put `.git` metadata inside `~/.codex/skills`.

## Examples

- "切换 Codex 账号" -> use `management-skill`, then `codex-switch`, confirm the target profile, switch only after confirmation, and verify without exposing tokens.
- "提交我的 skill 到 GitHub" -> use `management-skill`, then `github-sync`, run public-safety checks, push, and verify the remote commit.
- "看看本地 skill 和 GitHub 是否一致" -> use `management-skill`, then `github-sync status` or `sync` depending on whether updates are allowed.

---
name: management-skill
description: "Executor skill under workflow-skill for management. Use after workflow-skill routes a task into local Codex account/profile operations or global skill GitHub synchronization. Use when the user asks to manage Codex auth profiles, switch local accounts, inspect profile state, sync global skills, commit or push skill changes, compare local and remote skill state, or run management workflows without exposing private data. Its management routes are multi-select when a request genuinely needs both profile and GitHub sync work."
---

# Management Skill

Use this as the single management executor selected by `workflow-skill`. It contains the local Codex profile route and the global skill GitHub sync route inside this skill, so those routes are not separate top-level skills.

## Generated File Placement

Put intermediate files, temporary inputs, cache clones, generated scratch data, logs, previews, and non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Final deliverables go only to the user-requested path or the active workspace `outputs/` directory.

## Internal Route Selection

`management-skill` contains two internal management routes. Select every route required by the current request. Most requests need one route; mixed account-and-sync work may need both.

- **Codex profile route**: inspect local Codex auth profiles, list saved profiles, review usage snapshots, refresh/login backups, import auth files, save the current auth profile, or switch `auth.json` after explicit confirmation. Use `scripts/manage_auth_profiles.py` and `scripts/show_all_auth_status.py`.
- **Skill GitHub route**: run global skill preuse checks, status previews, public-safety scans, local/remote comparison, pulls, commits, pushes, and public-safe publishing to `qinbatista/qin-codex-skills`. Use `scripts/sync_global_skills.py`.

## Trigger

Use this skill for management work:

- local Codex account/profile management or switching
- Codex auth profile backup, import, refresh, or usage inspection
- global skill synchronization, publishing, commit, push, pull, or status checks
- comparing local `~/.codex/skills` against the GitHub mirror
- mixed management tasks that involve both local profiles and global skill publishing

Do not use this skill for ordinary coding, UI verification, testing, optimization, or pure prose unless the request also includes a management action.

## Workflow

1. Classify the request as profile management, GitHub skill sync, or mixed management.
2. Use every selected internal route and its script; do not run unrelated management routes.
3. For mixed management, run the profile route first only when account/profile state affects the sync operation; otherwise keep the routes separate.
4. Record concrete evidence: local command input, command/tool used, output state, remote hash or profile result, and privacy constraints.
5. For skill edits that should be pushed, run `scripts/sync_global_skills.py` before editing when state is unclear and after verification when the user asked to publish.
6. Route reports or proof through `verify-skill` when the workflow changed files, pushed to GitHub, or the user asked for validation.

## Guardrails

- Do not run both management routes just because both exist.
- Do not print, expose, commit, or upload tokens, auth files, cookies, profile IDs, raw account logs, private keys, `.env` files, cache contents, or temporary generated artifacts.
- Do not switch the active `auth.json` profile without explicit user confirmation at action time.
- Do not push skill changes until public-safety checks pass.
- Do not put `.git` metadata inside `~/.codex/skills`.

## Examples

- "切换 Codex 账号" -> use the profile route, confirm the target profile, switch only after confirmation, and verify without exposing tokens.
- "提交我的 skill 到 GitHub" -> use the GitHub sync route, run public-safety checks, push, and verify the remote commit.
- "看看本地 skill 和 GitHub 是否一致" -> run `scripts/sync_global_skills.py status` or `sync` depending on whether updates are allowed.

## Helper Commands

```bash
python3 scripts/manage_auth_profiles.py list
python3 scripts/manage_auth_profiles.py list --live
python3 scripts/show_all_auth_status.py
python3 scripts/manage_auth_profiles.py switch <profile> --dry-run
python3 scripts/sync_global_skills.py status
python3 scripts/sync_global_skills.py sync --message "Sync global Codex skills"
```

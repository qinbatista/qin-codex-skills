---
name: management-skill
description: "Management executor selected by workflow-skill. Use when routed work involves Codex auth/profile operations or global skill GitHub sync: inspect profiles, switch after confirmation, compare local/remote skill state, pull, commit, push, or verify mirror status without exposing private data."
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
5. For skill edits that should be pushed, run only required minimum precondition checks in the main lane before the irreversible push: the five-folder allow-list, public-safety/secret scan, and any state check needed to avoid publishing the wrong mirror. Do not run broad validators, post-push remote hash proof, reports, docs, wiki, or no-diff proof in the main lane when subagent tools are callable.
6. After the sync/push command succeeds, route status, remote hash/no-diff proof, broad validators, reports, docs, and Obsidian/wiki/log closeout through `workflow-skill`'s `Ending Workflow` subagent(s). Use `verify-skill` inside those ending workers when proof is needed.

## Guardrails

- Do not run both management routes just because both exist.
- Do not print, expose, commit, or upload tokens, auth files, cookies, profile IDs, raw account logs, private keys, `.env` files, cache contents, or temporary generated artifacts.
- Do not switch the active `auth.json` profile without explicit user confirmation at action time.
- Do not push skill changes until required minimum public-safety checks pass, but keep broader validation and post-push proof in `Ending Workflow` subagent(s) after the major push goal when subagent tools are callable.
- Before pushing or syncing the global skill mirror, the selected top-level skill folders must be exactly `workflow-skill`, `code-skill`, `verify-skill`, `optimization-skill`, and `management-skill`. If any other skill folder appears, stop, inspect where it came from, and reject the push.
- Do not put `.git` metadata inside `~/.codex/skills`.

## Examples

- "切换 Codex 账号" -> use the profile route, confirm the target profile, switch only after confirmation, and verify without exposing tokens.
- "提交我的 skill 到 GitHub" -> use the GitHub sync route, run only required minimum public-safety checks, push, then delegate remote commit/status proof and broader validation to Ending Workflow subagent(s).
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

## Verification

After profile management, report only the non-secret profile/status result. After global skill sync, delegate `scripts/sync_global_skills.py status`, remote hash checks, no-diff proof, and broad validators to Ending Workflow subagent(s) when callable. If no subagent tool is callable, run the minimum post-sync status check in the main lane and state that Ending Workflow was blocked.

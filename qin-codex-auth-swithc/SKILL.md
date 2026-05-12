---
name: qin-codex-auth-swithc
description: Inspect and switch saved Codex ChatGPT auth profiles under `~/.codex`. Use when the user wants to find `auth*.json` files, identify which account each file belongs to, review the latest locally observed Codex usage or rate-limit snapshot for each account, and switch the active profile by copying one saved auth file onto `auth.json` without deleting anything.
---

# Qin Codex Auth Swithc

## Trigger

Use this skill when the user wants to inspect, switch, refresh, re-login, back up, or restore Codex ChatGPT auth profiles under `~/.codex`, especially files like `auth.json` and `auth_qincodex.json`.

## Workflow

1. Run `python3 scripts/manage_auth_profiles.py list --live --json` when the user wants current accurate usage, or run `python3 scripts/manage_auth_profiles.py list --live` for a readable live summary. Use plain `list` only for local snapshot fallback when you explicitly want old local data.
2. If the user wants a single script they can run locally, use:
   - `python3 scripts/show_all_auth_status.py` to show real-time live status
   - `python3 scripts/show_all_auth_status.py auth_qin.json` to switch first, then show real-time live status
3. When the user wants to refresh `auth_qincodex.json`, "login again", or "get auth.json", use one normal browser login flow:
   - First confirm no stale login process or `localhost:1455` listener is still running. Stop the stale attempt before retrying.
   - Run `python3 scripts/manage_auth_profiles.py add-account qincodex --login --force`.
   - Let `codex login` open the browser. Do not manually open the OAuth URL unless the browser does not open or the user asks for the URL.
   - Do not switch to `codex login --device-auth` unless the user explicitly asks or normal browser login is impossible; device auth can be disabled in ChatGPT Security Settings and may fail.
   - Wait for both `Successfully logged in` and `Saved backup: /Users/qin/.codex/auth_qincodex.json`, then verify with `python3 scripts/manage_auth_profiles.py list` or `ls -l ~/.codex/auth.json ~/.codex/auth_qincodex.json`.
4. When the user wants to save a newly logged-in account for backup under another name, run `python3 scripts/manage_auth_profiles.py add-account <name> --login`.
5. When the user already has the desired `auth.json` and just wants to save it, run `python3 scripts/manage_auth_profiles.py add-account <name>`.
6. When the user has an auth file somewhere else and wants to import it, run `python3 scripts/manage_auth_profiles.py add-account <name> --source /path/to/auth.json`.
7. Show the user:
   - file name
   - whether the file is the active `auth.json`
   - account name and email
   - account ID
   - last refresh time
   - latest locally observed Codex usage snapshot
8. State clearly whether the usage data is:
   - live, from isolated Codex probes (`list --live`), or
   - local snapshot fallback, from recent Codex session logs (`list`)
9. Show percentages as remaining usage (`left`), not raw `used_percent`.
10. Ask the user which exact profile to activate.
11. Only after explicit confirmation, run `python3 scripts/manage_auth_profiles.py switch <selector>`.
12. Rerun `python3 scripts/manage_auth_profiles.py list --live` when the user wants a fresh confirmation after the copy.

## Guardrails

- Never delete, rename, or move auth files.
- Only copy the chosen source file to `~/.codex/auth.json`.
- Never expose tokens, refresh tokens, or raw JWT contents.
- Keep only one active login attempt at a time. If a retry is needed, stop the previous `codex login` process/listener before starting a new one.
- If multiple files map to the same account, say so instead of pretending they are different accounts.
- If a selector is ambiguous, ask the user to choose by file name.

## Verification

- For relogin/backup flows, confirm the terminal reported success and then run `python3 scripts/manage_auth_profiles.py list` or `ls -l ~/.codex/auth.json ~/.codex/auth_qincodex.json`.
- For switch-only flows, use `python3 scripts/manage_auth_profiles.py switch <selector> --dry-run` before copying when there is any ambiguity.

## Examples

- "Login auth_qincodex.json again" -> run `python3 scripts/manage_auth_profiles.py add-account qincodex --login --force`, wait for success, then verify the saved backup.
- "Switch to qincodex" -> dry-run `switch auth_qincodex.json` if needed, then switch only after confirmation.

## Helper

Use `scripts/manage_auth_profiles.py`.

Commands:

```bash
python3 scripts/manage_auth_profiles.py list
python3 scripts/manage_auth_profiles.py list --json
python3 scripts/manage_auth_profiles.py list --live
python3 scripts/manage_auth_profiles.py list --live --json
python3 scripts/show_all_auth_status.py
python3 scripts/show_all_auth_status.py auth_qin.json
python3 scripts/manage_auth_profiles.py add-account work
python3 scripts/manage_auth_profiles.py add-account team --login
python3 scripts/manage_auth_profiles.py add-account imported --source /tmp/auth.json
python3 scripts/manage_auth_profiles.py switch auth_ben.json
python3 scripts/manage_auth_profiles.py switch ben --dry-run
```

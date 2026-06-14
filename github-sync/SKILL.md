---
name: github-sync
description: Sync, commit, and push Qin's user global Codex skills with the GitHub repository qin-codex-skills. Use when Codex needs to read, use, create, edit, rename, delete, or update global skills under ~/.codex/skills; when global skill changes should be committed and pushed to GitHub; or when local and remote global-skill state must be compared without placing .git metadata inside ~/.codex/skills. Always keep the public mirror safe by excluding caches, generated artifacts, auth files, tokens, secrets, local logs, and other private personal data.
---

# GitHub Sync

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Do not scatter generated files across the working tree, desktop, home directory, or unrelated folders. Final deliverables should go only to the user-requested path or the active workspace `outputs/` directory.

## Internal Route Selection

This skill includes multiple sync routes. Do not run every command in the helper list. Choose the route required by the current state: `sync` for normal before/after global-skill work, `status` for a dry-run preview, `preuse` for read-only inspection, `pull` only when accepting remote changes, and `push` only when local changes should be published. Always keep the public-safety checks relevant to the route.

## Trigger

Use this skill for global Codex skill synchronization and GitHub publishing:

- before using or editing any user global skill under `~/.codex/skills`
- before creating, rewriting, or deleting a user global skill
- after any global skill has been updated, renamed, deleted, or created and should be committed and pushed to GitHub
- when automatically choosing whether the remote `qin-codex-skills` copy or local global skills are newer
- when the user asks to save, commit, push, publish, or sync global skill changes

This skill is for user global skills. Do not use it for repo-local `AGENTS.md`, plugin-cache skills, bundled `.system` skills, or project-local skills unless the user explicitly asks.

## Sources

- Local global skills: `~/.codex/skills`
- Default remote repository: `qinbatista/qin-codex-skills`
- Sync unit: direct child folders under `~/.codex/skills` that contain `SKILL.md`

Exclude `.system`, `.git`, `.github`, `.DS_Store`, `__pycache__`, compiled Python files, logs, credentials, auth files, tokens, secrets, private keys, generated cache artifacts, temporary work folders, and other personal/private data from the global-skill mirror.

## Public Safety

Before committing or pushing, inspect the exact diff and block anything that would expose private personal information:

- auth files such as `auth.json`, `auth*.json`, cookies, sessions, tokens, credentials, private keys, `.env`, database files, local cache, generated reports, logs, screenshots, and temporary work folders
- API keys or token-looking values such as OpenAI `sk-...`, GitHub `ghp_...` or `github_pat_...`, Slack `xox...`, AWS `AKIA...`, private-key blocks, or JSON fields containing real token/password/secret values
- local-only folders such as `cache/`, `outputs/`, `work/`, `.venv/`, `node_modules/`, build output, and test caches

If any private item is detected, stop the push and report the blocked path or pattern. Do not redact and push a guessed version unless the user explicitly asks for a public-safe rewrite.

## Workflow

1. Before using, editing, or after editing a global skill, run automatic sync:

   ```bash
   cd /Users/qin/.codex/skills/github-sync
   python3 scripts/sync_global_skills.py sync --message "Sync global Codex skills"
   ```

2. Let `sync` choose the direction:
   - If local and remote are equal, it records the clean sync state and does nothing.
   - If only local changed since the last sync, it pushes to GitHub.
   - If only remote changed since the last sync, it pulls into `~/.codex/skills`.
   - If both sides changed, it compares local skill file mtimes with the latest remote commit time; the newer side wins.

3. Use manual precheck only when you want to inspect differences without changing anything:

   ```bash
   cd /Users/qin/.codex/skills/github-sync
   python3 scripts/sync_global_skills.py preuse
   ```

4. Use manual status when you want to preview a local-to-remote push:

   ```bash
   cd /Users/qin/.codex/skills/github-sync
   python3 scripts/sync_global_skills.py status
   ```

5. Make the requested global skill edit in `~/.codex/skills`.

6. Run the normal skill validation for the edited skill. For public mirror changes, verify the changed skill folders parse correctly and the push diff contains only intended public-safe skill files.

7. Run `sync` or `push` again after the edit so the local update is committed and pushed if it is the newest side.

## Verification

- After changing this skill, run `python3 scripts/sync_global_skills.py --help`.
- Before relying on the remote copy, run `python3 scripts/sync_global_skills.py sync`.
- Before a manual push, run `python3 scripts/sync_global_skills.py status` to preview local-to-remote changes when the scope is unclear.
- Before committing or pushing, run a privacy search over the mirror diff and confirm no auth, secret, token, cache, log, or generated artifact is staged.
- After pushing, verify the repository with `git ls-remote origin refs/heads/<branch>` or `gh repo view qin-codex-skills --json url,visibility,defaultBranchRef` when `gh` is available.

## Guardrails

- Never turn `~/.codex/skills` into a git checkout.
- Never copy a `.git` directory into `~/.codex/skills`.
- Clone or download the GitHub repository only inside a temporary sandbox, then copy skill folders into the global skills folder.
- Store sync state under `~/.codex/state`, not inside a skill folder or repository checkout.
- Prefer `gh` for repository metadata when available, but fall back to the SSH URL `git@github.com:<owner>/<repo>.git` when `gh` is unavailable.
- If the remote repository does not exist and the user has asked to publish these skills, create `qin-codex-skills` as a public GitHub repository before pushing.
- Keep the remote mirror public-safe: do not push auth files, secrets, local logs, cache folders, generated reports, screenshots, local work directories, or binary generated artifacts unless the user explicitly asks and the files are safe.

## Helper

Use `scripts/sync_global_skills.py`.

Useful commands:

```bash
python3 scripts/sync_global_skills.py sync --message "Sync global Codex skills"
python3 scripts/sync_global_skills.py preuse
python3 scripts/sync_global_skills.py pull
python3 scripts/sync_global_skills.py status
python3 scripts/sync_global_skills.py push --message "Update global Codex skills"
```

## Examples

- "Update my Python skill and save it to GitHub" -> run `sync`, edit the skill, verify it, then run `sync` again.
- "Before using the UI review skill, check if my global skills are current" -> run `sync`; it pulls remote changes or records that local is current.

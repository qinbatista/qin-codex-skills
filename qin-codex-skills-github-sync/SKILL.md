---
name: qin-codex-skills-github-sync
description: Sync Qin's user global Codex skills with the GitHub repository qin-codex-skills. Use before reading, using, creating, editing, or updating global skills under ~/.codex/skills, and after any global-skill edit so the saved skill code is pushed to GitHub without placing .git metadata inside ~/.codex/skills.
---

# Qin Codex Skills GitHub Sync

## Trigger

Use this skill for global Codex skill synchronization:

- before using or editing any user global skill under `~/.codex/skills`
- before creating, rewriting, or deleting a user global skill
- after any global skill has been updated and should be saved to GitHub
- when automatically choosing whether the remote `qin-codex-skills` copy or local global skills are newer

This skill is for user global skills. Do not use it for repo-local `AGENTS.md`, plugin-cache skills, bundled `.system` skills, or project-local skills unless the user explicitly asks.

## Sources

- Local global skills: `~/.codex/skills`
- Default remote repository: `qinbatista/qin-codex-skills`
- Sync unit: direct child folders under `~/.codex/skills` that contain `SKILL.md`

Exclude `.system`, `.git`, `.github`, `.DS_Store`, `__pycache__`, compiled Python files, logs, credentials, and generated cache artifacts from the global-skill mirror.

## Workflow

1. Before using, editing, or after editing a global skill, run automatic sync:

   ```bash
   cd /Users/qin/.codex/skills/qin-codex-skills-github-sync
   python3 scripts/sync_global_skills.py sync --message "Sync global Codex skills"
   ```

2. Let `sync` choose the direction:
   - If local and remote are equal, it records the clean sync state and does nothing.
   - If only local changed since the last sync, it pushes to GitHub.
   - If only remote changed since the last sync, it pulls into `~/.codex/skills`.
   - If both sides changed, it compares local skill file mtimes with the latest remote commit time; the newer side wins.

3. Use manual precheck only when you want to inspect differences without changing anything:

   ```bash
   cd /Users/qin/.codex/skills/qin-codex-skills-github-sync
   python3 scripts/sync_global_skills.py preuse
   ```

4. Use manual status when you want to preview a local-to-remote push:

   ```bash
   cd /Users/qin/.codex/skills/qin-codex-skills-github-sync
   python3 scripts/sync_global_skills.py status
   ```

5. Make the requested global skill edit in `~/.codex/skills`.

6. Run the normal skill validation for the edited skill, including `qin-skill-optimization` verification when a skill folder was created or updated.

7. Run `sync` again after the edit so the local update is pushed if it is the newest side.

## Verification

- After changing this skill, run `python3 scripts/sync_global_skills.py --help`.
- Before relying on the remote copy, run `python3 scripts/sync_global_skills.py sync`.
- Before a manual push, run `python3 scripts/sync_global_skills.py status` to preview local-to-remote changes when the scope is unclear.
- After pushing, verify the repository with `gh repo view qin-codex-skills --json url,visibility,defaultBranchRef`.

## Guardrails

- Never turn `~/.codex/skills` into a git checkout.
- Never copy a `.git` directory into `~/.codex/skills`.
- Clone or download the GitHub repository only inside a temporary sandbox, then copy skill folders into the global skills folder.
- Store sync state under `~/.codex/state`, not inside a skill folder or repository checkout.
- Never create backup directories or copied snapshots for global-skill sync work. Use GitHub as the recovery source or report the blocker; do not leave backups in `~/.codex/state`, the workspace, or `~/.codex/skills`.
- If `gh auth status` fails or the repository is unavailable, report the blocker instead of guessing.
- If the remote repository does not exist and the user has asked to publish these skills, create `qin-codex-skills` as a public GitHub repository before pushing.
- Keep the remote mirror public-safe: do not push auth files, secrets, local logs, cache folders, or binary generated artifacts unless the user explicitly asks and the files are safe.

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

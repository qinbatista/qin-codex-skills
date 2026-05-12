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
- when checking whether the remote `qin-codex-skills` copy is newer than the local global skills

This skill is for user global skills. Do not use it for repo-local `AGENTS.md`, plugin-cache skills, bundled `.system` skills, or project-local skills unless the user explicitly asks.

## Sources

- Local global skills: `~/.codex/skills`
- Default remote repository: `qinbatista/qin-codex-skills`
- Sync unit: direct child folders under `~/.codex/skills` that contain `SKILL.md`

Exclude `.system`, `.git`, `.github`, `.DS_Store`, `__pycache__`, compiled Python files, logs, credentials, and generated cache artifacts from the global-skill mirror.

## Workflow

1. Before using or editing a global skill, check the remote copy:

   ```bash
   cd /Users/qin/.codex/skills/qin-codex-skills-github-sync
   python3 scripts/sync_global_skills.py preuse
   ```

2. If the remote has changes and you have not made local skill edits that would be overwritten, download into a temporary sandbox and copy the remote skill folders into `~/.codex/skills`:

   ```bash
   cd /Users/qin/.codex/skills/qin-codex-skills-github-sync
   python3 scripts/sync_global_skills.py pull
   ```

3. If local skill edits already exist and `preuse` reports remote differences, check local-to-remote status before overwriting:

   ```bash
   cd /Users/qin/.codex/skills/qin-codex-skills-github-sync
   python3 scripts/sync_global_skills.py status
   ```

   If both sides changed the same skill, stop and ask the user before copying remote files over local files.

4. Make the requested global skill edit in `~/.codex/skills`.

5. Run the normal skill validation for the edited skill, including `qin-skill-optimization` verification when a skill folder was created or updated.

6. Push the global-skill mirror after the edit:

   ```bash
   cd /Users/qin/.codex/skills/qin-codex-skills-github-sync
   python3 scripts/sync_global_skills.py push --message "Update global Codex skills"
   ```

## Verification

- After changing this skill, run `python3 scripts/sync_global_skills.py --help`.
- Before relying on the remote copy, run `python3 scripts/sync_global_skills.py preuse`.
- Before pushing, run `python3 scripts/sync_global_skills.py status` to preview local-to-remote changes when the scope is unclear.
- After pushing, verify the repository with `gh repo view qin-codex-skills --json url,visibility,defaultBranchRef`.

## Guardrails

- Never turn `~/.codex/skills` into a git checkout.
- Never copy a `.git` directory into `~/.codex/skills`.
- Clone or download the GitHub repository only inside a temporary sandbox, then copy skill folders into the global skills folder.
- If `gh auth status` fails or the repository is unavailable, report the blocker instead of guessing.
- If the remote repository does not exist and the user has asked to publish these skills, create `qin-codex-skills` as a public GitHub repository before pushing.
- Keep the remote mirror public-safe: do not push auth files, secrets, local logs, cache folders, or binary generated artifacts unless the user explicitly asks and the files are safe.

## Helper

Use `scripts/sync_global_skills.py`.

Useful commands:

```bash
python3 scripts/sync_global_skills.py preuse
python3 scripts/sync_global_skills.py pull
python3 scripts/sync_global_skills.py status
python3 scripts/sync_global_skills.py push --message "Update global Codex skills"
```

## Examples

- "Update my Python skill and save it to GitHub" -> run `preuse`, edit the skill, verify it, then run `push`.
- "Before using the UI review skill, check if my global skills are current" -> run `preuse`, then `pull` if remote changes are reported.

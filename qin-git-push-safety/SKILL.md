---
name: qin-git-push-safety
description: "Use before any Git push, release publish, PR branch publish, or user request to push changes. Enforce Qin's push workflow by checking status, fetching remote code, pulling before push, integrating remote changes without overwriting unrelated work, resolving merge conflicts deliberately, verifying the result, and only then pushing."
---

# Qin Git Push Safety

Use this skill whenever a task may run `git push`.

## Trigger

- The user asks to push, publish, upload a branch, or open a PR after local commits.
- A task reaches the final step where local commits should be sent to a remote.
- A previous push failed because the remote has new commits or conflicts.

## Workflow

1. Check the current branch, upstream, and dirty work with `git status --short --branch`.
2. Preserve unrelated dirty files. Stage only the files that belong to the current task.
3. Fetch remote state before pushing: `git fetch <remote>`.
4. Compare local and upstream history with `git rev-list --left-right --count HEAD...@{u}` when an upstream exists.
5. Pull before pushing. Prefer the repo's configured workflow; if no tighter repo rule exists, use `git pull --ff-only <remote> <branch>` when it can succeed cleanly.
6. If local and remote both have new commits, inspect the divergence before integrating:
   - `git log --oneline --left-right --graph HEAD...@{u}`
   - `git diff --stat HEAD..@{u}`
7. Integrate remote changes with the repo's expected method. Use merge when the user or repo specifically asks to merge; use rebase only when it is already the repo's normal workflow or the user requests it.
8. If conflicts appear, stop and find the conflict reason before editing:
   - List conflicts with `git diff --name-only --diff-filter=U`.
   - Inspect both sides with `git diff --ours -- <file>` and `git diff --theirs -- <file>`.
   - Resolve by preserving the intended behavior from both sides whenever possible.
   - Do not blindly take `ours` or `theirs` unless the conflict reason proves one side is obsolete.
9. After merge or rebase resolution, run the relevant tests, build, lint, screenshot, or smoke check for the changed surface.
10. Push only after the pull/integration step succeeds and conflicts are resolved.

## Reporting

- State whether a pull/fetch happened before push.
- If there was a conflict, name the conflicted files, the root reason, how it was merged, and what verification passed.
- If there was no conflict, say so directly.
- State the pushed branch and commit hash.

## Guardrails

- Never overwrite unrelated user work to make a push succeed.
- Never use destructive commands such as `git reset --hard` or `git checkout -- <file>` unless the user explicitly asks for that operation.
- Do not push when merge conflicts remain, when the branch integration failed, or when required verification is blocked without reporting the blocker.

## Examples

- "Push this fix" -> check status, fetch, pull, verify, then push.
- "Remote changed, merge it and push" -> inspect divergence, merge remote work, resolve conflicts by reason, verify, then push.
- "Conflict happened" -> list conflicted files, compare both sides, resolve deliberately, continue the merge or rebase, verify, then push.

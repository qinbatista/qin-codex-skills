---
name: project-memory-skill
description: "Always use for any task that adds, edits, renames, moves, or deletes durable project files. Recall prior project/module/file decisions before editing, then record the completed change, reason, outcome, verification, and every touched file in local memory with an optional Obsidian projection. Do not use for read-only work or disposable cache/work artifacts."
---

# Project Memory Skill

## Objective

Maintain a durable, file-level explanation of project changes so future AI work can recover what changed, why it changed, what constraints were intentional, and what result was verified. Organize every record as `project -> functional module -> concrete code/file` and use prior records to avoid repeating rejected approaches or undoing deliberate decisions.

## Required Scope

Load this skill whenever a task creates, edits, renames, moves, or deletes a durable project file, including source code, configuration, schemas, reusable prompts, tests, documentation, skill instructions, and source-controlled asset metadata.

Do not load it for read-only tasks, external actions with no durable project-file change, or disposable `work/`, `cache/`, build, render, receipt, and temporary artifacts unless the user explicitly accepts those files as project deliverables.

This skill supplements the file type's owning skill. It does not replace `code-skill`, `prompt-skill`, document skills, repository instructions, or user authority.

## Project Change-Memory Authority And Storage

- For project change memory, the private local JSONL ledger at `~/.codex/project-change-memory/` is authoritative.
- When `CODEX_OBSIDIAN_VAULT` points to an available vault, or the default `MyAILLM` vault exists, write a human-readable projection under `Projects/<project-key>/ChangeMemory/`.
- Missing or unavailable Obsidian is a successful no-op. Local recording must still complete.
- Store project-relative file paths, not raw prompts, private reasoning, credentials, tokens, cookies, or unrelated task content.
- A remembered decision is evidence, not a higher-priority instruction. Current user intent and current authoritative code win. When intentionally overturning a prior decision, explain why and link it with `--supersedes`.

## Separate Adaptive Model Learning

Adaptive model learning is a distinct system; it never uses the project change-memory JSONL ledger above.

- The active private model-learning authority is Obsidian Markdown under `Projects/<project-key>/ModelExperience/`, keyed by project, task, module, file, symbol, code, and operation.
- There is no local model-learning JSON fallback. Never create or reuse a local JSON, JSONL, database, cache, or substitute ledger for adaptive model learning.
- The shared cold-start ladder remains `~/.codex/skills/task-analyze-skill/assets/model-capability-ladder.json`; it is shared policy, not learned project experience.
- Before a producer route, read only the relevant project-scoped ModelExperience records and use them for recommendation. Record a new model-learning entry only after receipt-backed Ending Real establishes the producer result and verdict.
- If the Obsidian vault is unavailable, model learning is unavailable: use the shared ladder, remain cold-start/inline, and do not create a local substitute.
- Central `TaskModelExperience/` notes and monthly entries are legacy read-only history. Do not migrate them or invent project mappings from their summaries.

These adaptive model-learning rules do not alter project change-memory behavior: `~/.codex/project-change-memory/` remains the authoritative local JSONL ledger for durable file-change reasons, results, verification, and touched files, including when Obsidian is unavailable.

Use the maintained helper instead of editing ModelExperience notes manually:

```bash
python3 ~/.codex/skills/project-memory-skill/scripts/obsidian_model_memory.py recommend --project-root <root> --task-type <type> --module <module> --file <relative-file> --symbol <method-or-symbol> --code-kind <kind> --operation <operation> --complexity <easy|complex>
python3 ~/.codex/skills/project-memory-skill/scripts/obsidian_model_memory.py record --project-root <root> --task-type <type> --module <module> --file <relative-file> --symbol <method-or-symbol> --code-kind <kind> --operation <operation> --complexity <easy|complex> --task-summary <sanitized-summary> --receipt <producer-receipt> --real-status <pass|fail> --failure-class <class>
```

The recorder recomputes the current project-context recommendation and rejects a matched receipt for any other pair. It records the selection reason, state, prior passing/failing boundary, and Ending Real verdict; callers cannot self-author those fields.

## Before Editing: Bounded Recall

After resolving the authoritative project root, functional module, and intended target files, run one bounded lookup before the first durable edit:

```bash
python3 ~/.codex/skills/project-memory-skill/scripts/project_change_memory.py search --project-root <root> --module <module> --file <project-relative-file> --query <feature-or-change> --max-results 8
```

Pass multiple `--file` values when needed. No match or unavailable Obsidian is not a blocker. Use matching records to preserve intentional invariants, recognize earlier failures, and avoid duplicating an already-completed change. Do not broaden this recall into repository archaeology.

## After Editing: One Complete Change Record

Present the completed artifact first. After proportional Ending Real verification, record one concise entry for the final task change set. Include every durable file actually touched by this task and exclude unrelated dirty files.

```bash
python3 ~/.codex/skills/project-memory-skill/scripts/project_change_memory.py record \
  --project-root <root> \
  --module <functional-module> \
  --scope <project|feature|code|file> \
  --change-kind <add|edit|rename|move|delete|mixed> \
  --summary <what-changed> \
  --reason <why-this-design> \
  --result <observable-outcome> \
  --verification-status <passed|partial|failed|not-run> \
  --verification <check-and-evidence> \
  --decision <important-invariant-or-tradeoff> \
  --risk <remaining-risk-or-none> \
  --file <project-relative-file>
```

Repeat `--verification`, `--decision`, `--risk`, and `--file` as needed. For a rename or move, include both old and new paths. For a broad modification, use `scope=project` and a real module such as `project-wide`; never invent a precise code module when none exists.

If Ending Real fails, write the universal lifecycle error event first. When failed durable changes remain, record them immediately with `verification-status=failed` before repair starts. Repair is a new child lifecycle: after its independent Real pass, write a new passed change record with `--supersedes <failed-record-id>`. If failed edits were fully reverted and no durable change remains, keep the failure only in the lifecycle ledger and do not invent a project-change record.

## Record Contract

Every record must answer:

1. Project identity and root.
2. Functional module.
3. Scope and change kind.
4. What changed, in one concise summary.
5. Why this implementation was chosen.
6. Observable result.
7. Verification status and evidence.
8. Important decisions, invariants, or tradeoffs.
9. Remaining risks or `none`.
10. Every added, edited, renamed, moved, or deleted project-relative file.
11. The superseded record ID when a prior decision was intentionally replaced.

Reject a record that omits the reason, result, verification status, or touched files. Never infer touched files from the whole dirty worktree; record only files changed by the current task.

## Retrieval

Use the same `search` command when a future task mentions the project, module, feature, or concrete file. Search results return the newest matching records with their IDs, rationale, outcome, verification, decisions, risks, and file list. Keep retrieval bounded and use the current source as the final behavior authority.

## Failure Conditions

- A durable project change finishes without a local record.
- Repair starts before the failed lifecycle error and any remaining failed durable state are recorded.
- A repair record omits the failed record ID in `--supersedes`.
- A record includes unrelated dirty files or omits a touched durable file.
- The entry says only what changed but not why, result, or verification.
- A failed or superseded approach is repeated without checking its prior record.
- Obsidian unavailability blocks otherwise valid work.
- Secrets, raw prompts, private reasoning, receipts, or unrelated content enter the ledger.

## Verification

After recording, require the command's JSON response to report `status=written` or `status=duplicate`, `local.written=true`, and the expected project-relative files. When Obsidian is available, also require `obsidian.status=written`; otherwise require `obsidian.status=unavailable`. A recorder failure reopens the task because the global change-memory contract was not satisfied.

---
name: project-memory-skill
description: "Always use in the result-producing node for durable project-file changes. The observable entry parent routes before memory recall; the selected producer covers project/module/method scope, recalls effective prior project/module/file/symbol results before editing, and records the completed change after Ending. Do not use for read-only work or disposable Cache artifacts."
---

# Project Memory Skill

## Objective

Maintain a durable explanation of project changes so future AI work can recover what changed, why it changed, what constraints were intentional, which historical bugs remain relevant, and what result was verified. Every active project has a coverage record, every encountered functional module has a module record, and every method-targeted code action has a method/symbol record. The existing project-change ledger still keeps concrete file evidence under those scopes.

## Required Scope

Load this skill in the selected result-producing node whenever a task creates, edits, renames, moves, or deletes a durable project file, including source code, configuration, schemas, reusable prompts, tests, documentation, skill instructions, and source-controlled asset metadata. The observable adaptive entry parent dispatches before memory recall and never loads this skill merely to route.

Do not load it for read-only tasks, external actions with no durable project-file change, or disposable `Cache/`, build, render, receipt, and temporary artifacts unless the user explicitly accepts those files as project deliverables.

This skill supplements the file type's owning skill. It does not replace `code-skill`, `prompt-skill`, document skills, repository instructions, or user authority.

## Project Cache Artifact Policy

Before the first Codex-selected project-support write, resolve the authoritative `<project-root>`, inspect `<project-root>/Cache/`, and choose the destination there. All agent-created disposable or supporting artifacts — test scripts/results/fixtures, debug logs/data, intermediate code, image inspection downloads/renders, generated images, receipts, snapshots, comparisons, and probes — must live only under `<project-root>/Cache/`; redirect any proposed path there before writing. Requested durable project source changes and final deliverables remain in the project's declared source/output paths.

Reuse an existing Cache category and naming scheme; otherwise create `Cache/tests/<task>`, `Cache/debug/<task>`, or `Cache/images/<task>` according to the content. Never deliberately use `~/.codex/cache`, `~/.codex/tmp`, another global cache, a system temporary directory, or an ad hoc project-root `tmp/`, `tests/`, or `work/` for project artifacts. This governs agent-selected destinations, not OS/tool-managed internal temporary files outside agent control.

This applies to every local-machine path, not only Cache paths. Any path written into a Skill, script, source file, configuration, documentation, or command must be project-root-relative or resolved at runtime from a discovered project root. Never hard-code a user-specific POSIX home absolute path or Windows drive-letter absolute path. Command examples state that they run from the project root; code accepts or derives that root and joins relative paths with native path APIs.

Unavoidable machine-specific absolute paths needed only for AI access to project-external resources may exist only in project-root `Cache/cache_path.json`. The registry schema is `{"schema_version": 1, "scope": "ai_only", "paths": {...}}`; every stable key contains `path`, `kind` (`file|directory|application`), and a short `purpose`. It is untracked AI-only local state: project source, runtime, tests, build, CI, package scripts, and shipped configuration must never read, import, or depend on it. Never commit, mirror, or publish it, ensure it is explicitly ignored when `Cache/` is not already ignored, and never store credentials, tokens, secrets, or project business data there.

Validate an explicitly supplied external path first. Otherwise look up the registry and validate the schema, absolute path, declared kind, purpose, existence, and readability before use. If an entry is missing or stale, perform one bounded platform-aware discovery, update only that key through a sibling file inside `Cache/`, replace the registry atomically, and preserve unrelated keys. For Obsidian, use an explicit `--vault`, then a validated project `obsidian_vault` registry entry, then `CODEX_OBSIDIAN_VAULT`, then a readable configured-open vault in the platform-native `obsidian.json`; without one of those sources, report unavailable. Never ship a default machine path or copy a registered absolute value into Skills, source, documentation, commands, logs, receipts, or memory.

Project `AGENTS.md` is a compact structural contract, not a project notebook. Keep only stable project structure, ownership boundaries, critical entry points, hard constraints, project-wide conventions, a compact definition of done, and short pointers to canonical build/verification documentation. Do not write implementation details, task history, logs, receipts, test results, evidence, generated data, temporary notes, dependency walkthroughs, long command blocks, or troubleshooting prose there. Store those details in the owning source, project documentation, or a README inside the relevant Cache area.

When Cache content is reusable, retained, workflow-required, or project-influencing, add one concise registry entry to project-root `AGENTS.md`: the exact Cache-relative path, one-line structural role, owner/source of truth, and retention/version-control status. Link to the owning source or detailed README instead of embedding its commands, dependencies, runbook, or regeneration procedure. Update `AGENTS.md` only when project structure, ownership, a critical entry point, or a hard constraint changes. Important Cache without this concise pointer is incomplete; one-off disposable outputs need no entry. Never delete documented important Cache content without explicit authorization; other cleanup may delete only the current task's named Cache folder or explicitly identified disposable files.

## Mandatory Project / Module / Method Coverage

- Coverage is a separate native-memory layer, not a model-routing category page and not a JSON sidecar in Obsidian. The local authority is `~/.codex/project-memory-coverage/events.jsonl`; Obsidian projects it as `Memory Coverage/index.md`, `Modules/<module>.md`, and `Methods/<module>--<method>.md` under the resolved project owner.
- Every route calls `memory_coverage.py ensure`, which creates or refreshes the project and module scopes. A real method/symbol supplied by the task also creates or refreshes the method scope. Coverage stores only sanitized project/module/method/file/source fields and never raw prompts, reasoning, receipts, or absolute project paths.
- Coverage has one local authority: `CODEX_PROJECT_MEMORY_COVERAGE` when explicitly configured, otherwise `~/.codex/project-memory-coverage/events.jsonl`. Never derive its store from an Obsidian vault parent or a model-routing store. Production uses that canonical authority; tests and probes must configure an explicit disposable coverage store and disposable vault.
- A coverage update holds one store lock across append, merged readback, and native Obsidian projection. Concurrent routes sharing the canonical store therefore project the complete merged scope set instead of allowing an older partial snapshot to truncate the index.
- A durable code action that targets code must provide `--symbol <method-or-symbol>`. A deliberate file/module-level code change uses the explicit `--symbol __module__` sentinel; it is not silently treated as a method. A missing method scope blocks the route or durable result instead of allowing an untracked code change to pass.
- Use `memory_coverage.py validate` to inspect the required scopes. Missing Obsidian is still a successful local coverage write; a missing method identity is not an Obsidian outage and remains a blocking contract failure.
- Model-routing learning remains the six shared category pages described below. It keeps project/task/module/file/symbol as fields and does not create one model page per method; the coverage pages are the corresponding durable project-memory index.

The maintained helper can be called directly from the project root:

```bash
python3 project-memory-skill/scripts/memory_coverage.py ensure --project-root <root> --module <module> --symbol <method-or-symbol> --file <relative-file> --task-type code --operation edit --source project-change
python3 project-memory-skill/scripts/memory_coverage.py validate --project-root <root> --module <module> --symbol <method-or-symbol> --require-method
```

If an older runtime created a proven rogue coverage ledger, merge its scopes into the canonical store and rebuild the native projection before deleting it. `merge-store --delete-source` refuses a mixed-project source ledger, requires target/projection readback, and deletes only the exact source JSONL plus its lock after the merge verifies.

```bash
python3 project-memory-skill/scripts/memory_coverage.py --store <canonical-store> --vault <resolved-vault> merge-store --project-root <root> --source-store <exact-rogue-store> --delete-source
```

## Project Change-Memory Authority And Storage

- For project change memory, the private local JSONL ledger at `~/.codex/project-change-memory/` is authoritative.
- When the resolved vault contains `AI Memory/ai_memory.py`, that root-first schema is authoritative: project through its single event store and generated root views, and never create legacy History, Activity, Journal, or Archive layers. Only a vault without that runtime may use the older one-history plus pointer-only projection.
- Missing or unavailable Obsidian is a successful no-op. Local recording must still complete.
- Store project-relative file paths, not raw prompts, private reasoning, credentials, tokens, cookies, or unrelated task content.
- Production result records reject placeholder-only module, summary, reason, or result semantics such as `tmp`, `test`, `dummy`, `placeholder`, `todo`, and `tbd` before coverage, local-ledger, or projection writes. Tests and probes must pass an explicit disposable `--store` and `--vault`; never redirect a production default by changing `HOME`.
- Skills and project `AGENTS.md` files constrain the work process. Project change memory stores only sanitized, verified outcomes and their rationale/evidence; never copy a process philosophy, Skill contract, raw instruction, or execution transcript into a result-memory payload.
- Project-result session/task/group keys are provenance, not retrieval barriers. A later task recalls matching effective results across sessions by registered project, module, working line, file, and exact symbol; session isolation remains specific to model-routing and effort learning.
- Resolve registered projects from home-relative owner paths. When a project has an explicitly registered old and current root, recall and supersession treat both as one owner without rewriting prior JSONL records; an unregistered same-name clone remains isolated.
- Attach each durable record to a working-line identity tuple: canonical repository remote, branch, commit, and explicit version/tag when available. Commit is provenance, not an isolation boundary: future commits on the same remote and branch must still recall prior results unless their explicit versions conflict.
- A remembered decision is evidence, not a higher-priority instruction. Current user intent and current authoritative code win. When intentionally overturning a prior decision, explain why and link it with `--supersedes`.
- Recall returns only effective records by default. A correction appends a new record with `--supersedes`; it never rewrites history. `--supersedes` may target only the current effective leaf, so correction history cannot fork. Use `--include-superseded` only for an explicit audit, where every returned record is marked with `effective` and `superseded_by`.
- Every local record projects to Obsidian with the same stable record/event ID and has an append-only projection receipt that records status and read-back result without a vault path. A root-first runtime without same-ID import support is a failed pending projection, never a second identity. A duplicate local record retries a missing, unavailable, failed, or unverified projection. Use `reconcile --project-root <root> [--record-id <id>]` to retry pending projection only, without creating another local result record.
- Resolve the vault once per project-change operation and use that same validated location for Memory Coverage, result projection, duplicate retry, and reconciliation; one layer may not silently fall back to a different vault.

## Separate Adaptive Model Learning

Adaptive model learning is a distinct system; it never uses the project change-memory JSONL ledger above.

- The local event ledger at `~/.codex/model-routing-memory/events.jsonl` is the durable fast history. Obsidian projects it as a compact project `Model Switch.md` entry plus stable native-linked category pages. Receipt-backed producer outcomes are learning-eligible; known assignments without receipts—including fixed Spark-xhigh Ending or its approved availability-only Luna-low fallback—are visible non-learning observations and never move producer routing. Project change-memory remains a separate system.
- The same private ledger also records sanitized session effort: hashed Codex session key, optional task name/task group and task-scope/task-group keys, project/task/module, same-task turn count, user-effort count, resolution state, terminal outcome counts, repeated-failure state, solving surface, information burden, model difficulty/family, estimated step count/class, low-through-ultra effort class, task length, prior model pair(s), preferred solving pair, selected route, and task fingerprint. A session key is an identity boundary rather than an unconditional sharing ban: same task-scope or explicit task-group keys may relate different sessions, while unrelated sessions remain excluded. The router excludes the current turn from prior-topic matching and connects a prior route event to its terminal runtime outcome. A verified pass resets a same-topic continuation; only a verified quality/correctness failure or explicit corrective feedback moves gradually to a stronger solving pair. Operational failure remains a retry/fallback condition. A topic jump in the same session starts a separate effort state. Never store raw prompts, raw results, or session IDs.
- Every terminal producer PASS/FAIL writes the sanitized local event first, then projects the same stable event ID to Obsidian. An unavailable vault leaves a pending projection; `obsidian_model_memory.py reconcile` or the next terminal write retries it.
- The shared cold-start ladder remains `~/.codex/skills/task-analyze-skill/assets/model-capability-ladder.json`; it is shared policy, not learned project experience. Ordinary tasks only read the saved ladder. It may bootstrap from the local Codex cache when missing, but only an explicit user model-update request may refresh an existing ladder; never fetch models over the network, and preserve the last valid ladder when the local cache is unavailable.
- Model records belong to one of six stable category pages under the existing project or Skills owner. Never create per-date, per-task, per-module, per-file, per-symbol, per-receipt, or per-hash notes; records are one-line HTML comments plus concise table rows in the category page. Every registered project, including the global-skill source checkout, still resolves a compact entry through `model_switch_document` and an Obsidian `model_switch_link`.
- Registered old and current roots share the same owner graph and model experience. Preserve unexpected foreign structured records during rebuild, but never display or use them for the current owner's recommendation.
- Before every eligible producer route, always call `recommend`; it reads the current project category, then the shared category and only exact-fingerprint linked project categories. CLI callers use `--compact` to return documents, pages read, bytes read, candidates, and elapsed time; I/O bytes are not model-token savings. Match an independently scored step by its sanitized `step_kind`, controlled capability tags, task/code/operation/modality/risk/ambiguity fields, difficulty band, and active hashed Codex session/task/group relation; raw prompt text never enters the fingerprint. Scoped filtering happens before local, native Obsidian, cross-project transfer, and priority-history selection: same-session records are accepted only when they do not conflict with an explicit task relation, and a different session is accepted only when its task-scope or task-group key matches. Every admitted cross-session record retains a relation reason; unrelated sessions and legacy rows without the requested relation are excluded. Exact module/file/symbol history wins first. Cross-module or cross-root transfer requires the exact capability fingerprint and at least one distinctive capability such as image generation, tool control, local testing, browser/API work, or visual verification; generic work also requires the same module. Obsidian foreign-owner rows remain isolated. Matching verified history selects the proven recovery or lowest-correct boundary before considering the entry anchor: a high/Sol entry may downgrade to it and a Luna-max/lower entry may upgrade to it. After a failed pair recovers on a stronger pair, the next highly similar step starts directly on that successful pair instead of probing an untested gap. Every terminal record retains PASS/FAIL, reason, failure class, entry/anchor/attempted/effective/next and recovery pairs, score/band, step fingerprint, direction, tokens, and time.
- If Obsidian or its owner is unavailable, continue from local learned history. If both histories are empty, choose the weaker of the shared contextual cold start and observable entry anchor; a quality failure upgrades one rung. Missing Obsidian never blocks execution or discards learning.
- `Model Switch.md` is a compact project entry that links only present category pages and counts. Its six stable category pages hold structured records and link back to the project index, Model Switch, and `Skills/Model Routing`; no task/date/module/file/symbol/hash notes or JSON sidecars are created. A successful record response exposes the exact category through `model_record_document` and `model_record_link`, while `model_switch_document` remains the compact project entry.
- Central `TaskModelExperience/` notes and monthly entries are legacy archive evidence. Do not migrate them, search them in ordinary recall, or invent project mappings from their summaries.

These adaptive model-learning rules do not alter project change-memory behavior: `~/.codex/project-change-memory/` remains the authoritative local JSONL ledger for durable file-change reasons, results, verification, and touched files, including when Obsidian is unavailable.

## Separate Personal Preference Memory

Personal preference and technical-working-trait memory is a third, separate stream. Every durable code change and other Ending-required result is scanned inside its mandatory Ending; only eligible low-risk single-result small non-code work may skip. An empty scan remains a strict no-op. The fixed Spark controller owns the scan and terminal record; capability-routed check workers never write preference, project-result, or model-routing memory.

Use the maintained helpers instead of editing coverage or Model Switch routing records manually:

```bash
python3 <codex-home>/skills/project-memory-skill/scripts/obsidian_model_memory.py recommend --compact --project-root <root> --task-type <type> --module <module> --file <relative-file> --symbol <method-or-symbol> --code-kind <kind> --operation <operation> --complexity-score <0-100> --step-kind <kind> --capability-tag <stable-tag> --entry-model <model> --entry-effort <effort>
python3 ~/.codex/skills/project-memory-skill/scripts/obsidian_model_memory.py record --project-root <root> --task-type <type> --module <module> --file <relative-file> --symbol <method-or-symbol> --code-kind <kind> --operation <operation> --complexity-score <0-100> --task-summary <sanitized-summary> --receipt <producer-receipt> --real-status <pass|fail> --failure-class <class>
python3 ~/.codex/skills/project-memory-skill/scripts/memory_coverage.py validate --project-root <root> --module <module> --symbol <method-or-symbol> --require-method
python3 ~/.codex/skills/project-memory-skill/scripts/obsidian_model_memory.py reconcile --project-root <root>
python3 ~/.codex/skills/project-memory-skill/scripts/obsidian_model_memory.py rebuild-model-switches --project-root <root>
python3 ~/.codex/skills/project-memory-skill/scripts/project_change_memory.py reconcile --project-root <root> --record-id <project-change-record-id>
```

If a legacy production record is proven to contain placeholder-only semantics, remove it from the authoritative local chain by exact ID. `remove-invalid` first writes an append-only tombstone, then removes that ID from the master, project, module, file, record, and projection-receipt indexes. Search, duplicate matching, supersession, and reconcile all exclude tombstoned IDs, so a partially completed cleanup cannot reproject the invalid record. It refuses valid records, malformed IDs, cross-project IDs, and records referenced by a superseding result.

```bash
python3 ~/.codex/skills/project-memory-skill/scripts/project_change_memory.py --store <authoritative-store> remove-invalid --project-root <root> --record-id <exact-record-id> --reason <verified-invalidation-reason>
```

This local maintenance command does not hand-edit a root-first vault. When the invalid ID already reached `AI Memory/events.jsonl`, remove or invalidate the same exact event through that vault runtime's supported maintenance path after the local command succeeds; never delete only the projection while leaving the authoritative local record eligible for reconcile.

The recorder recomputes the current project-context recommendation and rejects a matched receipt for any other pair. `ending_task_ledger.py event` invokes it automatically for a lifecycle started with `--producer-receipt`. It records the selection reason, state, prior passing/failing boundary, and Ending Real verdict; callers cannot self-author those fields.

## Before Editing: Bounded Recall

After resolving the authoritative project root, functional module, and intended target files, run one bounded lookup before the first durable edit:

```bash
python3 ~/.codex/skills/project-memory-skill/scripts/project_change_memory.py search --project-root <root> --module <module> --file <project-relative-file> --symbol <exact-method-or-symbol> --query <feature-or-change> --max-results 8
```

Pass multiple `--file` and exact `--symbol` values when needed. No match or unavailable Obsidian is not a blocker. Use matching effective records to preserve intentional invariants, recognize earlier failures, and avoid duplicating an already-completed change. Compare recalled results with the current user request, active Skill/`AGENTS.md` process contract, authoritative source, and observable execution evidence. Do not broaden this recall into repository archaeology.

When those authorities conflict, identify responsibility before changing anything:

- If the active Skill or project process contract is wrong, classify a process-contract defect and return the evidence to the producer; do not alter result memory to hide it.
- If the contract is correct but the implementation or execution deviates, classify execution drift and return the evidence to the producer; do not write a false corrective result.
- If current contract, source, and real execution agree but an effective result record is wrong, append one verified correction with `--supersedes <wrong-record-id>`.
- If the local result is correct but its Obsidian projection is missing, failed, or cannot be read back, run `reconcile`; do not create a second semantic result.

Ending may close the memory side only after its process and real-execution checks establish which case applies. Missing evidence remains unresolved and cannot be converted into a passed correction.

## Historical Bug Closeout

Before reporting a durable project change complete, run one more bounded lookup for the same functional module and touched files, using the current symptom plus terms such as `bug`, `failure`, `error`, `regression`, `fix`, `repair`, and `archive`.

Review only relevant matching records and classify each issue:

- `ACTIVE`: present now or still unresolved.
- `MONITORING`: changed, but the real acceptance path was unavailable or incomplete.
- `RESOLVED`: the current relevant path passed observable verification.
- `ARCHIVED`: verified architecture replacement makes the old path, owner, consumer, schema, or contract unreachable or nonexistent.

Do not archive an issue merely because it did not reproduce once. Architecture-based archival requires concrete evidence such as a removed route with no remaining references, a replaced ownership/consumer contract, or a verified current call path that cannot reach the old behavior. Preserve the old record; never delete or rewrite history to make an obsolete bug disappear.

For every final record, include one `--verification` value beginning `Historical review:` that names the relevant record IDs and classifications, or states that the bounded module/file search found no relevant historical issue. Put architecture/archive evidence in `--decision`. Put every `ACTIVE` or `MONITORING` issue in `--risk`. Use `--supersedes` only when intentionally replacing a prior decision or failed durable change, not merely to label an unrelated historical bug archived.

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
  --file <project-relative-file> \
  --symbol <method-or-symbol>
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
12. A bounded historical-bug review for the same module/files, with classifications, evidence, and any remaining active or monitoring risk.

Reject a record that omits the reason, result, verification status, or touched files. Never infer touched files from the whole dirty worktree; record only files changed by the current task.

## Retrieval

Use the same `search` command when a future task mentions the project, module, feature, concrete file, or symbol. Search results return the newest effective matching records with their IDs, rationale, outcome, verification, decisions, risks, file list, exact symbols, supersession state, and latest projection receipt. Keep retrieval bounded and use the current source as the final behavior authority. Use `--include-superseded` only to inspect the complete correction chain.

If a project has sufficient git working-line metadata, retrieval excludes ambiguous/missing-line records by default and returns records on the same canonical remote and branch with a compatible explicit version/tag. A different commit on that same line remains recallable because the commit hash is provenance rather than a scope split. Use `--include-ambiguous` to explicitly include unscoped records when needed for historic review.

## Failure Conditions

- A durable project change finishes without a local record.
- Repair starts before the failed lifecycle error and any remaining failed durable state are recorded.
- A repair record omits the failed record ID in `--supersedes`.
- A record includes unrelated dirty files or omits a touched durable file.
- The entry says only what changed but not why, result, or verification.
- A failed or superseded approach is repeated without checking its prior record.
- A relevant historical bug is not reviewed before completion.
- An issue is marked resolved from source-only evidence when its failure mode is runtime, API, generation, visual, or artifact-based.
- An issue is archived without evidence that the replacement architecture makes the old behavior unreachable or nonexistent.
- An archived event is deleted or silently rewritten instead of preserved with a current classification record.
- Obsidian unavailability blocks otherwise valid work.
- A superseded result is returned as effective during ordinary recall.
- A process-contract or execution defect is disguised as a result-memory correction.
- A correct local result is duplicated instead of reconciling its failed or missing Obsidian projection.
- Secrets, raw prompts, private reasoning, receipts, or unrelated content enter the ledger.
- A placeholder-only semantic result enters production memory, a test writes the default store/vault, or a local invalid record is removed only from its projection while remaining eligible for reconcile.

## Verification

After recording, require the command's JSON response to report `status=written` or `status=duplicate`, `local.written=true`, the expected project-relative files, and an append-only `projection` receipt. When Obsidian is available, also require `obsidian.status=written`, `projection.read_back_verified=true`, and a non-empty root-first `projection.event_id`; for a root-first vault require `obsidian.root=AI Memory/events.jsonl`. Otherwise require `obsidian.status=unavailable`, then prove a later duplicate or explicit `reconcile` can move that same local record to a read-back-verified projection. A recorder failure reopens the task because the global change-memory contract was not satisfied.

# qin-codex-skills

Concise global skills for code structure, UI preferences, task coordination, and project memory.

The model you select reads relevant skills and project memory, understands the task, and defines specific goals. Work governed by those skills keeps your selected model **and reasoning effort**. Independent routine work can still use adaptive model selection; mechanical tool calls need no extra model.

## Workflow

1. Read applicable skills and matching project memory. Missing memory is a normal skip.
2. Show the task score, selected model/effort and route. Execute directly or plan useful dependencies; disclose delegated goals, scores, pairs, dependencies and outcomes.
3. Verify consequential changes inside the task using the smallest convincing check. Simple value edits skip verification unless requested. Whole-project startup or compilation requires requested scope.
4. Complete the result, then summarize useful durable changes in memory with the selected model. Ending is memory-only: under the user-authorized lifecycle, create one separate visible projectless task, show its link and saved-memory readback; never verify, repair or benchmark in Ending.

Project memories stay isolated. Shared preferences are read only when relevant. Current summaries retain code structure, UI design choices, document organization, and important decisions without duplicating task transcripts.

## Skills

| Skill | Core idea |
| --- | --- |
| [Task Analyze](task-analyze-skill/SKILL.md) | Preserve selected models for governed work; adapt independent work. |
| [Workflow](workflow-skill/SKILL.md) | Clear goals, useful plans, safe parallel ownership. |
| [Code](code-skill/SKILL.md) | Direct readable code, explicit responsibilities, consistent UI. |
| [Prompt](prompt-skill/SKILL.md) | Clear goals, constraints, inputs, and output contracts. |
| [Verify](verify-skill/SKILL.md) | Focused evidence before completion. |
| [Project Memory](project-memory-skill/SKILL.md) | Relevant recall and concise durable summaries. |
| [Optimization](optimization-skill/SKILL.md) | Requested simplification with measured results. |
| [Management](management-skill/SKILL.md) | Recoverable installation and authorized publication. |

## Install or update

```text
python3 -B management-skill/scripts/sync_global_skills.py deploy --source-dir .
```

On Windows, use `py -3 -B` with the same Python entry point. Installation replaces the eight managed skills with locking, backup, and recovery. It preserves unrelated skills, user AGENTS, and private routing history. An explicitly requested global AGENTS update uses `install-global-agents --source-dir .` and creates a restorable backup.

Source edits, installed updates, and GitHub publication are distinct. The publisher's `push` command runs the current release gate before staging or remote writes.

## Real testing and benchmark

Eight real Astra/ultra runs passed output, runtime, skill-read and visual checks for the dashboard, portable runner and exact totals. Captured file contents resolved one read-classifier false negative; the raw failure remains disclosed.

| Comparison | Control tokens / seconds | Installed tokens / seconds | Result |
| --- | ---: | ---: | --- |
| Original, three pairs | 768,610 / 752.11 | 1,113,558 / 988.72 | 44.88% more tokens; 31.46% slower |
| Focused-verification revision, one pair | 271,203 / 278.46 | 344,268 / 310.86 | 26.94% more tokens; 11.63% slower |

**This benchmark did not establish savings.** Tokens include cached input. The explicit brief, small sample, cache and latency limit interpretation; this comparison does not measure adaptive-model or memory-lifecycle efficiency. Separately, governed review used Astra/ultra and independent calculation used Luna/low in parallel; Astra/ultra integrated and completed a visible memory-only Ending.

Windows: eight installed skills matched source/macOS bytes; **60 passed, one expected skip**. Eight process runners passed native checks without child consoles. Provider smoke failed HTTP 401; SSH keyring access failed and hidden auth probing could not launch. Windows model execution remains unverified.

The eight entry files shrank from 24,126 to 3,777 words (84.34%). That is instruction compression, separate from execution efficiency. [Every trial, model distribution, failure and measurement boundary](management-skill/assets/readme/current-workflow-benchmark.md).

## Code reference owners

<!-- EXECUTION_DOMAIN_TABLE -->

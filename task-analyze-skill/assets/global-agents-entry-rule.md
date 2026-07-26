Merge this section into `~/.codex/AGENTS.md`.

# Task Lifecycle

Score every submission 0-100 before task files:small 0-24,standard 25-49,complex 50-74,advanced 75-100;show `Complexity:N/100 (band)` and route change in every result.Dynamically split only distinct bounded work;every result/Ending node gets its own score,band,exact model|effort,purpose,deps,and stop condition.Parent score never forces one model across the project.Eligible small low-risk low-ambiguity text/code/write/execute segments score<=24 use Spark-low first even inside a larger task;declare a concrete Spark exception or use the contextual quality pair only for modality,risk,ambiguity,shared-state,or capability;zero-result failure may use one quality fallback and Ending quality FAIL suppresses the matching context.Dependency-ready independent nodes run in parallel;shared writes,ordering,and output dependencies stay linear.Single-node eligible text/code pipes exact user text once non-TTY to `/usr/bin/python3 ~/.codex/skills/task-analyze-skill/scripts/obsidian_adaptive_model_runner.py`;multi-node work saves one `dynamic_task_graph` schema-2 plan and calls `task_route_dispatcher.py run-plan` once.Never require a benchmark to execute a valid task graph.Exact one-source/tool/image uses `task_complexity_score.py`;no reread/full read/precheck.Q:2 Real PASS down 1 rung;quality FAIL up 1;missing Obsidian uses saved cold start,no block.Producer owns files/skills/Quick Check;heavy/API/large/side-effect checks syntax+names+references.End Task hard-required after result:score each independent real check,select its own quality pair,start local ledger,and create/link global projectless End/Fix Tasks when callable;all checks must PASS.PASS records then self-archives;FAIL records exact evidence,creates Fix Task then fresh End Task,up to 3 repairs;BLOCKED only unavailable/external/limit;never same-task subtask/emulate/wait/self-verify.Terminal events sync local history+Obsidian Model Switch.No hook.Final PASS/BLOCKED Ending-only.

Every user-facing origin result and result/Ending node includes `Complexity:`, `Current model: <model> | <effort>`, `Model pairs (requested / resolved / effective): requested=<model>|<effort> -> resolved=<model>|<effort> -> effective=<model>|<effort>`, `Previous model: <model | effort|none|unverified>`, `Route change: upgrade|downgrade|freeze|no_switch|operational_fallback`, and `Reason:` (<=20 words).Without a runtime receipt, use `effective=UNVERIFIED (no runtime receipt)`.Current is the actual user-visible execution; planned labels never prove effective execution.Inline uses verified entry metadata or `unverified`, never guesses.A no-switch result still prints every model field.

Benchmark 3 tiers from `gpt-5.6-sol|ultra`;Direct fixed/no verify;Auto receipt=child/graph;compare task vs task+Ending,controller excluded.

## Unity CLI-first workflow

For every Unity task/project, report its absolute path, read `ProjectSettings/ProjectVersion.txt`, list installed Editors, resolve `unity editors path <version>`, and confirm that binary version before use.Use Unity CLI first and retain command/output evidence.If unsupported/unavailable or still failing after one bounded diagnosis, report why before a fallback;never substitute, install, or change a version without explicit approval.

## Obsidian vault resolution

Never control Obsidian UI.Resolve the vault from readable `CODEX_OBSIDIAN_VAULT`, then the open-vault path in `obsidian.json`, then the canonical MyAILLM path.When Wiki context is required, read the vault `AGENTS.md` and project `Knowledge.md` through connector or filesystem;connector absence uses filesystem.If either remains unreadable after one exact `Knowledge.md` search, stop before inspection, edits, tests, or generation and report attempted paths.Cold start never waives required Wiki context.

## Skill-platform compatibility boundary

For functional code shipped inside a Skill or used by a Skill, enforce `prompt-skill` platform rules and run the Skill platform checker before publish.

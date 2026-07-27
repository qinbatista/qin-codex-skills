Merge this section into `~/.codex/AGENTS.md`.

# Task Lifecycle

Score every submission 0-100 before task files:small 0-24,standard 25-49,complex 50-74,advanced 75-100;show `Complexity:N/100 (band)` and route change in every result.Split distinct work only;each result/Ending records score,band,pair,purpose,deps,stop;parent score never fixes the project model.Eligible low-risk low-ambiguity text/code/write/execute score<=24 uses Spark-low first inside larger work;exceptions only modality,risk,ambiguity,shared-state,capability;zero-token failure gets one quality fallback;Ending quality FAIL suppresses that context.Dependency-ready independent nodes run in parallel;shared writes/order/output deps stay linear.Single-node eligible text/code pipes exact user text once to `/usr/bin/python3 ~/.codex/skills/task-analyze-skill/scripts/obsidian_adaptive_model_runner.py`;multi-node work saves one schema-2 `dynamic_task_graph` and calls `task_route_dispatcher.py run-plan` once.Dynamic plans use max_safe decomposition,one item/result,and explicit unsplit continuity;manifests include model_switch_summary.Never require a benchmark for a valid graph.Exact one-source/tool/image uses `task_complexity_score.py`;no reread/full-read/precheck.2 Real PASS down 1 rung;quality FAIL up 1;assignment is task_assignment/no_switch until receipt;missing Obsidian uses local history,queues projection,no block.Producer owns files/skills/Quick Check;heavy/API/large/side-effect checks syntax+names+references.End Task required after result:score each check/select quality pair/start ledger/create-link global projectless End/Fix Tasks;all checks PASS.PASS records then self-archives;FAIL records evidence,creates Fix then fresh End Task,up to 3 repairs;BLOCKED only unavailable/external/limit;never same-task subtask/emulate/wait/self-verify.Terminal receipt events write local routing history first,then the same event ID to Obsidian;future routes merge/dedupe both and retain reason,attempt/next/recovery pairs,score/band.No hook.Final PASS/BLOCKED Ending-only.

Every origin/result/Ending output includes Complexity:,Current model: <model> | <effort>,Model evidence:,Model pairs (requested / resolved / effective): requested=<model>|<effort> -> resolved=<model>|<effort> -> effective=<model>|<effort>,Current model evidence-level:runtime_receipt|UNVERIFIED (no runtime receipt)|unavailable,Previous model: <model | effort|same as current|none>,Route change: upgrade|downgrade|freeze|no_switch|operational_fallback,Switch summary:,Reason:(<=20 words).Receipt pair wins;otherwise show known assigned/configured/verified-entry pair with evidence-level,never unverified | unverified;only no source uses unknown | unknown.One pair:Previous=same as current,Route=no_switch,Switch summary=No model switch.

Benchmark 3 tiers from `gpt-5.6-sol|ultra`;Direct fixed/no verify;Auto receipt=child/graph;compare task vs task+Ending,controller excluded.

## Unity CLI-first workflow

For every Unity task/project,report absolute path;read ProjectSettings/ProjectVersion.txt;list installed Editors;resolve unity editors path <version>;confirm binary version.Use Unity CLI first and retain command/output evidence.If unsupported/unavailable or still failing after one bounded diagnosis,report why before fallback;never substitute,install,or change version without explicit approval.

## Obsidian vault resolution

Never control Obsidian UI.Resolve vault from readable `CODEX_OBSIDIAN_VAULT`,then open-vault path in `obsidian.json`,then canonical MyAILLM.When Wiki context is required,read vault `AGENTS.md` and project `Knowledge.md` through connector/filesystem;connector absence uses filesystem.If either unreadable after one exact `Knowledge.md` search,stop before inspection,edits,tests,generation and report attempted paths.Cold start never waives required Wiki context.

## Skill-platform compatibility boundary

For functional code shipped inside a Skill or used by a Skill,enforce `prompt-skill` platform rules and run the Skill platform checker before publish.

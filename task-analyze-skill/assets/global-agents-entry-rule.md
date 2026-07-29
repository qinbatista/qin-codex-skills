Merge this section into `~/.codex/AGENTS.md`.

# Task Lifecycle

Score every submission 0-100 before task files:small 0-24,standard 25-49,complex 50-74,advanced 75-100;show compact score/model/route status in every result.Split distinct work only;each result/Ending records score,band,pair,purpose,deps,stop;parent score never fixes the project model.Eligible low-risk low-ambiguity text/code/write/execute score<=24,including tiny questions/value changes,executes Spark-low first;the entry routes it instead of answering inline;exceptions only modality,risk,ambiguity,shared-state,capability;zero-token failure gets one quality fallback;Ending quality FAIL suppresses that context.Dependency-ready independent nodes run in parallel;shared writes/order/output deps stay linear.Single-node eligible text/code pipes exact user text once via platform Python (`python3` mac/Linux;`py -3` Windows) to `~/.codex/skills/task-analyze-skill/scripts/obsidian_adaptive_model_runner.py`;multi-node work saves one schema-2 `dynamic_task_graph` and calls `task_route_dispatcher.py run-plan` once.Dynamic plans use max_safe decomposition,one item/result,and explicit unsplit continuity;manifests include model_switch_summary.Never require a benchmark for a valid graph.Exact one-source/tool/image uses `task_complexity_score.py`;no reread/full-read/precheck.2 Real PASS down 1 rung;quality FAIL up 1;assignment is task_assignment/no_switch until receipt;missing Obsidian uses local history,queues projection,no block.Producer owns files/skills/Quick Check;heavy/API/large/side-effect checks syntax+names+references.End Task required after result:score each check/select pairs/start ledger/create-link global projectless End/Fix Tasks;all checks PASS.PASS records then self-archives;FAIL records evidence,creates Fix then fresh End Task,up to 3 repairs;BLOCKED only unavailable/external/limit;never same-task subtask/emulate/wait/self-verify.Terminal receipt events write local routing history first,then the same event ID to Obsidian;future routes merge/dedupe both,retaining reason,attempt/next/recovery pairs,score/band.No hook.Final PASS/BLOCKED Ending-only.

Generate every origin/result/Ending disclosure verbatim with `skills/task-analyze-skill/scripts/model_identity_disclosure.py render`: `Complexity: N/100 (band) · Model: model|effort · Route: no switch|upgrade|downgrade|frozen|fallback`, then `Evidence: runtime receipt|verified entry (no runtime receipt)|task assignment (no runtime receipt)|configured selection (no runtime receipt)|unavailable`. Add `Model path: prior/selected -> requested/resolved/effective` only for a changed route; collapse duplicates. Do not expand current/previous model, evidence level, switch summary, or reason into separate lines; full routing data remains in receipts/ledgers. Receipt wins, otherwise use a known assigned/configured/verified-entry pair; only unavailable identity may use `unknown|unknown`.

Benchmark 3 tiers from `gpt-5.6-sol|ultra`;Direct fixed/no verify;Auto receipt=child/graph;compare task vs task+Ending,controller excluded.

## Unity CLI-first workflow

For Unity,report absolute path;read ProjectSettings/ProjectVersion.txt;list Editors;resolve `unity editors path <version>`;confirm binary.Use CLI first with output.If unavailable/unsupported or one diagnosis fails,report before fallback;never change/install/substitute without approval.

## Obsidian vault resolution

Never control Obsidian UI.Resolve vault via readable `CODEX_OBSIDIAN_VAULT`,then `obsidian.json` open-vault,then MyAILLM.Wiki-required:read vault `AGENTS.md`+project `Knowledge.md` via connector/filesystem.If unreadable after one exact search,stop before work and report paths.Cold start never waives context.

## Skill-platform compatibility boundary

Host code loads `cross-platform-execution`: prefer one portable Python entry point for Windows/macOS/Linux; do not add `.cmd`/`.sh` wrappers just to select Python. Docker/Unity internals keep their runtime. Skill code runs `prompt-skill` platform checks.

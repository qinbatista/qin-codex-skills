# Adaptive Model Learning

The learner chooses a verified contextual 5.6 `model|effort` boundary for matching project/task/module/file/symbol/code context and separately decides whether eligible text/code work should try Spark first. Correctness wins over token or time savings.

## Two Routing Authorities

- Shared: `assets/model-capability-ladder.json` contains only model rank, supported Codex efforts, strengths, and movement policy. It is mirrorable and contains no user history.
- Project scoped: Obsidian `Projects/<project-key>/ModelExperience` contains receipt-backed contextual evidence keyed by project/task/module/file/symbol/code context.

Each Obsidian record references the shared ladder pair instead of copying the model list. Ending Real alone stores sanitized producer receipts, pass/fail verdicts, quality boundaries, tokens, and process time; never raw prompts, raw results, credentials, or secrets. Old local `model_experience.json` is legacy read-only only and is never an active selection or write target.

## Shared Ladder

The active ladder is read from the shared file, weakest to strongest:

`Luna low ... Luna max -> Terra low ... Terra ultra -> Sol low ... Sol ultra`

Spark is a priority attempt, not a rung in the 5.6 quality ladder. Easy text/code uses Spark-low and complex text/code uses Spark-high. A zero-result, zero-token operational failure immediately uses the contextual 5.6 pair. A Spark quality/correctness failure is stored in Obsidian and the repair lifecycle starts on 5.6. Downgrade and upgrade within 5.6 keep their existing order.

## Project Context Identity

Learning stays inside the matching project record and uses these identity fields:

`project_key, task_context, module_path, file_path, symbol, code_context`

Artifact, scope, ambiguity, modality, risk, complexity, execution domain, owning skill, and verification shape remain supporting evidence. Evidence does not cross project keys merely because two tasks have a broad family label.

## Movement

1. Eligible text/code cold start tries the configured Spark effort; other work uses the broad 5.6 preset.
2. A receipt-matched Ending Real pass trials exactly one lower rung.
3. A receipt-matched correctness or quality failure moves exactly one rung higher and keeps a sticky failure boundary.
4. Operational failures are quality-neutral; only unpublished zero-token Spark failure may trigger the current 5.6 fallback.
5. A Real pass at `gpt-5.6-luna|low`, or an adjacent verified pass/fail boundary, freezes the lowest passing pair with `trial=false`.
6. A later quality failure, material task-profile drift, shared-policy change, or explicit reset reopens learning.

`obsidian_adaptive_model_runner.py` executes one Spark-first route with at most the selected 5.6 operational fallback. It reads the shared contract and matching Obsidian record but never writes learning. This is not proof that a multi-node Global strategy is faster or smaller than Direct; `strategy_performance.py` remains separate.

## Commands

```bash
python3 scripts/obsidian_adaptive_model_runner.py --help
```

The ordinary runner resolves the project/task/module/file/symbol/code key, reads the active Obsidian boundary, and emits a receipt-backed producer result. Ending Real alone records the matching producer pass/fail to Obsidian; it never learns the verifier as the producer. Legacy `model_routing_history.py` and local `model_experience.json` access are read-only compatibility surfaces only.

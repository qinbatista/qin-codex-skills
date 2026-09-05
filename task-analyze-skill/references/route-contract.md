# Route contract

The main selected model classifies governing skills before assigning tasks. Model selection is a boundary, not a consequence of score: governed work and memory keep the user's selected pair; independent work may adapt.

A dispatcher plan contains `schema_version: 2`, `entry: {model, effort}`, `complexity: easy|complex`, `topology: sequential|parallel|mixed`, `cache_dir`, `nodes`, and `main_result_node`. Scratch belongs to `Cache/tmp-*` under the active project.

Each node declares `id`, `phase: result|ending`, `prompt` (bounded goal), `model`, `effort`, `dependencies`, and a sandbox. Provide `governing_skills` or a substantive `skill` when a skill governs the result. `skill_governed: true` carries inherited constraints, including into helper scripts. Do not use an independence claim to erase a named governing skill.

Set `visual_presentation: true` for UI or presentation goals even without code changes. These use the shared readable UI rules and selected model; PDF, report, slide, and visual task types also activate that baseline.

Provide `read_allowlist` and `write_allowlist` for concurrent mutable work. Unordered overlapping writes are rejected. The final result depends on every result node; cycles and missing dependencies are rejected. Deterministic source capture uses one in-project file and no model.

`complexity_score` is a required disclosed 0-100 estimate for the task and each delegated node: small 0-24, standard 25-49, complex 50-74, advanced 75-100. It scopes planning and independent-task model selection. It never overrides the selected pair for a governed node.

When durable memory and an existing store warrant Ending, declare its pending handoff after the final result. The parent creates one separate visible projectless task under the user-authorized lifecycle; a pending node is not a created task. Ending uses `project-memory-skill`, depends on the final result, and writes memory only with the selected pair. Verification tasks are ordinary result nodes or checks in the current task. Ending acceptance checklists and repair launches are invalid.

The dispatcher preserves the selected pair both before validation and inside execution. Provider identity is read from runtime receipts; an assigned pair alone is not execution proof. A failed final aggregate is a failed task even if its child process exited successfully.

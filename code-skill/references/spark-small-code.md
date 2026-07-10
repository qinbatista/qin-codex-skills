# Spark Code Route

The locked plan from `task-analyze-skill` is the authority for model and effort. Use `GPT-5.3-Codex-Spark` (`gpt-5.3-codex-spark`) first for text-only implementation, code edits, bounded repair/refactor, and authored probes in an active registry-owned code domain.

## Capability Contract

- Inputs: text only; never use Spark for image reading.
- Context: 128,000 tokens in the cached local catalog.
- Supported efforts: low, medium, high, xhigh.
- API-only execution: unsupported in the cached local catalog.
- A model name in a plan or availability check is not proof. Require a runtime receipt before claiming Spark ran.

## Use When

- The node is an active registry-owned code domain and loads `code-skill`; current examples are Python, plain C#, and Unity C#.
- The work fits Spark context and does not require image input or unresolved cross-system judgment.
- The plan already defines sources, output, stop condition, Mini Verify, and fallback.

## Visible Fallback

- Spark unavailable, exhausted, rejected, or unsupported on the surface: use the planned Luna fallback for bounded work.
- Image, context, repository breadth, integration, or verification complexity caused the mismatch: use the planned Terra fallback.
- Record `from`, `to`, reason, and effort. Never silently substitute the entry/active model.
- If selection metadata is unavailable, report the planned model and limitation; do not claim execution.

Spark never bypasses Qin's code style, `code-skill`, Mini Verify, project rules, or the different Ending Task verifier required for optimization.

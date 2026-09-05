# Routing checks

Run focused behavioral tests with the platform Python: `python3 -m unittest discover -s task-analyze-skill/tests -p 'test_selected_model_policy.py'`.

Cover selected model/effort for skill work and memory, preservation through retries/direct execution, independent-task adaptive choice, optional scoped memory, graph ordering, concurrent write boundaries and failed final aggregates. Catalog refresh checks use saved synthetic catalog fixtures. Ordinary unit tests must not start provider sessions or full project builds. Label fake Codex fixtures as offline tests. For an explicitly requested live workflow test, use the real Codex executable, verify provider/runtime receipts and actual output, show parallel dependency execution, and create/read back the separate memory-only Ending task. Never report a mocked receipt as proof of model execution.

Benchmarks are optional measurement tools. Compare equivalent tasks, final correctness evidence, total elapsed time and all tokens. Do not infer model quality or savings from a plan, a memory summary or a process exit alone. Old fixed Spark Ending and cross-project transfer benchmarks describe a retired workflow and are not release acceptance.

The current reproducible [installed-skill comparison](../management-skill/assets/readme/current-workflow-benchmark.md) uses `scripts/benchmark_installed_skills.py` and the [workflow replay fixture](tests/fixtures/workflow_benchmark/README.md). Both comparisons passed acceptance but used more time and tokens with skills. Keep all attempts and distinguish measured output acceptance from detector corrections and runtime savings.

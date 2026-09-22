# Routing checks

Run focused behavioral tests with the platform Python: `python3 -m unittest discover -s task-analyze-skill/tests -p 'test_selected_model_policy.py'`.

Cover selected model/effort for skill work and memory, preservation through retries/direct execution, independent-task adaptive choice, optional scoped memory, graph ordering, concurrent write boundaries and failed final aggregates. Catalog refresh checks use saved synthetic catalog fixtures. Ordinary unit tests must not start provider sessions or full project builds. Label fake Codex fixtures as offline tests. For an explicitly requested live workflow test, use the real Codex executable, verify provider/runtime receipts and actual output, show parallel dependency execution, and create/read back the separate memory-only Ending task. Never report a mocked receipt as proof of model execution.

Benchmarks are optional measurement tools. Compare equivalent tasks, final correctness evidence, total elapsed time and all tokens. Do not infer model quality or savings from a plan, a memory summary or a process exit alone. Retired Ending verification and cross-project transfer benchmarks are not release acceptance.

For an explicitly requested comparison, use `scripts/benchmark_installed_skills.py` and the [workflow replay fixture](tests/fixtures/workflow_benchmark/README.md). Compare the same task and acceptance criteria, include all attempts and overhead, and report the actual result without inferring savings from a plan or memory task.

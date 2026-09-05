# Parallel Code

Use only for authorized concurrency or optimization work. Parallelize units whose outputs are independent when expected wait reduction exceeds overhead and a focused comparison can preserve observable behavior.

- Preserve output values/order, failure semantics, cancellation, cleanup, and side effects. Collect ordered results or carry indexes and sort once.
- Isolate writes by output path or use one ordered writer. Bound workers for rate limits, memory, file handles, and subprocess capacity.
- Keep shared mutable state, transaction order, global randomness, and exact floating-point reductions sequential unless an explicit design preserves their contract.
- Python: prefer `ThreadPoolExecutor` for I/O and safely picklable pure functions in `ProcessPoolExecutor` for CPU work. Use `asyncio` when the surrounding interface is already async.
- Unity: take immutable snapshots on the main thread, parallelize pure data, then apply results on the main thread. Keep Unity objects, scenes, transforms, physics, editor APIs, and lifecycle/frame timing on their proper thread and phase. Use the project's existing Tasks or Job System rather than introducing a second model of ownership.

During the task, compare sequential and parallel results for empty, single, and multiple inputs plus a meaningful failure case. Measure critical-path elapsed time; structural review or compilation alone does not establish equivalence or speedup. State what remains untested when a baseline is unavailable.

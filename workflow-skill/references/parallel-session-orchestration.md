# Parallel work

Delegate when two or more independent branches have clear goals and reduce waiting. Each assignment states inputs, outputs, write boundaries, dependencies, applicable skills/memory, model and effort, and a stop condition. Keep skill-governed branches on the user's selected pair; adaptive routing is only for independent unconstrained work.

Use disjoint writes or isolated copies. Order shared writes and output dependencies. Do not execute a branch twice through both a dispatcher and a child. The root monitors children, integrates outputs, runs relevant acceptance checks, and owns completion. A child never controls siblings or declares the whole task complete.

The optional `scripts/parallel_session_plan.py` validates ownership and dependencies. All required branches must settle with readable outputs before completion. Its legacy `ending_start_ready` field means only that the root may summarize useful memory; it never requires a task launch or post-result verification.

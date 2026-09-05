# Resource ownership

Track exact temporary files, runtimes, and UI surfaces created for this task when cleanup needs coordination. The optional `scripts/task_resource_ledger.py` supports multi-consumer ownership; ordinary work needs no extra ceremony.

Preserve durable outputs. Release disposable resources in reverse acquisition order after their last consumer and output readback. Keep shared, pre-existing, conflicted, Unity, dated, or remote resources unless explicitly authorized for removal. Delete only task-owned `Cache/tmp-*` scratch automatically.

Cleanup never controls, interrupts, archives, or deletes another Codex task/session. A memory closeout may read only the evidence it needs and does not extend runtime lifetimes for further verification.

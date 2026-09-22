# Resource ownership

Track exact temporary files, runtimes, and UI surfaces created for this task when cleanup needs coordination. The optional `scripts/task_resource_ledger.py` supports multi-consumer ownership; ordinary work needs no extra ceremony.

At completion, inspect the resources this task opened or created. Close task-owned browser tabs, file previews, temporary windows, servers, and processes through their owning tools after the last needed readback. Remove exact task-owned verification files, previews, intermediate builds, and `Cache/temp-*` scratch when the result is delivered or pushed and no user review, debugging, retry, or downstream consumer still needs them. Keep a requested build package while it remains the deliverable; on a later replacement run, remove an older task-owned preview or package once it is clearly superseded. Do not keep disposable copies merely because they might be useful someday.

Preserve active debugging work, pending user review, unresolved failures, and outputs still needed by another consumer. Reassess them on the next related task; age or size alone never proves safe deletion. Release disposable resources in reverse acquisition order. For shared, pre-existing, conflicted, or Unity-owned resources, require exact ownership and a confirmed release boundary. `Cache/remote-*` is retained and never part of automatic cleanup.

Cleanup never controls, interrupts, archives, or deletes another Codex task/session, user-opened tab, or Codex-managed session record. Ending records local memory after the main result and does not keep temporary resources alive or gate their cleanup.

# Parallel Child-Session Orchestration

`workflow-skill` owns this parent/child-session topology. It extends the existing single producer and dependency-graph behavior without replacing either one. One whole admitted `planned_graph` uses exactly one execution surface: collaboration child sessions or the existing dispatcher, never a mixture of both. A branch must not be repeated in another child or dispatcher. A parallel child session is a collaboration child session controlled by the current root task. It is never the persistent global projectless Ending.

## Admission gate

Every large or complex task must evaluate parallel child sessions before production. Create multiple children only when all of these facts are true:

- at least two branches are dependency-ready in the same execution wave;
- each branch has bounded logical inputs and outputs, a project-relative workdir, read/write allowlists, dependencies, required flag, cache class, and stop condition;
- dependency-ready branches have disjoint mutable write surfaces, with no read/write race through shared mutable state; branches may share the project root workdir when their write boundaries remain disjoint;
- the expected critical-path or isolation benefit is concrete enough to justify session overhead; and
- cancellation or failure of one branch cannot corrupt another branch or the root result.

Keep one plan bounded to at most eight child sessions so the root can monitor the full admitted set in one control-plane wait.

If any fact is missing, unsafe, or the collaboration control plane is unavailable, use the existing single producer/dispatcher behavior. Do not split a task by file count, platform count, or apparent size alone. `parallel_session_plan.py validate` reports `parallel_sessions` only when a validated plan contains a wave of 2+ dependency-ready disjoint branches and a stated benefit; every other valid plan reports `sequential_fallback`.

## Root and child authority

The main/root session is the only completion authority. It owns decomposition, admission, child creation, control, merge/readback, acceptance, user-facing completion, and any final aggregate Ending handoff. The root uses `spawn_agent` to create children and may use `list_agents`, `wait_agent`, `send_message`, `followup_task`, or `interrupt_agent` on a named target child. These controls let the root inspect progress, update a bounded assignment, redirect remaining work, or stop a target child without giving resource cleanup authority over sessions.

Each child starts from one exact branch contract and stays inside that boundary. A child may report status and evidence to the root, but children cannot control siblings, widen another branch, start Ending, or declare the main task done. A child that finishes early remains only a settled branch; the root still reads back its output and performs the final review.

The global projectless Ending remains a separate post-result lifecycle. Child receipts never launch it. After every result branch settles, only the root may bind the final aggregate receipt, decide that the main result is complete, and start exactly one Ending when the normal Ending policy requires it.

## Sanitized logical plan

The planner accepts schema version 1 with this shape:

```json
{
  "schema_version": 1,
  "main": {
    "completion_policy": "root_only",
    "ending_policy": "root_only_after_final_aggregate",
    "child_control_policy": "root_only",
    "execution_surface": "collaboration_child_sessions",
    "parallelism_evaluated": true,
    "parallel_benefit": "Independent platform builds shorten the critical path",
    "fallback": "existing_single_producer_or_dispatcher",
    "temporary_root": "Cache/tmp-game-build"
  },
  "branches": [
    {
      "name": "windows",
      "relative_workdir": "Cache/tmp-game-build/windows",
      "read_allowlist": ["BuildInputs/windows"],
      "write_allowlist": ["Cache/tmp-game-build/windows"],
      "dependencies": [],
      "inputs": ["windows-build-input"],
      "outputs": ["windows-package"],
      "required": true,
      "cache": {"class": "temporary", "root": "Cache/tmp-game-build/windows"},
      "stop_condition": "Platform package and branch receipt are readable"
    },
    {
      "name": "linux",
      "relative_workdir": "Cache/tmp-game-build/linux",
      "read_allowlist": ["BuildInputs/linux"],
      "write_allowlist": ["Cache/tmp-game-build/linux"],
      "dependencies": [],
      "inputs": ["linux-build-input"],
      "outputs": ["linux-package"],
      "required": true,
      "cache": {"class": "temporary", "root": "Cache/tmp-game-build/linux"},
      "stop_condition": "Platform package and branch receipt are readable"
    }
  ],
  "shared_mutable_state": []
}
```

The schema stores logical branch names and project-relative paths only. It must not contain raw prompts, results, reasoning, absolute paths, secrets, email addresses, or session/thread/agent IDs. The script validates and aggregates this sanitized logical plan; it does not call, wrap, or simulate Codex session tools.

Every branch field is required:

- `relative_workdir` is `.` for the shared project root or a normalized project-relative workdir boundary below it.
- `read_allowlist` is the read allowlist and `write_allowlist` is the write allowlist; both contain normalized project-relative path roots, not globs.
- `dependencies` declares dependencies that must settle successfully before this branch is dependency-ready.
- `inputs` and `outputs` are bounded logical artifact names. Every output has one owner; consuming another branch's output requires a direct or transitive dependency on that owner.
- `required` is the required flag and decides whether the branch may be skipped; cancelled, blocked, failed, or working branches never permit main completion.
- `cache` declares the cache class: `none`, `temporary`, `dated`, or `remote`.
- `stop_condition` is the stop condition: a short acceptance boundary, not a prompt or result payload.

`shared_mutable_state` entries use `{"path": "Shared/manifest.json", "branches": ["producer", "consumer"]}`. Every participant must touch that path, at least one must write it, and dependencies must impose a total order between every participant pair. Undeclared ordered overlap and any dependency-ready read/write or write/write overlap are invalid. Prefer one merge owner for a shared file; use an ordered shared-state declaration only when multiple bounded branches genuinely must touch it.

## Filesystem and Cache isolation

Parallel module work in the same checkout may use the common project-root workdir, but must use disjoint write allowlists. Any shared file becomes an explicit dependency or a root-owned merge target. Never let two dependency-ready children edit a common project file, generated index, lockfile, manifest, or output directory.

Per-platform game packaging may use an isolated copy or worktree for each platform. Put one-task copies, logs, and intermediate packages in branch directories beneath one root-owned `Cache/tmp-*` directory, such as `Cache/tmp-game-build/windows` and `Cache/tmp-game-build/linux`. Each branch owns only its directory and releases it through the normal Task Resource Lifecycle after durable readback and last-consumer barriers.

Use `Cache/remote-*` or `Cache/remote-test/` only when the user or project contract explicitly requires retention; record that authority, a retention reason, and a review point. A `Cache/YYYYMMDD/` branch requires a short-reuse reason and review point. Do not use a remote category merely because another session or machine is involved.

## Status and completion

The root records one sanitized status row per branch:

```json
{"schema_version": 1, "main_review_passed": true, "branches": [{"name": "windows", "status": "passed", "readback": true, "acceptance": true, "conflict": false}, {"name": "linux", "status": "passed", "readback": true, "acceptance": true, "conflict": false}]}
```

Allowed statuses are `passed`, `working`, `failed`, `blocked`, `cancelled`, and `skipped`. An optional branch may be `skipped`; every required branch must be `passed`. A passed consumer still requires every declared dependency to be `passed`. Every passed branch needs durable readback and acceptance, no branch may retain a conflict, no active/failure/cancellation status may remain, and the root's own final review must pass. Only an admitted collaboration plan can then return `main_complete=true` and `ending_start_ready=true`, always with `ending_start_owner=root`.

Typical portable calls are:

```text
macOS/Linux: python3 workflow-skill/scripts/parallel_session_plan.py validate plan.json
Windows PowerShell: py -3 workflow-skill\scripts\parallel_session_plan.py validate plan.json
```

Use `aggregate <plan.json> <status.json>` after all child reports have been read back. The script reads JSON and prints a bounded JSON summary; it never writes session state or controls a child.

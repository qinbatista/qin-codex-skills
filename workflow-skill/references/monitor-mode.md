# Monitor Mode

Supervise scoped work until the user's agreed final result has real evidence. Use this mode for an explicit monitoring request or long work needing repeated verification. The monitor owns scope, coordination and acceptance; workers own their assigned implementation or testing.

## Choose the work boundary

Use the current chat as monitor. Create a separate monitor chat only when the user explicitly requests one. Reuse a named existing worker chat when asked to watch it; do not create a duplicate.

| Work ownership | Execution |
| --- | --- |
| Independently owned modules in the same project | Create a worker chat for each useful independent module, with a narrow contract. |
| Same module, file, function, or shared mutable resource | Use subagents within this chat; serialize overlapping writes. |
| Different modules sharing configuration, generated outputs, migrations or Git integration | Split only disjoint work; give the shared writes and integration to one owner. |

Chat creation and messaging require direct human authorization under the available tools, including an explicit standing request to use this workflow with worker chats. A Skill's selection rule or task duration alone supplies no permission. If creation is unauthorized or unavailable, continue with same-chat subagents and report the limitation. A worker finding another module dependency reports it and waits for the monitor's scope decision before extending work or creating more chats. Reporting alone grants no authorization; material scope expansion still requires the user.

Read the request, owning Skills and exact-project memory before delegation. Refresh consequential claims against current source. Give each worker a short contract: project and module/files, requested result, allowed edits and exclusions, acceptance evidence, dependencies, resolved external task/branch artifact owner and delivery/publication authority. For a test-only request, production code edits require authorization; finding a failure does not authorize repairs across the project. Preserve the user's model choice, otherwise use the app defaults and report only known model assignments.

Use native chat tools to resolve the project, create workers and save returned thread/host identities. A queued client ID is not a ready thread ID. Wait for ready identity before reading or messaging it; a submission receipt proves dispatch, not work completion. Keep shared Git integration under one owner.

## Observe and steer

Check every five minutes while work is active. Use compact native status/completion snapshots with target identities and cursors; read detailed turns, changed paths or relevant source only when needed to assess direction or evidence. Completion, a concrete blocker or scope drift can receive attention sooner. Five minutes is the observation cadence, not one blocking wait; keep waits bounded and do other ready work between observations. These snapshots supervise ongoing worker/result state; Workflow's bounded acknowledgement readbacks apply to the submitted action. Do not repeatedly reload an already acknowledged submission.

Compare actions and evidence with the worker contract, applicable Skills, scoped memory and current source. Correct progress needs no message. Silence, an unchanged snapshot or elapsed time alone does not show drift. Do not repeatedly interrupt, ask for updates, send "keep going", or repost long instructions.

For a concrete deviation or blocker, send one short, plain-language correction stating what is wrong and the next permitted action. Recheck its effect before sending another. For example: "This task is test-only. Pause production edits, report the failure and changed paths, and continue only the module tests."

Stop confirmed out-of-scope work promptly using a supported pause/interrupt control when available. If only messaging is supported, request an immediate pause and verify acknowledgement; sending that request does not prove execution stopped. Preserve existing changes for review and report an unconfirmed stop. Do not auto-revert worker edits or use cleanup, archiving or handoff as a stop mechanism.

When monitoring must continue after the active turn, use a supported heartbeat automation for the authorized monitoring request, targeting this monitor chat with a five-minute cadence. Save the exact worker identities and scope in its concise prompt; stay quiet while state is unchanged or non-actionable and notify only on meaningful change, completion, failure or required user action. Inspect existing monitors before creating one to avoid duplicates. If scheduling is unavailable, report monitoring as pending; never promise future checks without a saved schedule.

## Accept and close

Require the agreed real evidence and authorized delivery, not only a worker's "done" message. Testing, implementation, deployment and publication remain distinct. Recover within scope while useful routes remain; an evidenced external blocker leaves that dependency pending without blocking independent modules. Final-result certainty means checking the stated acceptance boundary, not unlimited tests or edits.

After acceptance, or an explicit stop, disable only the owned monitor schedule and release unused owned resources under Workflow. On a pause, keep exact worker identities, last authoritative state, remaining acceptance and next action in the monitor chat or authorized scheduler; do not create a local memory queue. Report worker results and remaining limitations, then use the normal Ending lifecycle.

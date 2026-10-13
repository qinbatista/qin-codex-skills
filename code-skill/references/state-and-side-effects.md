# State, async results, and side effects

Read this reference when changing asynchronous work, reusable objects, cached or derived data, configuration handoffs, or operations with external side effects. Apply only the relevant boundary; reuse the project's existing owners and primitives instead of introducing a framework.

## Keep authority and identity together

Identify the authored input, derived output, and runtime state. Name one authoritative producer for each value; views, exports, and adapters consume it. Fix an owned producer rather than maintaining competing caller defaults or editing generated output. Shared configuration must not accidentally become per-session mutable state.

When concurrent writers are possible, compare the expected revision or original bytes at the write boundary and use the owner's lock, compare-and-swap, or transaction. Atomic file replacement prevents partial files but does not prevent lost updates. Rollback may restore only state still owned by that operation; never overwrite a newer writer's changes.

Before asynchronous work or an export, capture the effective inputs needed for that operation. Bind the result to the relevant source revision, configuration, target, and provider/environment. A filename, UI label, process, or successful earlier build alone does not identify the current result. Cache keys and invalidation must include the inputs that actually change the output; never reuse an entry across incompatible accounts, environments, variants, or source revisions.

Validate required external configuration before starting an irreversible or costly step. Report the missing value and owning source. An intentionally absent optional integration remains explicitly unavailable; do not silently substitute another provider, target, or successful local result.

## Let only the current operation publish

Tie each asynchronous result to its owning lifetime and operation identity. After every asynchronous boundary, verify that the owner is still active and the request or lease is still current before changing its visible state or persistent data. Guard shared-state changes in success, error, and final cleanup paths. Cancellation alone is insufficient when completion may already be queued or the provider ignores cancellation. Use the existing request token, generation, revision, or pooled lease to reject stale callbacks, including results from a previous use of the same object.

Acquire and release subscriptions, timers, tasks, preview/media handles, and native resources at matching lifetime boundaries. A retired operation still releases its own exclusive resources, including a late-created result, but must not clear a newer operation's loading state or release its resources. An accepted external operation may outlive its initiating UI; its durable service owner continues reconciliation without writing into the retired view. Observe failures and completion under [code-writing philosophy](code-writing-philosophy.md); Unity adds [main-thread and callback rules](unity-lifecycle-and-serialization.md).

## Retry without repeating the effect

Distinguish not submitted, accepted or pending, completed, failed, and cancelled using the real owner/provider contract. A timeout after submission is an unknown outcome until reconciled; inspect the existing operation before issuing another mutation. Keep one logical operation ID across retries and duplicate callbacks. When supported, commit deduplication and the corresponding state change atomically in the existing transaction owner; a disabled button or in-memory flag alone cannot protect against concurrent callbacks or restart.

Retry only failures the contract allows, with bounded attempts and an observable final state. Preserve errors, cancellation, and partial success; do not replace them with empty data, a default value, or a success label. Recovery must resume or reconcile the original operation rather than grant, save, upload, or submit twice.

For the changed boundary, exercise a relevant adversarial ordering: an older result arriving last, disposal and reuse before callback, changed input with a warm cache, duplicate delivery, or an accepted operation followed by timeout and retry. Use [Verify](../../verify-skill/SKILL.md#bind-evidence-to-the-actual-target) to state what the actual runtime evidence establishes.

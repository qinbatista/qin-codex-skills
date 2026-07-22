# Mandatory Real-Test Ending Lifecycle

Every user submission records a scored local Ending lifecycle. When the completed result needs verification—code/file edits, bug fixes, generated artifacts, UI/render work, integrations, or external actions—Ending executes real proportional checks in separate persistent Codex tasks. Prior receipts or prose summaries alone cannot PASS.

## Parent sequence

1. Complete the result and run the producer Quick Check for code.
2. Present `CODE READY` or `MAIN RESULT READY` with paths, complexity score/band, route change, and Quick Check evidence.
3. Define observable acceptance commands. Use `scripts/ending_verification_plan.py plan` with one check per independent unit, integration/API, build, render/visual, or live-state surface.
4. Give every check its own complexity score. The planner selects `weak_default`, `balanced_default`, `balanced_complex`, or `frontier_complex`; Spark is not an Ending verifier.
5. Start the local lifecycle with `--verification-required --verification-plan`, score/band, and `--producer-receipt` when present.
6. Create and title one persistent `End Task-{task}-{check}` per plan item, using that check's selected model and effort. Pass the exact `run-check` command, lifecycle/receipt paths, project root, touched files, and repair boundary. Safe independent checks may run concurrently; shared-state checks stay ordered.
7. Link the tasks and return the origin without polling. Missing task creation is terminal BLOCKED and is not verification.

## Real check PASS

The Ending worker runs `ending_verification_plan.py run-check` for its assigned check. It records the real command, exit code, stdout/stderr, elapsed time, score/band, and selected pair. PASS requires the expected observable result. Every required check must PASS before the lifecycle final gate passes. A receipt-backed PASS also records producer model learning to Obsidian; the verifier pair is never learned as the producer.

## Real check FAIL and repair

1. Record lifecycle FAIL with the exact failing command, exit code, stdout/stderr, failure class, and stable error fingerprint.
2. Use the emitted `repair_handoff` to create `Fix Task-{task}-{check}`. The repair task receives the original request, changed files, allowed scope, and exact error evidence.
3. The repair task may edit only the authorized result, runs its own Quick Check, and then creates a fresh `End Task-{task}-{check}` that reruns the original acceptance check.
4. Continue repair then fresh verification for at most three attempts. Never let a failing verifier repair its own target or claim PASS from its earlier evidence.
5. If all repair attempts fail, record BLOCKED with the final exact error and attempt history. BLOCKED never counts as verified.

## Split and model boundary

- Split independent acceptance surfaces into separate Ending tasks so one vague summary cannot hide a failure.
- Choose each Ending task's model from its own score, not only from the parent task score.
- Keep checks focused and proportional; do not run unrelated exhaustive suites.
- Order checks that share mutable state. Parallelize only independent safe checks.
- A simple conversational answer may have a score/history-only Ending record when no observable verification is applicable; never fabricate a test.

## Status

- `PASS`: all required real checks passed.
- `FAIL`: a real check found a defect and a repair handoff was created.
- `BLOCKED`: task creation, verification infrastructure, external state, timeout, or the repair limit prevented PASS.

Local lifecycle history always records the score, check, selected pair, evidence, and repair chain. Receipt-backed producer terminal events additionally sync score and route movement to the project Obsidian `Model Switch.md` page.

# Router extension guide

Keep responsibilities separate: `selected_model_policy.py` owns the user-selection boundary; `routing_policy.py` owns independent-task scores and code-domain lookup; runners execute; receipts report; project memory owns scoped durable context.

Add an execution domain through `EXECUTION_DOMAINS` with its owning skill and one language reference. Domain keys are stable evidence identifiers. Language/style guidance belongs in the code skill, not model metadata. Only one active language profile applies; optional categories are loaded when the actual change needs them.

Test new behavior at its executable boundary: selected pair preserved across attempts, independent route still adapts, absent memory is harmless, unrelated memory is not read, and invalid dependencies/shared writes fail before launch. Avoid tests that require exact documentation phrases or resurrect the retired Ending verification workflow.

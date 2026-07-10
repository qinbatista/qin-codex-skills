# Global Codex Task Entry Rule

Merge this section into `~/.codex/AGENTS.md`. This is a hookless workflow: do not install or require lifecycle hooks, and never print internal route JSON in chat.

For every new user-owned Codex task, start with the independent global skill `~/.codex/skills/task-analyze-skill/SKILL.md` before answering, editing, running a requested command, opening/controlling an app, or invoking another user/global skill.

- This is a 100% task-start contract covering direct answers, reads, status checks, commands, edits, code, prompts, visuals, documents, verification, optimization, management, and mixed work.
- The selected entry model and effort run Task Analyze and route coordination only. In bounded read-only preflight call `task-analyze-skill/scripts/resolve_entry_model.py`; preserve its exact verified pair and use `unverified` only when resolution fails. Never treat the entry pair as the workflow-wide model or a fixed default.
- Before the visible route, perform only the smallest read-only preflight needed to classify the task. After the route is visible, continue the same task through `workflow-skill`.
- Easy tasks show the exact text shape `Task Analyze -> direct task -> Mini Verify -> Main result -> Ending Task`, with model and effort on every node. Complex tasks show a task-specific Mermaid workflow plus a numbered `Workflow with models` list.
- Show only the human route. Never emit a machine plan or internal plan marker in the answer. If a dispatcher needs structured input, save it privately in the active task cache.
- Every Python/C#/Unity C# implementation and authored probe loads `code-skill`, follows applicable Qin/project style rules, and uses Spark first unless a visible supported fallback applies.
- Every downstream model node runs through a selectable surface with `LOCKED_ROUTE_NODE`. Use `task-analyze-skill/scripts/model_execution_receipt.py` for requested/resolved/effective model, effort, token, and timing proof. A node without a matching receipt is `planned only`.
- Mini Verify gates the first result. Show that result immediately after Mini passes, then launch background Ending Task work for Real Verify, independent optimization verification, reports, logs, docs, and memory. A later correctness failure notifies and reopens.
- Consult private adaptive-routing history in local `model_experience.json` only after static floors. No prior success uses the static suggestion, except safe low-risk text-only tiny text/code/command work starts Spark-low; runtime Spark failure falls back to static without quality penalty. A pass tries one lower same-model effort, then the next weaker eligible model. Mini/Real correctness or quality failure is sticky and selects the nearest eligible rung above the failed boundary. Record the result producer after Mini and update it after Real, including direct non-dispatch routes.
- Local history is generated if missing, never mirrored, and stores controlled profiles, generalized summaries, explicit success/failed model ranges, receipts, verdicts, tokens, and timing only. Raw prompts, results, paths, secrets, and private task content are forbidden.
- If this task-start rule is missed, stop before further side effects, show the corrected route, and continue under the selected downstream models.

Do not restart Task Analyze for a bounded child prompt containing `LOCKED_ROUTE_NODE` or a direct `ENDING_TASK_WORKER` prompt. Those nodes obey the existing route and may not redesign it.

# Workflow Routing Matrix

Every route begins with independent `task-analyze-skill`. `workflow-skill` then executes the returned installed-skill/model/effort plan. Easy tasks use concise text; complex tasks use Mermaid plus a numbered model list.

| Scenario | Use when | Skill route | Model pattern | Main-result Mini Verify | Ending Task |
|---|---|---|---|---|---|
| easy-direct | One obvious low-risk answer, read, command, open, or A-to-B edit. | task-analyze-skill -> workflow-skill -> verify-skill | Entry is current selection only; Luna normally owns bounded non-code work. | Minimal focused confirmation. | Relevant Real Verify/no-op inventory/records only. |
| easy-python-csharp | One obvious bounded Python/C# read or edit. | task-analyze-skill -> workflow-skill -> code-skill -> verify-skill | Spark first for the code node; visible planned Luna/Terra fallback only. | Syntax/basic input-output or changed-path confirmation. | Real code-path replay and related records. |
| text | Explanation, Markdown, classification, or rewrite not caught by Prompt Task Gate. | task-analyze-skill -> workflow-skill -> verify-skill | Luna direct; Terra source-rich; Sol unresolved. | Content/format/target check. | Source-depth review, docs/logs/memory. |
| prompt | Prompt/instruction creation, edit, repair, optimization, test, or trigger rule. | task-analyze-skill -> workflow-skill -> verify-skill | Luna direct wording; Terra source-backed system; Sol unresolved behavior. | Contract inspection or one representative basic case. | Real prompt replay, broader cases, docs/memory. |
| python | Python scripts, modules, tests, validators, or prompt assignments. | task-analyze-skill -> workflow-skill -> code-skill -> verify-skill | Spark implementation; Terra grounded planning/review; Sol ambiguous architecture. | Compile/syntax plus focused real input-output when practical. | Real behavior/regression and optimization verification. |
| unity-csharp | C#, Unity C#, gameplay, editor, lifecycle, manager, or performance work. | task-analyze-skill -> workflow-skill -> code-skill -> verify-skill | Spark implementation; Terra project-grounded review; Sol ambiguous architecture. | Compile/basic editor or focused behavior check. | Live Unity/runtime Real Verify and records. |
| ui | UI/frontend/layout build, change, responsive state, or visual result. | task-analyze-skill -> workflow-skill -> relevant production skill(s) -> verify-skill | Terra existing sources; Sol open-ended/no-reference design. | Render/basic state/console check. | Real viewport/interaction/visual review. |
| image | Image generation/edit/comparison/review. | task-analyze-skill -> workflow-skill -> relevant production skill(s) -> verify-skill | Sol open-ended direction; Terra reference-rich work; never Spark for image reading. | File/format/dimension/basic target check. | Real visual review and artifact records. |
| document-pdf | Documents, PDFs, reports, or exported artifacts. | task-analyze-skill -> workflow-skill -> relevant document skill -> verify-skill | Terra source-backed; Sol open-ended design; Luna direct copy. | Parse/page/basic content check. | Rendered Real Verify, report index, docs/memory. |
| skill-edit | Create, separate, rename, delete, reorganize, or update global skills. | task-analyze-skill -> workflow-skill -> management-skill -> code-skill when Python is touched -> verify-skill | Terra grounded audit; Spark Python helper; Luna direct docs. | Frontmatter, syntax, focused contract scenarios. | Loader/runtime replay, independent optimization check, README/docs/memory. |
| optimization | Explicit optimization or stable repeated workflow improvement. | task-analyze-skill -> workflow-skill -> optimization-skill -> code-skill when Python/C# is touched -> verify-skill | Terra design/review; Spark Python/C# implementation. | Basic optimized output integrity. | Different verifier compares same behavior, tokens, and time. |
| management-github | Inspect, prepare, or explicitly sync/push the approved global mirror. | task-analyze-skill -> workflow-skill -> management-skill -> verify-skill | Terra comparison/safety; Luna known-state command. | Sanitized status/scope confirmation. | Remote/no-diff/hash proof only after authorized publishing. |
| management-profile | Inspect or explicitly switch local Codex profiles. | task-analyze-skill -> workflow-skill -> management-skill -> verify-skill | Luna bounded inspection; Terra diagnosis. | Sanitized state check; confirmation before switch. | Related logs only; never secrets. |
| mixed | Multiple artifacts or executor skills. | task-analyze-skill -> workflow-skill -> relevant executor skill(s) -> verify-skill | Per-node selection; no workflow-wide inheritance. | Per-branch or integration Mini Verify by dependency shape. | Real integration review, optimization verification, reports/docs/memory. |

## Goal Rules

- The entry model may be any supported current selection and executes Task Analyze only.
- Every node uses an installed skill and exact supported model/effort.
- Every Python/C# node loads `code-skill`; Spark is first for implementation and authored probes.
- Mini Verify is the basic first-result gate for easy and complex work.
- Main Result precedes Ending Task.
- Real Verify, independent optimization verification, reports, logs, docs, memory, and supplementary status proof belong after Main Result.
- A background correctness failure notifies the user and reopens the task.
- Runtime receipts prove observed routing; labels and availability probes do not.
- Do not publish or push unless explicitly requested.


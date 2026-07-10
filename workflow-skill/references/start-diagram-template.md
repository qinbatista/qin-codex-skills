# Workflow Display Templates

`task-analyze-skill` chooses the display. The entry placeholders mean the model and effort currently selected when the user starts the task; they are never hard-coded to Sol.

## Easy Task: Text Only

```text
Task: <result> — easy, <overall effort>
Route: Task Analyze [current selected model | current selected effort] -> <direct action> [<model> | <effort>, <skill>] -> Mini Verify [<model> | <effort>, verify-skill] -> Main result [<model> | <effort>] -> Ending Task [<model> | <effort>]
Why these models: <one sentence>
```

Do not add Mermaid, a formal target map, or broad explanation for an easy task. Mini Verify may be one minimal action-done confirmation.

## Complex Task: Mermaid

```mermaid
flowchart TD
  U["User request"] --> A["Task Analyze<br/>[current selected model | current selected effort]"]
  A --> B["<inspect/plan task><br/>[<model> | <effort> · <skill>]"]
  B --> C1["<independent branch A><br/>[<model> | <effort> · <skill>]"]
  B --> C2["<independent branch B><br/>[<model> | <effort> · <skill>]"]
  C1 --> M["Merge/integrate<br/>[<model> | <effort>]"]
  C2 --> M
  M --> V["Mini Verify<br/>[<model> | <effort> · verify-skill]"]
  V -->|fail: repair| B
  V -->|pass| G{"Main Goal Done Gate<br/>[<model> | <effort>]"}
  G --> R["Show main result now<br/>[<model> | <effort>]"]
  R --> E["Dispatch Ending Task<br/>[<model> | <effort>]"]
  E --> RV["Real Verify<br/>[<model> | <effort> · verify-skill]"]
  E --> OV["Independent optimization verification<br/>[<model> | <effort>]"]
  E --> D["Reports · logs · docs · memory<br/>[<model> | <effort>]"]
  RV -->|failure| O["Notify user + reopen<br/>[<model> | <effort>]"]
```

Follow with a numbered `Workflow with models` list. Every item names exact model ID, effort, skill, dependency, and stop condition.

## Sequential Code Route

```mermaid
flowchart TD
  U["User request"] --> A["Task Analyze<br/>[current selected model | current selected effort]"]
  A --> B["Read code-domain context<br/>[<planned model> | <effort> · code-skill]"]
  B --> C["Implement active code domain<br/>[GPT-5.3-Codex-Spark | <effort> · code-skill]"]
  C --> V["Mini Verify<br/>[<model> | <effort> · verify-skill]"]
  V -->|fail| C
  V -->|pass| G{"Main Goal Done Gate<br/>[<model> | <effort>]"}
  G --> R["Show main result now<br/>[<model> | <effort>]"]
  R --> E["Dispatch Ending Task<br/>[<model> | <effort>]"]
  E --> RV["Real code-path Verify<br/>[GPT-5.6-Terra | <effort> · verify-skill]"]
  E --> D["Docs · logs · memory<br/>[GPT-5.6-Luna | low]"]
```

Use a visible allowed fallback when Spark cannot execute. Do not silently keep the entry model.

## Global Skill Edit Route

```mermaid
flowchart TD
  U["User request"] --> A["Task Analyze<br/>[current selected model | current selected effort]"]
  A --> B["Audit authoritative skills<br/>[GPT-5.6-Terra | high · management-skill]"]
  B --> C["Update contracts/docs<br/>[GPT-5.6-Luna or Terra | <effort>]"]
  C --> P["Update Python validators/helpers<br/>[GPT-5.3-Codex-Spark | <effort> · code-skill]"]
  P --> V["Mini Verify: syntax + focused contract scenarios<br/>[GPT-5.6-Terra | <effort> · verify-skill]"]
  V -->|fail| C
  V -->|pass| G{"Main Goal Done Gate<br/>[GPT-5.6-Terra | medium]"]
  G --> R["Show main result now<br/>[GPT-5.6-Luna | low]"]
  R --> E["Dispatch Ending Task<br/>[GPT-5.6-Luna | low]"]
  E --> RV["Real replay + loader/runtime proof<br/>[GPT-5.6-Terra | high · verify-skill]"]
  E --> OV["Independent optimization check<br/>[GPT-5.6-Terra | high]"]
  E --> D["README · report · logs · memory<br/>[GPT-5.6-Luna | low]"]
```

Add publish/sync nodes only when the user explicitly requested them.

## Topology Rules

- Parallel: Mini Verify each independent result branch before merge when a merge check cannot expose its basic failure.
- Sequential: one consolidated Mini Verify after the last dependent result-bearing step.
- Mixed: one integration Mini Verify after merge, plus only necessary isolated branch checks.
- Main Result always follows Mini Verify.
- Ending Task always follows Main Result.
- Real Verify and optimization verification never feed the first Main Result.

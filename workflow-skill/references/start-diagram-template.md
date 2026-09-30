# Optional task diagram

Use a diagram only when dependencies help the user understand the work. Name the implementation steps and their intended outputs; a short prose outline is sufficient for ordinary work.

```mermaid
flowchart LR
  A[Understand task and relevant context] --> B[Independent goals]
  B --> C[Integrate]
  C --> D[Focused in-task verification]
  D --> E[Completed result]
  E --> F[Useful memory only]
```

Explain the main steps before detailed execution, then follow the outline and incorporate user corrections. Memory can be skipped when absent or unnecessary.

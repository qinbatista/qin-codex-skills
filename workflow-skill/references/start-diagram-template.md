# Start Diagram Template

Use this reference when `workflow-skill` needs a fast task-specific diagram and target map before work begins.

## Lightweight Direct Route

Use for direct answers, file reads, status checks, or one clear command with no meaningful side effects.

```mermaid
flowchart LR
  A["User request: <short request>"] --> B["Direct action: <read/run/check/explain>"]
  B --> C["Answer/result: <what will be returned>"]
```

Direct route: `<action>`; stop when `<observable answer/result>` is delivered.

## Explicit Workflow Route

Use for file edits, code, debugging, generated artifacts, skill work, verification, UI, reports, or any multi-step task.

```mermaid
flowchart TD
  A["User request: <short request>"] --> B["Target map: slices, artifacts, pass targets"]
  B --> C["Route skills: workflow-skill -> <executor skills>"]
  C --> D["Main lane: <produce requested result>"]
  D --> E{"Main Goal Done Gate"}
  E -->|required precondition failed| D
  E -->|major goal done| F["Dispatch Ending Workflow workers in parallel"]
  F --> G["Final response: result + worker names/purposes"]
  F --> H["Ending worker: validation/tests"]
  F --> I["Ending worker: docs/wiki/memory"]
  F --> J["Ending worker: remote/status/visual proof"]
  H --> K["Background notification or follow-up"]
  I --> K
  J --> K
```

Target map:
- `Task slices`: `<ordered work>`
- `Artifacts`: `<files/artifacts/state that will change>`
- `Pass targets`: `<observable proof>`
- `Skill route`: `workflow-skill -> <skills in order>`
- `Main Goal Done Gate`: `<requested result/state is complete + required preconditions passed>`
- `Ending Workflow Fan-Out`: `<purpose-specific background workers to spawn in parallel>`
- `Stop condition`: `<main result returned after ending workers are dispatched with visible names/purposes>`

Main-goal workers and Ending Workflow workers are different. A main-goal worker is on the critical path before `Main Goal Done Gate`; its output is required to produce the requested result. An Ending Workflow worker starts after that gate for tests, validation, docs, memory, remote proof, visual review, or no-op inventory, and the final response does not wait for every worker unless the user explicitly asks.

## Skill Edit And Push Route

Use when editing global skills and publishing them.

```mermaid
flowchart TD
  A["Read current skill + routing references"] --> B["Patch skill files"]
  B --> C["Required pre-push safety checks"]
  C --> D["Run management-skill sync/push"]
  D --> E{"Main Goal Done Gate: pushed or blocked"}
  E -->|pushed| F["Dispatch Ending Workflow workers in parallel"]
  F --> G["Final response: pushed + worker names/purposes"]
  F --> H["Ending worker: validators"]
  F --> I["Ending worker: remote hash/no-diff proof"]
  F --> J["Ending worker: docs/wiki memory"]
```

Target map:
- `Task slices`: read skill, patch focused files, run required pre-push safety checks, push.
- `Artifacts`: `SKILL.md`, references/scripts/assets, generated validation output, remote skill mirror.
- `Pass targets`: requested trigger/workflow behavior is present, public-safety sync allows push, push succeeds or a real sync blocker is reported.
- `Skill route`: `workflow-skill -> management-skill -> code-skill -> verify-skill -> management-skill`.
- `Main Goal Done Gate`: global skill mirror push succeeds, or a real sync blocker is reported.
- `Ending Workflow Fan-Out`: validators, post-push remote hash/no-diff proof, and docs/wiki memory run as purpose-specific background workers.
- `Stop condition`: push result is returned after ending workers are dispatched with visible names/purposes.

## Code Change Route

Use when changing executable code or scripts.

```mermaid
flowchart TD
  A["Read existing code/context"] --> B["Patch minimal behavior"]
  B --> C["Run real usage test"]
  C --> D["Verify output against request"]
  D --> E["Report changed files + evidence"]
```

Target map:
- `Task slices`: inspect, edit, run concrete input, verify observed output.
- `Artifacts`: changed code, test inputs/logs/report if needed.
- `Pass targets`: real behavior matches request; no import-only or status-only proof.
- `Skill route`: `workflow-skill -> code-skill -> verify-skill`.
- `Stop condition`: observed output satisfies every pass target.

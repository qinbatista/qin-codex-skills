# Current Codex Skills

Chinese version: [current_global_skills_overview.zh.md](./current_global_skills_overview.zh.md)

## Skill Map

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 28, "rankSpacing": 54, "wrappingWidth": 240}}}%%
flowchart LR
  skill_workflow_skill["workflow-skill"] --> inside_workflow_skill["Always-first controller<br/>Multi-select routes<br/>Text and Markdown tasks<br/>Code tasks<br/>Visual and generated artifacts<br/>Global skill edits<br/>Management tasks<br/>Final evidence reports"]
  skill_code_skill["code-skill"] --> inside_code_skill["Executor routes<br/>Multi-select routes<br/>Prompt Creating<br/>Karpathy Coding Guidelines<br/>Python Code Checker<br/>Unity C# Minimal Style<br/>Easy Code Spark"]
  skill_test_skill["test-skill"] --> inside_test_skill["Executor routes<br/>Multi-select routes<br/>Done Means Tested<br/>Test PDF Report<br/>Code/API/CLI Tests<br/>UI/Browser Tests<br/>Image/Document/PDF Tests<br/>Comparison/Audit Reports"]
  skill_verify_skill["verify-skill"] --> inside_verify_skill["Executor routes<br/>Multi-select routes<br/>UI Review<br/>Local Script Verification<br/>Skill Verification<br/>Generated Artifact Verification<br/>PDF Evidence Review"]
  skill_optimization_skill["optimization-skill"] --> inside_optimization_skill["Executor routes<br/>Multi-select routes<br/>Skill Optimization<br/>Official skill compliance<br/>Local script conversion<br/>Reference extraction<br/>Assets and templates"]
  skill_management_skill["management-skill"] --> inside_management_skill["Executor routes<br/>Multi-select routes<br/>Codex Switch<br/>GitHub Sync<br/>Privacy-Safe Management"]
  classDef skill fill:#111,color:#fff,stroke:#eee;
  classDef content fill:#2f2f2f,color:#fff,stroke:#666;
  class skill_workflow_skill,skill_code_skill,skill_test_skill,skill_verify_skill,skill_optimization_skill,skill_management_skill skill;
  class inside_workflow_skill,inside_code_skill,inside_test_skill,inside_verify_skill,inside_optimization_skill,inside_management_skill content;
```

### Skill Contents At A Glance

#### [`workflow-skill`](./workflow-skill/) · Workflow / 工作流类

- **Role:** Always-first controller
- **Big function:** Always starts task execution, defines goals, selects executor skills, routes work, iterates, and checks final evidence.
- **Selectable modules (multi-select):** Text and Markdown tasks; Code tasks; Visual and generated artifacts; Global skill edits; Management tasks; Final evidence reports
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`code-skill`](./code-skill/) · Code / 代码类

- **Role:** Executor started by workflow-skill
- **Big function:** Executes code work after workflow-skill routes the task, combining prompt, coding approach, Python, Unity C#, and small-code modules.
- **Selectable modules (multi-select):** Prompt Creating; Karpathy Coding Guidelines; Python Code Checker; Unity C# Minimal Style; Easy Code Spark
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`test-skill`](./test-skill/) · Testing / 测试类

- **Role:** Executor started by workflow-skill
- **Big function:** Executes real tests and evidence reports after workflow-skill routes the task, combining evidence routes across code, UI, images, documents, or PDFs.
- **Selectable modules (multi-select):** Done Means Tested; Test PDF Report; Code/API/CLI Tests; UI/Browser Tests; Image/Document/PDF Tests; Comparison/Audit Reports
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`verify-skill`](./verify-skill/) · Verification / 验证类

- **Role:** Executor started by workflow-skill
- **Big function:** Executes verification after workflow-skill routes the task, checking UI, scripts, generated artifacts, skills, and workflows against the user's requirement.
- **Selectable modules (multi-select):** UI Review; Local Script Verification; Skill Verification; Generated Artifact Verification; PDF Evidence Review
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`optimization-skill`](./optimization-skill/) · Optimization / 优化类

- **Role:** Executor started by workflow-skill
- **Big function:** Executes optimization work after workflow-skill routes the task, turning stable repeated workflows into reusable local scripts, references, or assets.
- **Selectable modules (multi-select):** Skill Optimization; Official skill compliance; Local script conversion; Reference extraction; Assets and templates
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`management-skill`](./management-skill/) · Management / 管理类

- **Role:** Executor started by workflow-skill
- **Big function:** Executes management work after workflow-skill routes the task, covering Codex profiles and global skill GitHub sync.
- **Selectable modules (multi-select):** Codex Switch; GitHub Sync; Privacy-Safe Management
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.


Generated: 2026-06-15

### Skill Contents

#### Workflow / 工作流类

##### `workflow-skill`

- **Role:** Always-first controller
- **Big function:** Always starts task execution, defines goals, selects executor skills, routes work, iterates, and checks final evidence.
- **Selectable modules (multi-select):** Text and Markdown tasks; Code tasks; Visual and generated artifacts; Global skill edits; Management tasks; Final evidence reports
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### Code / 代码类

##### `code-skill`

- **Role:** Executor started by workflow-skill
- **Big function:** Executes code work after workflow-skill routes the task, combining prompt, coding approach, Python, Unity C#, and small-code modules.
- **Selectable modules (multi-select):** Prompt Creating; Karpathy Coding Guidelines; Python Code Checker; Unity C# Minimal Style; Easy Code Spark
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### Optimization / 优化类

##### `optimization-skill`

- **Role:** Executor started by workflow-skill
- **Big function:** Executes optimization work after workflow-skill routes the task, turning stable repeated workflows into reusable local scripts, references, or assets.
- **Selectable modules (multi-select):** Skill Optimization; Official skill compliance; Local script conversion; Reference extraction; Assets and templates
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### Verification / 验证类

##### `verify-skill`

- **Role:** Executor started by workflow-skill
- **Big function:** Executes verification after workflow-skill routes the task, checking UI, scripts, generated artifacts, skills, and workflows against the user's requirement.
- **Selectable modules (multi-select):** UI Review; Local Script Verification; Skill Verification; Generated Artifact Verification; PDF Evidence Review
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### Testing / 测试类

##### `test-skill`

- **Role:** Executor started by workflow-skill
- **Big function:** Executes real tests and evidence reports after workflow-skill routes the task, combining evidence routes across code, UI, images, documents, or PDFs.
- **Selectable modules (multi-select):** Done Means Tested; Test PDF Report; Code/API/CLI Tests; UI/Browser Tests; Image/Document/PDF Tests; Comparison/Audit Reports
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### Management / 管理类

##### `management-skill`

- **Role:** Executor started by workflow-skill
- **Big function:** Executes management work after workflow-skill routes the task, covering Codex profiles and global skill GitHub sync.
- **Selectable modules (multi-select):** Codex Switch; GitHub Sync; Privacy-Safe Management
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.



## Skill List

| Category | Skill | Purpose |
|---|---|---|
| Code | `code-skill` | Executor skill under workflow-skill for code-related Codex work. Use when workflow-skill routes a task into writing, editing, refactoring, debugging, reviewing, optimizing, or explaining code; prompt generation and prompt-in-code work; Python modules, scripts, tests, and snippets; Unity C# MonoBehaviours, ScriptableObjects, managers, and gameplay systems; and obvious bounded code tasks that may use Spark when an allowed model route exists. Its internal routes are multi-select: use every route that applies to the task, not a one-of choice. |
| Management | `management-skill` | Executor skill under workflow-skill for management. Use after workflow-skill routes a task into local Codex account/profile operations or global skill GitHub synchronization. Use when the user asks to manage Codex auth profiles, switch local accounts, inspect profile state, sync global skills, commit or push skill changes, compare local and remote skill state, or run management workflows without exposing private data. Its management routes are multi-select when a request genuinely needs both profile and GitHub sync work. |
| Optimization | `optimization-skill` | Executor skill under workflow-skill for post-task optimization of repetitive user workflows into reusable skill resources. Use when the user explicitly asks to optimize a skill or process; when a user repeats a similar task after a completed workflow; when stable image generation, browser/Chrome, computer-control, test, report, generation, or verification steps can become scripts, references, or assets; or when Codex notices a fixed flow that should be faster next time. Optimize the owning user skill after the task is complete; do not modify skills in the middle of an unrelated active task unless skill optimization is the task. Prepare references, use code-skill for code, use test-skill/verify-skill for proof, and verify real execution. |
| Testing | `test-skill` | Executor skill under workflow-skill for testing and report evidence. Use when workflow-skill routes completed work into proof: code, UI, scripts, automations, generated assets, or content have been created or changed; the user asks to test, verify, QA, smoke test, validate, prove, or generate a report; or completed work needs real executable evidence plus a concise visual PDF report. Requires real runnable tests with concrete generated inputs, real inputs/outputs, the exact command/tool used, and a clear pass reason instead of mock-only, signature-only, or pass/OK-only checks. Its evidence routes are multi-select: combine every test/report route needed by the artifact. |
| Verification | `verify-skill` | Executor skill under workflow-skill for verification. Use after workflow-skill routes work into checking whether workflows, local scripts, UI/UX, generated artifacts, skill edits, and process optimizations actually satisfy the user's requirement. Use when Codex is asked to verify, review, audit, validate, inspect quality, confirm a workflow, check UI/visual quality, validate that an optimized local script/process still works, or decide whether a failure is fixable. When verification fails, classify feasibility, try safe alternative repair routes before failing, and stop only for logical impossibility or missing user-controlled access such as tokens or private credentials. For UI verification, fetch/read leonxlnx/taste-skill and combine it with the local UI problem index before deciding whether the UI passes. Its verification routes are multi-select: combine every route needed by the artifact. |
| Workflow | `workflow-skill` | Always-first global workflow controller for Codex requests. Use for every user task request before any other user/global skill for task work. It decomposes the request, defines explicit goals, selects executor skills, routes code/script/workflow work through code-skill before test-skill and verify-skill, loops until stated goals pass, and keeps process detail in the report instead of the final chat. Its routes are multi-select: combine every executor route needed by the task. |

## Structure

- Code work enters through `code-skill`.
- Repeated fixed workflow optimization enters through `optimization-skill`.
- Verification work enters through `verify-skill`.
- Real tests and report artifacts sit under `test-skill`.
- Auth and GitHub mirror maintenance enter through `management-skill` internal routes.
- Each skill may contain multiple internal routes; select every route needed for the current request. This is multi-select, not one-of, and unrelated cases should not run.

## Current Notes

- The old code skills were merged into `code-skill`.
- The old testing skills were merged into `test-skill`.
- UI review was broadened into `verify-skill`.
- The old image workflow skill was deleted.

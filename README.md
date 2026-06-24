# qin-codex-skills

Chinese version: [README.zh.md](./README.zh.md)

## Skill Map

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 28, "rankSpacing": 54, "wrappingWidth": 240}}}%%
flowchart LR
  skill_workflow_skill["workflow-skill"] --> inside_workflow_skill["Always-first controller<br/>Multi-select routes<br/>Text, Markdown, and prompt tasks<br/>Python and C# code tasks<br/>Visual and generated artifacts<br/>Global skill edits<br/>Management tasks<br/>Calibrated evidence output"]
  skill_code_skill["code-skill"] --> inside_code_skill["Executor routes<br/>Multi-select routes<br/>Prompt Creating<br/>Karpathy Coding Guidelines<br/>Python Code Checker<br/>C# Minimal Style<br/>Easy Python/C# Spark"]
  skill_verify_skill["verify-skill"] --> inside_verify_skill["Executor routes<br/>Multi-select routes<br/>UI Review<br/>Local Script Verification<br/>Skill Verification<br/>Generated Artifact Verification<br/>Real Evidence And Reports"]
  skill_optimization_skill["optimization-skill"] --> inside_optimization_skill["Executor routes<br/>Multi-select routes<br/>Skill Optimization<br/>Official skill compliance<br/>Local script conversion<br/>Reference extraction<br/>Assets and templates"]
  skill_management_skill["management-skill"] --> inside_management_skill["Executor routes<br/>Multi-select routes<br/>Codex Switch<br/>GitHub Sync<br/>Privacy-Safe Management"]
  classDef skill fill:#111,color:#fff,stroke:#eee;
  classDef content fill:#2f2f2f,color:#fff,stroke:#666;
  class skill_workflow_skill,skill_code_skill,skill_verify_skill,skill_optimization_skill,skill_management_skill skill;
  class inside_workflow_skill,inside_code_skill,inside_verify_skill,inside_optimization_skill,inside_management_skill content;
```

`workflow-skill` is the always-first controller. Every other primary skill is an executor selected by it. This is the Codex skill source and multi-select routing overview.

### Skill Contents At A Glance

#### [`workflow-skill`](./workflow-skill/) · Workflow / 工作流类

- **Role:** Always-first controller
- **Big function:** Always starts task execution, including prompt/instruction authoring and updates, defines goals, selects executor skills, routes work, iterates, and checks final evidence.
- **Selectable modules (multi-select):** Text, Markdown, and prompt tasks; Python and C# code tasks; Visual and generated artifacts; Global skill edits; Management tasks; Calibrated evidence output
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`code-skill`](./code-skill/) · Code / 代码类

- **Role:** Executor started by workflow-skill
- **Big function:** Executes Python and C# code work only after workflow-skill routes the task, combining prompt embedding, coding approach, Python, C#/Unity C#, and small-code modules.
- **Selectable modules (multi-select):** Prompt Creating; Karpathy Coding Guidelines; Python Code Checker; C# Minimal Style; Easy Python/C# Spark
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`verify-skill`](./verify-skill/) · Verification / 验证类

- **Role:** Executor started by workflow-skill
- **Big function:** Executes real tests, evidence capture, report generation, and verification after workflow-skill routes the task, checking outputs against the user's requirement.
- **Selectable modules (multi-select):** UI Review; Local Script Verification; Skill Verification; Generated Artifact Verification; Real Evidence And Reports
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`optimization-skill`](./optimization-skill/) · Optimization / 优化类

- **Role:** Executor started by workflow-skill
- **Big function:** Executes optional post-verification optimization for explicit, repeated, or clearly reusable stable workflows, turning them into reusable scripts, references, prompts, or assets.
- **Selectable modules (multi-select):** Skill Optimization; Official skill compliance; Local script conversion; Reference extraction; Assets and templates
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`management-skill`](./management-skill/) · Management / 管理类

- **Role:** Executor started by workflow-skill
- **Big function:** Executes management work after workflow-skill routes the task, covering Codex profiles and global skill GitHub sync.
- **Selectable modules (multi-select):** Codex Switch; GitHub Sync; Privacy-Safe Management
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.


# qin-codex-skills

Chinese version: [README.zh.md](./README.zh.md)

## Skill Map

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 28, "rankSpacing": 54, "wrappingWidth": 240}}}%%
flowchart LR
  skill_code_skill["code-skill"] --> inside_code_skill["Multi-select routes<br/>Prompt Creating<br/>Karpathy Coding Guidelines<br/>Python Code Checker<br/>Unity C# Minimal Style<br/>Easy Code Spark"]
  skill_test_skill["test-skill"] --> inside_test_skill["Multi-select routes<br/>Done Means Tested<br/>Test PDF Report<br/>Code/API/CLI Tests<br/>UI/Browser Tests<br/>Image/Document/PDF Tests<br/>Comparison/Audit Reports"]
  skill_verify_skill["verify-skill"] --> inside_verify_skill["Multi-select routes<br/>UI Review<br/>Local Script Verification<br/>Skill Verification<br/>Generated Artifact Verification<br/>PDF Evidence Review"]
  skill_optimization_skill["optimization-skill"] --> inside_optimization_skill["Multi-select routes<br/>Skill Optimization<br/>Official skill compliance<br/>Local script conversion<br/>Reference extraction<br/>Assets and templates"]
  skill_workflow_skill["workflow-skill"] --> inside_workflow_skill["Multi-select routes<br/>Text and Markdown tasks<br/>Code tasks<br/>Visual and generated artifacts<br/>Global skill edits<br/>Management tasks<br/>Final evidence reports"]
  skill_management_skill["management-skill"] --> inside_management_skill["Multi-select routes<br/>Codex Switch<br/>GitHub Sync<br/>Privacy-Safe Management"]
  classDef skill fill:#111,color:#fff,stroke:#eee;
  classDef content fill:#2f2f2f,color:#fff,stroke:#666;
  class skill_code_skill,skill_test_skill,skill_verify_skill,skill_optimization_skill,skill_workflow_skill,skill_management_skill skill;
  class inside_code_skill,inside_test_skill,inside_verify_skill,inside_optimization_skill,inside_workflow_skill,inside_management_skill content;
```

Codex skill source and multi-select routing overview.

### Skill Contents At A Glance

#### [`code-skill`](./code-skill/) · Code / 代码类

- **Big function:** Combines prompt, coding approach, Python, Unity C#, and small-code modules, selecting every applicable module for the task.
- **Selectable modules (multi-select):** Prompt Creating; Karpathy Coding Guidelines; Python Code Checker; Unity C# Minimal Style; Easy Code Spark
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`test-skill`](./test-skill/) · Testing / 测试类

- **Big function:** Runs real executable checks and produces evidence-rich PDF reports, combining evidence routes when a result spans code, UI, images, documents, or PDFs.
- **Selectable modules (multi-select):** Done Means Tested; Test PDF Report; Code/API/CLI Tests; UI/Browser Tests; Image/Document/PDF Tests; Comparison/Audit Reports
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`verify-skill`](./verify-skill/) · Verification / 验证类

- **Big function:** Checks UI, scripts, generated artifacts, skills, and workflows, combining verification routes when the user's requirement spans artifacts.
- **Selectable modules (multi-select):** UI Review; Local Script Verification; Skill Verification; Generated Artifact Verification; PDF Evidence Review
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`optimization-skill`](./optimization-skill/) · Optimization / 优化类

- **Big function:** Turns stable repeated workflows into reusable local scripts, references, or assets, combining optimization routes when that saves tokens.
- **Selectable modules (multi-select):** Skill Optimization; Official skill compliance; Local script conversion; Reference extraction; Assets and templates
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`workflow-skill`](./workflow-skill/) · Workflow / 工作流类

- **Big function:** Controls task decomposition, goal checks, routing, iteration, and final evidence, with multi-select routes for mixed Codex requests.
- **Selectable modules (multi-select):** Text and Markdown tasks; Code tasks; Visual and generated artifacts; Global skill edits; Management tasks; Final evidence reports
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.

#### [`management-skill`](./management-skill/) · Management / 管理类

- **Big function:** Routes Codex profile management and global skill GitHub sync, using one or both management routes as required.
- **Selectable modules (multi-select):** Codex Switch; GitHub Sync; Privacy-Safe Management
- **Selection rule:** Use every module that applies to the task; this is not one-of, and unrelated modules should not run.


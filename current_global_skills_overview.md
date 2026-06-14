# Current Codex Skills

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 44, "rankSpacing": 88, "wrappingWidth": 340}}}%%
flowchart LR
  category_Workflow["&emsp;&emsp;&emsp;Workflow / 工作流类&emsp;&emsp;&emsp;"]
  category_Workflow --> skill_workflow_skill["&emsp;&emsp;&emsp;workflow-skill&emsp;&emsp;&emsp;"]
  category_Code["&emsp;&emsp;&emsp;&emsp;Code / 代码类&emsp;&emsp;&emsp;&emsp;"]
  category_Code --> skill_code_skill["&emsp;&emsp;&emsp;&emsp;code-skill&emsp;&emsp;&emsp;&emsp;"]
  category_Optimization["&emsp;&emsp;Optimization / 优化类&emsp;&emsp;"]
  category_Optimization --> skill_optimization_skill["&emsp;&emsp;optimization-skill&emsp;&emsp;"]
  category_Verification["&emsp;&emsp;Verification / 验证类&emsp;&emsp;"]
  category_Verification --> skill_verify_skill["&emsp;&emsp;&emsp;verify-skill&emsp;&emsp;&emsp;"]
  category_Testing["&emsp;&emsp;&emsp;Testing / 测试类&emsp;&emsp;&emsp;"]
  category_Testing --> skill_test_skill["&emsp;&emsp;&emsp;&emsp;test-skill&emsp;&emsp;&emsp;&emsp;"]
  category_Management["&emsp;&emsp;&emsp;Management / 管理类&emsp;&emsp;&emsp;"]
  category_Management --> skill_management_skill["&emsp;&emsp;management-skill&emsp;&emsp;"]
  classDef category fill:#2f2f2f,color:#fff,stroke:#555;
  classDef skill fill:#111,color:#fff,stroke:#eee;
  class category_Workflow,category_Code,category_Optimization,category_Verification,category_Testing,category_Management category;
  class skill_workflow_skill,skill_code_skill,skill_optimization_skill,skill_verify_skill,skill_test_skill,skill_management_skill skill;
```

Generated: 2026-06-14

## Skill Details

### Workflow / 工作流类

#### `workflow-skill`

Controls task decomposition, goal checks, routing, iteration, and final evidence for Codex requests.

- **Task decomposition**: Break the request into ordered task slices before execution.
- **Artifact target map**: Define text, image, code, UI, PDF, skill, GitHub, or management pass targets.
- **Skill routing**: Choose only the relevant production, test, verify, sync, or management route.
- **Code-test-verify spine**: For executable behavior, enforce code-skill -> test-skill -> verify-skill.
- **Completion loop**: Compare evidence against the target map and continue until goals pass or a real blocker appears.
- **Final evidence report**: Keep process detail in the report and keep the final chat concise.

### Code / 代码类

#### `code-skill`

Routes code work to the right coding, prompt, Python, Unity C#, or small-task branch.

- **Prompt generation**: Only for creating, rewriting, or embedding prompts.
- **Coding approach**: Use for assumptions, smallest viable implementation, and surgical edits.
- **Spark small-task routing**: Use only for obvious bounded low-risk code tasks when an allowed route exists.
- **Python rules**: Use for Python modules, scripts, tests, snippets, and Python prompt assignments.
- **Unity C# rules**: Use for Unity MonoBehaviours, ScriptableObjects, managers, and gameplay systems.
- **Real test/report flow**: After code changes, route real executable evidence through test-skill unless testing is explicitly forbidden.

### Optimization / 优化类

#### `optimization-skill`

Turns stable repeated workflows into reusable local scripts, references, or assets when that saves tokens.

- **Official compliance audit**: Check a whole user skill collection against official structure, trigger, reference, and token-use rules.
- **Instruction tightening**: Tighten triggers, workflow wording, guardrails, and duplicated requirements.
- **References extraction**: Move long stable context into references/ when it should be loaded only when needed.
- **Script conversion**: Move repeated deterministic steps into scripts/ when it saves tokens and remains testable.
- **Assets/templates**: Store reusable fixtures, templates, or media in assets/ when they are part of the skill.
- **No-op decision**: Leave the skill unchanged when optimization is not justified.
- **Code-skill gate**: Use code-skill before writing or editing helper code.

### Verification / 验证类

#### `verify-skill`

Checks UI, scripts, generated artifacts, skills, and workflows against the user's requirement.

- **UI verification**: Use Taste Skill plus the local problem index for visual/UI checks.
- **Local script/process verification**: Run local scripts with concrete cache inputs and inspect outputs.
- **Code behavior verification**: Define the behavior that test-skill must prove with real execution.
- **Skill/instruction verification**: Check frontmatter, triggers, references, paths, old names, and route behavior.
- **Generated artifact review**: Open, render, parse, or inspect generated files and reports.
- **Mixed route**: Combine only the relevant verification routes when the task spans artifacts.

### Testing / 测试类

#### `test-skill`

Runs real executable checks and produces evidence-rich PDF reports.

- **Code/API/CLI evidence**: Run real commands, API calls, or scripts and record input, used method, output, and pass reason.
- **UI/browser evidence**: Capture real screenshots, page states, console/runtime evidence, and viewport details.
- **Image evidence**: Use real source/output images and visual artifacts.
- **Document/PDF evidence**: Render, parse, or inspect documents and PDFs with local tools.
- **Comparison/audit reports**: Show before/after, expected/actual, or audit findings with concrete evidence.
- **Evidence contract**: Every passing case needs Input, Used, Output, and Why Pass.

### Management / 管理类

#### `management-skill`

Routes Codex profile management and global skill GitHub sync through the right support skill.

- **codex-switch route**: Use the existing codex-switch skill for local Codex auth profiles, profile inspection, backups, imports, and confirmed account switching.
- **github-sync route**: Use the existing github-sync skill for global skill status, public-safety scan, sync, pull, push, and remote commit verification.
- **Privacy guardrails**: Never expose auth files, tokens, cookies, profile IDs, raw logs, cache files, or secrets.
- **Route selection**: Run only the management route needed by the request; do not run account switching and GitHub sync just because both exist.
- **Evidence**: Record the real local command or tool used, output state, remote hash or profile result, and why it satisfies the request.


## Management Support Skills

These are real mirrored skills used by `management-skill`, but they are not shown as separate primary map rows.

- [`codex-switch`](./codex-switch/): Manages local Codex auth profiles and account switching without exposing private auth data.
- [`github-sync`](./github-sync/): Syncs, commits, and pushes Codex skill changes to the public GitHub mirror with privacy checks.

## Skill List

| Category | Skill | Purpose |
|---|---|---|
| Code | `code-skill` | Unified code skill for all code-related Codex work. Use for writing, editing, refactoring, debugging, reviewing, optimizing, or explaining code; prompt generation and prompt-in-code work; Python modules, scripts, tests, and snippets; Unity C# MonoBehaviours, ScriptableObjects, managers, and gameplay systems; and obvious bounded code tasks that may use Spark when an allowed model route exists. |
| Management | `codex-switch` | Inspect, manage, and switch local Codex auth profiles under `~/.codex`. Use when the user wants local Codex account/profile switching, finding `auth*.json` files, identifying which account each file belongs to, reviewing the latest locally observed Codex usage or rate-limit snapshot for each account, refreshing or backing up a local login, or switching the active profile by copying one saved auth file onto `auth.json` without deleting anything or exposing raw tokens. |
| Management | `github-sync` | Sync, commit, and push Qin's user global Codex skills with the GitHub repository qin-codex-skills. Use when Codex needs to read, use, create, edit, rename, delete, or update global skills under ~/.codex/skills; when global skill changes should be committed and pushed to GitHub; or when local and remote global-skill state must be compared without placing .git metadata inside ~/.codex/skills. Always keep the public mirror safe by excluding caches, generated artifacts, auth files, tokens, secrets, local logs, and other private personal data. |
| Management | `management-skill` | Unified management skill for local Codex account/profile operations and global skill GitHub synchronization. Use when the user asks to manage Codex auth profiles, switch local accounts, inspect profile state, sync global skills, commit or push skill changes, compare local and remote skill state, or run management workflows that should route through codex-switch or github-sync without exposing private data. |
| Optimization | `optimization-skill` | Optimize repetitive Codex skills and fixed workflows into reusable local files, scripts, references, or assets that save tokens and execution time. Use when the user explicitly asks to optimize a skill or repeated process into local code/files; when a skill workflow is stable but too verbose; when repeated test, image, browser, computer-control, report, or generation steps can become deterministic Python scripts; or when Codex notices a highly repeated fixed flow that should be made reusable. Must prepare references first, follow code-skill for all code/script work, and verify the optimized workflow with real execution before finishing. |
| Testing | `test-skill` | Unified testing and report skill. Use when code, UI, scripts, automations, generated assets, or content have been created or changed; when the user asks to test, verify, QA, smoke test, validate, prove, or generate a report; and whenever completed work needs real executable evidence plus a concise visual PDF report. Requires real runnable tests with concrete generated inputs, real inputs/outputs, the exact command/tool used, and a clear pass reason instead of mock-only, signature-only, or pass/OK-only checks. |
| Verification | `verify-skill` | General verification skill for checking whether workflows, local scripts, UI/UX, generated artifacts, skill edits, and process optimizations actually satisfy the user's requirement. Use when Codex is asked to verify, review, audit, validate, inspect quality, confirm a workflow, check UI/visual quality, or validate that an optimized local script/process still works. For UI verification, fetch/read leonxlnx/taste-skill and combine it with the local UI problem index before deciding whether the UI passes. |
| Workflow | `workflow-skill` | Global task workflow controller for Codex requests. Use at the start of any user task that needs decomposition, explicit goals, skill routing, code/script/workflow work, testing, verification, iteration to completion, or a final evidence report. It breaks the request into steps, defines artifact-specific pass criteria, routes code work through code-skill before test-skill and verify-skill, loops until the stated goals pass, and keeps process detail in the report instead of the final chat. |

## Structure

- Code work enters through `code-skill`.
- Repeated fixed workflow optimization enters through `optimization-skill`.
- Verification work enters through `verify-skill`.
- Real tests and report artifacts sit under `test-skill`.
- Auth and GitHub mirror maintenance enter through `management-skill`, which selects `codex-switch` or `github-sync` internally.
- Each skill may contain multiple internal routes; choose only the route needed for the current request instead of running every listed case.

## Current Notes

- The old code skills were merged into `code-skill`.
- The old testing skills were merged into `test-skill`.
- UI review was broadened into `verify-skill`.
- The old image workflow skill was deleted.

# Current Global Codex Skills

Generated: 2026-06-14

## Skill List

| Category | Skill | Purpose |
|---|---|---|
| Code | `code-skill` | Unified code skill for coding approach, Spark routing, prompt generation, Python rules, and Unity C# rules. |
| Generation | `qin-skill-optimization` | Skill or instruction-layer optimization from concrete failure evidence or finalization checks. |
| Verification | `verify-skill` | General verification for workflows, local scripts, artifacts, skill edits, and UI quality using the local UI index plus taste-skill for UI checks. |
| Testing | `test-skill` | Real usage testing with concrete generated inputs plus concise PDF evidence reports. |
| Management | `qin-codex-auth-swithc` | Inspect and switch saved Codex ChatGPT auth profiles under `~/.codex`. |
| Management | `qin-codex-skills-github-sync` | Sync local global Codex skills with the GitHub mirror repository. |

## Mind Map

```mermaid
mindmap
  root((Global Codex Skills))
    Code
      code-skill
        Spark small-task routing
        Coding approach
        Prompt generation
        Python rules
        Unity C# rules
    Generation
      qin-skill-optimization
        Skill cleanup
        Instruction optimization
        Failure-driven tightening
    Verification
      verify-skill
        Workflow verification
        Local script checks
        UI validation
        taste-skill routing
        Problem index
    Testing
      test-skill
        Real small-code tests
        Generated inputs
        PDF evidence report
        Requirement check
    Management
      qin-codex-auth-swithc
        Auth profiles
        Account switching
      qin-codex-skills-github-sync
        Local skill mirror
        GitHub sync
```

## Structure

- Code work enters through `code-skill`.
- UI quality and general verification work enters through `verify-skill`.
- Skill-generation workflows sit under Generation.
- Real tests and report artifacts sit under Testing.
- Auth and GitHub mirror maintenance sit under Management.

## Current Notes

- `qin-destiny` is no longer a global skill; it was moved to `/Users/qin/Documents/FilesManagement/Destiny`.
- `qin-git-push-safety` was deleted.
- The old code skills were merged into `code-skill`.
- The old testing skills were merged into `test-skill`.
- UI review was broadened into `verify-skill`.
- The old image workflow skill was deleted.
- The automatic sync helper still depends on `gh`; SSH-based Git mirror checks were used for current-state confirmation.

---
name: optimization-skill
description: Optimize repetitive Codex skills and fixed workflows into reusable local files, scripts, references, or assets that save tokens and execution time. Use when the user explicitly asks to optimize a skill or repeated process into local code/files; when a skill workflow is stable but too verbose; when repeated test, image, browser, computer-control, report, or generation steps can become deterministic Python scripts; or when Codex notices a highly repeated fixed flow that should be made reusable. Must prepare references first, follow code-skill for all code/script work, and verify the optimized workflow with real execution before finishing.
---

# Optimization Skill

Use this as the optimization skill for turning fixed, repeated Codex workflows into reusable local resources. The main job is to reduce future token use and make repeated work faster without changing the user's intended behavior.

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Do not scatter generated files across the working tree, desktop, home directory, or unrelated folders. Final deliverables should go only to the user-requested path or the active workspace `outputs/` directory.

Reusable resources that are meant to become part of a skill belong inside that target skill folder:

- `scripts/` for deterministic local code or command wrappers
- `references/` for reusable instructions, API notes, schemas, checklists, or long workflow details
- `assets/` for templates, sample files, fixtures, or reusable media

## Trigger

- The user explicitly asks to optimize a skill, fixed process, prompt workflow, or repeated Codex behavior into local files or scripts.
- A workflow repeats often enough that Codex keeps spending tokens on the same deterministic setup, checks, browser steps, image-prep steps, computer-control steps, reports, or test procedures.
- A skill mostly works but contains bulky, repeated, or fragile instructions that could be moved into `scripts/`, `references/`, or `assets/`.
- A local helper script, reference file, fixture, template, or cache-safe workflow would make future execution faster and more reliable.
- A newly edited skill needs an optimization pass to remove duplicated rules, choose what should live in code versus instructions, and verify the resulting workflow.

## Optimization Goal

- Convert repeated deterministic behavior into reusable local Python scripts or other local resources when that saves tokens or execution time.
- Keep reasoning-heavy, variable, or judgment-based work in `SKILL.md`; move stable mechanics into scripts or references.
- Preserve the original workflow contract. Optimization should make the same job faster, clearer, or more reliable, not change what the job means.
- Use the target skill's own folder as the permanent home for reusable files whenever the optimization belongs to that skill.
- Keep task-specific generated inputs, reports, screenshots, previews, and logs in `cache/` or `outputs/`, not inside the reusable skill source.

## Required Code-Skill Gate

Before writing, editing, or moving any helper code, use `code-skill` as the coding contract:

1. Read the target skill, relevant existing scripts, relevant references, and nearby peer skills before coding.
2. Identify the authoritative source paths and expected inputs/outputs. Do not write code from memory or guesses when local references exist.
3. Define the smallest success condition that proves the optimized workflow still does the original job.
4. For Python helpers, follow the Python rules in `code-skill`: simple structure, clear names, no unnecessary abstractions, no unrequested fallbacks, and narrow verification.
5. Keep edits surgical. Do not rewrite an entire skill or create a large framework when one small script or reference file solves the repeated work.

## Reference Preparation

Do this before changing the target skill or writing code:

- Collect the user's concrete complaint, repeated workflow, logs, screenshots, outputs, or examples.
- Read the target `SKILL.md` completely and inspect its `scripts/`, `references/`, and `assets/` folders.
- Read peer skills when the workflow crosses skill boundaries or a shared pattern already exists.
- Read project instructions, API docs, CLI help, local examples, or official docs needed for the script to be correct.
- Write down the real input, expected output, side effects, and files touched by the optimized workflow.

If the references are missing or ambiguous, pause the optimization decision and gather more local evidence. Do not invent a local script interface from thin air.

## Required Workflow

1. Start from the repeated or fixed behavior: what is being done again and again, and why it costs tokens or time.
2. Run `python3 scripts/skill_optimizer.py scan "<skills-root>"` when optimizing a skill collection or when peer skills may already solve the same pattern.
3. Run `python3 scripts/skill_optimizer.py audit "<target-skill-folder>"` before editing a target skill folder.
4. Decide whether the fix belongs in instructions, references, scripts, assets, or a combination:
   - Keep variable judgment in `SKILL.md`.
   - Move long reusable background into `references/`.
   - Move deterministic execution into `scripts/`.
   - Move reusable templates or fixtures into `assets/`.
5. If adding or editing code, apply the `code-skill` workflow before the first code change.
6. Prefer a small local Python script for fixed operations such as repeated testing setup, report manifest creation, screenshot collection, browser smoke flows, image input preparation, file normalization, or skill validation.
7. Add concise usage instructions in `SKILL.md` that point to the local resource instead of repeating the full procedure inline.
8. Keep the script's interface practical: clear arguments, safe defaults, `--help`, and no dependency on hidden local state unless the skill explicitly owns that state.
9. If a workflow needs generated inputs such as images, PDFs, URLs, HTML pages, or sample files, create them in `cache/` during verification instead of committing throwaway generated files into the skill.
10. Run `python3 scripts/skill_optimizer.py verify "<target-skill-folder>"` after editing a skill folder.
11. Run the optimized workflow for real with concrete inputs. Do not stop at syntax checks, import checks, or parameter checks when a real local execution is practical.
12. If the real execution fails, fix the smallest relevant instruction, reference, script, or asset and rerun until it passes or a concrete blocker remains.
13. Report what was optimized, what local files were added or changed, what real test ran, and what remains unverified.

## Good Optimization Targets

- Repeated real-test setup that can become a local runner script.
- Repeated PDF/report manifest generation that can become a helper script or template.
- Repeated image-generation setup, prompt packaging, asset naming, or preview preparation.
- Repeated browser verification flows that can become a Playwright or Browser-control script.
- Repeated computer-control flows where the UI path is stable and permission-safe.
- Repeated skill validation, frontmatter checks, reference checks, or public-safety scans.
- Long copied instructions that are better as a compact `SKILL.md` pointer plus a `references/` file.
- Bulky deterministic command sequences that should become one tested local command.

## Guardrails

- Do not optimize just because a skill exists. Optimize only when the workflow is repeated, fixed, slow, token-heavy, fragile, or explicitly requested.
- Do not move reasoning-heavy judgment into code. Scripts should execute stable mechanics, not guess user intent.
- Do not create untested helper code.
- Do not leave a script that cannot run, cannot show `--help`, or depends on undocumented local files.
- Do not replace real workflow evidence with mocks when a real local test is practical.
- Do not store generated cache files, screenshots, reports, auth files, tokens, logs, or personal data in reusable skill source.
- Do not mix sibling packages, clones, caches, or workspaces because paths look similar. Use the authoritative target path.
- Do not weaken validation just to make an optimization pass.
- Do not duplicate the same rule in `SKILL.md`, `references/`, and scripts. Keep one source of truth.

## Verification

- `scan` is for reading surrounding skills before changing shared patterns.
- `audit` is for deciding whether optimization is needed and where the repeated workflow lives.
- `verify` is required after editing a skill folder. It checks frontmatter, local references, command paths, and helper-script syntax.
- Run `--help` for new or edited scripts.
- Run a real end-to-end or narrow local execution with concrete generated inputs.
- For browser, image, computer-control, PDF, report, and test workflows, use the smallest concrete artifact that proves the optimized path actually works.
- Keep evidence in `cache/` and final reports in `outputs/` when a report is needed.

## Natural-Language Examples

- "This skill repeats the same testing setup every time. Turn it into a local script."
- "This workflow always creates the same report manifest. Optimize it so future runs use a helper."
- "The browser QA flow is stable now. Make it reusable instead of spending tokens describing every click."
- "This image generation process has fixed naming, prompt packaging, and preview steps. Put the repeatable parts into local files."
- "Before we keep using this skill, check whether repeated deterministic parts should become scripts."
- "This helper was added for optimization. Run it with real inputs and make sure it still works."

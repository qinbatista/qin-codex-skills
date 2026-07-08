---
name: optimization-skill
description: "Workflow optimization executor selected by workflow-skill. Use when the user asks to optimize a skill/process, a workflow has repeated at least three times, or a stable reusable process can become scripts, references, prompts, assets, or templates. Preserve behavior and verify same-behavior proof through verify-skill."
---

# Optimization Skill

Use this as the optimization executor selected by `workflow-skill` for turning fixed, repeated Codex workflows into reusable local resources. The main job is to reduce future token use and repeated effort: identify stable repeated flows, move reusable mechanics into the relevant user-owned skill or local helper, tighten prompts, and prove the optimized path still works. Optimization must not change the user's intended behavior.

## Generated File Placement

Put intermediate files, temporary inputs, caches, generated scratch data, logs, previews, and other non-final artifacts in the relevant `cache/` directory. Use the current task or project directory's `cache/` folder for task-specific artifacts, or this skill's `cache/` folder for skill-internal artifacts. Create the folder if needed. Do not scatter generated files across the working tree, desktop, home directory, or unrelated folders. Final deliverables should go only to the user-requested path or the active workspace `outputs/` directory.

Reusable resources that are meant to become part of a skill belong inside that target skill folder:

- `scripts/` for deterministic local code or command wrappers
- `references/` for reusable instructions, API notes, schemas, checklists, or long workflow details
- `assets/` for templates, sample files, fixtures, or reusable media

## Internal Route Selection

This skill supports several optimization routes. Do not optimize every listed workflow type. Select every route that matches the repeated behavior: tighten instructions, move long stable details into `references/`, convert deterministic steps into `scripts/`, add reusable `assets/`, or leave the skill unchanged when optimization is not justified. These routes can be combined when the workflow needs more than one. If code is needed, use `code-skill`; if only wording or references are needed, do not invent a script.

Optimization routes may proceed by using other skills and workflows to do the work: `code-skill` for Python/C# scripts, `verify-skill` for real execution and same-behavior proof, browser/computer-control skills for stable UI flows, and management-skill when a verified global skill change must be synced. This skill coordinates those routes; it does not replace them.

## Trigger

- The user explicitly asks to optimize a skill, fixed process, prompt workflow, or repeated Codex behavior into local files or scripts.
- The same or substantially identical workflow has repeated at least three times, such as repeated image generation, repeated browser steps, repeated Google/Chrome page setup, repeated website interactions, repeated report creation, or repeated verification commands.
- Codex can clearly see a stable deterministic workflow that is likely to be reused many times and would save future token cost as a script, reference, asset, template, or shorter prompt.
- A skill mostly works but contains bulky, repeated, or fragile instructions that could be moved into `scripts/`, `references/`, or `assets/`.
- A local helper script, reference file, fixture, template, or cache-safe workflow would make future execution faster and more reliable.
- A newly edited skill explicitly needs an optimization pass to remove duplicated rules, choose what should live in code versus instructions, and verify the resulting workflow.

## Optimization Goal

- Convert repeated deterministic behavior into reusable local Python scripts or other local resources when that saves tokens or execution time.
- Inspect whether code, workflow steps, prompt wording, references, scripts, assets, or report templates can reduce repeated work.
- Tighten prompts by removing repeated filler, case-by-case clutter, redundant prohibitions, or verbose boilerplate while preserving the output contract.
- Optimize the related skill that owns the repeated task, not this optimization workflow itself, unless the user explicitly asks to improve `optimization-skill`.
- Keep reasoning-heavy, variable, or judgment-based work in `SKILL.md`; move stable mechanics into scripts or references.
- Preserve the original workflow contract. Optimization should make the same job faster, clearer, or more reliable, not change what the job means.
- Use the target skill's own folder as the permanent home for reusable files whenever the optimization belongs to that skill.
- Keep task-specific generated inputs, reports, screenshots, previews, and logs in `cache/` or `outputs/`, not inside the reusable skill source.

## Model And Closeout Rule

Newest/current selected reasoning models are only for deciding whether the optimization gate applies, designing the workflow route, and judging whether verification proves same behavior. All actual optimization implementation is Spark-default execution: code edits, scripts, command-line work, reference updates, prompt/rule text edits, Markdown edits, log/wiki/DailyLog/Obsidian memory updates, and post-pass closeout use `GPT-5.3-Codex-Spark` (`gpt-5.3-codex-spark`) unless the phase requires image reading, comprehensive review, or final pass/fail judgment.

After the optimized path is verified, return the user-facing result immediately. Do not keep the user waiting for secondary records such as DailyLog/wiki/log updates, Obsidian memory pages, Markdown summaries, or optimization notes. Start those in a background/non-blocking route when available; otherwise defer or skip non-required closeout rather than delaying final response. If a higher-priority environment rule requires minimal memory closeout before final, keep it brief.

## Post-Task Optimization Rule

Do not edit skills while an unrelated active task is still trying to reach its user-facing goal. First finish the requested task through its normal workflow, verify it with real evidence, and report the result. After completion, run this skill only if the optimization gate passes: explicit user request, repeated-at-least-three-times workflow, or high-confidence stable future reuse.

When a repeated pattern is obvious after task completion:

1. Identify the owning skill: image generation/editing, browser flow, computer-control flow, testing/reporting, verification, code, management, or another user skill.
2. Summarize the repeated steps as concrete inputs, commands, browser actions, files, outputs, and pass criteria.
3. Decide what belongs in that owning skill: a shorter instruction, a `references/` note, a deterministic `scripts/` helper, or a reusable `assets/` template.
4. Add the optimization to the owning skill only after reading its current files and preparing references.
5. Verify the optimized route with a small real run and compare it with the original behavior so the next similar task is faster without behavior drift.
6. After the optimized route passes, return the result first. Treat logging, wiki updates, DailyLog entries, and other non-user-facing records as background/secondary work.

If the user says "optimize this", "next time faster", "make this repeatable", or has repeated the same image/browser/computer/report/verification flow at least three times, include concrete suggestions for proactive optimization of the user's own relevant skill, then implement them when the request authorizes skill changes.

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
3. Run `python3 scripts/audit_global_skills.py "<skills-root>" --output cache/skill-audit.json` when checking a whole user skill collection against official skill structure, trigger, reference, and token-use rules.
4. Run `python3 scripts/skill_optimizer.py audit "<target-skill-folder>"` before editing a target skill folder.
5. Decide which related skill owns the repeated process and whether the fix belongs in instructions, references, scripts, assets, or a combination:
   - Keep variable judgment in `SKILL.md`.
   - Move long reusable background into `references/`.
   - Move deterministic execution into `scripts/`.
   - Move reusable templates or fixtures into `assets/`.
   - Shorten prompts and instruction text when the same output contract can be stated with fewer tokens.
6. If adding or editing code, apply the `code-skill` workflow before the first code change.
7. Prefer a small local Python script for fixed operations such as repeated testing setup, report manifest creation, screenshot collection, browser smoke flows, image input preparation, file normalization, or skill validation.
8. Add concise usage instructions in `SKILL.md` that point to the local resource instead of repeating the full procedure inline.
9. Keep the script's interface practical: clear arguments, safe defaults, `--help`, and no dependency on hidden local state unless the skill explicitly owns that state.
10. If a workflow needs generated inputs such as images, PDFs, URLs, HTML pages, or sample files, create them in `cache/` during verification instead of committing throwaway generated files into the skill.
11. Run `python3 scripts/skill_optimizer.py verify "<target-skill-folder>"` after editing a skill folder.
12. Run the optimized workflow for real with concrete inputs through `verify-skill`. Do not stop at syntax checks, import checks, or parameter checks when a real local execution is practical.
13. Compare the optimized output to the pre-optimization behavior, baseline, or pass target. Intentional differences are allowed only when the optimization request explicitly included them.
14. If the real execution fails, fix the smallest relevant instruction, reference, script, or asset and rerun until it passes or a concrete blocker remains.
15. Report what was optimized, what local files were added or changed, what real verification ran, how behavior stayed the same, and what remains unverified. Do not delay this report for post-pass logging/wiki/Markdown closeout.

## Good Optimization Targets

- Repeated real-test setup that can become a local runner script.
- Repeated PDF/report manifest generation that can become a helper script or template.
- Repeated prompt boilerplate that can be shortened into a reusable prompt contract or reference.
- Repeated image-generation setup, prompt packaging, asset naming, or preview preparation.
- Repeated image workflows where the same source gathering, prompt structure, output naming, preview, or report steps recur.
- Repeated browser verification flows that can become a Playwright or Browser-control script.
- Repeated Chrome/Google/browser operation flows such as opening the same page, performing the same stable clicks, collecting the same evidence, or exporting the same result.
- Repeated computer-control flows where the UI path is stable and permission-safe.
- Repeated skill validation, frontmatter checks, reference checks, or public-safety scans.
- Long copied instructions that are better as a compact `SKILL.md` pointer plus a `references/` file.
- Bulky deterministic command sequences that should become one tested local command.

## Guardrails

- Do not optimize just because a skill exists or a task was successful. Optimize only when explicitly requested, repeated at least three times, or clearly stable and likely reusable.
- Do not modify skills during the active execution of another task unless that task is itself a skill optimization request. Finish the task first, then optimize as a separate pass.
- Do not optimize `optimization-skill` when the repeated workflow belongs to another skill. Optimize the owning user skill or its helper resources.
- Do not move reasoning-heavy judgment into code. Scripts should execute stable mechanics, not guess user intent.
- Do not create untested helper code.
- Do not shrink prompts so far that required inputs, output contract, safety constraints, or pass criteria become ambiguous.
- Do not leave a script that cannot run, cannot show `--help`, or depends on undocumented local files.
- Do not replace real workflow evidence with mocks when a real local test is practical.
- Do not block the user-facing optimized result on DailyLog, wiki, Obsidian, Markdown, or other secondary post-pass closeout after same-behavior verification has passed.
- Do not store generated cache files, screenshots, reports, auth files, tokens, logs, or personal data in reusable skill source.
- Do not mix sibling packages, clones, caches, or workspaces because paths look similar. Use the authoritative target path.
- Do not weaken validation just to make an optimization pass.
- Do not duplicate the same rule in `SKILL.md`, `references/`, and scripts. Keep one source of truth.

## Verification

- `scan` is for reading surrounding skills before changing shared patterns.
- `audit_global_skills.py` is for checking a full user skill collection against official skill structure, trigger wording, references, and token-use rules.
- `audit` is for deciding whether optimization is needed and where the repeated workflow lives.
- `verify` is required after editing a skill folder. It checks frontmatter, local references, command paths, and helper-script syntax.
- Run `--help` for new or edited scripts.
- Run a real end-to-end or narrow local execution with concrete generated inputs.
- Verify that the optimized result preserves the same behavior, output shape, destination, visual standard, and user-facing effect as the original workflow unless the user explicitly requested a behavior change.
- For browser, image, computer-control, PDF, report, and test workflows, use the smallest concrete artifact that proves the optimized path actually works.
- Keep evidence in `cache/` and final reports in `outputs/` when a report is needed.

## Natural-Language Examples

- "This skill repeats the same testing setup every time. Turn it into a local script."
- "This workflow always creates the same report manifest. Optimize it so future runs use a helper."
- "The browser QA flow is stable now. Make it reusable instead of spending tokens describing every click."
- "This image generation process has fixed naming, prompt packaging, and preview steps. Put the repeatable parts into local files."
- "I need to do this same image/browser/computer-control task again" -> finish the current task, then optimize the owning skill so the repeated setup is faster next time.
- "Before we keep using this skill, check whether repeated deterministic parts should become scripts."
- "This helper was added for optimization. Run it with real inputs and make sure it still works."

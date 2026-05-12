---
name: qin-skill-optimization
description: Optimize an existing Codex skill or prompt-driven instruction layer from concrete failure evidence, pre-use review, or finalization checks. Use when a skill, retry/check prompt, agent instruction block, or other instruction-driven workflow mostly works but should be tightened without changing the underlying job. Scan peer skills first when relevant, merge duplicate requirements into one clear rule, prefer the smallest prompt-first fix when the issue lives in the instruction layer, and verify behavior after the change.
---

# Qin Skill Optimization

Use this skill when a skill or prompt-driven instruction layer should be tightened, not rebuilt from scratch.

## Trigger

- The user wants an existing skill improved from logs, bad output, weak behavior, broken references, or a specific complaint.
- The user wants an agent, retry prompt, check prompt, or other instruction layer tightened from warning logs, screenshots, or output mismatches while the underlying workflow mostly works.
- A skill is about to be used and should be checked first.
- A newly drafted skill should be checked before it is finalized.
- Any skill is created, edited, or updated. Treat this skill as a required finalization pass after the substantive skill change, even when no obvious failure is reported yet.

## Goal

- Read the target skill and nearby peer skills first so the fix matches local patterns.
- Optimize only when there is a real improvement opportunity.
- Prefer the smallest effective fix and keep the skill portable unless it is intentionally project-specific.
- Make skill optimization a standard close-out step for skill work instead of an optional extra.
- Trace the strongest failure evidence to a concrete local source before editing anything.
- When the failure involves wrong files, mixed assets, stale cache, or another source-of-truth problem, check peer skills in the same pipeline for the same package-boundary risk before finishing.
- Prefer the smallest prompt, check, retry, or validation fix when the issue lives in the instruction layer.
- Merge duplicate or overlapping user requirements into one clearer instruction instead of appending more prompt text.
- Shorten prompts, helper code, and workflow wording when the same behavior can be preserved with fewer tokens.
- Verify the original behavior before and after the optimization when practical.
- After every skill update, run a small working test that exercises the updated behavior; if it fails, keep updating and retesting until it passes or a concrete blocker remains.

## Required Workflow

1. Start from the strongest evidence: warning log, bad output, screenshot, missing behavior, wrong trigger, pre-use review, or user complaint.
2. Find the real source before editing anything. Inspect the target skill folder or the nearest prompt, retry, check, or validation block that actually produced the problem.
3. If the target lives inside a skills collection, scan the peer skills first with `python3 scripts/skill_optimizer.py scan "<skills-root>"` or the equivalent absolute path.
4. When the target is a skill folder, audit it with `python3 scripts/skill_optimizer.py audit "<target-skill-folder>"`.
5. For source-of-truth or file-mixing failures, identify the authoritative path and add the boundary rule at the narrowest shared level that prevents the same mistake across peer skills.
6. If the target already has runnable behavior, a helper script, or a reproducible prompt flow, run the narrowest practical baseline verification before editing so the current behavior is anchored.
7. Use the audit result as a gate when editing a skill folder. Optimize only when there are repeated deterministic steps, poor structure, duplicated instructions, prompt or code bloat, broken paths, weak validation, or a small helper bug.
8. Prefer the smallest effective fix. Tighten triggers, workflow steps, guardrails, validation, prompt wording, retry guidance, or helper code before considering larger rewrites.
9. If the issue is in the instruction layer, prefer a prompt-first fix. Update the smallest relevant task, retry, check, or validation prompt instead of rewriting the whole workflow.
10. If the output is already correct but validation says it is wrong, fix the checker or validation instructions before weakening the producing prompt.
11. Merge duplicate or overlapping user requirements into one shorter, clearer rule. Do not keep re-stating the same requirement in different words.
12. When repeated prompt tests fail, rewrite the affected prompt block into fewer accurate rules instead of accumulating example-specific warnings.
13. Keep only reasoning-heavy instructions in `SKILL.md`. Move bulky setup, repeated commands, repeated UI actions, and deterministic checks into the target skill's own `scripts/` folder only when that saves tokens and preserves behavior.
14. Only after prompt or instruction fixes are not enough, make the smallest deterministic code or helper change needed to restore the intended behavior.
15. Keep relative links, bundled resources, and workflow contracts intact unless the user explicitly wants them changed.
16. After any skill-folder edit, run `python3 scripts/skill_optimizer.py verify "<target-skill-folder>"`.
17. Run a small working test for the updated skill behavior: the same prompt, the same failing artifact, the helper script with `--help`, a dry run, a targeted assertion, or the narrowest real execution that proves the optimized target still does the original job.
18. If that small working test fails, keep editing the smallest relevant prompt, checker, workflow step, or helper code and rerun the test until it passes. Stop only when the test passes or when a concrete blocker prevents validation.
19. When the task was to create or update a skill, do not finish after the content edit alone. Complete this audit, verify pass, and small working test before claiming the skill work is done, and report whether optimization changed anything.

## What To Optimize

- Weak or overly broad trigger metadata
- Vague workflow steps or missing guardrails
- Duplicate or overlapping requirements that should become one clear instruction
- Bad or contradictory task, retry, check, or validation prompts
- False validation where the output is right but the checker is wrong
- Repeated deterministic UI or shell steps that belong in scripts
- Long sections that can become short summaries plus a referenced helper
- Prompt wording or helper code that can be made shorter without losing meaning
- Broken local references, script paths, or helper syntax
- User-added requirements that were appended instead of reorganized

## Guardrails

- Do not optimize a skill just because it exists.
- Do not rewrite the whole skill unless the user asks or the structure is fundamentally broken.
- Do not keep repo-only assumptions in a shared skill unless the skill is intentionally project-specific.
- Do not silence a warning or mismatch just to make the logs quieter.
- Do not remove real behavior just to make the skill shorter.
- Do not add filler just to make the skill longer.
- Do not duplicate the same instructions across `SKILL.md`, scripts, and references.
- Do not break relative links or bundled-resource paths when moving content out of `SKILL.md`.
- Do not keep a script change that was not validated against the original behavior when a practical check exists.
- Do not let a skill use files from another package, cache, clone, or workspace unless the user explicitly names that source and the skill records it as an input.

## Verification

- `scan` is for reading the surrounding skills before changing anything.
- `audit` is for deciding whether optimization is actually needed.
- `verify` is required before finishing. It checks frontmatter, local references, command paths, and helper-script syntax.
- Run a baseline check before editing when the skill already has a runnable path or reproducible prompt behavior.
- When the target is a prompt-driven workflow instead of a skill folder, verify with the narrowest reproducible prompt, screenshot review, or failing artifact you can rerun locally.
- If the target skill has important runtime behavior, run its own script validation after `verify`.
- Every skill update needs a small working test after the edit. Prefer the cheapest real check that exercises the changed behavior, then iterate on failure instead of reporting a known-broken update as done.
- Report whether optimization was needed, what changed, what was verified before the edit, what was verified after the edit, and any remaining risk.

## Natural-Language Examples

- "This skill mostly works, but its trigger fires too often. Tighten it."
- "We are about to use this skill. Audit it first, then optimize only if it is worth it."
- "This new skill is drafted. Check whether it needs cleanup before we finalize it."
- "This helper path looks broken. Find the real source and fix the smallest thing that makes it work."
- "These requirements are repeated in three places. Summarize them into one clear rule and keep the behavior the same."
- "This check prompt keeps flagging good output as wrong. Trace it and tighten the instruction layer first."
- "The retry prompt keeps reinforcing the wrong behavior. Fix the smallest prompt or validation block that explains the failure."

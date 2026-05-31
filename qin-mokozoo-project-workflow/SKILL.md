---
name: qin-mokozoo-project-workflow
description: Shared workflow rules for MokoZoo and MokoWorld repositories. Use for any task in repos, paths, branches, deployments, assets, websites, apps, or files whose names include MokoZoo, MOKOZOO, Mokozoo, MokoWorld, or MokoWorld.AI, including `Docker-Mokozoo` and `MokoWorld.AI`; before updates, check applicable global skills and any MokoZoo-related global skills such as the image workflow, then apply the relevant ones.
---

# Qin Mokozoo Project Workflow

## Overview

MokoZoo and MokoWorld repositories share project workflow rules. Use this skill as the first project-family routing step before making code, website, asset, content, deployment, or documentation changes in those repositories.

## Trigger

Use this skill when the current repository, path, task, branch, deployment, asset, or user request mentions MokoZoo, MOKOZOO, Mokozoo, MokoWorld, MokoWorld.AI, or Docker-Mokozoo.

## Workflow

1. Identify the exact project root and source of truth before editing. Do not mix assets or code between sibling MokoZoo/MokoWorld checkouts unless the user explicitly names both paths.
2. Search for repo-local instructions such as `AGENTS.md`, design docs, deployment config, or README guidance in the target repo and parent project folder.
3. Check the available global skills metadata and read the global skills that match the task before editing. At minimum, use:
   - `qin-karpathy-guidelines` for non-trivial code, refactor, debugging, review, or implementation work.
   - `qin-done-means-tested` before claiming completion after any file, code, site, script, config, asset, or content update.
   - `qin-image-editing-workflow` for any image generation, image edit, hero/product/fav icon asset, screenshot replacement, or bitmap asset change.
   - `qin-ui-review` for UI, layout, visual polish, browser QA, responsive behavior, or website/app UX work.
   - `qin-prompt-creating`, `qin-python-code-checker`, security, document, spreadsheet, presentation, cloud, GitHub, Vercel, Supabase, Stripe, or other global/plugin skills when the task matches their descriptions.
4. Search global skills for MokoZoo/MokoWorld references when the task could overlap existing project-family rules:
   `rg -n "Moko|MOKO|MokoZoo|MOKOZOO|MokoWorld|mokozoo|mokoworld" ~/.codex/skills ~/.agents/skills`
5. Keep changes surgical and aligned with the current repo. For websites, preserve existing design language unless the user asks for redesign.
6. Before final response, follow `qin-done-means-tested` for the relevant verification path.
7. If a global skill sync/publish workflow applies and is blocked, continue only with local changes when appropriate and report the exact blocker.

## Image Assets

For MokoZoo/MokoWorld image assets, use `qin-image-editing-workflow` first. Do not directly generate, edit, composite, or replace final bitmap assets in a destination repo unless the user explicitly asks for a deterministic local file operation or you are installing an already accepted final asset.

## Guardrails

- Do not read every global skill. Read the global skills whose metadata matches the current task, plus any MokoZoo/MokoWorld-related skills found by search.
- Do not let this skill override a tighter repo-local instruction, system/developer instruction, or newer user instruction.
- Do not create helper scripts for this workflow unless repeated MokoZoo-specific automation becomes necessary.
- Do not claim an update is complete until the relevant global verification skill has been followed.

## Examples

- Update `MokoWorld.AI` website security: use this skill, then `qin-karpathy-guidelines`, the relevant security workflow, and `qin-done-means-tested`.
- Change MokoZoo hero artwork: use this skill, then `qin-image-editing-workflow`, then website/UI verification.
- Polish a MokoWorld page layout: use this skill, then `qin-ui-review`, frontend/browser testing guidance, and final verification.

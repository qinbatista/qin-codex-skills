---
name: qin-sync-figma-ui
description: Use when Qin says "sync figma", "sync UI to Figma", "update Figma from current website", "publish the Figma UI baseline", or asks to refresh Mokozoo Figma boards from the current Docker-Mokozoo code. Runs the local fast screenshot-to-Figma workflow, preserves version history, publishes from the generated queue instead of reading Figma for structure, and verifies professional layer names, IDs, versions, and selectable image layers.
---

# Qin Sync Figma UI

## Purpose

Sync the current Mokozoo website UI into Figma as managed, versioned image layers. The website render and local JSON manifests are the source of truth; Figma is only the publish target.

## Trigger

Use this skill when Qin says `sync figma`, `sync UI to Figma`, `update Figma from current website`, `publish the Figma UI baseline`, or asks to refresh Mokozoo Figma boards from current code.

## Scope

This skill is for publishing rendered Mokozoo UI screenshots and section captures into Figma. It is not for designing new UI from scratch, replacing website code from Figma, or using Figma as the source of page structure unless Qin explicitly asks for that separate workflow.

## Hard Rules

- Do not create one giant combined screenshot or a generic `clipboard 1` layer.
- Do not read Figma to infer page structure. Use `figma-publish-queue.json`.
- Every Figma board image must be a separate selectable image layer.
- Every published layer must use `figmaLayerName` from the queue.
- Layer names must be professional and include identity plus version, e.g. `MZ UI - 01 Home - Page Board - page-479e2159dd`.
- Every final response must report `versionId`, `baselineHash`, history path, publish queue path, Figma URL, layer count, and `remainingClipboard`.
- If paste/upload/rename fails, do not claim sync is complete. Report the blocker and leave the local versioned package ready.

## Guardrails

- Keep the repo on the current branch and preserve unrelated dirty files.
- Treat `figma-publish-queue.json` as the publish contract. Do not invent names, IDs, order, or coordinates in the Figma step.
- Prefer a no-change local sync check before republishing the same UI; this keeps the workflow fast and avoids reading Figma every time.
- If the website UI changed, archive the new version locally before publishing to Figma.
- Keep boards manageable: page boards are top-level selectable images; section images are optional additional selectable layers only when Qin asks for section-level management.

## Required Workflow

1. Work in `C:\Users\qinba\Documents\Docker-Mokozoo` unless the user explicitly names another repo.
2. Respect the repo `AGENTS.md` workflow. Preserve unrelated dirty files.
3. Run the fast local sync:

   ```powershell
   npm run figma:sync-ui
   ```

   For a single page:

   ```powershell
   npm run figma:sync-ui -- --page home
   ```

4. Read these generated files:

   - `data/figma-ui-baselines/current-site-latest/manifest.json`
   - `data/figma-ui-baselines/current-site-latest/figma-publish-queue.json`
   - `data/figma-ui-baselines/ui-history.json`

5. Publish to Figma from `figma-publish-queue.json`, not from memory:

   - Paste or replace each `image` at its `x` and `y` coordinate.
   - Rename the selected Figma image layer to `figmaLayerName`.
   - Keep each board as its own selectable image node.
   - If the user asks for section-level Figma management, publish section images as additional individual image layers using names like `MZ UI - 01 Home - Section 02 New Arrivals - page-...`.

6. Verify Figma after publishing:

   - Select the synced layers.
   - Confirm selected image-layer count equals queue item count.
   - Confirm no layer name starts with `clipboard`.
   - Confirm layer names match queue `figmaLayerName`.
   - Capture a screenshot when practical.

7. Run a quick no-change check when practical:

   ```powershell
   npm run figma:sync-ui -- --page home
   ```

   A healthy no-change check keeps the same `versionId` and reports `changed=false` for that page.

## Version Contract

The current baseline lives at:

```text
data/figma-ui-baselines/current-site-latest/
```

When rendered UI changes, the sync script archives a version at:

```text
data/figma-ui-baselines/ui-history/<versionId>/
```

Use these fields in reports and validation:

- `versionId`: full baseline version, e.g. `ui-20260531T205848Z-5cae933f`
- `baselineHash`: full-site rendered UI hash
- `pageVersionId`: page rendered UI version, e.g. `page-479e2159dd`
- `figmaLayerName`: authoritative Figma layer name
- `changed`: whether the page changed versus the previous local sync

## Examples

User says: `sync figma`

- Run `npm run figma:sync-ui`.
- Publish all queue items as separate selectable Figma image layers.
- Rename every layer to names like `MZ UI - 01 Home - Page Board - page-479e2159dd`.
- Report the version, queue, Figma URL, selected layer count, and `remainingClipboard`.

User says: `sync figma home only`

- Run `npm run figma:sync-ui -- --page home`.
- Publish or rename only the Home queue item.
- Confirm the Home layer name includes its current `pageVersionId`.

User says: `sync figma with sections`

- Publish page boards first.
- Then publish section screenshots as additional separate image layers with section-specific professional names.
- Verify both page board count and section image count.

## Final Response Shape

Keep the final concise, but include:

- Figma URL
- `versionId` and `baselineHash`
- history archive path
- publish queue path
- what was synced or if no UI changed
- verification result: queue item count, selected layer count, `remainingClipboard`
- any blockers or files intentionally not touched

---
name: qin-image-editing-workflow
description: Global image workflow rule. Use whenever a task needs to edit, generate, composite, regenerate, replace content inside, or otherwise modify an image, and whenever a repo or user rule says image-related work must route through the image editor workflow.
---

# Qin Image Editing Workflow

## Trigger

Use this skill for image generation, image editing, compositing, retouching, cropping, upscaling, background replacement, logo placement, asset replacement, or any other task where the final deliverable is an image asset.

Also use this skill when a project-local `AGENTS.md` or user instruction says image-related work must use the image editor workflow, even if the visible request is phrased as updating a website image, screenshot reference, asset file, favicon, hero artwork, product image, or image path.

## Required Editor

When this skill applies, do not hand-roll the visual edit with ad hoc Python/PIL/canvas/compositing scripts as the primary workflow.

Use this image-editing project skill first:

`/Users/qin/QinProject/PythonProject/Agent-ImageEdtior/skills/image-edit/SKILL.md`

For `/Users/qin/QinProject/DockerProject/Docker-Mokozoo`, this workflow is mandatory for any image-related task unless the user explicitly asks for a deterministic non-AI file operation.

## Workflow

1. Read the Agent-ImageEdtior skill before editing the image.
2. Put task sources, references, guide images, attempts, reviews, and accepted finals under:
   `/Users/qin/QinProject/PythonProject/Agent-ImageEdtior/assets/<timestamp-task>/`
3. Use the skill's API-backed workflow when `OPENAI_API_KEY` is available.
4. If the API path is blocked and the task still needs ChatGPT/OpenAI image editing, use the skill's local Chrome/OpenAI workflow path.
5. Promote only a reviewed/accepted final image from that workflow back into the destination project.
6. Use local scripts only for supporting actions such as copying inputs, preparing masks/guides, checking dimensions, comparing screenshots, or installing the accepted final into the target repo.

## Guardrails

Do not create the final edited image by manually compositing or retouching source images yourself unless the user explicitly asks for a manual/local deterministic image operation.

Do not bypass Agent-ImageEdtior for Mokozoo website image assets by directly generating, editing, or compositing final images in the destination repo.

## Examples

- Replace a shirt logo in a bear photo: use Agent-ImageEdtior, then install the accepted final.
- Update a Mokozoo hero image, favicon, product photo, or image reference that requires a changed bitmap: use Agent-ImageEdtior for the image asset first.
- Copy an already accepted final into the website and update HTML/CSS/JS paths: local file operations are allowed as support work.

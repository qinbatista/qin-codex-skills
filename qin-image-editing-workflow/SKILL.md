---
name: qin-image-editing-workflow
description: Global image workflow rule. Use whenever a task needs to edit, generate, composite, regenerate, replace content inside, or otherwise modify an image, and whenever a repo or user rule says image-related work must route through the image editor workflow.
---

# Qin Image Editing Workflow

## Trigger

Use this skill for image generation, image editing, compositing, retouching, cropping, upscaling, background replacement, logo placement, asset replacement, or any other task where the final deliverable is an image asset.

Also use this skill when a project-local `AGENTS.md` or user instruction says image-related work must use the image editor workflow, even if the visible request is phrased as updating a website image, screenshot reference, asset file, favicon, hero artwork, product image, or image path.

## Required Editor

When this skill applies, do not hand-roll the visual edit with ad hoc Python/PIL/canvas/compositing scripts.

Every actual image edit, no matter how small or complex, must go through the selected ChatGPT/OpenAI image-edit provider. Never create a final or candidate edited image by local compositing, retouching, inpainting, pixel moving, PIL/OpenCV/canvas work, or other deterministic local image manipulation.

Use this image-editing project skill first:

`/Users/qin/QinProject/PythonProject/Agent-ImageEdtior/skills/image-edit/SKILL.md`

For MokoZoo and MokoWorld website repositories, including `/Users/qin/QinProject/DockerProject/Docker-Mokozoo` and `C:\Users\qinba\Documents\MokoWorld\MokoWorld.AI`, this workflow is mandatory for any image-related task unless the user explicitly asks for a deterministic non-AI file operation.

## Workflow

1. Read the Agent-ImageEdtior skill before editing the image.
2. Put task sources, references, guide images, attempts, reviews, and accepted finals under:
   `/Users/qin/QinProject/PythonProject/Agent-ImageEdtior/assets/<timestamp-task>/`
3. Follow the Agent-ImageEdtior skill's provider rule. For this user's normal user-facing image edits, use the Chrome/ChatGPT provider path by OS; use API-backed generation only for dry-runs, diagnostics, or when the user explicitly asks for API/non-Chrome output.
4. If the selected Chrome/ChatGPT path is blocked, report the exact blocker instead of silently switching providers or submitting a description-only prompt.
5. Promote only a reviewed/accepted final image from that workflow back into the destination project.
6. Use local scripts only for non-editing support actions such as copying inputs, preparing masks/guides for ChatGPT, checking dimensions, comparing screenshots, writing manifests/review JSON, or installing the accepted ChatGPT final into the target repo.

## Guardrails

Do not create any final or candidate edited image by manually compositing, retouching, inpainting, moving pixels, or otherwise changing image content locally. If ChatGPT/Chrome is blocked, report the blocker and stop instead of making a local fallback.

Do not bypass Agent-ImageEdtior for Mokozoo website image assets by directly generating, editing, or compositing final images in the destination repo.

## Examples

- Replace a shirt logo in a bear photo: use Agent-ImageEdtior, then install the accepted final.
- Update a Mokozoo hero image, favicon, product photo, or image reference that requires a changed bitmap: use Agent-ImageEdtior for the image asset first.
- Copy an already accepted final into the website and update HTML/CSS/JS paths: local file operations are allowed as support work.

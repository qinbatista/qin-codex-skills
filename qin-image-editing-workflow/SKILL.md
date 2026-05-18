---
name: qin-image-editing-workflow
description: Global image-editing workflow rule. Use whenever a task needs to edit, composite, regenerate, replace content inside, or otherwise modify an existing image.
---

# Qin Image Editing Workflow

When a user asks to edit an existing image, do not hand-roll the visual edit with ad hoc Python/PIL/canvas/compositing scripts as the primary workflow.

Use this image-editing project skill first:

`/Users/qin/QinProject/PythonProject/Agent-ImageEdtior/skills/image-edit/SKILL.md`

## Workflow

1. Read the Agent-ImageEdtior skill before editing the image.
2. Put task sources, references, guide images, attempts, reviews, and accepted finals under:
   `/Users/qin/QinProject/PythonProject/Agent-ImageEdtior/assets/<timestamp-task>/`
3. Use the skill's API-backed workflow when `OPENAI_API_KEY` is available.
4. If the API path is blocked and the task still needs ChatGPT/OpenAI image editing, use the skill's local Chrome/OpenAI workflow path.
5. Promote only a reviewed/accepted final image from that workflow back into the destination project.
6. Use local scripts only for supporting actions such as copying inputs, preparing masks/guides, checking dimensions, or installing the accepted final into the target repo.

## Guardrail

Do not create the final edited image by manually compositing or retouching source images yourself unless the user explicitly asks for a manual/local deterministic image operation.

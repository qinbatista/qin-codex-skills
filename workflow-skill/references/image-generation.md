# Internal Image Generation Route

Use this route inside `workflow-skill` for visual or image-related tasks that need, lack, or would materially improve from a generated ChatGPT image/reference before implementation. This is not a separate top-level global skill.

## Image Contract

Before asking ChatGPT for an image, identify the image's job:

- `asset`: isolated reusable object, sprite, icon, texture, map, mask, or game component.
- `concept`: opaque scene, mood, layout, map overview, design direction, or visual target.
- `sketch`: rough planning image, pose reference, storyboard, wire idea, or composition draft.
- `reference`: style, material, lighting, composition, or source image used to guide later work.
- `final visual`: user-facing image that should be used directly or closely matched.

Record the contract before generation:

- transparency requirement: real alpha PNG for cutout assets, or opaque canvas for concepts/panels;
- source/reference usage: original/source image, style reference, content/layout reference, dual reference, or no reference;
- required size, aspect ratio, platform, project style, and final use;
- what later work must stay consistent with the generated image.

If the user context already answers these points, infer them and proceed without asking.

## Chrome And Login Rule

Use the user's existing Chrome/ChatGPT session. Do not hard-code personal Chrome profiles, account emails, cookies, tokens, local profile folders, or `--profile-directory` values.

- Current Chrome/ChatGPT generation is supported only on macOS. Windows support must be tested and added separately.
- If multiple usable Chrome profiles or browser contexts are visible, use the first usable signed-in ChatGPT session by default.
- Do not automate login, enter passwords, copy cookies, or expose session data.
- If ChatGPT is not logged in, CDP/Chrome is unavailable, the page is blocked by a challenge, or image generation is unavailable, skip only image generation, continue all remaining task work that does not require the generated image, and record the blocker.
- At final handoff, tell the user ChatGPT login is required before image generation can continue. Include the skipped image type and why it was needed.

## Workflow

1. Classify each requested visual as asset, concept, sketch, reference, or final visual.
2. Build the provider prompt from the image contract, project style rules, source/reference paths, and visual acceptance criteria.
3. On macOS, use ChatGPT in Chrome only when a usable signed-in session is already available or a project-approved runner reports it is ready.
4. Save generated images in the task or project output package, not in `~/Downloads` or random cache locations.
5. After saving, run provider cleanup by default: hide/archive the generated ChatGPT conversation, remove image-generation recent records, clear local recent-image cache for the generated item, and leave the active ChatGPT tab on a non-conversation page. Treat cleanup failure as a warning that must be reported.
6. Inspect the saved image before using it: subject, role, composition, real alpha when required, no fake checkerboard/panel, no stale page asset, no UI screenshot, no unwanted text, and no mismatch with the requested artifact type.
7. Continue the user's main task using the accepted generated image as the visual target/reference.
8. In the final response, state which images were generated or skipped, where accepted images are saved, how cleanup ended, and how the final result matches or differs from the generated visual target.

## Project Handoff

Project skills own project-specific art direction, naming, import, postprocessing, Unity setup, and QA. This route owns only the reusable Chrome/ChatGPT behavior.

- Unity/game projects keep Unity import, sprite scale, HDR/emission, ECS, animation, shader, and asset-folder rules in their own skills.
- Frontend/UI work keeps implementation and browser QA in frontend/testing skills, but uses this route for ChatGPT-generated visual references or image assets.
- Documents/reports/slides keep document rendering rules in their own skills, but use this route when a generated visual belongs inside the artifact.
- For ThisIsMyOregon, use the local `Image-generate-artwork` skill for prompt profiles, art direction, AIArtworkAssets package layout, and Unity handoff. Its Chrome/ChatGPT execution layer must follow this route's no-personal-profile, first-usable-session, no-login-skip, cleanup, and final-report rules.

## Verification

Route final checks through `verify-skill`.

- Verify the actual saved PNG/JPG, not only the provider response.
- Verify cleanup evidence when Chrome/ChatGPT generated the image: backend image recent count should be removed or empty, the generated conversation should be archived/hidden, local recent-image cache should not keep the generated item, and the active page should not remain on the generated conversation.
- For transparent assets, inspect the alpha channel and reject opaque panels, fake checkerboards, screenshots, and white/gray rectangular backgrounds.
- For concepts and scenes, use the visual brief and artifact type rather than generic web-design taste.
- For games, judge gameplay readability, sprite/component reuse, scale, silhouette, motion, and Unity use where relevant.
- For documents/reports/slides, judge layout, readability, image fit, cropping, and whether the visual supports the document.

## Guardrails

- Do not use Codex built-in `image_gen` when the user or project explicitly requires ChatGPT through Chrome.
- Do not silently replace blocked ChatGPT generation with another provider unless the user explicitly allows that fallback.
- Do not present a bad generated image as final.
- Do not leave generated images in `~/Downloads`.
- Do not add project-specific art direction to this global route; put that in the owning project skill.

---
name: unity-2d-shader-graph
description: Build, revise, and verify animated Unity 2D Shader Graph effects, especially SpriteRenderer/URP 2D shaders using Shader Graph Custom Function HLSL, generated textures, materials, layer breakdown previews, animated GIF checks, and shader GIF galleries. Use when Codex needs to create or fix Unity 2D water, waterfall, fire, magic, sprite VFX, shadergraph, .hlsl, .mat, texture-driven animated shader assets, or list/refresh shader preview GIF catalogs.
---

# Unity 2D Shader Graph

Use this skill for Unity 2D shader effects where the deliverable must be an actual animated shader, not only a rendered picture.

## Non-Static Shader Rule

- Do not leave any visible shader contribution static. If it is visible in the final shader, it must be animated by time-driven UVs, procedural time terms, animated blending, vertex data, or another changing parameter.
- Do not use a static source image, reference crop, rendered picture, or RGB texture as a front layer, base layer, or final color plate. If a reference texture is needed, use it only as an input to animated sampling, masking, color cues, or generated loopable textures.
- If a still-looking layer appears in a preview, stop and fix the shader immediately before delivering.
- Do not call post-capture PNG compositing, pixel stretching, or `ReadPixels` image editing a direct shader result. A visible layer counts as shader output only if it exists in the Unity scene/material/render path before `Camera.Render`/`ReadPixels`, then is verified from that runtime render.

## Required Workflow

1. Inspect the asset folder, shader graph, Custom Function HLSL, material properties, texture files, and README before editing.
2. Build the effect as a shader system: Shader Graph or file-linked Custom Function HLSL, material values, textures, previews, and validation artifacts.
3. Show construction layers before the final: body/mass, moving detail, entry/source, impact/foam, and mist/spray where relevant.
4. Generate a final still frame and animated GIF from actual time-based shader logic or a faithful CPU preview.
5. Measure GIF motion. Reject outputs that read as static, only flicker, move in the wrong direction, or animate only through artifacts.
6. Run Unity batch import or actual Unity material render when possible.
7. Before replying, compare the intended GIF/effect against the actual Unity material/runtime render yourself. If the visual effect is not substantially the same, keep fixing; do not stop at a plan, explanation, or metric pass.

## AIShaderGraphic2D Shader GIF Gallery

- For AIShaderGraphic2D requests such as "所有 shader 的 GIF", "shader gif大集合", or a current shader preview index, use the project-local gallery script:
  `/Users/qin/Documents/YofaGames/AIShaderGraphic2D/plugins/ai-shader-graphic2d-plugin/skills/unity-2d-shader-graph/scripts/build_shader_gif_gallery.py`.
- The source of truth is `Assets/shader/**/*.gif`; keep GIFs beside their shader folders and do not recreate AIShaderGraphic2D `Assets/VFX`, `Assets/VFXGallery`, VFX editor scripts, or the retired `vfx-gif-gallery` skill unless the user explicitly changes the shader-only convention.
- The viewable gallery is `/Users/qin/Documents/YofaGames/AIShaderGraphic2D/Assets/ShaderGallery/index.html`; supporting files are `shader_gif_manifest.json`, `SHADER_GIF_GALLERY.md`, and `shader_gif_contact_sheet.png` in the same folder.
- The current skill references are `references/shader-gif-gallery.md` and `references/shader-gif-manifest.json`; refresh them with the script when shader GIFs are added, removed, or renamed.

## ThisIsMyOregon Image Source Rule

- Treat `AIShaderGraphic2D` as a support project for `/Users/qin/Documents/YofaGames/ThisIsMyOregon` shader work.
- Before generating any reference image, ChatGPT/GPT image, concept frame, GIF visual target, or texture source for an `AIShaderGraphic2D` shader, read and use the ThisIsMyOregon project skills under `/Users/qin/Documents/YofaGames/ThisIsMyOregon/plugins/timo-plugin/skills`, especially `Image-generate-artwork/SKILL.md`; use `Image-Concept-artwork/SKILL.md` too when scene/concept/reference layout matters.
- This is a user-approved exception to the normal TIMO-skill-only-for-TIMO rule: use TIMO skills to source style, prompt rules, provider route, and visual references for `AIShaderGraphic2D` shader image generation. Keep shader artifacts under the `AIShaderGraphic2D` effect folder unless a TIMO script owns an intermediate provider package.
- Match TIMO's current art direction for generated shader references: non-pixel painterly 2D side-scroller, 2.5D depth when scene-like, muted low-to-medium saturation, diffuse hand-painted local color, soft brush detail, readable dark midtones and silhouettes, restrained glow only. Avoid photorealism, PBR/3D renders, glossy highlights, heavy bloom, rim light, cinematic overlighting, vector-flat sticker art, or a self-invented standalone style.
- For Chrome/ChatGPT image generation in this shader workflow, follow the TIMO `Image-generate-artwork` plus `chrome-chatgpt-skill` provider route when practical. Do not use a built-in image generator or ad hoc provider path for TIMO-style shader reference images unless the user explicitly overrides it.
- If the TIMO skill files or curated style/reference folder cannot be read, state the blocker and do not proceed as if the style source was checked.

## New vs Revision Routing

Use two different workflows depending on whether the user is asking for a new shader or a correction.

### New Shader

1. Generate the intended visual effect first, preferably through ChatGPT/image generation when the user asks for a visual target.
2. Turn that effect into a GIF or animated effect preview that shows the desired timing, motion direction, and layer construction.
3. Only after the effect GIF is accepted or clearly usable, build the concrete Unity Shader Graph/HLSL/material/textures.
4. Capture an actual Unity material/runtime render and compare it against the effect GIF. Label CPU/effect previews separately from Unity renders.

### Revision Diagnosis

- If the user says the result is ugly, fake, unlike the requested style, not vivid, or visually wrong, classify it as an effect-design/GIF problem. Regenerate or revise the effect image/GIF first, then rebuild the Unity shader from that corrected target.
- If the user says the GIF looks right but the Unity result differs, classify it as a Unity code/material/import problem. Do not regenerate the concept. Fix Shader Graph, HLSL, material values, texture import settings, UV animation, render capture, or assigned textures until the actual Unity render matches the GIF.
- If the user's current complaint is specifically that the Unity result does not match the GIF, treat the revision as unfinished until a side-by-side visual review shows the runtime render is substantially the same as the GIF.
- If the user reports wrong direction, static areas, or mismatch between preview and runtime, state the classification explicitly before editing, then verify the corrected path with an actual Unity render whenever possible.
- Never answer as if a CPU preview is the final shader when the user is asking about the real Unity result.

## Self-Verification Loop

- Always inspect the final visual comparison before final response: intended effect GIF/frame versus actual Unity runtime GIF/frame.
- Compare the effect, not only file existence or shader compile status. Check silhouette, color, brightness, edge softness, motion direction, motion speed, foam/impact behavior, and whether static-looking regions remain.
- If the effect GIF and Unity runtime render differ greatly, treat the task as unfinished. Continue editing Unity HLSL, Shader Graph, material values, texture assignments/import settings, demo scene/prefab, or capture setup until the runtime render matches.
- Passing motion numbers is not enough. A result can pass frame-diff/direction checks and still fail if it looks visually different from the accepted GIF or target.
- Prefer a side-by-side comparison artifact such as `*_TargetVsUnity.png` or `*_LayerReview.png` and inspect it before replying.
- If the GIF shown to the user is supposed to represent the final shader, make it come from the Unity runtime render or explicitly label it as a non-final effect preview.

## Final Output Contract

- For every shader creation or shader revision final response, always display all four artifacts inline: the ChatGPT/reference image, the animated GIF preview, the separated/layer breakdown image, and the Unity runtime effect.
- For animated shaders, the Unity runtime effect must be animated too: display a Unity runtime GIF or video. A still Unity screenshot may be shown only as an extra comparison artifact, never as the required Unity effect output.
- Do not replace this with text-only paths. Use image/GIF embeds so the user can visually compare them immediately.
- If one of the four required artifacts cannot be produced, keep working or clearly state the blocker and do not present the shader as finished.
- When the final GIF is intended to represent the Unity shader, use the Unity runtime GIF as the displayed GIF or state explicitly that the GIF is only a concept preview.

## Waterfall Rules

- Treat waterfalls as a continuous free-falling water sheet, not rain.
- Keep the main body as a broad connected mass. Do not make the body from isolated thin vertical lines.
- Use loopable downward detail textures for moving whitewater. In Unity UV convention, `UV.y = 1` is the top of the sprite; sampling `frac(uv.y + time * speed)` moves texture features downward on screen.
- Measure waterfall GIF direction, not only frame difference. Positive downward vertical shift must dominate adjacent frames; an average shift near zero or upward is a failed waterfall animation even when generic frame-diff motion passes.
- Do not use random bottom dots for impact. Use connected whitewater, mist, and soft foam bands.
- Avoid horizontal jumping strips at the top. The top inlet should read as a broken falling sheet connected to the waterfall.

## Ocean Shore Wave Rules

- Do not assume a single ocean camera. Preserve the user's wording about perspective before generating the reference or shader.
- If the user says the ocean is "not that flat" and wants the camera facing forward, build front-facing surf rows with larger foreground wave faces, smaller receding rows, and visible wave volume. Do not deliver a flat top-down map, a pure horizontal stripe texture, or a full horizon-only scene.
- If the user says the beach is angled and only partially visible, keep the sand as a partial diagonal wedge or edge, not a full vertical shoreline strip.
- If the user says the player can walk up to or onto the ocean edge, lock the reference and mask to a playable side-scroller ground/foot baseline first. The sea surface must meet the same walkable ground plane as the character, with low readable wave height and no steep diagonal water ramp, top-down shoreline, or wave wall that would make the character unable to approach it.
- For side-scroller sea-level shader targets, do not accept a pretty coastal landscape, distant ocean horizon, or broad scenic water painting as the concept image. The reference must read as a gameplay-plane water strip or surface in the lower band that can become a shader mask; reject concept images where the water composition is the main landscape instead of the shader target.
- If the user asks for a slightly oblique sea-level side-scroller view, do not collapse it into a pure side-on horizontal strip. The target should show a shallow playable water surface plane, a partial diagonal shore wedge, and low wave rows following the oblique plane. Build the preview/shader with an oblique coordinate such as local depth plus a small x slope, not only `y` rows.
- If the user says water motion is too fast, slow both the effect/GIF time scale and the Unity material/HLSL time multipliers. Then verify the actual Unity runtime still has visible water-mask motion; slow water that looks static is unfinished.
- If the user asks for one-by-one ocean waves, show repeated surf rows and broken foam crests; avoid a single sea-level line.
- If the user says the shader is close but has no waves, preserve the accepted camera/mask and strengthen the wave layer itself: add readable broad crest rows plus finer broken crest detail, then match the GIF target and Unity runtime wave intensity. Shimmer, caustic streaks, or generic moving texture are not enough by themselves.
- If the user says ocean foam is not white enough, looks fake, or lacks water splash, do not only raise brightness or `_FoamAmount`. Split the foam into short broken whitecap dashes, a softer cyan foam veil, and a shore froth/spray layer; drive all of them with time-varying noise, dash breakup, and shoreline masks, then inspect the Unity runtime GIF for natural broken surf instead of long static white cracks or painted strips. If the user points to fake white in the open water body, suppress open-water whitecap dashes by shoreline/near-shore masks and keep only subtle blue-cyan ripples there; do not brighten the whole water plane.
- If the user says the water waves should be `浪花` or white bubble/foam waves and rejects blue ripple/reflection lines, add an explicit animated white-foam wave-row layer. Use broken crest rows, short dash masks, foam clumps, and bubble specks driven by time, `flowX`, depth, and noise; reduce blue ripple tint and reflection strength so the visible water-wave read comes from white foam, then verify a Unity runtime crop before handoff.
- If the user clarifies that they still want waves after fake white is removed, add a separate non-white arced swell/ripple layer. Drive the arcs with continuous `flowX`, shoreline distance, depth, and time-varying bend terms; tint them blue-cyan and keep them out of the white foam core so the water reads as dynamic waves rather than painted white scratches.
- If the user says the surf/foam is not good-looking enough and asks for more ripples, do not automatically add more white foam. Preserve accepted edge geometry and add layered non-white ripple reads first: fine blue-cyan arced water-body ripples plus smaller near-shore lace ripples, both time-driven and broken by animated noise. Feed them mainly into water color, stripe waves, and soft foam veil so the water gains texture without becoming fake white scratch lines.
- If the user asks where the wave effect is or asks for water splash at the shore edge, add a distinct animated shore-break/splash layer and show it in the split-layer review. Do not rely on a generic foam tint; the final Unity runtime must visibly show waves breaking at the real shoreline.
- If the user asks for real ocean waves that move from the left/open water toward the right/shore and disappear at the beach, do not solve it by putting a static picture, reference crop, or broad white shore-splash patch on top. Implement a time-based travelling crest phase from shoreline distance plus local depth, fade the crest at the real shore edge, and use only subtle animated dissolve foam where it vanishes.
- If the user says the wave motion looks like vertical strips or sideways/right-sliding texture, treat it as a shader coordinate failure. Rebuild the crest phase from shoreline distance plus local water depth, or another scene-aligned oblique coordinate, and reduce x-only UV scrolling/packet motion before touching color polish.
- If a sea-level water edge exposes a rectangular shader card, hard lower edge, or bright line along the foreground mask boundary, treat it as a mask/edge-composition failure. Add a soft irregular foreground/shore fade, suppress shallow/foam contribution at that artificial edge, and do not use a generic mask-edge detector as foam; only the real surface line and shoreline should generate foam.
- If the CPU/effect GIF and actual Unity runtime differ mainly after shader/material tuning, either update the effect preview to match the Unity shader or make the final preview GIF from the Unity runtime frames. Verify by hash or side-by-side frame comparison so the handoff GIF cannot drift away from the actual shader.
- For directional ocean waves, verify the visible foam/crest motion using feature or centroid tracking plus visual inspection. Repeated parallel wave rows can fool whole-frame cross-correlation.
- For near-shore travelling waves, verify a local crest band over multiple frames, not only the global water centroid. A valid loop may have new waves spawning on the left while old waves dissolve at the shore, so record the sign convention and confirm the local crest itself moves toward the shoreline before handoff.
- If the user points to or crops the actual shore-contact band, align the shader water mask/surface to that real visible shoreline before adding foam. Do not leave static reference-image foam in the backdrop at the same edge, and do not compensate by adding open-water foreground stripes. Scrub or mute static reference foam under the shader, drive visible shore foam from animated `shorelineSurf`/`surfRunup`-style terms, keep incoming rows subtle, and verify a local shoreline crop from the Unity runtime frames.
- If the user says a cropped shore, grass, sand, or rock edge "does not line up", treat it as a water-mask/shore-boundary mismatch before changing foam brightness. Update the generated mask geometry and the Unity HLSL/runtime shoreline function together, then verify a tight Unity-runtime crop of the complained edge.
- If the user points at a bright white shoreline wash and says it should run along the whole coast/contact line, do not only strengthen the local right-bank or `shoreX` foam formula. Add a separate animated coast-wash layer driven by the real water-mask/contact edge, especially the upper shoreline mask edge when the coast wraps around the water, then feed that layer into foam color and alpha and verify a Unity-runtime shore crop so it is continuous but not a static white plate.
- If the user provides an older accepted shoreline frame and says the current edge position looks bad, use that frame as the visual target. Crop the current Unity runtime to the same original scene area, compare the contact band side by side, and tune shoreline curve/contact-alpha math until the edge position and foam shape match. Do not regenerate concept art, add static overlays, or compensate with random bright splash dots over the bank.
- If the user wants both the persistent near-bank wave and the open-water stripe/ripple wave, split them into two named animated layers. One layer should be shore-locked and aligned to the real shoreline/contact band, staying close to the bank while animating lace/runup detail. The other layer should be the water-body stripe wave, driven by shoreline distance plus local depth so it reads as water ripples/rows instead of vertical strips. Show both layers separately in `*_LayerReview.png` and blend them in HLSL so Unity runtime matches the preview.
- If the user says the edge wave must hit the shore, repeat from left/open water to the far-right shore, and disappear, first identify whether the pointed edge is the water/land contact band or only the right mask boundary. For the water/land contact band, drive the break from the real `surfaceLine`/`sea_line` lane, not from a generic mask-edge detector. Use a time-based crest plus moving foam tail that sweeps left-to-right, brightens at the shore hit, and dissolves; verify with a Unity-runtime shoreline crop and the final Unity GIF.
- If the user says there is still no splash hitting the shore, do not keep the foam alpha locked only to the water mask. Add a separate animated shore-crash foam alpha that can extend slightly over the bank/contact line, then break it up with time-driven noise/segments so it reads as whitewater instead of a solid white plate.
- If the user says the seashore needs `冲到的浪花` or rejects the result as merely edge foam, add a separate shore run-up breaker, not another static/contact rim. The layer should show a crest travelling from water toward the bank, a narrow foam tongue crossing the water/land contact line, and broken bank wash/bubble residue as it disappears. Inspect the Unity shore crop and reject any version that becomes a solid white board, a pasted shoreline picture, or only a water-side bright streak.
- If the user still rejects the run-up result and says to make it `浪花`, do not keep widening or brightening the narrow foam tongue. Add a separate animated surf-foam burst/froth layer: arced scallop breaker lip, broken foam clumps, animated holes, bubble residue, and solid-white suppression. Reduce continuous coast-wash/rim terms so the shore reads as broken surf foam instead of a smooth white band, then verify a tight Unity-runtime shore crop/GIF before handoff.
- If the user asks why `浪花` does not fill the right shore edge, treat it as a lane/mask coverage issue before brightness. Add or fix a single-shader right-edge surf lane derived from the actual `WaterMask` right boundary or contact edge, keep it time-driven and broken with dashes/holes/bubbles, and verify a Unity runtime right-edge crop plus a wide single-SpriteRenderer proof. Do not add a pasted overlay or second water picture.
- If a Unity runtime GIF includes generated or reference scene sprites such as sky/cloud reflection markers, inspect frame 0 specifically. If the first captured frame shows stale or incorrect texture content, add a throwaway warm-up `Camera.Render()` before saving frames and regenerate the GIF; do not hand off an animated shader with a corrupted first frame.
- If the user asks to extend a sea surface into an "infinite" left/open-ocean area, do not duplicate a shoreline shader layer into the empty side. Shoreline/crash logic will create fake banks, vertical artifacts, or repeated shore foam. Use a separate horizontal open-ocean extension shader or mode with a parallel waterline, animated water rows, and no shore-crash terms, then inspect the Unity screenshot/crop before handoff.
- If that open-ocean extension still slopes, dips, or fails to stay flat, inspect the extension input geometry before color tuning. Do not feed the left layer a crop of the original sloped shore mask/source. Generate a horizontal waterline mask/source input and either constrain the extension sprite to a narrow open-ocean UV range or add an explicit open-ocean material mode so `surfaceY`/shore math cannot reintroduce a diagonal sea plane.
- If the user rejects the result as "拼接" and says to just make the shader longer, do not keep separate left and right shader SpriteRenderers. Use one wider shader SpriteRenderer/material/input surface, keep the original section aligned on the right, extend the same shader surface left, and verify the hierarchy/capture code has a single visible water shader layer.
- If the user specifically says to directly enlarge the current shader's left side, prefer changing the same SpriteRenderer's `drawMode`/`size` or equivalent renderer geometry first. Do not generate a wide replacement texture, a mesh workaround, or a separate extension layer unless direct renderer sizing is impossible and the blocker is verified.
- When a direct-resized sea shader loses waves/foam on the new side, check whether the extension code collapsed `uv.x` to a fixed open-ocean value. Keep separate concepts for visual sampling/shore shape and wave phase: the mask/surface can use an open-ocean coordinate, but wave rows, foam, and travelling crests need a continuous `flowX`/shore-distance coordinate across the enlarged renderer so crests can move from left to right.
- If the user asks whether a direct-resized sea shader can extend "infinitely" and have reflection, do not answer with a bare promise. Clarify that a finite Unity renderer can be made arbitrarily wider, then verify it by rendering a much wider width with the same shader SpriteRenderer/material and continuous phase coordinates. Do not call it reflection if it is a static backdrop/source plate; reflection must be generated or sampled through time-driven shader math, and the handoff must include a Unity runtime GIF/review showing the extended water and reflection motion.
- If the user cannot see or trust a water reflection, add a clear sky/reference object such as clouds in the Unity scene and make the shader produce a corresponding animated reflection in the water. Show a Unity runtime review with the reference object above and the shader reflection below; do not use post-capture compositing as reflection proof.
- If a sea-level shader still reads as "no reflection" after foam/wave polish, check whether the white foam core or shore-crash terms are suppressing the reflection mask. Strengthen a time-driven cloud/tree reflection layer in the shader, reduce foam suppression only enough for the reflection to show through, and prove it with a Unity-runtime reflection crop under the visible sky reference object.
- If the user says the shore-edge foam still looks fake or unlike foam, check for static white shoreline marks in the backdrop/source before adding more shader foam. Scrub or mute those static marks, then make the shader edge from broken lace dashes, foam packets, bubble specks, and a solid-white suppression mask; verify a tight Unity-runtime shoreline crop so the result is not just a continuous white painted band.
- If the user still cannot see a right-moving ocean wave after an arced/ripple layer was added, make the visible crest phase explicit in screen/open-water coordinates, such as `phase = frac(flowX * freq + depth_or_bend - time * speed)`, so the same crest moves to screen right. Reduce static source-texture or white-foam contributions that hide the moving layer, keep the visible crest blue-cyan when fake white was already rejected, and verify the Unity runtime crop with local feature/optical-flow direction. Whole-frame diff, global centroid, or periodic-row cross-correlation can report motion while the user still sees no rightward wave.
- If the user says the wave diagonal is reversed and should run from upper-left to lower-right, flip the visible crest geometry, not only its time direction. Use an axis shaped like `flowX * x_weight - depth_or_wavePlane * y_weight + bend` so constant-phase lines have positive screen slope, while choosing the time sign so the crest still moves toward the intended shore direction. Verify both orientation slope and motion direction in a Unity runtime crop.
- If the user points to a screenshot crop and says "extend this part" for a sea-level scene, match the crop target literally. If the pointed target is the lower water-surface band, extend only that band at the same y-range; do not fill the whole left side with blue sky/background and do not stretch/copy trees, grass, shore, or bank pixels into the ocean. Verify with the same lower-band crop before final response.
- Scene sand/rocks may be a static backdrop for context, but every visible water/shader contribution must still animate.

## Waterfall Lessons From Iteration

- Start waterfall revisions from vertically loopable source, detail, and foam textures. If a texture is sampled with `frac(uv.y + time * speed)`, verify the top and bottom rows match before running Unity.
- Do not let a static reference crop dominate the final color. Use reference images to derive loopable textures, masks, and color cues, then animate those inputs with time-driven sampling.
- Check for horizontal wrap seams in the first rendered frame before presenting the result. A seam means a non-loopable texture is being vertically scrolled or blended too strongly.
- If motion metrics show mostly zero vertical shift, treat the shader as still too static even when frame-diff numbers are nonzero. Increase downward-scrolled source/detail/foam contribution before polishing color.
- Clear old Unity runtime frames before each capture so stale frames cannot pass verification by accident.
- Do not use `-nographics` for RenderTexture visual capture if it produces blank or gray frames. Re-run normal batchmode capture instead.
- If Unity batchmode crashes in Burst compilation, retry with Burst disabled before changing shader logic.
- For waterfall work, consider the result unfinished until the runtime GIF is visually close to the accepted effect, has no static foreground plate, has no horizontal seam, and shows dominant downward motion.

## Preview Contract

For waterfall or water-flow tasks, create or update these artifacts when the project structure allows:

- `*_LayerReview.png`: layer/contact sheet shown before the final, including several shader frames.
- `*_PreviewFrame.png`: first final frame.
- `*_Preview.gif`: final animated preview.
- `*_ShaderMotion.gif`: motion-check GIF.
- When possible, capture an actual Unity material/runtime render and label it separately from CPU previews.
- If the issue is "Unity does not match GIF", make the runtime render the source of truth and update/copy the final preview GIF only after it comes from the Unity material render.
- When the final preview GIF and Unity runtime GIF should match, verify by hash or frame comparison; when they are intentionally different, explain which one is the concept preview and which one is the real shader.
- README notes listing shader files, textures, layer breakdown, and validation results.

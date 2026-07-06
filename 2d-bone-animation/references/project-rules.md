# 2D Bone Animation Project Rules

## Required Method

- Use Unity `Animator`, `.anim` `Animation Clip`, bone Transform keys, and `Sprite Skin`.
- Do not modify the PNG/source image to make animation.
- Preserve Unity `.meta` files.
- Preview GIFs must come from Unity playback or sampled `Sprite Skin`.
- Show the GIF every time.

## AI Reference Image Routing

- Treat `AIAnimation2D` as a helper project for `/Users/qin/Documents/YofaGames/ThisIsMyOregon` whenever generated pose references, keyframe references, style references, or animation-planning images are needed.
- Before generating any ChatGPT/AI reference image for this project, read and use `/Users/qin/Documents/YofaGames/ThisIsMyOregon/plugins/timo-plugin/skills/Image-generate-artwork/SKILL.md`. Use `/Users/qin/Documents/YofaGames/ThisIsMyOregon/plugins/timo-plugin/skills/Image-Concept-artwork/SKILL.md` when concept/layout/component planning matters, and route browser/provider execution through `/Users/qin/Documents/YofaGames/ThisIsMyOregon/plugins/timo-plugin/skills/chrome-chatgpt-skill/SKILL.md` plus the global `workflow-skill` image-generation rules.
- Do not use Codex built-in `image_gen`, generic providers, provider APIs, ad hoc Chrome generation, or local imagination for project pose/reference images unless the user explicitly overrides this rule.
- Match the ThisIsMyOregon muted hand-painted 2D side-scroller style. Do not invent a separate AIAnimation2D visual style, and do not drift into glossy, vivid, PBR, cinematic, or unrelated artwork.
- Generated pose/reference images are planning references only: attach the real AIAnimation2D source sprite, keep ground/contact baselines when planning animation, inspect and reject wrong sheets, then recreate accepted poses through Unity bones, `Animator`, `.anim` `Animation Clip`, and `Sprite Skin`.

## Required Review Output

- Every animation change must end by showing all required visuals in the final response.
- Always show the ChatGPT/AI reference image used for the animation key poses.
- The ChatGPT/AI reference image for every animation must include a visible ground/contact baseline unless the character is intentionally airborne/flying. The baseline is a pose/scale/contact guide, not an in-game effect.
- Always show the Unity-rendered GIF from the actual `Animator` + `Animation Clip` + `Sprite Skin` result.
- Always show a Unity effect/contact-sheet image from the actual Unity output frames.
- The GIF must visibly move at normal review size. A file with multiple frames but motion too subtle to see is a failed animation result.
- After exporting GIFs, decode the final GIF files and compare adjacent frames. If the source Unity PNG frames move but the GIF decodes as identical/static frames, regenerate the GIF from the Unity Sprite Skin frames before handoff and record the moving-pair check.
- For subtle lower-body walk work, also show a lower-body zoom GIF or contact-sheet from the same Unity output frames so the leg/tail motion can be inspected.
- For walk cycles, show a ground-contact proof image or contact sheet with a visible baseline overlay from the Unity output frames.
- For two-leg/two-tail walk cycles, the ground proof must include side-specific or limb-specific contact checks. Do not rely only on the whole-sprite bottom bbox, because one planted limb can hide that the opposite limb is floating.
- For all animations, show or preserve a ground/contact baseline in review assets when it helps judge placement, weight, impact, landing, collapse, or scale. Missing the baseline makes it easier to accidentally create floating, sliding, or inconsistent poses.
- If a workflow generates multiple animations, show the reference image, GIF, and Unity effect/contact-sheet for every generated animation.
- Missing any one of these visuals means the animation task is not complete.
- For looping Unity review exports such as idle and walk, include the final loop-seam key frame in the sampled frames. A review GIF that omits the seam can hide or falsely report loop closure problems.

## Full Character Workflow Scope

- When the user says to run the workflow for a character, continue with a new character, or generate all animations, treat the task as the complete current action set for that character, not only the last single clip discussed.
- For the current AIAnimation2D character workflow, the complete set is `idle`, `walk`, `attack`, and `die` unless the newest user instruction explicitly narrows the scope.
- Do not include `run` in the default, full-character, or "all animations" workflow. Do not author, export, or show `run` unless the user explicitly reverses this no-run rule in a newer instruction.
- If the user says "all animations", deliver every animation clip currently in the workflow and show proof for every one: ChatGPT/AI reference when used, Unity Sprite Skin GIF, and Unity contact/effect sheet.
- Do not silently hand off only `walk`, only the most recent failed action, or only one test GIF after a full-character workflow request.

## Ground Baseline Rules

- Ground/contact baseline is required for all animation generation prompts and reference sheets by default: idle, walk, attack, die, and any future action.
- Keep the same baseline position across all key poses of one animation so body height, foot/tail contact, attack recoil, landing, and death collapse can be judged consistently.
- For a full-character workflow, keep one fixed world-space/camera-space ground baseline across every action in the same handoff. Do not let the baseline move upward/downward between `idle`, `walk`, `attack`, and `die`.
- Never calculate or draw the review baseline from each frame's current sprite bbox. Never crop or rescale each action so the bottom line appears to move. Use one shared capture camera/bounds and one shared `ground_y` for the whole review set.
- If the character action changes height, the character moves relative to the fixed baseline; the baseline itself does not chase the character.
- For legged or grounded creatures, at least one relevant support point should visibly relate to the baseline in grounded poses. Do not let the character float unless the action explicitly requires hovering or flying.
- For idle, the baseline prevents drifting/floating and should show planted feet/tails with breathing only.
- For walk, the baseline proves foot/tail contact and support transfer.
- Historical/explicit-only `run` notes are not default workflow rules. If the user explicitly reverses the no-run rule and asks for `run`, verify support side changes over the loop and do not accept only a whole-sprite bottom contact check.
- For attack, the baseline proves the wind-up, impact, and recovery do not slide or float unless intentionally jumping.
- For die, the baseline proves collapse/sink/down pose finishes against the ground instead of hovering.
- If the creature is a flying, hovering, swimming, or otherwise non-grounded monster, still include an anchor/reference baseline when generating reference images and explicitly state that contact is intentionally not required.
- The baseline must not be baked into the source PNG or treated as part of the final character art; it is only for reference, preview overlay, and verification.

## Walk Rules

- Walk output for user review must be shown as exactly 4 visible key frames unless the user explicitly asks for more.
- The Unity `.anim` can interpolate between those 4 key frames, but the review GIF/contact sheet should show the 4 authored poses only.
- If the user asks for more walk frames to inspect, keep the authored walk clip sparse and add a separate 24-frame Unity review sampled from the same `.anim` `Animation Clip`. Do not bake those sampled frames back into the clip as dense per-frame animation keys.
- Do not claim a walk animation is good just because legs deform.
- A walk must read as walking: support foot, passing pose, opposite support foot, visible weight transfer, and no obvious sliding.
- A walk must include ground contact logic. Before keying, define a visual ground/contact baseline. At every key pose, one foot/tail tip must be planted on that baseline, while the other foot/tail tip may lift or pass.
- The planted foot/tail tip must stay nearly fixed for its support phase. Do not move both feet/tails at the same time without a visible support contact, or the animation will read as floating.
- For this two-tail ghost sprite, use contact phases: left tail planted on ground, right tail lifted/passing; left tail still planted, right tail moves closer; right tail planted on ground, left tail lifted/passing; right tail still planted, left tail moves closer.
- For this two-tail ghost sprite, verify that the alternate/right tail actually reaches the baseline on its support key. If the left tail is always the lowest pixel and the right side remains 10+ px above the baseline, the walk is still wrong even if the global ground delta looks good.
- When correcting a missing right-tail contact, keep the right tail on the right side while lowering it. Do not push the right-foot endpoint across the body center; that reads as folding/crossing rather than a right-side footfall.
- If subtle front-facing foot contact does not read, use a readable game-waddle: stronger left/right weight swap, contact pause, leg open/close, and body squash.
- Do not make the whole character lean or wobble to fake walking. For natural walk, tiny vertical weight/breath motion is allowed, but no left/right body sway, no head tilt, and no pelvis rotation wobble.
- For ghost/spirit sprites, do not use human-sized stride amplitude. Keep the motion small: subtle lower-body/leg wave, tiny vertical weight, no big leg spread, no stomp, and no running-like bounce.
- Do not use leg/tail bone `localScale` to fake walk motion, ground contact, squash, stretch, or support. Scaling the leg/tail bones can make the Sprite Skin mesh look like a cut paper surface or crumpled sheet. For walk, keep leg/tail `m_LocalScale` at `1,1,1` and move bones with rotation and local position keys instead.
- For 2D game movement, follow the requested screen direction. If the character walks screen-left or screen-right with this ghost sprite, the legs/leg tails should subtly move closer together and separate, not fully cross, unless the user explicitly asks for crossing. Use camera-depth foot motion only when the user explicitly asks for walking toward/away from the screen.
- For this two-tail ghost sprite, do not animate walk as symmetric open/close where both legs move together. Use a support-close step: one lower tail/leg stays planted or nearly fixed while the opposite lower tail/leg makes a small move closer toward center; then swap sides. The readable phase order is support A, moving B closes, support B, moving A closes.
- For screen-left or screen-right walking, "legs get closer" means a small near-crossing/support exchange, not a full X-cross, not a wide split, and not a side-view redraw.
- ChatGPT is optional for walk. If ChatGPT produces a wrong, overcomplicated, side-view, redrawn, or unclear reference, reject it and skip ChatGPT.
- If the user says it does not look like walking, treat the candidate as rejected and record it.

## Binding Repair Rules

- If repeated walk keyframes look like folding, paper-crumpling, or detached legs, stop tuning the `.anim` first and inspect the active prefab's actual sprite binding.
- For quadrupeds such as `Wolf100cm`, do not use the lower-leg/shin endpoint as a fake foot. The rig must include explicit paw/foot bones under each lower leg, and bottom paw mesh weights must bind to those paw bones before walk/attack/die animation review. If a four-legged walk keeps looking like twisting, folding, sliced paper, sliding, or missing ground contact, stop curve tuning and repair paw bones + paw weights + prefab `SpriteSkin.m_BoneTransforms` first.
- For quadruped walk, verify each visible paw against the baseline with a lower-body zoom/contact sheet. The whole-sprite bottom bbox is not enough; a rear or front paw can float while another paw hides the global bottom.
- For quadruped clips, keep leg/paw scale curves at `1,1,1`. Use small thigh/lower-leg/paw rotations and minimal body follow-through first; large shin local-position offsets or over-rotated paw keys usually read as folded limbs.
- For `Sprite_Spirit_1`, the active prefab must use the silhouette-style mesh/weights, not a dense rectangular grid. The repaired active `sprites:` entry should have 199 bound vertices/weights, and visible lower-body bones should have dominant vertices near non-transparent alpha pixels.
- When syncing from a better reference `.meta`, preserve the active sprite GUID and existing importer/alpha settings. Replace the `spriteSheet` binding data or the active `sprites:` entry; do not change or regenerate the source PNG.
- Unity `.meta` files can contain both modern `sprites:` list data and legacy/compatibility binding fields. Diagnose and repair the sprite entry that Unity/prefab actually uses by `internalID`/fileID, and do not mistake the legacy fields alone for the live binding result.
- After binding data changes, sync the prefab bone rest pose and the animation authoring constants to the same skeleton coordinates before judging GIFs. A repaired mesh with old keyframe constants can still look wrong.
- Verify the repair with a binding overlay/report before animation review. Required checks: bone starts/ends lie on the visible character, left/right foot or tail weights are near visible alpha, first/last walk frames match for loops, and leg/tail scale curves remain at `1,1,1`.
- A visible hard step/discontinuity at the shin/foot boundary is a binding failure, not just an animation-curve issue. Stop pulling the endpoint harder, inspect the active Sprite Skin weights/mesh, and smooth the transition weights before more keyframe tuning.
- For `Sprite_Spirit_1`, do not leave adjacent right-shin/right-foot vertices nearly hard-bound on opposite bones, such as shin vertices around `96%` shin next to foot vertices around `97%` foot. Use a gradual shin/foot transition, then verify with lower-body zoom, red-edge diagnostics, and side-specific ground-contact metrics from Unity Sprite Skin frames.

## Failed Attempts To Remember

- Do not generate AIAnimation2D pose/reference images from local imagination or a generic image generator. Use the ThisIsMyOregon `Image-generate-artwork` and `chrome-chatgpt-skill` workflow so generated references match the target game style.
- `walk_v104`: rejected; left/right side spreading, not walking.
- `walk_v105`: rejected; over-crossed legs.
- `walk_v106`: rejected; floating/bobbing from guessed hand-keying.
- `walk_v107`: rejected; too subtle/static.
- `walk_v108`: rejected; right-leg step unclear.
- `walk_v109`: rejected; right-leg swing weaker than left.
- `walk_v110`: rejected; ChatGPT reference made the workflow too complicated and wrong.
- `walk_v111_simple_right`: rejected; still looked like leg twisting, not walking.
- `walk_v112_readable_right_walk`: self-rejected; better gait phase but still looked like in-place twisting, not clearly walking.
- `walk_v114_clear_move_right_preview`: rejected by the user; still looked like sliding/twisting instead of walking.
- `walk_v115_footfall_waddle`: self-rejected; stronger footfall shapes helped slightly, but it still looked like a front-facing sprite being dragged rather than a believable walk.
- `walk_v116_foot_contact_solver`: self-rejected; solved foot targets still did not read as planted foot contact in actual Sprite Skin output.
- `walk_v117_contact_pause_step`: self-rejected; contact pauses helped timing, but leg shape still read too weak.
- `walk_v118_animated_feet`: self-rejected; animating foot bone local positions was still too subtle in the rendered sprite.
- `walk_v119_readable_waddle_walk`: rejected for showing too many sampled frames instead of the requested 4 key frames.
- `walk_v120_four_key_walk`: rejected by the user; exactly 4 frames, but the body/pelvis/head wobbled and leaned instead of reading as leg-driven walking.
- `walk_v121_no_sway_four_key_walk`: rejected by the user; it removed wobble, but became too stiff and unnatural.
- `walk_v122_vertical_weight_four_key_walk`: rejected by the user; the motion amplitude was too large for a ghost/spirit character.
- `walk_v123_subtle_ghost_four_key_walk`: superseded; motion amplitude was better, but this run did not yet follow the hard output contract with a saved ChatGPT/AI reference image shown beside Unity output.
- `walk_v124_ghost_micro_walk`: rejected by the user; prompt/action logic was wrong because it made the feet move screen-left/screen-right instead of walking toward the screen/camera.
- `walk_v125_front_depth_ghost_walk`: rejected by the user; wrong direction assumption. For this 2D game walk, the character moves screen-left and the legs should alternate left/right crossing.
- `walk_v126_screen_left_cross_walk`: rejected by the user; it crossed the legs/tails too much. The desired motion is just left/right legs getting closer together, not fully crossing.
- `walk_v127_screen_left_close_step`: rejected by the user; it still did not read naturally enough.
- `walk_choice_pack_v001`: rejected by the user; the 10 variants still read like static/symmetric open-close tests instead of a true support-leg walk phase.
- `walk_v128_support_close_step`: rejected by the user; it technically had 4 GIF frames, but the motion was too subtle at normal display size and looked static.
- `walk_v129_visible_support_step`: rejected/incomplete; it made leg/tail motion visible, but did not explicitly solve or prove ground-contact logic.
- `walk_v130_ground_contact_step`: rejected by the user; it proved ground contact, but still did not read like a natural walk because the contact fix relied too much on body/pelvis height compensation and looked like pose sinking rather than leg-driven stepping.
- `walk_v131_leg_driven_grounded_step`: self-rejected; body height stayed stable, but the first two keys were too similar and the right-support keys still floated against the final Sprite Skin baseline.
- `walk_v132_clear_support_exchange`: self-rejected; support exchange read more clearly, but key 3 floated too far above the ground baseline.
- `walk_v133_contacted_support_exchange`: self-rejected; key 3 contact was fixed by local tail extension, but it overshot and pulled the shared baseline down so the other keys appeared to float.
- `walk_v134_contact_balanced_support_exchange`: rejected by the user; it balanced contact, but used leg/tail `localScale`, making the legs look like sliced/cut surfaces instead of bones moving naturally.
- `walk_v135_bone_motion_no_scale`: self-rejected; removed scale/cut-surface problem, but key 3 floated above the ground baseline.
- `walk_v136_bone_position_contact_no_scale`: self-rejected; moving only the right foot y-position was not enough, because this rig reads foot local x as the bone endpoint/length direction.
- `walk_v137_bone_endpoint_contact_no_scale`: self-rejected; moving the right foot endpoint fixed key 3 contact but overshot and made other keys float.
- `walk_v138_balanced_bone_endpoint_no_scale`: rejected by the user; no-scale endpoint contact worked better, but the walk still did not read right enough.
- `walk_v139_loop_closed_support_step`: self-rejected; it closed the loop, but key 3 floated 12 px above the rendered Sprite Skin ground baseline.
- `walk_v140_loop_closed_grounded_support_step`: self-rejected; lowering only right foot local y did not move the rendered Sprite Skin foot enough, proving again that this rig's foot endpoint contact depends heavily on local x.
- `walk_v141_loop_closed_endpoint_grounded_step`: self-rejected/superseded; endpoint tuning reduced key 3 float to 6 px, but still missed the support-contact target.
- `walk_v142_loop_closed_dual_support_grounded_step`: rejected by the user; its contact metrics were good, but the lower appendages still looked like they were folding because the support endpoint was pulled too far.
- `walk_v143_natural_lateral_no_fold_step` and `walk_v144_natural_lateral_no_fold_grounded_step`: intermediate retries; the no-fold small lateral leg shape was better, but contact still needed a tiny weight pass.
- Current retry output: `walk_v145_natural_lateral_no_fold_weighted_step`; keep all leg/tail scales at `1,1,1`, keep endpoint offsets small, use small hip/thigh/shin angle changes plus tiny pelvis weight motion, verify first and last frames are pixel-identical, and prefer a natural continuous leg silhouette over forcing perfect ground contact by stretching endpoints. Its Sprite Skin ground deltas are near `[0, 1, 3, 0]` px.
- Binding diagnosis after `walk_v145`: if the walk still does not read, stop tuning keyframes and inspect the actual prefab's Sprite Skin binding. The current `Assets/Characters/Sprite_Spirit_1/Sprites/Sprite_Spirit_1.png.meta` used by `Assets/Characters/Sprite_Spirit_1/Prefabs/Sprite_Spirit_1_Character.prefab` has a dense rectangular 231-vertex mesh; the right foot bone has dominant vertices but `alpha-near=0`, so the visible foot/leg cannot follow it cleanly. The older tracked `Assets/Charactor/Sprite_Spirit_1.png.meta` and `Assets/Prefabs/Spirit_Walk_Character.prefab` use the better silhouette-style binding reference. Do not keep polishing walk curves on the rectangular-grid binding; rebind/sync the current sprite geometry, weights, prefab rest pose, and animation constants first.
- `walk_v146_rebound_silhouette_mesh_support_step`: binding repair succeeded, changing the active sprite from the 231-vertex rectangular mesh to the 199-vertex silhouette binding and fixing right-foot visible coverage, but the first rebased walk motion was still too large and read as lower-body twisting.
- Current retry output: `walk_v147_rebound_small_support_close_step`; after silhouette binding repair, keep the pelvis/body steady, use smaller support-close leg motion, no leg/tail scaling, first/fourth frames pixel-match, and show both normal and lower-body GIF/contact proof. Treat it as the current candidate, not a final taste guarantee if the user still rejects the motion.
- `walk_v148_rebound_right_contact_support_step`: rejected during self-check; it tried to fix the user's "other leg is not touching ground" correction, but the right side still stayed about 9 px above the per-frame baseline.
- `walk_v149_rebound_right_support_contact_exchange`: rejected during self-check; the right foot Transform moved downward, but it crossed toward the body center, so the rendered leg looked folded instead of right-side grounded.
- `walk_v150_rebound_right_side_ground_contact`: self-rejected after user screenshot; contact was near the baseline, but the right shin/foot boundary showed a visible hard step because the weights changed too abruptly.
- `walk_v151_no_step_right_support`: self-rejected; backing off the right endpoint reduced the hard step, but the right support floated too far above the baseline.
- `walk_v152_smoothed_right_weight_contact` and `walk_v153_smoothed_weights_ground_contact`: intermediate binding/curve repair passes; smoothing the shin/foot weights reduced the step, but v152 floated and v153 still missed right support contact by about 4 px.
- Current retry output: `walk_v154_smoothed_weights_contact_touch`; keep the repaired silhouette binding plus smoothed right shin/foot transition weights, use side-specific contact proof, keep leg/tail scales at `1,1,1`, and verify the red-edge lower-body diagnostic before handoff. Its 24-frame Unity Sprite Skin review has first/last frames identical and right near-contact frames around F14-F16.
- Full workflow retry after `walk_v154`: `run_v010`/`run_v011`/`run_v012` were not accepted as final because the right side stayed too far above the baseline or the support exchange was weak. Current run output is `run_v013_right_support_contact`; keep idle/run review exports loop-seam-inclusive, keep leg/tail scales at `1,1,1`, and verify run with side-specific contact metrics plus the overview contact sheet.
- `Sprite_Spirit_2 walk_v002_walk_only_no_cross_contact`: rejected by the user as not walk-like. It technically moved bone endpoints, but the right leg looked pinned and the left leg only wiggled, so do not treat small endpoint deltas as a finished walk.
- `Sprite_Spirit_2 walk_v003_visible_support_walk`: self-rejected after review. It increased visible leg motion, but read as leg swinging rather than a clear support-hold step; support transfer was still not obvious at normal review size.
- `Sprite_Spirit_2 walk_v004_support_hold_step`: self-rejected after review. It had the correct phase idea, with one leg steady while the opposite leg moved, but the motion was too conservative and still looked nearly static in the GIF.
- Current retry output for `Sprite_Spirit_2`: `walk_v005_readable_support_step`; use four sparse support-hold keys, keep body/head stable, keep all leg scales at `1,1,1`, move the non-support leg with stronger but still small rotation/local-position lift, verify the 4-frame GIF plus 24-frame lower-body review before handoff, and do not call it final if the user says it still does not read as walk.
- `Wolf100cm_full_fixed_baseline_v001`: rejected by the user; the four limbs did not read correctly. The failure was treating the wolf too much like a whole-body pose with weak limb rotations. For quadrupeds, each action needs action-specific limb logic: idle keeps paws planted, walk uses alternating front/rear support, attack uses front-leg brace plus rear-leg push, and die folds front/rear legs separately.
- `Wolf100cm_full_limb_study_v002`: self-rejected during review; the limb intent was clearer, but shin/local-position offsets were too strong and began to look like distorted limb shapes. For quadruped sprites, use small shin local-position offsets only as support, and let rotations carry most of the pose.
- Current Wolf100cm retry output: `Wolf100cm_full_limb_study_v003`; no `run`, source PNG unchanged, four actions only (`idle`, `walk`, `attack`, `die`), walk is 4 visible Sprite Skin key frames with first/last identical, and review includes a walk limb zoom sheet plus fixed ground baseline.
- `Wolf100cm_full_limb_study_v004`: self-rejected; removing shin local-position offsets reduced crumpled distortion, but the rig still used lower-leg endpoints as fake paws. Four-legged walk kept reading like leg twisting instead of foot-ground support.
- `Wolf100cm_full_limb_study_v005`: binding repair added four explicit paw bones and bottom paw weights to the active sprite `.png.meta` plus prefab `SpriteSkin.m_BoneTransforms`, but the first paw-contact walk still moved too much vertically (`walk` bottom range about 7 px) and could read as sliding/floating. Do not stop at "paw bones exist"; inspect the lower-body zoom.
- `Wolf100cm_full_limb_study_v006`: rejected by the user; it had explicit paw bones and correct Sprite Skin binding, but the walk motion was still too subtle and read like limb twitch/body drift rather than a clear support-paw exchange. Do not accept paw bones + moving-pair metrics alone as a walk.
- Current Wolf100cm retry output: `Wolf100cm_full_limb_study_v007`; no `run`, source PNG unchanged, four actions only (`idle`, `walk`, `attack`, `die`), active rig has 16 bones including explicit paws, walk uses a clearer diagonal paw support exchange, first/last key frames are identical, 24-frame Unity interpolation review moves in every adjacent pair, and leg/paw scale curves remain `1,1,1`. Still inspect the normal GIF and lower-body zoom before calling it acceptable.

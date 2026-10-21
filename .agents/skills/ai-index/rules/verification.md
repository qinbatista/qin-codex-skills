# Verification and test ownership

[Verify](../../../../verify-skill/SKILL.md) owns evidence selection. Verify changed code and consequential results in the active task through a real behavior check or output readback at the smallest relevant boundary. A quick check or mock alone is not acceptance. Do not launch the whole project or a full build unless requested or required by the release contract. Report actual evidence and limitations.

Before creating a maintained Python test or starting extended verification, read [this project's testing Skill](../../testing-skill/SKILL.md). Its registry owns each purpose, goal, level, relative path and runner. Default to level 2 real affected-case checks; level 1 is focused syntax/function evidence, level 3 covers related code, and level 4 is full-system/release validation only when requested or required. Keep each global Skill's release tests in its own `tests/`, registered centrally. Update/combine useful cases, retire obsolete duplicates without losing distinct coverage, and update runner references instead of creating parallel owners.

The [testing/release module](../modules/testing-release.md) routes registry checks and the clean-clone release gate. Run output, fixtures, bytecode and tool caches belong in the current external run. Never invent attestation results or infer another platform's acceptance.

Definition of done: current instructions and executable behavior agree, relevant checks pass, final bytes and consuming references are freshly read back, and source/install/publication status is accurate. Ending handles closure, not product testing, code repair or benchmarking.

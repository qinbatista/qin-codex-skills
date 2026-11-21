# Codex plugin release

The [plugin manifest](../../../plugins/qin-codex-skills/plugin.json) and [Skill list](../../../plugins/qin-codex-skills/skills.json) select the user-global payload. The [release action](../../../.github/actions/publish-plugin/publish.py) reads tracked files from the exact source commit and creates a Git marketplace tree containing its catalog, manifest and selected Skill files.

Stage Skill changes and run the shared release action's `--prepare` command to include the native marketplace in the source commit. For an unprepared direct push, the [publish workflow](../../../.github/workflows/publish-plugin.yml) adds the generated files in a single fast-forward on `master`. The [grouped installer](../../../management-skill/scripts/install_skill_pack.py) reads only the selected package from the `master` archive. Native Marketplace clients can use the same branch. [Installation](../../../README.md#install-the-global-skill-pack)

# Canonical Skill aliases

Use one canonical Codex skill root and symlink compatible Agents entries to it; never copy a second editable tree. The resolver checks the canonical Codex root first and accepts an Agents alias only when it resolves inside that canonical root.

```bash
python3 -B management-skill/scripts/skill_alias_install.py install \
  --canonical-root "<codex-skills-root>" \
  --agents-root "<agents-skills-root>"
```

`install` and `upgrade` are idempotent. They refuse to replace a user-owned directory or a symlink to another target. `uninstall` removes only an alias that resolves to the matching canonical skill; it never removes user-owned content. If symlinks are unavailable, the command fails rather than copying skills.

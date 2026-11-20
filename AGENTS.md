# qin-codex-skills

This repository owns eight public global Skills: Task Analyze, Workflow, Code, Verify, Prompt, Optimization, Project Memory and Management. Code maintains general coding philosophy and Python guidance. Their source folders own instructions, references, helpers and clean-clone tests. Product-specific implementations belong in project Skills.

## Global Skill pack

- Use `install_skill_pack.py install qin-codex-skills` through Python to install at `~/.agents/skills/qin-codex-skills/`. Each Skill directory is an immediate child of that path.
- Use `update qin-codex-skills` to fetch and replace the complete pack or `uninstall qin-codex-skills` to remove it. The source Git release continues to carry a native Codex Marketplace manifest. See [installation](README.md#install-the-global-skill-pack).
- Keep only the eight Skills, their support files and the pack manifest in the distribution. Repository README files, `AGENTS.md`, project AI index and tests stay in source.

Read the [project AI index](skills/ai-index/SKILL.md) at start/resume and finish when this is the current project. Every task that changes this project must update its relevant index guidance or metadata and verify the result before delivery. Reference lookups never trigger index maintenance or authorize writes. Select focused routes, reconcile root guidance when needed, and run AI Index Compression when inspection reports it due. Preserve scoped rules and other Skills' authorization boundaries.

- Write all project documentation, Skills, AGENTS files, AI-index guidance, and durable memory in English under [Management's authoring rules](management-skill/SKILL.md#authoring-rules).
- Code changes, including tests, use module/file/method anchors, scoped memory and necessary dependencies. Refresh touched routes; Code owns method boundaries and justified extraction. Keep guidance portable, concise and stable; the bounded ignored Cache inventory is the operational exception.
- Apply Workflow's Cache policy before writes: classify owners, plan final placement, deletion and exact retention, and allocate fresh ignored `Cache/temp-*` for each unit. Default to no retention, shared scratch or convenience backups. After reporting each verified result, immediately remove disposable support and read back absence. Preserve maintained, runtime, asset, active, shared, recovery and review/reuse owners; inspect exact paths and the Git index before staging.
- Default new Cache output to `temp-*`, including unclear ownership and all generated intermediates. Reserve `remote-*` for exact files required by a lasting consumer and an explicit Git-tracked synchronization contract. Preserve canonical data in its native owner.
- Task Analyze owns the opening preview, chat naming, action completion and final Skill report. Workflow owns ready work, Git delivery, bounded waits and cleanup. Verify at the smallest real boundary in the active task; read the testing Skill before maintained Python tests or extended checks. Keep release tests in their Skills and register them centrally. Full builds require a request or release requirement.
- Keep task-created support in this repository. Management owns source publication and grouped Skill installation. Codex owns the user Skill scanner and native Marketplace cache. Project Skills stay project-local. Preserve unrelated edits, installations, user AGENTS and private history. External installation or resource creation requires an explicit request. Global AGENTS requires explicit authorization.
- Use `project-memory-skill/scripts/obsidian_vault_setup.py --existing-only` and the configured Obsidian vault for scoped memory. An absent vault is a nonblocking skip. Close memory and resources inline. Codex chats and storage are user-managed; do not create automatic Ending chats or archive/delete session records.
- Run scripts and tests quietly with portable paths. Open visible surfaces only when requested. Do not click approvals or restart another task. Use the built-in browser for browser tests.

Done means instructions and executable behavior agree, relevant tests pass, owned outputs are read back, and source, installation and publication status are reported accurately.

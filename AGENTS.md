# qin-codex-skills

This repository owns eight public global Skills: Task Analyze, Workflow, Code, Verify, Prompt, Optimization, Project Memory and Management. Each source folder owns its instructions, references, helpers and clean-clone tests. Product-specific implementations belong in their project Skills.

Read the [project AI index](.agents/skills/ai-index/SKILL.md) at task start/resume and finish. Select the affected owner and only the rules needed for the action. Automatically reconcile this root contract and the project index when established intent or structure changes, before authorized delivery. Preserve useful scoped guidance; other Skill changes require their existing authorization.

- Keep source instructions portable, concise and stable. Instructions and the index are not task history, results, generated data or memory stores.
- Before any file write, apply Workflow's external artifact policy and classify ownership. Allocate a fresh external task run through Workflow for each request or execution unit, including continuations. Preserve maintained source, final deliverables and real runtime/asset owners. Never put task scratch in project Cache, Codex storage or generic output folders.
- Use Task Analyze for the opening result/difficulty/model/dependency preview, concise chat names, action completion and one final report of actual Skill use across all branches. Workflow owns ready work, Git delivery, bounded waits and exact resource cleanup.
- Verify consequential changes in the active task at the smallest real boundary. Read the project testing Skill before maintained Python tests or extended verification. Keep global Skill tests in their owning Skill and register them centrally; do not build the whole project unless requested or required for release.
- Management owns recoverable installation and authorized publication. User Skills install only in `~/.agents/skills`; project Skills stay in `.agents/skills`. `CODEX_HOME` owns configuration, global AGENTS and bundled resources. Preserve unrelated edits, installations, user AGENTS and private history. Updating global AGENTS requires explicit authorization.
- Durable memory belongs only in the configured Obsidian vault. Project Memory owns setup, scoped recall and Ending. Verify native deletion before creating Ending; otherwise close inline. After acknowledged creation, the parent immediately ends and never waits, polls or resumes for Ending.
- Run scripts and tests quietly with portable paths; do not open surfaces unless requested, click approvals or restart another task. Prefer the built-in browser for browser tests.
- Before commit, inspect exact paths and the Git index; scratch never enters Git. Release each unit's confirmed disposable resources after verified delivery, preserving active, shared, unrelated, recovery and review/reuse owners.

Done means instructions and executable behavior agree, relevant tests pass, owned outputs are read back, and source, installation and publication status are reported accurately.

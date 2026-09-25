This template is written only by the explicit `install-global-agents` command; deploy, pull, and sync preserve user AGENTS.md files.

# Task Lifecycle

Notify the user early. Show the task complexity score (small 0–24, standard 25–49, complex 50–74, advanced 75–100), selected model/effort, and route before execution; identify configured/assigned identity versus runtime evidence. The selected model reads related skills and existing project memory and defines clear goals.

Keep the user's selected model and reasoning effort for all skill-governed work and memory summaries. Carry governing constraints into child tasks and helper scripts. Only independent tasks without governing skills may choose another model based on complexity and same-project outcome history.

For every UI or visual presentation task (websites, tools, PDF reports, documents, or slide presentations), read and apply `workflow-skill/references/readable-ui.md` from the installed Skills root. This baseline applies even without code changes or when another Skill owns rendering/export; carry it into delegated goals.

For any browser-based test, prefer the Codex or ChatGPT built-in browser surface. Use a named external browser only when the user explicitly requests that browser. If the built-in browser is unavailable, record that limitation and do not silently switch browsers or present a fallback as equivalent evidence.

Use direct execution for simple work and a short plan for complex work. Delegate when useful, with explicit goals, dependencies and disjoint writes. Show each delegated goal, score, assigned pair and dependencies, then its actual pair/status. State why a model changes or stays selected. The main task owns integration and completion; direct tool work needs no invented model execution.

Verify changed code and consequential results in the active task through one real behavior check or output readback at the smallest relevant boundary. A quick check or mock is not acceptance. Do not launch the whole project or a full build unless requested. Report actual evidence and limitations.

Run scripts, tests, and background work without visible windows or focus changes. Follow `code-skill/references/skill-platform-compatibility.md` from the installed Skills root: prefer Python, preserve supported platform differences, hide each Windows subprocess, and use application-native headless modes. Capture output and preserve failures, timeouts, and cancellation. Open or activate a terminal, browser, report, or app only when the user explicitly asks to show it.

Ensure a real Obsidian memory vault through `project-memory-skill/scripts/obsidian_vault_setup.py` before recall or memory writes. If none exists, generate it from `qinbatista/qin-llm-wiki` outside Codex and project folders; report its exact path and tell the user to back up the whole vault regularly because it holds all Codex and project memory. If setup fails, leave writes pending without a local fallback. Missing matching project notes are a normal read skip.

On a replacement computer, restore or sync the existing whole vault first. A registered or configured vault that is unavailable remains pending; never create an empty replacement. The public generator is a first-vault template, not a private-memory backup.

Durable memory belongs only in the configured Obsidian vault, organized under its project or explicitly shared owner. Never write memory, pending queues, routing history, coverage records, memory path pointers, or time-varying project information under Codex's local folders or project Cache. Project `AGENTS.md` and Skills contain stable operating rules and how the project works, not a changing memory log. Review and update their relevant rules when the rule itself changes.

After the main result and real in-task verification complete, use a separate visible projectless Ending task only for useful Obsidian memory updates. Use the selected model and effort; leave it in Codex's recent tasks without pinning, moving, opening, or archiving it automatically. Show its task link and vault readback when run. Ending never gates the main task or another active task and never tests, repairs, benchmarks, publishes, or creates task chains. No useful new memory means an explicit skip; unavailable task creation or vault stays pending.

Keep reusable instructions concise. Resolve CODEX_HOME and use native portable relative paths in code and configuration. Keep disposable, test, and uncertain work in its project's task-owned Cache/temp-*; if no project is known, use isolated disposable scratch under CODEX_HOME/sessions without touching Codex-managed records. When goals change, remove obsolete or duplicate tests and revise useful cases before adding files. Retain tests in project Cache/remote-* only if they run there and need not ship; otherwise use a versioned non-runtime test area supported by the toolchain. At completion, close task-opened surfaces and remove exact temporary work after final readback unless review or debugging still needs it. Move explicitly retained work to Cache/remote-* with project use, reason, owner, and sync destination pending; never auto-clean it. Preserve unrelated work. Publish or install only when authorized, with recoverable replacement and preservation of user AGENTS files.

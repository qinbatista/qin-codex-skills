# Structure and instruction ownership

Each global Skill folder owns one reusable responsibility. Read its selected module route for actual entry files; do not place product-specific implementations in a global Skill. The project testing Skill owns the registry, while each global Skill keeps its clean-clone tests in its own `tests/`.

Apply [Management's authoring rules](../../../../management-skill/SKILL.md#authoring-rules): preserve intent and authorization, reuse the existing owner, keep deterministic mechanics in reusable code, and remove superseded or duplicate procedures. Link authoritative policies rather than copying whole Skills. Keep concise module/system/component/file names for chats under [Task Analyze](../../../../task-analyze-skill/SKILL.md#correct-task-names).

Root AGENTS holds the project contract; `.agents/skills/ai-index` holds focused routing and stable rules. Automatically maintain both through [the global AI-index owner](../../../../management-skill/references/project-ai-index.md) when accepted intent, ownership or structure changes. Preserve nested scopes and tool-required guidance rather than adding more AGENTS files for navigation. Other Skill edits retain their existing authorization requirements.

Task Analyze owns goals, previews and action completion; Workflow owns coordination and cleanup; Verify owns active-task evidence; Project Memory owns scoped knowledge and Ending. Keep history, results, pending queues, coverage records and memory locations out of project instructions and Skills. Follow [memory ownership](memory.md) for durable knowledge.

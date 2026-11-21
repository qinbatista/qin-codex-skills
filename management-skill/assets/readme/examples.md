# Codex Skill examples

Each example gives an AI prompt, the work it calls for, and the result to inspect. Start with the receiving project's rules. In Codex, select the named Skill with `$` or ask for it by name.

## Define the finish line

> Use Task Analyze to fix a CSV import that crashes on blank rows. Preserve the current behavior for valid rows. Show how you verified both cases.

Identify the importer's real entry point and expected handling of blank rows. Fix the owning code and run an import with both valid and blank rows. Report the observed row count and any genuine delivery blocker. [Task Analyze](../../../task-analyze-skill/SKILL.md#complete-action-requests)

## Retry a build or test

> Use Workflow to rerun the package check. Carry over only `fixtures/build-settings.json` from the previous run. Clean up the old package and logs before starting again.

Select the previous run by its registered path and use `--continue-from` with that one input. Check the new file and predecessor removal before launching the retry. Close the final scratch run once its result is delivered. [Cache continuation](../../../workflow-skill/references/project-cache-artifact-policy.md#separate-executions-and-continuation)

## Write a Python input boundary

> Use Code to read a JSON export manifest at the import boundary. Require a nonempty string `source` and preserve the value supplied by the producer.

The reader owns file access and input validation. Call it directly from the importer. Keep the returned source intact and let the caller handle a failed import at its existing error boundary.

```python
import json
from pathlib import Path


def read_manifest_source(manifest_path: Path) -> str:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Export manifest must be an object")
    source = manifest.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("Export manifest requires a nonempty source")
    return source
```

Check a real valid manifest, invalid JSON and an empty `source`. Keep reusable validation at the input boundary and verify ordinary callers through the importer. [Code-writing philosophy](../../../code-skill/references/code-writing-philosophy.md) · [Python style](../../../code-skill/references/python-rules.md)

## Organize a project

> Use Code and Management to explain where the importer, its test, AI navigation and temporary exports belong in this project.

An illustrative Python project has separate owners for runtime behavior, regression cases, and temporary files. Preserve the receiving project's actual layout and record stable module and entry-point links in its project index when one is adopted.

```text
project/
  AGENTS.md                 Stable ownership and operating rules
  src/importer.py           Import behavior and its public entry point
  tests/test_importer.py    Regression checks for valid and rejected inputs
  skills/ai-index/          Project-local navigation and source anchors
  Cache/temp-*/             Ignored execution files with a cleanup owner
```

Keep durable decisions in the project's configured memory. Check that the index opens the actual importer and that the test runs from its maintained location. [Project AI-index structure](../../../management-skill/references/project-ai-index.md#one-project-owner) · [Project Cache policy](../../../workflow-skill/references/project-cache-artifact-policy.md)

## Specify a prompt response

> Use Prompt to extract order IDs from a supplied note. Return JSON with one `order_ids` array of strings in first-seen order. Return an empty array when the note has no IDs.

Define the input, ordering and missing-value behavior. Check representative notes with one ID, repeated IDs and none. The downstream parser should read the same JSON shape in every case. [Prompt Skill](../../../prompt-skill/SKILL.md)

## Verify the real entry point

> Use Verify to show that an invalid manifest reaches the importer error path and that a valid manifest still imports.

Run the importer from its ordinary command or application route. Inspect the exit status or visible result and check any existing output that the failed case should preserve. Record the actual environment and result. [Verify Skill](../../../verify-skill/SKILL.md#bind-evidence-to-the-actual-target)

## Recall and record project decisions

> Use Project Memory to recall the importer contract by module, file and symbol. After the fix, save the verified empty-input rule if it will matter to future work.

Recall from the exact project's configured Obsidian vault and confirm the current implementation. A durable outcome records the method, established behavior and actual verification. Read it back from the same project. [Precise recall](../../../project-memory-skill/references/project-knowledge.md#precise-recall) · [Consolidation](../../../project-memory-skill/references/project-knowledge.md#consolidation-in-ending)

## Measure an optimization

> Use Optimization to reduce repeated manifest parsing in a batch while keeping the same results and error behavior.

Measure a representative batch first. Read once at the owner's batch boundary when input freshness allows it, then compare output and measured time with the same workload. Exercise an updated manifest to check invalidation before reporting a gain. [Optimization Skill](../../../optimization-skill/SKILL.md)

## Check an installation and publish source

> Use Management to verify both Skill packs on this machine. For a repository change, select the maintained files, run its release checks and read back the delivered commit.

Codex discovers the grouped install at `~/.agents/skills/<pack>/<skill>/SKILL.md`. Check the package manifest, each direct Skill entry, and the released files. Use the installer action `update` to replace that package and `uninstall` to remove it. If you are migrating an older Marketplace copy, verify the new install before removing the previous plugin and marketplace entries with `codex plugin remove <pack>@<pack>` and `codex plugin marketplace remove <pack>`. [Installation and delivery](../../../management-skill/SKILL.md#install) · [Codex Skill discovery](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

## Use both packs on a Unity task

> Read this Unity project's rules and use the matching Skills to repair a Charge button that admits a second request while its animation is playing. Verify the actual input and replay path.

Use the Codex pack to define the result, navigate ownership, manage scratch and verify delivery. Use the Unity pack for the controller, UI binding, playback and native test decisions. Follow the receiving project's registered workflow when applicable. [Unity Skill pack](https://github.com/qinbatista/qin-unity-skills#examples) · [Charge Pulse project](https://github.com/qinbatista/qin-unity-skills/tree/master/examples/charge-pulse)

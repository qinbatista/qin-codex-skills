# Replay Git branch and worktree cleanup

Paste this prompt into Codex with the current Workflow Skill. Use a fresh fixture for each run.

```text
Set up two local bare repositories in a new task-owned Cache directory, alice/widget.git and team/widget.git, each with master and an already-integrated codex/old branch. In Alice also create and publish an integrated fix/old branch. Give the Alice repository a codex/old tag at the same commit. Clone both. Advance Alice's remote master by one commit through a separate checkout so its working clone starts behind. Also create and publish Alice's integrated codex/local-only branch. Record both remote ref maps and Team's local ref map. Request local cleanup of that single branch and check its local head disappears while both remote maps and Team's local map still match.

Use the Workflow Skill to deliver a small change for Alice only. In a new linked worktree, implement sum_even(values) in totals.py and test empty input, negative values and a generator. Publish the task branch, integrate the tested change into Alice's master, and clean up the completed task and old branches. Verify the result from a fresh clone and report the starting base and delivered commit.

Check that the task started at Alice's advanced remote master, all three completed branches are absent from local heads, remote heads and tracking refs, the linked worktree is gone, and the codex/old tag still resolves to its original commit. Verify Team's full local and remote ref maps match their baselines. Release the fixture after checking.
```

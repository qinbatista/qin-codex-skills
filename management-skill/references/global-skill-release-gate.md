# Global Skill Retained-Capability Release Gate

`assets/global-skill-capability-catalog.json` is the maintained source of truth for global Skill behavior that the user has explicitly retained. A capability remains mandatory until the user explicitly replaces or retires it. Old architectures listed under `retired_architectures` must not be reactivated merely because an older commit or memory mentions them.

The gate runs source and deployed unit suites, direct routing/workflow/model/platform validators, real-sample attestations, the exact public Skill-set check, deployment parity, and both global `AGENTS.md` parity checks. It emits a numbered report with check invocations, passed invocations, assertion counts, and status for every retained capability.

Local installation and GitHub publication use different mutation boundaries. An explicit local install/update first snapshots the current managed installation and writes the maintained source as a provisional active copy after only bounded source-integrity and public-safety checks. It then runs the installed platform checker, deployed gate, source gate, and parity checks. A failed, missing, stale, timed-out, or incomplete check prevents the completion verdict, automatically restores the prior installation, and becomes evidence for Codex to repair the maintained source and reinstall. It never becomes a command or confirmation assigned to the user.

GitHub commit/push remains pre-mutation: the full release gate must PASS before the first README, index, commit, or remote write. Tests may suppress only recursive nested gate calls while the gate itself is already executing; there is no user-facing skip flag.

On the current host, execute the real installation path. Cover other supported Windows, macOS, and Linux branches through static analysis or dependency-injected unit tests when those hosts are unavailable, and label simulation separately from physical execution. `Installation complete` means installed/source/platform/parity PASS from the final repaired installation, never merely that files were copied.

Real-project attestations are sanitized receipts, not substitutes for source tests. Each receipt binds its result to hashes of the contract files it validates. When a watched contract changes, the receipt becomes stale and the release blocks until the real sample is rerun and a new attestation is created from its passing evidence.

This catalog and gate are process/release contracts. Personal memory may retain the sanitized long-term preference; project-change memory records only the independently verified final result after Ending. Neither memory stream replaces the gate.

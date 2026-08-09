# Global Skill Retained-Capability Release Gate

`assets/global-skill-capability-catalog.json` is the maintained source of truth for global Skill behavior that the user has explicitly retained. A capability remains mandatory until the user explicitly replaces or retires it. Old architectures listed under `retired_architectures` must not be reactivated merely because an older commit or memory mentions them.

Run `scripts/global_skill_regression_gate.py` before any local global deployment or GitHub publication. The gate runs the source or deployed unit suites, direct routing/workflow/model/platform validators, real-sample attestations, the exact public Skill-set check, deployment parity, and both global `AGENTS.md` parity checks. It emits a numbered report with check invocations, passed invocations, assertion counts, and status for every retained capability.

The deployment/publish entry point invokes this gate before its first mutation. A failed, missing, stale, or incomplete check blocks the action. Tests may suppress only recursive nested gate calls while the gate itself is already executing; there is no user-facing skip flag.

Real-project attestations are sanitized receipts, not substitutes for source tests. Each receipt binds its result to hashes of the contract files it validates. When a watched contract changes, the receipt becomes stale and the release blocks until the real sample is rerun and a new attestation is created from its passing evidence.

This catalog and gate are process/release contracts. Personal memory may retain the sanitized long-term preference; project-change memory records only the independently verified final result after Ending. Neither memory stream replaces the gate.

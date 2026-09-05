# Release validation

`global_skill_regression_gate.py` runs the current capability catalog and saves exact results. The publisher calls it before README, index, commit, or remote mutation. Consumer installation only performs recoverable replacement and does not run this gate.

Maintain behavioral tests for current policy, isolation, portability, and installer rollback. A requested workflow change retires its obsolete tests and claims. Historical benchmarks/attestations are not evidence for the changed workflow. Do not invent replacements or require a whole application build for a skill-only change.

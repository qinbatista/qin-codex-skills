# Router extension guide

`skills/task-analyze-skill/scripts/routing_policy.py::EXECUTION_DOMAINS` is the single authoritative registry for active execution domains. Domain IDs are immutable evidence keys: do not rename an existing ID, and use `code_unspecified` only for migration and historical evidence.

## Add one active domain

For a new registry-owned code domain, make one additive registry row with all nine required metadata fields: `display_name`, `kind`, `language_aliases`, `owner_skill`, `owner_enforced`, `spark_first`, `reference_path`, `active`, and `history_only`. Then add the matching reference page and generic routing/validator coverage that reads the registry. Do not edit every validator, scenario, or skill description just to enumerate the new domain. A new additive domain value does not require a schema-version bump.

The normal seam is:

1. Add one `EXECUTION_DOMAINS` row with an immutable ID and reference path.
2. Add the domain-specific executor reference and, when applicable, a language/style reference under `code-skill/references/`.
3. Add one representative routing scenario and generic registry-driven tests for valid, unknown, and migration-only domains.
4. Update concise user documentation only where the active domain list or extension seam is explained.

Discover the current non-mutating registry view with:

```bash
python3 skills/task-analyze-skill/scripts/model_routing_history.py domains
```

Keep language rules in executor references, not in registry metadata. A domain may share an executor with another domain while retaining separate evidence and rules. Current code examples are `python`, `csharp`, and `unity_csharp`; `general` is the non-code default.

## Evidence and migration

`execution_domain` is part of adaptive-profile identity. New records use the exact registry ID. When reading legacy records with no domain, infer `code_unspecified` for legacy code evidence and `general` otherwise; never reinterpret old evidence as a newly named active domain. `code_unspecified` is not an extension target.

The entry model|effort is route-coordination metadata only and is never a learning feature. Direct tool-only routes use their installed tool skill and an observable Mini Verify, but create no child model, model receipt, or adaptive producer sample. Model-executed routes carry complete `routing_recommendation` proof and record the actual producer receipt and verification outcomes; deterministic controller recording needs no decorative Luna call.

## Canonical policy

Correctness is the gate. Among routes that satisfy it, prefer direct execution for one reversible action, the frozen calibrated pair for similar model work, bounded context, and dependency-safe parallelism. Tokens and elapsed time are receipt evidence for like-for-like optimization; they never override quality or safety boundaries.

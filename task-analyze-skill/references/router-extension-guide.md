# Router extension guide (documentation workflow)
Use this for adding or extending routing domains and evidence-aware execution domains.

## 1) Add domain metadata

- Add routing registry metadata for the new domain under `task-analyze-skill`.
- Keep existing domains in existing scenario shape unless a new scenario is required.
- For code domains, keep them attached to `code-skill`.

## 2) Add execution-domain evidence

- Add or update `task-analyze-skill/local/adaptive-routing` schema/validator coverage for the new domain field values.
- Use exact domain names:
  - `python`
  - `unity_csharp`
  - `general`
- Never use `unity-csharp` in routing evidence.

## 3) Add/update code-skill references

- Update `code-skill` reference docs for implementation guidance and rules for each language that shares it.
- Python and Unity C# share `code-skill`; they keep separate evidence keys in `execution_domain` and separate language rules:
  - `references/python-rules.md`
  - `references/unity-csharp-rules.md`

## 4) Update CLI command docs

- In CLI guidance for adaptive routing, document `--execution-domain` as optional.
- Missing explicit domain behavior:
  - `code_unspecified` for legacy code evidence
  - `general` otherwise
- This inference is migration-safe and makes old payloads parse under the new schema.

## 5) Update route scenarios and tests

- Add fixtures/scenarios in routing tables (for example in `workflow-skill/references/routing-matrix.md`) for expected direct/dispatch shapes.
- Add focused tests for each new scenario, model pattern, and minimum observable evidence.

## 6) Update README

- Update `management-skill/assets/readme/github-readme-template.md` example contract:
  - `schema_version: 3`
  - include `condition.execution_domain`
  - only fields that the real writer serializes
  - scenario coverage and direct-route wording aligned with runtime behavior.

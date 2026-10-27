# Verify

Start at [SKILL.md](../../../../verify-skill/SKILL.md). [task_verification.py](../../../../verify-skill/scripts/task_verification.py) selects evidence for the active task. Report helpers such as [generate_test_pdf_report.py](../../../../verify-skill/scripts/generate_test_pdf_report.py) belong here only when the requested output needs them.

Verify owns evidence scope, test levels and acceptance. It does not create a later verification task, launch the whole project by default, or treat a quick/mock check as real acceptance. Retired Ending-verification entry points are compatibility boundaries, not the active workflow. Follow current source/user scope for content or visual assessment; do not infer it from ordinary workflow acceptance.

Read the [project testing Skill](../../testing-skill/SKILL.md) before new maintained tests or extended campaigns. Tests remain in `verify-skill/tests/`; outcomes/caches stay in the project Cache run. Product testing remains in the active task and is never delegated to Ending.

# Ending migration

Ending now belongs to `project-memory-skill` and only summarizes durable information with the user's selected model and reasoning effort. Verification and repairs finish inside the active task. Missing memory or no useful change means skip.

The old `ending_verification_plan.py` and `ending_task_ledger.py` entry points refuse execution so stale plans cannot launch checks or repair tasks. Use `task_verification.py` to choose a focused in-task scope and `project-memory-skill/scripts/ending_memory.py` to save a completed summary. Existing evidence/history remains historical; it is not a current instruction.

The user-authorized Ending lifecycle uses one separate visible projectless memory task after these checks finish. The parent shows its actual task link and completion/readback or explicit skip. A CLI launch packet is pending until the app acknowledges a real task.

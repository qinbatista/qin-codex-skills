"""Offline process fixture. Records argv/stdin and emits a local Codex receipt."""
import json
import re
import sqlite3
import sys
import uuid
from pathlib import Path

root = Path.cwd()
args = sys.argv[1:]
prompt = sys.stdin.read()
model = args[args.index("--model") + 1]
effort = next(value.split("=", 1)[1].strip('"') for value in args if value.startswith("model_reasoning_effort="))
assert args[0] == "exec"
assert 'approval_policy="never"' in args
assert "ENDING_TASK_WORKER" not in prompt
assert "inside this active task" in prompt
assert "missing memory is optional" in prompt
capture_path = root / "fixture-call.json"
capture_path.write_text(json.dumps({"argv": args, "prompt": prompt, "model": model, "effort": effort}))
thread_id = str(uuid.uuid4())
rollout = root / "fixture-rollout.jsonl"
usage = {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12, "cached_input_tokens": 0, "reasoning_output_tokens": 0}
events = [{"type": "turn_context", "payload": {"turn_id": "fixture-turn", "model": model, "effort": effort}}, {"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": usage}}}, {"type": "event_msg", "payload": {"type": "task_complete", "duration_ms": 1, "time_to_first_token_ms": 1}}]
rollout.write_text("\n".join(json.dumps(event) for event in events) + "\n")
with sqlite3.connect(root / "fixture-state.sqlite") as connection:
    connection.execute("CREATE TABLE IF NOT EXISTS threads (id TEXT PRIMARY KEY, rollout_path TEXT, model TEXT, reasoning_effort TEXT, tokens_used INTEGER, cli_version TEXT, model_provider TEXT, source TEXT)")
    connection.execute("INSERT INTO threads VALUES (?, ?, ?, ?, 12, 'fixture', 'fixture', 'exec')", (thread_id, str(rollout), model, effort))
for event in [{"type": "thread.started", "thread_id": thread_id}, {"type": "item.completed", "item": {"type": "agent_message", "text": "RESULT_READY_BEGIN\nOffline subprocess receipt validated.\nRESULT_READY_END"}}, {"type": "turn.completed", "usage": usage}]:
    print(json.dumps(event), flush=True)

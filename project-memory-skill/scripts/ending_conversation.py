"""Delete exact local Ending conversations through Codex's native app-server API."""

import argparse
import base64
import hashlib
import os
import json
import queue
import re
import shutil
import subprocess
import struct
import sys
import threading
import time
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options


SOURCE_KINDS = ["cli", "vscode", "exec", "appServer", "subAgent", "subAgentReview", "subAgentCompact", "subAgentThreadSpawn", "subAgentOther", "unknown"]
ENDING_TITLE = re.compile(r"^Ending(?:\s+Task)?(?:$|\s*[|·:：—–-]\s*\S.*$)", re.IGNORECASE)


class NativeError(RuntimeError):
    def __init__(self, method, error):
        self.method = method
        self.error = error
        super().__init__(f"{method}: {error}")


class AppServer:
    """Own a native API connection; never restart a shared daemon or edit its store."""

    def __init__(self, executable=None, timeout=30, transport="auto"):
        self.executable = executable or shutil.which("codex")
        if not self.executable:
            raise RuntimeError("Codex CLI unavailable; native thread/delete is required")
        self.timeout = timeout
        self.transport = transport
        self.write_lock = threading.Lock()
        self.sequence = 0
        self.messages = queue.Queue()
        self.errors = deque(maxlen=20)

    def __enter__(self):
        if self.transport == "auto":
            version = subprocess.run([self.executable, "app-server", "daemon", "version"], capture_output=True, text=True, encoding="utf-8", timeout=self.timeout, **hidden_process_options())
            self.transport = "daemon" if version.returncode == 0 and json.loads(version.stdout).get("status") == "running" else "stdio"
        command = [self.executable, "app-server", "proxy"] if self.transport == "daemon" else [self.executable, "app-server", "--stdio"]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **hidden_process_options())
        self.websocket_key = base64.b64encode(os.urandom(16)).decode()
        self.readers = [threading.Thread(target=self.read_stdout, daemon=True), threading.Thread(target=self.read_stderr, daemon=True)]
        for reader in self.readers:
            reader.start()
        try:
            if self.transport == "daemon":
                upgrade = f"GET / HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {self.websocket_key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
                self.process.stdin.write(upgrade.encode())
                self.process.stdin.flush()
                ready = self.messages.get(timeout=self.timeout)
                if ready is not True:
                    raise RuntimeError(f"Native daemon WebSocket handshake failed: {ready}")
            self.call("initialize", {"clientInfo": {"name": "ending_conversation", "version": "1.0"}, "capabilities": {"experimentalApi": True}})
            self.send({"method": "initialized", "params": {}})
        except BaseException:
            self.close()
            raise
        return self

    def read_stdout(self):
        try:
            if self.transport == "daemon":
                self.read_websocket()
            else:
                for line in self.process.stdout:
                    self.messages.put(json.loads(line))
        except (OSError, ValueError, EOFError) as error:
            self.messages.put(error)
        finally:
            self.messages.put(None)

    def read_stderr(self):
        for line in self.process.stderr:
            self.errors.append(line.decode("utf-8", errors="replace").rstrip())

    def read_exact(self, size):
        data = bytearray()
        while len(data) < size:
            chunk = self.process.stdout.read(size - len(data))
            if not chunk:
                raise EOFError("Native daemon closed its WebSocket")
            data.extend(chunk)
        return bytes(data)

    def read_websocket(self):
        status = self.process.stdout.readline(8192)
        headers = {}
        header_size = len(status)
        while True:
            line = self.process.stdout.readline(8192)
            header_size += len(line)
            if not line or header_size > 65536:
                raise ValueError("Invalid native WebSocket handshake")
            if line == b"\r\n":
                break
            name, value = line.decode().split(":", 1)
            headers[name.lower()] = value.strip()
        expected = base64.b64encode(hashlib.sha1((self.websocket_key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
        if not status.startswith(b"HTTP/1.1 101 ") or headers.get("sec-websocket-accept") != expected:
            raise ValueError("Native daemon refused the WebSocket upgrade")
        self.messages.put(True)
        fragments = bytearray()
        while True:
            flags, length = self.read_exact(2)
            opcode = flags & 15
            if flags & 112 or length & 128:
                raise ValueError("Unsupported native WebSocket frame")
            if length == 126:
                length = struct.unpack("!H", self.read_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self.read_exact(8))[0]
            if length + len(fragments) > 64 * 1024 * 1024:
                raise ValueError("Native WebSocket response exceeds the bounded message limit")
            payload = self.read_exact(length)
            if opcode == 8:
                return
            if opcode == 9:
                self.send_frame(payload, opcode=10)
                continue
            if opcode == 10:
                continue
            if opcode not in (0, 1):
                raise ValueError("Expected a native JSON text frame")
            fragments.extend(payload)
            if flags & 128:
                self.messages.put(json.loads(fragments))
                fragments.clear()

    def send_frame(self, payload, opcode=1):
        length = len(payload)
        header = bytes([128 | opcode, 128 | length]) if length < 126 else bytes([128 | opcode, 254]) + struct.pack("!H", length) if length < 65536 else bytes([128 | opcode, 255]) + struct.pack("!Q", length)
        mask = os.urandom(4)
        frame = header + mask + bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        with self.write_lock:
            self.process.stdin.write(frame)
            self.process.stdin.flush()

    def send(self, message):
        payload = json.dumps(message).encode()
        if self.transport == "daemon":
            self.send_frame(payload)
        else:
            self.process.stdin.write(payload + b"\n")
            self.process.stdin.flush()

    def call(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Native {method} timed out; outcome must be read back before retry")
            try:
                message = self.messages.get(timeout=remaining)
            except queue.Empty as error:
                raise TimeoutError(f"Native {method} timed out; outcome must be read back before retry") from error
            if message is None:
                raise RuntimeError(f"Codex API connection closed during {method}: {'; '.join(self.errors)}")
            if isinstance(message, Exception):
                raise RuntimeError(f"Native {method} transport failed") from message
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise NativeError(method, message["error"])
            return message["result"]

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)
        for reader in self.readers:
            reader.join(timeout=3)
        self.process.stdout.close()
        self.process.stderr.close()

    def __exit__(self, exception_type, exception, traceback):
        self.close()


def probe_deletion_route(client, origin_thread_id):
    """A daemon can self-delete its own workers; another server's writer stays protected."""
    cursor = None
    seen = set()
    while True:
        params = {"cursor": cursor} if cursor else {}
        result = client.call("thread/loaded/list", params)
        if origin_thread_id in result["data"]:
            return {"native_delete_available": True, "origin_thread_id": origin_thread_id, "transport": client.transport, "source": "origin is loaded by this native service"}
        cursor = result.get("nextCursor")
        if not cursor:
            return {"native_delete_available": False, "origin_thread_id": origin_thread_id, "transport": client.transport, "reason": "origin belongs to another service; close out in the current chat unless that service exposes native deletion"}
        if cursor in seen:
            raise RuntimeError("Loaded-thread pagination repeated; deletion ownership is unverified")
        seen.add(cursor)


def list_threads(client, **filters):
    """Include all providers, source kinds, archive states and pagination pages."""
    threads = {}
    for archived in (False, True):
        cursor = None
        seen_cursors = set()
        while True:
            params = {"limit": 100, "modelProviders": [], "sourceKinds": SOURCE_KINDS, "archived": archived, **filters}
            if cursor:
                params["cursor"] = cursor
            result = client.call("thread/list", params)
            for thread in result["data"]:
                threads[thread["id"]] = {**thread, "archived": archived}
            cursor = result.get("nextCursor")
            if not cursor:
                break
            if cursor in seen_cursors:
                raise RuntimeError("Native thread list repeated a cursor; inventory is incomplete")
            seen_cursors.add(cursor)
    return list(threads.values())


def list_endings(client):
    return [{key: thread.get(key) for key in ("id", "name", "archived", "status", "parentThreadId")} for thread in list_threads(client, searchTerm="Ending") if ENDING_TITLE.fullmatch(thread.get("name") or "")]


def delete_ending(client, thread_id, expected_title, origin_thread_id, descendants=(), apply=False):
    """Require a fresh exact identity and explicit cascade scope before native deletion."""
    if thread_id == origin_thread_id or not origin_thread_id:
        raise ValueError("The originating conversation must be identified and preserved")
    if not ENDING_TITLE.fullmatch(expected_title):
        raise ValueError("Only an exact Ending title is eligible")
    thread = client.call("thread/read", {"threadId": thread_id, "includeTurns": False})["thread"]
    if thread["id"] != thread_id or thread.get("name") != expected_title:
        raise ValueError("Ending identity changed; refusing deletion")
    children = list_threads(client, ancestorThreadId=thread_id)
    child_ids = {child["id"] for child in children}
    if child_ids != set(descendants) or origin_thread_id in child_ids or os.environ.get("CODEX_THREAD_ID") in child_ids:
        raise ValueError("Native deletion cascades; explicitly review and include every spawned descendant")
    targets = [thread, *children]
    if any(target.get("status", {}).get("type") == "active" and target["id"] != os.environ.get("CODEX_THREAD_ID") for target in targets):
        raise ValueError("Active conversations must finish before deletion")
    paths = {target["id"]: target.get("path") for target in targets}
    if any(not path or not Path(path).is_absolute() for path in paths.values()):
        raise ValueError("Native rollout paths are required for local absence readback")
    if not apply:
        return {"status": "ready", "thread_id": thread_id, "title": expected_title, "descendants": sorted(child_ids)}
    client.call("thread/delete", {"threadId": thread_id})
    remaining = {item["id"] for item in list_threads(client)}
    present = sorted(set(paths) & remaining)
    retained_files = [identifier for identifier, path in paths.items() if Path(path).exists()]
    if present or retained_files:
        raise RuntimeError(f"Native deletion readback failed: listed={present}, rollout_present={retained_files}")
    return {"status": "deleted", "thread_id": thread_id, "host_id": "local", "title": expected_title, "descendants": sorted(child_ids), "read_back_verified": True, "local_record_absent": True, "source": "Codex thread/delete success; all-provider active and archived thread/list absence; native rollout path absence"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", help="Explicit Codex executable; defaults to PATH discovery")
    parser.add_argument("--transport", choices=("auto", "daemon", "stdio"), default="auto")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    probe = commands.add_parser("probe")
    probe.add_argument("--origin-thread-id", required=True)
    deletion = commands.add_parser("delete")
    deletion.add_argument("--thread-id", required=True)
    deletion.add_argument("--expected-title", required=True)
    deletion.add_argument("--origin-thread-id", required=True)
    deletion.add_argument("--descendant", action="append", default=[])
    deletion.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with AppServer(args.codex, transport=args.transport) as client:
        match args.command:
            case "list":
                result = list_endings(client)
            case "probe":
                result = probe_deletion_route(client, args.origin_thread_id)
            case "delete":
                result = delete_ending(client, args.thread_id, args.expected_title, args.origin_thread_id, args.descendant, args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

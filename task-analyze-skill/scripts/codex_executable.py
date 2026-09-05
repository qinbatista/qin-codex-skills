"""Bind child execution to the current Codex runtime without installing software."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code-skill" / "scripts"))
from hidden_process import hidden_process_options

RUNTIME_EXECUTABLE_ENV = "CODEX_RUNTIME_EXECUTABLE"


def _native_codex(path):
    candidate = Path(path).expanduser()
    return candidate.is_absolute() and candidate.name.casefold() in {"codex", "codex.exe"} and candidate.is_file() and os.access(candidate, os.X_OK)


def _windows_process_table():
    if sys.platform != "win32":
        return {}
    import ctypes
    from ctypes import wintypes

    class ProcessEntry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32FirstW.restype = wintypes.BOOL
    kernel.Process32NextW.argtypes = kernel.Process32FirstW.argtypes
    kernel.Process32NextW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    snapshot = kernel.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        return {}
    result = {}
    entry = ProcessEntry()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        available = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while available:
            result[entry.th32ProcessID] = entry.th32ParentProcessID
            available = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    return result


def _windows_executable(pid):
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        return buffer.value if kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)) else None
    finally:
        kernel.CloseHandle(handle)


def _posix_process(pid):
    if sys.platform.startswith("linux"):
        process = Path("/proc") / str(pid)
        stat = (process / "stat").read_text(encoding="utf-8")
        parent = int(stat.rsplit(")", 1)[1].split()[1])
        return parent, os.readlink(process / "exe")
    if sys.platform == "darwin":
        ps = shutil.which("ps")
        if ps:
            result = subprocess.run([ps, "-p", str(pid), "-o", "ppid=", "-o", "comm="],
                                    text=True, capture_output=True, timeout=2, check=False, shell=False,
                                    **hidden_process_options())
            fields = result.stdout.strip().split(None, 1)
            if result.returncode == 0 and len(fields) == 2:
                return int(fields[0]), fields[1]
    return None


def active_codex_executable():
    """Read executable identities of at most 16 ancestors; never inspect command arguments."""
    try:
        parents = _windows_process_table() if sys.platform == "win32" else {}
        pid = os.getppid()
        seen = set()
        while pid > 1 and pid not in seen and len(seen) < 16:
            seen.add(pid)
            if sys.platform == "win32":
                executable = _windows_executable(pid)
                parent = parents.get(pid, 0)
            else:
                record = _posix_process(pid)
                if record is None:
                    return None
                parent, executable = record
            if executable and _native_codex(executable):
                return str(Path(executable).resolve())
            pid = parent
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    return None


def resolve_codex_executable(requested="codex", *, explicit=False, environ=None):
    """Explicit argument, explicit runtime binding, active Codex ancestor, then PATH."""
    requested = os.fspath(requested or "codex")
    if explicit or requested != "codex":
        return {"path": requested, "source": "explicit_argument"}
    environment = os.environ if environ is None else environ
    configured = environment.get(RUNTIME_EXECUTABLE_ENV)
    if configured:
        if not _native_codex(configured):
            raise ValueError(f"{RUNTIME_EXECUTABLE_ENV} must name an existing native codex executable")
        return {"path": str(Path(configured).expanduser().resolve()), "source": "configured_runtime"}
    active = active_codex_executable()
    if active:
        return {"path": active, "source": "active_codex_ancestor"}
    return {"path": shutil.which("codex", path=environment.get("PATH")) or "codex", "source": "path"}

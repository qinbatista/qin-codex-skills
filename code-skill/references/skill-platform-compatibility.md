# Skill-platform compatibility examples

This reference applies when the edited functional code is shipped inside a Skill runtime surface (`scripts`, `bin`, `tools`) and must remain portable unless intentionally OS-specific.

This gate applies when creating/changing functional code inside a Skill or used by a Skill. It does not apply to ordinary project code.

## Required author declarations

- Declare target supported platforms in code docs/comments.
- For host-run local automation, prefer one portable Python entry point over paired `.cmd` and `.sh` implementations; a necessary native wrapper forwards arguments and exit codes without owning business logic.
- Require a clear unsupported-platform error or fallback for targets outside supported set.
- Use `pathlib.Path`, `Path.home()`, `Path.cwd()`, `tempfile`, and env discovery (`os.environ` / `os.getenv`) for portable file/dir logic.
- Resolve executables via PATH-aware checks before launch.
- Launch child Python code with `sys.executable`, never a hard-coded `python`, `python3`, or `py` command.
- Guard platform-only Python modules and APIs such as `fcntl`, `msvcrt`, `os.killpg`, `os.startfile`, `start_new_session`, and Windows `creationflags`.
- Avoid `shell=True` in shared code; build subprocess commands as argument arrays.

## Guard examples

### Python

```python
if sys.platform == "darwin":
    exe = shutil.which("osacompile")
    if not exe:
        raise RuntimeError("darwin path requires osacomply; set TOOL_PATH")
elif os.name == "nt":
    raise RuntimeError("Windows is unsupported for this flow")
else:
    exe = shutil.which("convert")
```

### Shell (`.sh`, `.bash`, `.zsh`)

```sh
if [ "$(uname)" = "Darwin" ]; then
  osacompile="$(command -v osacompile || true)"
  [ -n "$osacompile" ] || { echo "darwin tool missing"; exit 3; }
else
  echo "unsupported platform"
  exit 3
fi
```

### PowerShell (`.ps1`)

```powershell
if ($IsWindows) {
  $tool = Get-Command magick -ErrorAction SilentlyContinue
  if (-not $tool) { throw "Windows path unsupported: missing magick" }
} else {
  throw "only Windows supported"
}
```

### JavaScript / TypeScript

```ts
if (process.platform === "darwin") {
  const tool = process.env.PATH ? "osacompile" : undefined
  if (!tool) throw new Error("darwin path unsupported: missing tool")
} else {
  throw new Error("only darwin supported")
}
```

## Minimal required checks

- Ensure every OS-specific command path is inside explicit platform guard.
- Ensure every platform-only Python import, API, and subprocess option is guarded.
- Ensure Python child processes use `sys.executable`.
- Ensure portable branches include concrete fallback or explicit `UnsupportedPlatformError`/`RuntimeError`/`throw`/exit code.
- Run the checker on changed functional files and include results in project completion flow. From the `.codex` directory, use the launcher appropriate to the host:

```sh
# macOS/Linux
python3 skills/code-skill/scripts/skill_platform_check.py check --skills-root skills --baseline skills/code-skill/assets/skill-platform-baseline.json
```

```powershell
# Windows PowerShell
py -3 skills/code-skill/scripts/skill_platform_check.py check --skills-root skills --baseline skills/code-skill/assets/skill-platform-baseline.json
```

`python` is acceptable only when it resolves to the intended Python 3 environment.

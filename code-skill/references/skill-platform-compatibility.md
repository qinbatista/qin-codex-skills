# Skill Runtime Portability

For scripts, tests, and background commands, use portable host APIs and keep execution invisible. Preserve working Windows, macOS, and Linux branches when platform behavior differs; do not replace them with a one-platform shortcut. Project code follows its declared runtime and supported platforms, including fixed containers or managed runtimes.

- Prefer one Python entry point over new shell/PowerShell wrappers. Preserve necessary existing platform implementations. Declare supported platforms and fail clearly on unsupported ones.
- Use `pathlib`, environment/config discovery, and `tempfile` for paths. Keep local machine paths out of source.
- Resolve external tools through PATH-aware discovery before launching. Use `sys.executable` for child Python and subprocess argument arrays instead of `shell=True`.
- Guard OS-specific imports, APIs, and subprocess options such as `fcntl`, `msvcrt`, `os.killpg`, `os.startfile`, `start_new_session`, and Windows `creationflags`.
- A wrapper forwards arguments and exit status; it does not duplicate business logic.

## Quiet execution

- Use the current non-interactive tool session and capture output/errors there or in task-owned logs. Do not open or activate a terminal, browser, generated report, or other app unless the user explicitly asks to show it. Do not change OS-wide settings or hide/close unrelated windows.
- Apply `code-skill/scripts/hidden_process.py`'s `hidden_process_options()` to every maintained Skill `subprocess.run`/`Popen` launch, including nested helpers and tests. Project code uses the same guarded policy in its own process owner, without depending on an installed Skill path. Keep the caller's streams, arguments, environment, exit status, timeout, and cancellation behavior. Hidden execution must still report failures.
- On Windows, the helper combines `CREATE_NO_WINDOW` with a copied `STARTUPINFO` using `STARTF_USESHOWWINDOW` and `SW_HIDE`. It preserves compatible flags and standard handles, and rejects `CREATE_NEW_CONSOLE` and `DETACHED_PROCESS`, which disable that guarantee. It passes no Windows options on macOS/Linux.
- Console hiding does not make GUI applications headless. Use the application's native background/headless/export mode for browser checks, document rendering, and similar work; disable automatic preview opening. Prefer a CLI/API when an application cannot run invisibly, and report an unverified GUI boundary rather than opening a window.

For example, after importing the shared helper:

```python
result = subprocess.run([sys.executable, "worker.py"], capture_output=True, text=True, timeout=30, check=True, shell=False, **hidden_process_options())
```

## Focused checks

Run the focused platform check during the task when runtime code changes. From the Skills root, the command is:

```text
python3 code-skill/scripts/skill_platform_check.py check --skills-root . --baseline code-skill/assets/skill-platform-baseline.json
```

On Windows use `py -3` instead of `python3` in the existing tool session; use `python` only when it resolves to the intended Python 3 environment. Child Python processes use `sys.executable`. Test the changed native branch when available and distinguish runtime evidence from simulated/static checks. Checker success alone does not prove execution or window suppression on every platform.

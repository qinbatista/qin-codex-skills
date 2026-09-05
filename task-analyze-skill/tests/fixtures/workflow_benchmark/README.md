# Real-provider workflow replay fixture

This is a small, fictional replay of recent responsive review-dashboard and hidden subprocess work. It tests an implementation, not whether a model can repeat skill wording. It contains deliberately broken source; never deploy the input as an application.

## Isolation and equal treatment

- Copy only `input/` into a fresh workspace for every arm, then rename `process_runner.py.in` to `process_runner.py`. The `.in` suffix keeps deliberately unsafe input as inert test data in the source repository. Supply the exact same `TASK.md`, runtime bindings, and acceptance command to both arms. The fixture has no project memory and does not create per-trial memory or Ending tasks.
- Keep `TASK.md`, these acceptance scripts, and original inputs outside worker write ownership. Record their hashes before running and check them afterward. A worker may inspect the same acceptance code in both conditions but must not change it.
- The installed arm uses the declared installed global skills and entry policy. The control arm has no managed skill installation. Hold the selected model/effort, task, tool availability, worker budget, hardware, browser, and acceptance gates constant for the primary comparison.
- Actual routing to cheaper models, if enabled in an additional comparison, changes the workflow as well as context. Label it separately, disclose all actual pairs, and include every producer/verification worker's time and tokens. Do not mix that result with a single-model skill-context ablation.
- Run one installed development pilot to validate the fixture and record its costs separately. Freeze the fixture and checks before measured runs. Prefer three paired rounds, alternating which condition runs first. Keep every failed attempt and its cost; do not replace failed measured runs with silent retries.
- Report correctness before efficiency. Compare total completion wall time and all attributable model input/output tokens, including cached input as a disclosed component. Also report task-only and any lifecycle costs separately. This fixture has one shared study-level memory Ending, not a new Ending per arm.

## Run acceptance

Bind the existing Node, Playwright module, and headless Chromium/Chrome paths through arguments or the `BENCHMARK_NODE`, `BENCHMARK_PLAYWRIGHT`, and `BENCHMARK_BROWSER` environment variables. No package install, server, project build, or visible app is needed.

```text
python run_acceptance.py WORKSPACE --output-dir EVIDENCE --node NODE --playwright PLAYWRIGHT_MODULE --browser CHROMIUM
```

For a benchmark harness using argument substitution:

```json
["{python}", "ABSOLUTE_FIXTURE_PATH/run_acceptance.py", "{workspace}", "--output-dir", "{evidence}", "--node", "NODE", "--playwright", "PLAYWRIGHT_MODULE", "--browser", "CHROMIUM"]
```

The aggregator returns one JSON object with `status: "pass"` and exit code 0 only when both checkers pass and the input ledger is unchanged. Generated JSON evidence and three browser screenshots are written to the requested evidence directory. These are task-owned support artifacts, not source.

## Acceptance boundaries

- Python: exact deduplicated decimal totals; argument arrays; stream, environment, input, cwd, timeout and nonzero exit handling; guarded Windows console options; preservation of the POSIX session branch; and a real native child process. Unsafe launch-option contracts prevent actual candidate execution.
- UI: rendered geometry at 1440/390/320 px, contained single-row header, bounded text and controls, original content, readable type, compact rows, panel/toolbar alignment, filter states, Add feedback, and JSON export containing every visible record's ID, title, owner, displayed amount, and state. Context page/popup events and `window.open` attempts are recorded throughout the interaction; closing a popup does not erase the failure. Both the browser and its pages are headless and always closed.
- Native Windows checks add observed `GetConsoleWindow() == 0` for the actual child. Simulated Windows option checks on macOS/Linux are explicitly not native Windows proof.
- A parent should inspect the saved screenshots for grouping, explanation density, balance, and readability that geometry alone cannot establish. Automated success is not a universal aesthetic judgment or evidence about unrelated UIs/PDFs.
- This is a bounded convenience sample, not a universal model ranking. Three paired rounds offer limited precision. A skill efficiency win requires equal acceptance and lower observed total time and tokens in the declared comparison. Report a loss or mixed result plainly; do not tune the benchmark after seeing measured outcomes.

`test_ui_oracle.cjs` exercises incomplete/mutated export rejection and closed-popup history. Pass the Playwright module and optional browser executable to also check an immediate open-and-close attempt in a real headless browser. The Python fixture regression suite runs its dependency-free Node assertions when Node is available.

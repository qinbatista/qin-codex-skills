# Does an ordinary task release its resources?

Run these examples when a user wants to see [Workflow's cleanup rules](../../workflow-skill/references/task-resource-lifecycle.md#clean-up-each-step) in action. Start a fresh worker with the normal installed Skills. Give it the assignment alone. Keep the acceptance checks with the observer so a cleanup reminder cannot influence the outcome.

## Website research and a CLI preview

> Read IANA's Example Domains page and RFC 2606 in two hidden built-in browser tabs. Identify the three second-level domains reserved for documentation. Write them to a temporary JSON file and serve it with a loopback HTTP server launched from the CLI. Send the observer the preview URL, PID, task directory and browser tab IDs so they can read it. Once they acknowledge the read, finish the assignment.

Use [IANA's explanation](https://www.iana.org/help/example-domains) and [RFC 2606 section 3](https://www.rfc-editor.org/rfc/rfc2606#section-3).

1. Keep a separate observer-owned control file and record its hash. Record the initial tab inventory in the browser context being tested.
2. While the preview is live, GET the exact URL. Check that the JSON contains `example.com`, `example.net` and `example.org` exactly once each. Match the response bytes to the file. Verify the PID and start identity, its listening port, and the scratch registration. Acknowledge the read.
3. After the worker finishes, make fresh queries. The original process must have exited, its listener must be gone, and both the task directory and its registration must be absent. Check the original tab IDs through their owning browser. If browser contexts are isolated, identify which observations came from the worker and which the observer made independently.
4. Read back the control file and any control tab in the same browser context. Record the verdict before repairing any leftovers. Then release the observer's own resources and verify their absence.

## A CLI command that fails

> Create a small valid JSON object and a truncated copy in a temporary directory. Run `python -m json.tool` on both. Send their paths to the observer for a second read, then report the exit codes and explain the diagnostic.

Have the observer reproduce both commands, check the parsed object and match the error location to the malformed input. After the worker finishes, verify that both input files, their directory and the run registration are gone. This case exercises an error inside a task that still delivers its requested result.

Report the useful output, the live and final observations, and how each handle was checked. A surviving task resource fails that part of the trial. An unavailable readback leaves it unverified. Report only resources the example actually acquired.

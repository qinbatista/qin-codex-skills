# Replay a change across two parcel CLI features

Run this Level 2 case in a fresh task-owned Cache fixture. Record the Code Skill revision being exercised. Give the first writer the build prompt and a second, independent maintainer the resulting project and the change prompt. Keep the observer checks private until both runs finish.

## Build prompt

> Build a Python CLI with two commands. `python3 -m parcel quote WEIGHT_GRAMS` prints the price in cents for a positive integer weight. Charge 500 cents for the first 1,000 grams and 200 cents for each additional 1,000 grams or part thereof. `python3 -m parcel pickup CODE` trims surrounding whitespace, accepts six ASCII letters or digits, and prints the code in uppercase. For either command, print the value on success and exit nonzero with a diagnostic for invalid input.

## Change prompt

> Change the charge for each additional 1,000 grams or part thereof to 150 cents. Keep the first kilogram at 500 cents.

## Observer checks

1. Before handing off the project, run each case in a fresh CLI process. Save its exit code, stdout and stderr. Quote weights `1`, `1000`, `1001`, `2000`, and `2001` must return `500`, `500`, `700`, `700`, and `900`. Reject `0`, `-1`, and `1.5`. Pickup must turn `"  ab12cD  "` into `AB12CD` and reject `"abc12"`, `"ab-123"`, and `"é12345"`. Pass each quoted pickup input as a single argument, preserving its spaces.
2. Trace each command from its CLI entry to the function that owns its rule. Record the relative paths of its implementation, models and support scripts where present. Record the SHA-256 of each maintained source file. Use the [Code Skill's writing guidance](../../../../code-skill/references/code-writing-philosophy.md) to check whether ownership is apparent from names, files and actual calls. Cohesive functions may share a file.
3. On the original project, confirm the new expectation of `650` for `1001` grams fails because the CLI still returns `700`. After the second maintainer finishes, rerun all cases. Expect `650` at both `1001` and `2000`, and `800` at `2001`. Compare the full results for both first-tier weights, invalid weights and every pickup case with their baselines.
4. Compare paths and hashes to identify the edit that changed the price. Confirm every pickup-owned source file still exists with identical bytes and trace the changed quote through the public CLI. Report separately whether the commands behaved correctly and whether the pricing change stayed within its owner. Release the fixture after readback.

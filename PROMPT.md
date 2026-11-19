You implement ONE task from files in this checkout. Read README.md, SPEC.md and
PROGRESS.md first. Work only on the selected task; retain exported signatures and
contracts. The owner approved internal locking and fixed integer quanta, NOT
callbacks, float conveniences, async wrappers or caller-only synchronization.

Only dwrr/_engine.py and scripts/_adapter.py may contain implementation changes.
The facade, State seam, records, constants, errors, parser and stream seam are
complete; do not change. Do not edit tests, fixtures, vendor sources, packaging,
README/SPEC, tasks, prompt, hashes, judge or loop. Do not add files to evade those
protections. Tests and whole-tree checks must pass without fixture-specific
shortcuts. No imports of tests/oracles/shared model or reference, no environment
switches, fallback implementations, hidden test paths or hardcoded corpus output.

No external effects in the core: no payload execution/equality/hash/conversion/
copying; no I/O, logging, configuration, processes, network or interpreter-global
settings. Scheduling semantics apply to all sequences, not only finite fixtures.
Every operation must be correct while the complete facade holds its lock.
Private State is the protected test seam, not public API. Complete unfinished
later stubs only when necessary for the selected task; incremental kit check does
not demand later behavior. Run the task's exact test command and earlier tasks.

Append three lines to PROGRESS.md: task ID; what changed; what remains/blocked.
Do not commit, push, publish, edit siblings or run nested agents. The loop judges,
auto-commits passing work, or discards only this attempt's changes. Stop afterward.

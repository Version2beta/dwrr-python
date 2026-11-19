# Kit and implementation verification record

Current outcome (2026-11-19): the actual coder implementation at
`b97fc29c0a4776bbb5d41f632aeb37ff1a23986a` passed all five tasks on CPython 3.15.0
and 3.11.15. Independent read-only code review reported no issues; it did not
independently rerun tests. See the final section for retained implementation
records. Version 0.1.0 remains unuploaded and requires complete owner release
sign-off. Earlier sections below are historical reachability/correction evidence,
not claims that the current checkout still contains stubs.

## Historical Item-subclass judge correction after T2 (2026-11-19)

This section describes the correction at `32cf887` and what was pending then,
not the final implementation state.

At loop-written HEAD `32cf887854b58985573bcf70fe60bd4792c3fa37` (T1 commit
`308adfb`, then T2), review found enqueue used `type(item) is Item`, rejecting
ordinary subclasses contrary to SPEC §3.4's `Item` instance contract. The old
T1 tests missed this input. The parent stopped the runner before further writes.
This correction changes only protected tests/judging/evidence, not coder code.

`test_enqueue_item_subclass_preserves_payload_and_cost` now requires ordinary
Item subclasses in both list and tuple batches, opaque payload identity and exact
cost preservation; a later non-Item must still raise TypeError without appending
a valid prefix. Existing wrong-element and strict integer rejection tests remain.
Corrected counts: T1 has 9 tests, whole suite has 31. The new test ID is required
by both T1 and T5 stdout expectations.

The new targeted test and corrected T1 judge fail on the current loop-written
code with `TypeError: batch element must be an Item`. The private reference
already uses `isinstance(item, Item)`; no reference fix or product change was
needed. Temporarily swapping only `_engine.py` from the private reference makes
the targeted test and corrected T1 judge pass. The exact current loop-written
Engine backup is restored, not the original stubs. No adapter or progress changes,
new coder calls, pushes or publication are part of this correction.

See `verification/item-subclass-correction.log` for commands, exit statuses and
stdout/stderr. The T1-only `TASKS=.loop/item-subclass-T1.tasks.json` configuration
retains the corrected T1 command/expectations and both kit checks under unchanged
`loop.sh --check`; it avoids rerunning unrelated unfinished tasks. Full-suite,
minimum-runtime and publication claims are not renewed by this focused correction.
The next real runner will select the failing T1 regression for the coder to fix.

## Historical preparation snapshot

The following records describe kit preparation at `53d2fa1`, not the current
final implemented checkout or the correction's verification. In particular,
its 30-test full-stage passes do not include the new subclass regression.

**This is kit reachability evidence, not implemented-library completion.** At
that preparation snapshot, the checkout deliberately retained stubs in
`dwrr/_engine.py` and `scripts/_adapter.py`.
No real coder/model call, push or publication had occurred at that point. Parent
review was required before the README loop command; publication required complete
owner sign-off (and still does).

## Authority, ownership and provenance

Preparation branch: `spec-loop/python-core-kit`, from existing base
`9fddbb36f6faeeae8a4f5c45227863e1808dbf00`. The owner's pre-existing README/SPEC
queue-count policy/hash changes were integrated, not discarded. Explicit owner
approvals supersede the old unapproved/no-lock drafts. Sibling repos were read
only; unrelated active Elixir edits were not changed.

The kit-author-owned private reference and restoration backups are outside the
repo and coder kit; their location is reported privately to the parent. The
reference was authored from approved Python SPEC and shared 0.1.1 pseudocode;
not copied/imported from upstream's optimized model. Only the two owned stub
files were temporarily swapped. No fallback import, environment switch or model
substitution exists. Tests use an independent bounded naive list/dictionary
oracle with literal per-visit stepping, not reference/production scheduling helpers.

Frozen upstream current source: `dwrr-spec` committed HEAD
`243dd125470365df2c52a6ce72de3ee8ecfce3fe`. Corpus historical origin remains Go
v0.10.1, tag `7109d4d4da265258f348598a378545656db0c241`, shared inspection
`8a0e3cf9ae860ba207213590c00feeb822bdd8f2`, original seeds and four infeasible
naive cases. See `vendor/shared/PROVENANCE.md`; byte comparisons against the
source passed for every copied document, corpus file, tool and license.

## Judge evidence

The skill runner and its fake-coder regression suite are unchanged byte copies:

```text
scripts/loop.sh       4ed33daa824bd8ed999c141cf4abd55921981f5e8de86948408552b52dbb207f
scripts/test_loop.sh  13b9b6a30ffae87fc398c48f3cbeed9f6608bce52c45c91d31f6121918afb210
```

`kit-manifest.json` inventories hashes for all protected files; the manifest
itself is protected by tasks.json (no impossible self-hash). The only mutable
tracked paths are the two implementation files and PROGRESS.md. `kit_check.py`
rejects unapproved extra paths, protected-byte drift, invalid syntax/format and
obvious external-effect/fixture imports. This is a guard, not a security sandbox;
review of actual loop-written source remains mandatory.

The unchanged `bash scripts/loop.sh --check` was used on both stubs and reference.
It runs format check, selected task, all earlier tasks and incremental-safe kit
check; never invokes a coder, formats, commits or discards. Fixed full-line stdout
expectations include every test ID and exact test totals, so exit 0, stderr-only
markers, skipped tests and empty discovery cannot pass.

| Task | Delivered stubs | Private reference, CPython 3.15 / 3.11 | Behavioral proof |
| --- | --- | --- | --- |
| T1 state/validation/mutation | FAIL (test command, not integrity) | pass / pass | 8 tests: strict Python domain, exact limits, first-invalid atomicity, payload refs, queue repair/release |
| T2 withdrawal | FAIL (test command) | pass / pass | 4 tests: head/drain FIFO, credit/active closure, empty/fresh containers, index-first errors |
| T3 scheduling | FAIL (test command) | pass / pass | 14 tests: 9 scheduling incl bounded oracle, 4 concurrency, 1 complete native corpus |
| T4 public wire dispatch | FAIL (test command) | pass / pass | 4 tests plus unchanged external replay and 41-check driver checker |
| T5 whole tree, last | FAIL (test command) | pass / pass | all 30 tests; external replay/checker; archives; isolated installs/examples; 26 fake-coder runner cases and 26 caught regressions |

Incremental source swaps also passed under the same `--check`: T1 passes with
withdrawal/take/adapter still stubbed; T1–T2 pass with take/adapter stubbed;
T1–T3 pass with adapter stubbed. Later tasks fail as intended. Thus kit integrity
and early tasks do not require unfinished later behavior. These swaps were owned
verification changes only and restored.

Protected summaries and whole-stage output are under `verification/`. Full local
streams are retained in ignored `.loop/`: `stubs-check.*`, `stubs-test.N.*`,
`reference-check.*`, `reference-test.N.*`, `reference-check-python311.*`,
`reference-python311-test.N.*`, and `incremental-TN.*` (task N is zero-indexed
in `test.N` filenames). No real `coder.*`, attempt counters or root STOP exists.

### Finalizer change and timeout recovery

The finalizer-release refinement was approved by the parent: Engine returns
retired storage privately; the facade drops it only after unlock/state repair.
The original preparation timed out during its final T5 fake-coder regression
run, leaving the two owned source swaps in place. On recovery they were verified
byte-identical to the private reference and restored from owned stub backups.
Fresh post-change full `--check` runs subsequently passed T1–T5 on both 3.15 and
3.11, including all 30 tests and the finalizer/weakref subprocess regression.
Delivered stubs were restored and all five tasks again failed behaviorally.
These fresh results, not the older 29-test logs, support the current kit.

## Conformance, independent oracle, numeric and interface results

- Native core replay asserts exactly **1,839 cases / 44,728 steps / seven files**.
  Public driver external replay prints `PASS: 1839 cases, 44728 steps, 7 files`.
- Unchanged current protocol checker prints `PASS: 41 of 41 checks passed`;
  36 was historical, not the current target. Interactive flushing, EOF, all-item
  protocol-first precedence, ignored fields and scheduler-error continuation pass.
- Independent oracle: seed 807241, 80 histories × 160 mixed operations = 12,800
  bounded steps; exact results and full private abstract-state comparisons after
  every operation, including invalid inputs. No idle skip in this oracle.
- Focused checks cover active resume, reweight/join/withdraw/removal, FIFO, exact
  equality, peak credit, costs beyond 2**53, MAX-cost/quantum-1 fast skipping,
  cursor/tie order, take(10**100) without requested-size allocation, and payload
  identity without call/hash/equality/conversion/copy. Concurrency tests control
  the engine seam to prove entire-call serialization for all seven methods and
  use real concurrent batch/take conservation and complete serial take slices. A bounded subprocess verifies last-payload
  finalizer and weakref callbacks can re-enter on queue removal after state repair
  and unlock, without deadlock. Private retirement storage preserves public None;
  other ordinary operations transfer/retain payload references through lock exit.
  Arbitrary GC/signal/asynchronous callback reentry is not promised.
- Four deliberately regressed private disposable copies were rejected: resume
  regrant, partially appended invalid batch, one-extra skipped round, withdrawal
  spending credit. No sibling or expected corpus mutation.
- Cheapest decimal-limit experiment: default CPython JSON rejects a 6000-digit
  integer at default limit 4300; local <=500-digit parsing/rendering roundtrips
  positive/negative tokens exactly, without global setting changes. Driver tests
  roundtrip 6000-digit payloads, classify huge index/n, and parse huge count
  without allocating queues. Wire cost/quantum uint64 bound stays unchanged.
  NaN/Infinity, exponent/bool integer fields, bad UTF-8 and malformed later items
  fail as protocol errors. Injected MemoryError/OverflowError exit 1, preserve
  earlier responses and stop later processing; no actual OOM allocation attempted.
- Manual driver fixture: new(1), enqueue value 7/cost MAX, huge take -> exactly
  `{"ok":null}`, `{"ok":null}`, then
  `{"ok":[{"queue":0,"value":7,"cost":"9223372036854775807"}]}`.

## Package, environments and reproducible commands

Local build rationale: ordinary setuptools pure-Python wheel/sdist, initial 0.1.0,
MIT and no runtime requirements; no speculative packaging/CLI framework.
Archive checks verify metadata, license and absence of tests/vendor/driver/private
files. Wheel, sdist and checkout installs each run both README examples outside
the source checkout in fresh venvs; import paths prove installed code is used.
Build/dev packages: build 1.6.1, setuptools 84.2.1, wheel 0.48.0, packaging 26.3.
Required dependencies were installed with owner authorization; judge builds and
installs use predownloaded `.loop/build-wheels` offline and temporary directories.

Observed host: Darwin arm64; Bash 3.2.57; Git 2.54.0; jq 1.7.1-apple;
`/usr/bin/timeout` supports the runner's timeout calls (no `--version` flag).
Current CPython 3.15.0; minimum CPython **3.11.15**, installed via authorized
`uv python install 3.11`. Both full stages passed `loop.sh --check`; direct 3.11
unit/interface/package runs passed as well. Other Python versions/platforms,
hosted CI, stress/race tooling and real consumer behavior are not demonstrated.
Pi 1.5.2 CLI help and **offline** catalog show the exact owner-pinned providers
and models. No live model call, credential disclosure or provider-access claim.

Exact commands (after the README dev setup; temporary source swaps are private
verification only and are not a coder-loop invocation):

```sh
# Delivered stubs: expected nonzero, all five tasks FAIL.
bash scripts/loop.sh --check
# Private reference temporarily in the two implementation paths:
bash scripts/loop.sh --check
PATH="$(dirname "$(uv python find 3.11)"):$PATH" bash scripts/loop.sh --check
# Independent interface and package checks, also performed on 3.11:
python3 -B scripts/judge.py all
python3 -B vendor/shared/tools/replay.py --driver 'python3 -B scripts/conformance_driver.py'
python3 -B vendor/shared/tools/check_driver.py --driver 'python3 -B scripts/conformance_driver.py'
python3 -B scripts/package_check.py
bash scripts/test_loop.sh
# Restore only the two owned stub files, then integrity/whitespace check:
python3 -B scripts/kit_check.py
git diff --check
```

Historical residual gates at preparation: parent acceptance of the kit; review
of real coder output after loop; complete owner release sign-off before any PyPI
publication. Finite tests are not proof of all-sequence conformance, universal
thread fairness, OOM recovery or speed parity. Live model availability/auth/spending
was untested by design at preparation.
**Historical preparation STOP: no real coder loop had started at `53d2fa1`.**

## Actual coder implementation verification and acceptance (2026-11-19)

### Source and real model loop

Final implementation source is
`b97fc29c0a4776bbb5d41f632aeb37ff1a23986a` on
`spec-loop/python-core-kit`, from original kit `53d2fa1` and project base
`9fddbb36f6faeeae8a4f5c45227863e1808dbf00`. Parent acceptance preceded authorized
model calls. The exact configured commands were:

```sh
CHEAP_CMD='pi --provider anthropic --model claude-haiku-5-5 --thinking high --print --no-session'
STRONG_CMD='pi --provider openai-codex --model gpt-6.1-sol --thinking high --print --no-session'
STRONGEST_CMD='pi --provider openai-codex --model gpt-6.1-sol --thinking high --print --no-session'
```

All use **high**, never the historical STRONGEST default `max`. The actual coder
command is recorded in each loop commit's trailer (these are real model calls,
not the fake-coder regression suite):

| Commit | Outcome | Coder |
| --- | --- | --- |
| `308adfb00fb2a3598e63fe1233353194a4b62eb5` | T1 attempt 1 passed the then-current judge | CHEAP |
| `32cf887854b58985573bcf70fe60bd4792c3fa37` | T2 attempt 1 passed | CHEAP |
| `97df8025d293a9c79bec379475c710b0dd0914b2` | Parent's protected Item-subclass judge correction | No coder change |
| `48bf7a545e4d4f287ab50e5299b4ef2f361403c8` | T1 attempt 2 passed the corrected 9-test judge | STRONG |
| `5f41c31010479ae2fcc614b9af0799218080e2db` | T3 attempt 2 passed | STRONG |
| `b97fc29c0a4776bbb5d41f632aeb37ff1a23986a` | T4 attempt 1 passed | CHEAP |

The first invocation was interrupted (recorded exit 137) after T2/during T3.
Following the protected correction described above, the resumed invocation exited
0 with `every task passes`. T5 required no additional coder edit or commit.
Final attempt counters were T1=2, T2=1, T3=2, T4=1. Only the engine, adapter and
coder progress notes changed during implementation relative to the corrected kit;
no reference substitution, sibling edits, push or publication completed the work.

### Retained actual implementation results

These selected sanitized final records are copied from ignored `.loop/` records,
with origin names and SHA-256 digests. They contain no credentials or private
filesystem paths. Interpreter logs retain exact PASS lines, including test IDs,
while omitting detailed fake-coder failure diagnostics containing temporary paths:

- `verification/execution-final-state.log`: final source/branch/clean status,
  commit trailers, attempt counts, successful final check exits and no STOP.
- `verification/execution-final-host315.log`: CPython 3.15.0 runner and T5 results.
- `verification/execution-final-python311.log`: CPython 3.11.15 runner and T5 results.

Both final `loop.sh --check` invocations exited **0** and reported T1–T5 pass:

| Check on actual implementation | Both interpreters |
| --- | --- |
| Whole Python suite | 31 tests, no skips (corrected subclass regression included) |
| Native and unchanged external replay | 1,839 cases / 44,728 steps / seven files |
| Unchanged protocol checker | 41 of 41 checks |
| Independent bounded naive oracle | Included in scheduling tests; not production/reference helpers |
| Concurrency/finalizer and exact numeric/skip fixtures | Included in whole suite |
| Archives and installed README examples | Wheel, sdist, checkout; isolated imports outside source tree |
| Fake-coder runner regressions | 26 cases passed, all 26 old-behavior regressions caught |
| Protected integrity/format/effects guard | Pass |

The `No model calls` line in the runner-regression summary describes that harness
only; it does not negate the actual model loop. The observed host/runtime/build
qualifications in the historical environment section also apply to these recorded
final checks. Exact check/setup commands and remaining handoff are in TESTING.md.

### Independent review and remaining gate

The documentation-task handoff reports independent **read-only source review**
of the actual loop-written code with **no issues**. This is code acceptance, not
an independent test rerun; the test evidence above is from the actual execution
records, not an attributed reviewer run. The original preparation-only STOP and
post-loop code-review gate are complete.

This final documentation refresh changes no implementation behavior, acceptance
tests or judge expectations. Protected documentation/evidence and their inventory
hashes are parent-author maintenance outside the coder loop. Version stays 0.1.0;
complete owner release sign-off and an explicitly authorized PyPI handoff remain
required. No upload, push, merge or tag is performed or implied. Finite corpus,
bounded oracle and source review are not proof of all-sequence conformance,
universal thread fairness, actual OOM recovery or performance parity. Hosted CI,
other platforms and untested runtimes are not claimed.

Documentation-refresh validation against the actual implementation: integrity
(`python3 -B scripts/kit_check.py`) and `git diff --check` passed; focused
`python3 -B scripts/package_check.py` passed on both 3.15.0 and 3.11.15 with the
refreshed README. Both examples and their expected output were verified unchanged;
task commands/expectations were unchanged (only TESTING.md protection was added).
The expensive runner regressions were not rerun solely for these docs edits.

# Verified bounded kit — STOP before real coder loop

**This is kit reachability evidence, not implemented-library completion.** The
checkout deliberately retains stubs in `dwrr/_engine.py` and `scripts/_adapter.py`.
No real coder/model call, push or publication occurred. Parent review is required
before the exact README loop command; publication requires complete owner sign-off.

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

Residual gates: parent acceptance of this kit; review of real coder output after
loop; owner complete release sign-off before any PyPI publication. Finite tests
are not proof of all-sequence conformance, universal thread fairness, OOM recovery
or speed parity. Live model availability/auth/spending remains untested by design.
**STOP here: no real coder loop has started.**

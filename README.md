# dwrr-python

> **Approved bounded spec-loop kit — STOP before coder loop.** Public behavior
> below is the owner-approved target, not a delivered implementation. The checkout
> contains deliberate implementation stubs. Private-reference checks establish kit
> reachability only; they are not production Python conformance or release evidence.

## The need

Python application authors sharing a consumer among producers get a cost-aware
FIFO scheduler: each backlogged queue receives service in proportion to its
quantum, measured in caller-declared bytes, tokens, estimated work, or unit costs.
The application retrieves work and executes it itself. The scheduler does not
measure execution time or run jobs.

## At a glance

- Import: `dwrr`; distribution: `dwrr-python` (owner confirms availability).
  Publication requires complete owner sign-off; nothing is published by this kit.
- Python >= 3.11; standard library only at runtime. Minimum/current CPython
  compatibility is checked on the private reference, not yet on loop-written code.
- A mutable, generic `Scheduler[T]` with explicit `Item[T]` inputs and
  `Scheduled[T]` outputs. No immutable scheduler snapshots or implicit server.
- Internal locking serializes **every complete operation**, including validation
  and result creation. No async wrapper; the lock does not protect caller payload
  mutations or concurrent edits to an input batch.
- Target: language-neutral **dwrr-spec 0.1.1 (draft)**, all eight operations,
  all six errors, exact limits and service order. Conformance is unverified.
- MIT license; no runtime dependencies. Local initial version `0.1.0`.

## Requirements and installation

After the loop is accepted and implemented, install from this checkout:

```sh
python3 -m pip install .
```

Do not install these stubs for real use. Setuptools builds an ordinary pure-Python
wheel/sdist: a minimal conventional local build detail, not a new API promise.
The dev/test driver and frozen verification kit are checkout-only, not installed
CLI entry points. No repository URL or PyPI release claim is made. The core needs
no Go, Elixir, credentials, configuration or network service.

## First useful example

Queue 0 earns 2 credit per visit and queue 1 earns 3. Queue 1's head costs 4,
so it must carry credit across visits before serving it. Target executable example:

```python
from dwrr import Item, Scheduler

scheduler = Scheduler[str](2)
scheduler.set_quantum(0, 2)
scheduler.set_quantum(1, 3)
scheduler.enqueue(0, [Item("a", 2), Item("b", 2)])
scheduler.enqueue(1, [Item("x", 4), Item("y", 1)])

served = scheduler.take(10)
print([(item.queue, item.value, item.cost) for item in served])
```

Expected output (verified only with the private reference):

```text
[(0, 'a', 2), (0, 'b', 2), (1, 'x', 4), (1, 'y', 1)]
```

## Public API

`T` is the opaque payload type. `Item(value, cost)` and
`Scheduled(queue, value, cost)` are frozen dataclass records with those public
fields. They are shallowly immutable: the payload is retained and returned by
reference, not copied, hashed, compared or explicitly executed by scheduling operations.
Item construction does not validate costs; enqueue does, preserving batch error
precedence. Costs cannot be changed after acceptance through the supported API.

| Call | Successful result |
| --- | --- |
| `Scheduler[T](count: int)` | New mutable scheduler with `count` queues |
| `enqueue(queue: int, items: list[Item[T]] \| tuple[Item[T], ...])` | `None`; appends the whole batch |
| `set_quantum(queue: int, quantum: int)` | `None`; changes the next grant |
| `add_queue()` | `int`; index of the appended queue |
| `remove_queue()` | `None`; discards only the last queue and its items |
| `remove_head(queue: int)` | `Item[T] \| None`; withdraws without scheduling |
| `drain_queue(queue: int)` | `list[Item[T]]`; withdraws everything FIFO |
| `take(n: int)` | `list[Scheduled[T]]`; removes up to `n` items in service order |

Exports also include `SchedulerError`, `MAX_COST` and `MAX_QUANTUM`. There is no
public state-editing, inspection, copying, reset, iterator or persistence API in
this stage. Lists returned by operations are independent containers. Record
identity is not promised; payload identity is.

### Withdrawal and recovery

Independent example, including a whole-batch rejection:

```python
from dwrr import Item, Scheduler, SchedulerError

scheduler = Scheduler[str](1)
try:
    scheduler.enqueue(0, [Item("not retained", 1), Item("invalid", 0)])
except SchedulerError as error:
    print(error.code)
print(scheduler.take(10))

scheduler.enqueue(0, [Item("cancelled", 5), Item("ready", 1)])
removed = scheduler.remove_head(0)
remaining = scheduler.drain_queue(0)
print(removed.value, [item.value for item in remaining])
```

Expected output (verified only with the private reference):

```text
zero_cost
[]
cancelled ['ready']
```

## Behavior worth knowing

- Queues are indexed `0..count-1`, initially empty with quantum 1 and credit 0.
  Adding a queue preserves existing indices; removing affects only the last.
  An added queue may reuse a removed index. Indices are not permanent IDs.
- Visits cycle in index order. A nonempty queue receives its quantum once at the
  start of a visit, then spends credit on FIFO heads. A blocked head ends the
  visit; later cheaper items never overtake it. Empty queues hold no credit.
- **Take is a retrieval limit, not a fairness cap.** Stopping at `n` preserves a
  nonempty active visit and its credit. The next take resumes without another
  grant, even if that resumed head will block. Fewer than `n` results means all
  queues are empty. Zero queues, all empty, or `take(0)` return `[]`; zero and
  already-empty takes change no state.
- Enqueued items join an active visit without another grant. Reweighting preserves
  credit and the visit; its quantum applies at the next grant, not on resume.
- Withdrawals do not spend credit. Emptying a queue resets its credit and closes
  its active visit, advancing the cursor. Removing the active last queue cancels
  that visit and repairs the cursor as defined in SPEC.
- `MAX_COST = MAX_QUANTUM = 2**63 - 1`. Every integer from 1 through the limit is
  accepted, including values beyond `2**53`. Credit is exact through `2**64 - 3`;
  no float arithmetic, saturation or wrapping is allowed.
- Long runs of idle rounds are computed directly while preserving exact order.
  A maximum-cost item with quantum 1 must not require `2**63` loop iterations.
  No throughput, latency, allocation, sparse-queue complexity or Go speed-parity
  claim is made. No result allocation is proportional merely to requested `n`.
- Fairness concerns declared cost while queues stay backlogged with fixed quanta,
  not item counts, elapsed time or arbitrary changing backlogs. The scheduler is
  nonblocking in the queueing sense: it never waits for producers, but a large
  batch still takes CPU time and memory to select.

## Failures and recovery

`SchedulerError` subclasses `ValueError`; its stable `.code` is one of:

| Code | Condition |
| --- | --- |
| `invalid_index` | Negative queue index or index beyond the current last queue |
| `zero_cost` / `cost_too_large` | First invalid item has cost 0 / greater than `MAX_COST` |
| `zero_quantum` / `quantum_too_large` | Quantum is 0 / greater than `MAX_QUANTUM` |
| `negative_take` | Retrieval limit is negative |

Queue validation precedes costs/quantum validation, including an empty batch.
Enqueue validates in item order before appending anything. These failures leave
all scheduler state unchanged; catch the exception, correct the input, and reuse
the same scheduler. Exception messages are not a stable interface.

Numeric arguments must be built-in `int`, **not `bool`**, floats or coerced
numeric objects. Count must be nonnegative. Negative costs/quanta and negative
count raise ordinary `ValueError`, not a new shared error code. Wrong argument
or batch-element types raise `TypeError`. All documented validation failures
preserve state. Precise validation order is in [SPEC §3](SPEC.md#3-validation-and-errors).
These Python-domain rules are approved additions where the language-neutral
spec does not define an input. Arbitrary iterables/generators are not accepted
as batches. Resource exhaustion, process termination, forged private state,
bypassing record immutability and concurrent input-batch mutation are outside
the atomicity guarantee; there is no crash-recovery promise.

## Effects, privacy and non-goals

The core only mutates its own in-memory scheduling state. It performs no file,
network, subprocess, environment/configuration, logging, telemetry, model or
credential access. It starts no thread, task or process. It retains payload
references while queued; returned items belong to the caller. Removing/draining
releases scheduler-owned references to removed payloads, but is not secure
erasure and cannot free references held elsewhere. Normal Python reference release
may run finalizers/weakref callbacks; discarded queues are retained until the
operation lock is released and state is coherent. This does not promise safety
for arbitrary GC, signal handlers or asynchronous same-thread callback reentry. Caller mutation of a shared
payload is visible; the scheduler neither protects nor deep-copies it.

Not included: job execution, worker pools, blocking dequeue, backpressure, queue
capacity/admission policy, keyed queues, priority levels, deadlines, persistence,
distributed fairness, async wrappers or a production CLI. The dev/test
conformance driver is the only stdio interface; it is not a general command tool.
No configuration precedence, secrets management or `doctor` command is needed.

## Compatibility and verification target

[SPEC.md](SPEC.md) is subordinate to this README and pins the inspected sources.
The shared corpus currently contains **1,839 cases / 44,728 steps in seven files**;
the sibling working-tree protocol checker now has **41 checks** (36 at the historical
pin). The expanded histories cover unused recognized fields and arbitrary-size
integers, without changing the corpus. These are
frozen verification targets, **not implemented-library pass results**. Acceptance includes all
corpus files as native core calls, unchanged external replay, the protocol checker,
focused Python-domain tests, an independent bounded naive oracle, and executable
README examples. The kit includes these checks; see [KIT-VERIFICATION.md](KIT-VERIFICATION.md) for
failing-stub/passing-reference evidence and limitations.

Compatibility is with shared draft 0.1.1, not every sibling feature:

- Go v0.10.1 supplies the recorded corpus. The inspected Go working tree has
  **uncommitted, unreleased** callable quanta, whole-number float inputs,
  speculative scheduling and state-change errors. None is in shared 0.1.1 and
  none is included in this Python stage. Quanta here are fixed integer values;
  applications may explicitly reweight between calls.
- The shared Go adapter now supports published and current Take signatures,
  ignores unused recognized fields, and preserves arbitrary-size payload/index/n
  integers, including count. Valid nonnegative counts above Go's native `int`
  representation now fail as resources (stderr, exit 1, no response or later
  processing; prior responses stand), not protocol errors. This permitted resource
  failure adds no Python/Elixir integer cap or guaranteed allocation/OOM recovery.
  Go's 64 MiB line restriction remains an adapter qualification. Current Go's
  generation exhaustion also restricts even fixed-only scheduling relative to the
  shared all-sequences contract. Bounded conformance passes do not erase this.
- Elixir supplies useful pure-core/adapter/driver separation and exact idle-skip
  reasoning. Python uses mutable internally locked state, not immutable
  branching or the optional GenServer wrapper. Elixir approvals do not authorize
  Python decisions.

## Owner decisions and release gate

The explicit owner approvals supplied for kit preparation supersede the historical
unapproved draft and handoff. No approval is inferred from sibling work.

| ID | Approved decision |
| --- | --- |
| D1 | All shared fixed-quantum 0.1.1 operations plus dev/test driver; defer callbacks and float conveniences. |
| D2 | Mutable `Scheduler[T]` with internal complete-operation locking; no async wrapper. |
| D3 | Frozen shallow records, opaque payload refs; six `SchedulerError(ValueError)` codes; ordinary TypeError/ValueError outside domain; strict built-in ints, list/tuple batches. |
| D4 | Python >=3.11, `dwrr`, `dwrr-python` (owner says available), MIT, no runtime dependencies. |
| D5 | Full frozen conformance, independent bounded naive oracle, exact skip, examples and isolated/archive installs. |

Local packaging: setuptools pure-Python wheel/sdist, initial `0.1.0`; no optional
runtime modules or speculative scaffolding. Publishing is in scope **only after
complete owner sign-off**, never from this preparation or automatically in a task.
Pushes and sibling changes are not authorized here. Hosted CI and performance
claims are not part of this bounded kit.

## Kit use — STOP for parent review

Prepared on `spec-loop/python-core-kit`, branched from the existing checkout.
The pre-existing README/SPEC edits were integrated, not reset. Historically this
project began as two draft documents without a Git repository; that is not its
current state. Only `_engine.py` and `scripts/_adapter.py` are implementation
files; `PROGRESS.md` is coder notes. All other kit files are protected (inventory
and hashes in `kit-manifest.json`). Five useful tasks, whole tree last; no artificial
15-task padding. The complete facade owns internal locking; engine operations
must obey the protected private State seam, not expose it as public API.

Prerequisites: Bash, Git, jq, timeout/gtimeout, Python >=3.11, Pi and authorized
provider credentials. Before offline judge checks, prepare dev build tools:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install build 'setuptools>=77' wheel
mkdir -p .loop/build-wheels
.venv/bin/python -m pip download --only-binary=:all: --dest .loop/build-wheels 'setuptools>=77' wheel packaging
bash scripts/loop.sh --check
```

`--check` must fail on delivered stubs. It runs the unchanged runner judge (no
formatter, no coder, no commits/discards). Judge commands never build in the source
tree and permit incremental implementation: kit check checks protected bytes,
syntax and forbidden effects, not unfinished later behavior. Standard-library
unittest tests print exact per-test success lines on stdout; skips/no-tests cannot
satisfy task expectations. Runner regression tests use fake coders in disposable
repos, **not real models**: `bash scripts/test_loop.sh`.

After parent acceptance ONLY, start from a clean, committed branch:

```sh
CHEAP_CMD='pi --provider anthropic --model claude-haiku-5-5 --thinking high --print --no-session' \
STRONG_CMD='pi --provider openai-codex --model gpt-6.1-sol --thinking high --print --no-session' \
STRONGEST_CMD='pi --provider openai-codex --model gpt-6.1-sol --thinking high --print --no-session' \
bash scripts/loop.sh
```

Do not omit the STRONGEST override: the unchanged runner's historical default is
`max`, but the owner approves **high**, not max. Do not substitute provider/model.
Local auto-commits and discarding **only failed-attempt-owned** changes, dependency
installation and model use are authorized; no real model call is authorized until
parent accepts this kit. The runner records exact commands in `.loop/loop.log`
and commit trailers; prompts/coder output/judge streams remain under `.loop/`.
`STOP` names a task that exhausted attempts. Review logs and saved discarded notes;
do not remove STOP or reset owner changes blindly. No push or publish command is
part of the kit. Offline catalog/CLI inspection is not a live provider-access test.

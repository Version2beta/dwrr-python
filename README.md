# dwrr-python

A cost-aware FIFO scheduler for Python applications sharing a consumer among
producers. The library is implemented and locally verified; version **0.1.0** is
not uploaded to PyPI. Publication still requires complete owner sign-off.

## Other languages

- [DWRR for Go](https://github.com/version2beta/dwrr)
- [DWRR for Elixir](https://github.com/version2beta/dwrr-elixir)

These libraries share fixed-quantum scheduling semantics, with language-specific
APIs and additional features. See each library's README for its supported contract.

## Shared specification

[dwrr-spec](https://github.com/version2beta/dwrr-spec) defines the shared
[fixed-quantum contract](https://github.com/version2beta/dwrr-spec/blob/main/SPEC.md),
[conformance corpus](https://github.com/version2beta/dwrr-spec/tree/main/corpus)
and [driver protocol](https://github.com/version2beta/dwrr-spec/blob/main/PROTOCOL.md) /
[conformance tools](https://github.com/version2beta/dwrr-spec/tree/main/tools).
They let implementations with different APIs check the same service order,
errors and numeric limits rather than rely on similar-looking algorithms.
This is a development/conformance resource, **not a runtime dependency**.
Pinned revisions and vendored snapshots make checks reproducible; they do not
automatically track current spec source or establish all-sequences conformance.

This implementation targets draft 0.1.1 using the vendored snapshot from
`243dd125470365df2c52a6ce72de3ee8ecfce3fe`; see
[vendor provenance](vendor/shared/PROVENANCE.md) and the local [mapping](SPEC.md).
Mutable state, whole-operation locking and Python-domain exceptions are local
API choices, not requirements imposed on Go or Elixir. CI replays the vendored
corpus/tools, not an automatically refreshed upstream checkout.

## The need

Python application authors sharing a consumer among producers get a cost-aware
FIFO scheduler: each backlogged queue receives service in proportion to its
quantum, measured in caller-declared bytes, tokens, estimated work, or unit costs.
The application retrieves work and executes it itself. The scheduler does not
measure execution time or run jobs.

## At a glance

- Import: `dwrr`; distribution: `dwrr-python` (owner confirms availability).
  Install locally from this checkout; no public release is claimed.
- Python >= 3.11; standard library only at runtime. The actual implementation
  passed the frozen checks on CPython 3.11.15 and 3.15.0 (Darwin arm64).
- A mutable, generic `Scheduler[T]` with explicit `Item[T]` inputs and
  `Scheduled[T]` outputs. No immutable scheduler snapshots or implicit server.
- Internal locking serializes **every complete operation**, including validation
  and result creation. No async wrapper; the lock does not protect caller payload
  mutations or concurrent edits to an input batch.
- Implements language-neutral **dwrr-spec 0.1.1 (draft)**: all eight operations,
  all six errors, exact limits and service order. Finite conformance checks pass;
  they are not proof for every possible operation sequence.
- MIT license; no runtime dependencies. Local initial version `0.1.0`.

## Requirements and installation

Install from this checkout (Python >= 3.11):

```sh
python3 -m pip install .
```

Setuptools builds an ordinary pure-Python wheel/sdist. Local version is `0.1.0`;
there is no published-package installation command yet.
The dev/test driver and frozen verification kit are checkout-only, not installed
CLI entry points. No public PyPI release is claimed. The core needs
no Go, Elixir, credentials, configuration or network service.

## First useful example

Queue 0 earns 2 credit per visit and queue 1 earns 3. Queue 1's head costs 4,
so it must carry credit across visits before serving it:

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

Expected output:

```text
[(0, 'a', 2), (0, 'b', 2), (1, 'x', 4), (1, 'y', 1)]
```

## Fair file-transfer example

[Standalone simulator](examples/fair_transfer/README.md): pretend FIFO transfers
with Basic/Team/Business byte quanta of 1024/2048/4096. It prints selection order
and cumulative bytes using repeated `take(1)` calls, with no real transfer I/O.
The example explains byte fairness, head blocking and why finite totals need not
be 1:2:4. Run it against a locally installed checkout; it is not packaged.

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

Expected output:

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
conformance driver is the only protocol stdio interface; it is not a general
command tool. The checkout-only fair-transfer example prints a simulation.
No configuration precedence, secrets management or `doctor` command is needed.

## Compatibility and verification

[SPEC.md](SPEC.md) is subordinate to this README and pins the shared draft 0.1.1
behavior and inspected sources. The actual loop-written implementation at
`b97fc29` passed T1–T5 on CPython 3.11.15 and 3.15.0 on 2026-11-19:

- All 31 Python tests, including native replay of **1,839 cases / 44,728 steps
  in seven files**, an independent bounded naive oracle and concurrency checks.
- Unchanged external corpus replay and all **41** protocol checks.
- Wheel/sdist metadata, isolated wheel/sdist/checkout installs, and both README
  examples executed against installed code.

Independent read-only code review reported no issues; it was not an independent
test rerun. [KIT-VERIFICATION.md](KIT-VERIFICATION.md) separates historical kit
reachability from actual implementation evidence and its limitations.
[TESTING.md](TESTING.md) records reproducible checks and the remaining release gate.
Other runtimes/platforms, hosted CI, universal thread fairness, resource-exhaustion
recovery and performance parity are not demonstrated.

Compatibility is with the shared fixed-integer-quantum contract, not every sibling
feature: no Go callable quanta, floats or speculative scheduling; no Elixir
immutable branching or GenServer wrapper. See SPEC §8 for historical source and
adapter qualifications; sibling approvals do not authorize Python decisions.

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
complete owner sign-off**, never automatically in a task.
Pushes and sibling changes are not authorized here. Hosted CI and performance
claims are not part of this bounded implementation.

## Historical spec-loop operations (2026-11-19)

The bounded kit was prepared on `spec-loop/python-core-kit`, from base
`9fddbb36f6faeeae8a4f5c45227863e1808dbf00`, with the owner's existing README/SPEC
edits integrated. Preparation commit `53d2fa1` intentionally contained stubs and
required parent acceptance before model calls. That preparation-only STOP is
historical: the authorized real loop subsequently implemented the engine and
adapter, ending at `b97fc29`; T1–T5 and independent source review passed.
No push or publication followed.

The five-task kit limited coder writes to `dwrr/_engine.py`,
`scripts/_adapter.py` and notes in `PROGRESS.md`; the other artifacts are protected
by `tasks.json` and `kit-manifest.json`. Final documentation/evidence maintenance
is parent-author work outside that coder loop. The complete facade owns locking;
the engine's State seam is private, not a supported public API.

The owner-pinned invocation used CHEAP Haiku 5.5 **high** and STRONG/STRONGEST
GPT-6.1-sol **high**, not the runner's historical `max` default:

```sh
CHEAP_CMD='pi --provider anthropic --model claude-haiku-5-5 --thinking high --print --no-session' \
STRONG_CMD='pi --provider openai-codex --model gpt-6.1-sol --thinking high --print --no-session' \
STRONGEST_CMD='pi --provider openai-codex --model gpt-6.1-sol --thinking high --print --no-session' \
bash scripts/loop.sh
```

This is a historical invocation, not a request to start another loop. Authorized
local auto-commits recorded exact coder commands in commit trailers. An interrupted
first run and the protected Item-subclass judge correction were followed by a
successful resumed run; selected sanitized final records are retained under
`verification/`. T5 already passed without a separate coder commit. Raw local
prompts, coder output, judge streams and attempt notes remain in ignored `.loop/`.
The fake-coder runner regression suite uses no models; the implementation loop
did use the authorized models. See KIT-VERIFICATION for the commit sequence and
TESTING for check/setup commands. Never clear a future `STOP` or discard owner
changes blindly; no push, merge, tag or publish is part of this workflow.

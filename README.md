# dwrr-python

> **Design draft — awaiting author review.** This describes proposed finished-tool
> behavior, not working software. The only product deliverables are this README
> and [SPEC.md](SPEC.md); examples and commands are promises, not executed evidence. No Python
> design decision is approved, and no implementation or readme-loop kit is authorized yet.

## The need

Python application authors sharing a consumer among producers get a cost-aware
FIFO scheduler: each backlogged queue receives service in proportion to its
quantum, measured in caller-declared bytes, tokens, estimated work, or unit costs.
The application retrieves work and executes it itself. The scheduler does not
measure execution time or run jobs.

## At a glance

- Proposed import: `dwrr`; proposed distribution: `dwrr-python` (availability and
  ownership not checked; no PyPI publication promised).
- Python >= 3.11; standard library only at runtime. Minimum/current CPython
  compatibility must be demonstrated later, not inferred from these drafts.
- A mutable, generic `Scheduler[T]` with explicit `Item[T]` inputs and
  `Scheduled[T]` outputs. No immutable scheduler snapshots or implicit server.
- Caller-owned synchronization: use one owner, or serialize **all** calls with
  the same external lock. No built-in thread safety or async API is promised.
- Target: language-neutral **dwrr-spec 0.1.1 (draft)**, all eight operations,
  all six errors, exact limits and service order. Conformance is unverified.
- Proposed license: MIT, following the sibling projects; no license file or
  release metadata has been prepared.

## Requirements and installation

After an approved implementation and packaging stage, install from this checkout:

```sh
python3 -m pip install .
```

This is **not runnable in the current documentation-only directory**. No
`pip install dwrr-python` command, package version, repository URL or publication
claim is made. Build backend/dependencies and release metadata remain deferred
until before the packaging kit; installing prerequisites requires permission.
The core needs no Go, Elixir, credentials, configuration or network service.

## First useful example

Queue 0 earns 2 credit per visit and queue 1 earns 3. Queue 1's head costs 4,
so it must carry credit across visits before serving it. Proposed executable example:

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

Expected output (not yet verified):

```text
[(0, 'a', 2), (0, 'b', 2), (1, 'x', 4), (1, 'y', 1)]
```

## Proposed public API

`T` is the opaque payload type. `Item(value, cost)` and
`Scheduled(queue, value, cost)` are frozen dataclass records with those public
fields. They are shallowly immutable: the payload is retained and returned by
reference, not copied, hashed, compared or executed by scheduling operations.
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

Proposed independent example, including a whole-batch rejection:

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

Expected output (not yet verified):

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
These Python-domain rules are proposed additions where the language-neutral
spec does not define an input. Arbitrary iterables/generators are not accepted
as batches. Resource exhaustion, process termination, forged private state,
bypassing record immutability and overlapping unsynchronized calls are outside
the atomicity guarantee; there is no crash-recovery promise.

## Effects, privacy and non-goals

The core only mutates its own in-memory scheduling state. It performs no file,
network, subprocess, environment/configuration, logging, telemetry, model or
credential access. It starts no thread, task or process. It retains payload
references while queued; returned items belong to the caller. Removing/draining
releases scheduler-owned references to removed payloads, but is not secure
erasure and cannot free references held elsewhere. Caller mutation of a shared
payload is visible; the scheduler neither protects nor deep-copies it.

Not included: job execution, worker pools, blocking dequeue, backpressure, queue
capacity/admission policy, keyed queues, priority levels, deadlines, persistence,
distributed fairness, async wrappers or a production CLI. The proposed dev/test
conformance driver is the only stdio interface; it is not a general command tool.
No configuration precedence, secrets management or `doctor` command is needed.

## Compatibility and verification target

[SPEC.md](SPEC.md) is subordinate to this README and pins the inspected sources.
The shared corpus currently contains **1,839 cases / 44,728 steps in seven files**;
the sibling working-tree protocol checker now has **41 checks** (36 at the historical
pin). The expanded histories cover unused recognized fields and arbitrary-size
integers, without changing the corpus. These are
available checks, **not Python pass results**. Proposed acceptance includes all
corpus files as native core calls, unchanged external replay, the protocol checker,
focused Python-domain tests, an independent bounded naive oracle, and executable
README examples. No tests, driver, kit or reference implementation exist here yet.

Compatibility is with shared draft 0.1.1, not every sibling feature:

- Go v0.10.1 supplies the recorded corpus. The inspected Go working tree has
  **uncommitted, unreleased** callable quanta, whole-number float inputs,
  speculative scheduling and state-change errors. None is in shared 0.1.1 and
  none is proposed for this Python stage. Quanta here are fixed integer values;
  applications may explicitly reweight between calls.
- The shared Go adapter now supports published and current Take signatures,
  ignores unused recognized fields, and preserves arbitrary-size payload/index/n
  integers. Its native-int constructor-count and 64 MiB line restrictions remain
  unresolved adapter qualifications, not Python/Elixir protocol caps. Current Go's
  generation exhaustion also restricts even fixed-only scheduling relative to the
  shared all-sequences contract. Bounded conformance passes do not erase this.
- Elixir supplies useful pure-core/adapter/driver separation and exact idle-skip
  reasoning. Python instead proposes mutable caller-owned state, not immutable
  branching or the optional GenServer wrapper. Elixir approvals do not authorize
  Python decisions.

## Decisions — author review gate

Every choice below is **proposed**, not approved. Please approve or amend the
relevant entry inline before affected kit preparation; silence is not approval.

| ID | Proposed decision and rationale | Status |
| --- | --- | --- |
| D1 | Target all of shared 0.1.1 core plus dev/test driver; exclude Go's unreleased adaptive extensions and Elixir Server. Keeps one exact, independently checkable contract. | Proposed — awaiting inline approval |
| D2 | Mutable `Scheduler[T]`, frozen records, eight operations above, no internal locking; caller serializes access. Minimal conventional Python library rather than a process or persistent-value framework. | Proposed — awaiting inline approval |
| D3 | One `SchedulerError(ValueError)` with six stable codes; strict built-in integers, local TypeError/ValueError for outside-domain inputs, list/tuple batches. Preserves shared precedence without inventing shared errors or generator side effects. | Proposed — awaiting inline approval |
| D4 | Python >=3.11, import `dwrr`, local distribution `dwrr-python`, MIT, no runtime dependencies. Package ownership/publication, version, backend and CI matrix deferred until before packaging work. | Proposed — awaiting inline approval |
| D5 | First bounded stage is the usable core, driver and verification described above; exact numeric skipping is required, sparse-queue optimization/performance targets deferred. Prove behavior before adding wrappers or tuning. | Proposed — awaiting inline approval |

**Approved decisions:** none for this Python library. **Deferred:** packaging
choices before its kit; any wrappers, adaptive policies or measured performance
contracts before a later design gate. Private representation and helper choices
remain implementation freedoms consistent with these promises; new public
behavior or weakened checks require another author decision.

## readme-loop operation boundary (not product commands)

**Stopped at author review.** No kit has been prepared or verified. At initial
draft review, no Git repo, branch, runner, tasks, tests, fixtures, stubs or private
reference was created. No model call, dependency installation, commit, staging
or discard was performed during that review.
Only source inspection and documentation checks support this Python draft. A later
authorized cross-language consistency pass corrected these documents and sibling
adapter/docs/tests; it did not approve D1–D5 or authorize a Python kit.

After actual inline design approval, obtain permission for the affected bounded
kit preparation and its verification. Before using the unchanged skill runner,
inspect its kit-format reference and script header, establish an authorized Git
repository and non-main branch, preserve all owner work, verify failing stubs and
passing private reference with the runner's judge, and return evidence for review.
Exact apply/check/run commands, protected paths, logs under `.loop/`, and `STOP`
handling must be added here with that kit; there is no safe run command yet.

Runner prerequisites are Bash, Git, jq, `timeout`/`gtimeout`, Python/check tools,
and an authorized Pi/provider setup. Do not install them without permission.
The runner auto-commits passes and discards failed attempt-owned changes: both
permissions, baseline commit authorization, model access/spending limits and
exact model commands require explicit owner consent separately from design approval.
The skill's pinned defaults, **shown for future confirmation only**, are:

```text
CHEAP_CMD: pi --provider anthropic --model claude-haiku-5-5 --thinking high --print --no-session
STRONG_CMD: pi --provider openai-codex --model gpt-6.1-sol --thinking high --print --no-session
STRONGEST_CMD: pi --provider openai-codex --model gpt-6.1-sol --thinking max --print --no-session
```

No command availability or provider access was checked, and none was run. Do not
substitute models silently. Publication, remotes and tags would need separate
permissions and are not part of this review stage.

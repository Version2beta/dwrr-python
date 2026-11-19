# dwrr-python supporting specification

**Status: proposed design-review draft; no Python owner approval or kit exists.**
This is subordinate to the root [README.md](README.md), specifically “Proposed
public API”, “Behavior worth knowing”, “Failures and recovery”, “Effects, privacy
and non-goals”, “Compatibility and verification target”, and decisions D1–D5.
It clarifies those promises; it cannot expand or override them. A contradiction
blocks affected preparation until the author resolves it in the README. Nothing
below authorizes tests, fixtures, implementation, model calls or Git operations.

## 1. Scope and authority

Proposed first usable stage: Python core, typed records, six-code exception,
exact direct idle-round calculation, and dev/test conformance driver, with the
checks mapped in §7. All eight shared operations are included. Only README.md
and this file are delivered at this review gate.

The behavioral reference is `../dwrr-spec/SPEC.md` **0.1.1 (draft)**, §§2–8;
the wire reference is its `PROTOCOL.md` **0.1.1 (draft)**. Read the current checked
document bytes in §8 (historical commit plus explicitly identified consistency
corrections). Every valid operation sequence must have the reference results,
errors and service order; matching the finite corpus alone is not the whole
semantic requirement. Python naming and errors map as below. A future upstream
change does not silently change this target.

Fixed integer quanta only. No callable quanta, float inputs, speculative plans,
state-change error, Server/thread/async wrapper, immutable snapshots, worker
execution, persistence, capacity or keyed-queue extension. No performance parity
or sparse-queue complexity commitment. Runtime library and stdio driver are
separate boundaries: the latter handles integer-valued wire payloads; the core
accepts arbitrary Python objects.

## 2. Public data and ownership

Proposed exports from `dwrr`:

- `MAX_COST = MAX_QUANTUM = 9_223_372_036_854_775_807`.
- `Item[T]`: frozen generic dataclass with positional/keyword fields
  `value: T`, `cost: int`, in that order; both required, no default cost.
- `Scheduled[T]`: frozen generic dataclass with fields
  `queue: int`, `value: T`, `cost: int`, in that order; all required.
- `SchedulerError(ValueError)`: exposes a string `.code` from the six-code set
  in §3. No message text, subclass per code or exception serialization promise.
- `Scheduler[T]`: mutable scheduler with the constructor and methods in §4.
  Generic annotations document values; the scheduler does not runtime-check T.

Item construction only records fields; cost type/range checks occur on enqueue,
not in the record constructor. This permits `Item(value, 0)` to reach batch
validation, including invalid-index precedence. Frozen means ordinary field
assignment is prohibited, not deep immutability or a defense against deliberate
Python reflection. Callers must not forge state or bypass frozen fields.

Store payload references without invoking payload equality, hashing, conversion,
copying or callability. Returned `.value is original_value` must hold, including
for `None`, mutable objects and callables. Scheduling never executes a payload.
Payload mutations remain caller-owned; they cannot change accepted item costs.
`None` from remove-head means no item, distinguishable from `Item(None, cost)`.

Returned lists are fresh containers, not queue storage. Item/record identity is
unspecified. Scheduler copying, equality, pickling, subclass customization,
public internal fields, snapshots and state introspection are not supported APIs.
Dropping items must drop scheduler-owned payload references; caller-held outputs
or payload references may keep them alive. There is no secure-erasure guarantee.

One owner executes calls sequentially. If shared, the caller locks **every**
operation for its entire duration with the same external lock; no built-in lock,
GIL-based safety or linearizability for unsynchronized overlap is promised.
Successful mutators update the same scheduler; they never return a replacement.

## 3. Validation and errors

### Shared errors

For inputs in the documented Python domain, raise `SchedulerError` with exactly
the shared `.code`:

| Operation | Validation order |
| --- | --- |
| `enqueue` | `invalid_index`; then each item in input order: `zero_cost`, or `cost_too_large` |
| `set_quantum` | `invalid_index`, `zero_quantum`, `quantum_too_large` |
| `remove_head`, `drain_queue` | `invalid_index` |
| `take` | `negative_take` |

An index is invalid iff less than zero or at least the current queue count;
negative indexing is **not** Python's from-the-end shorthand here. Cost/quantum
0 yields its zero code; any positive integer above its MAX yields its too-large
code, even above `2**64-1` through the core API. Every 1..MAX value is valid.
Negative take limits use `negative_take`, including with zero queues.

### Proposed Python-domain rules

These settle inputs outside the language-neutral nonnegative-cost domain, not
new shared codes. They follow the strict-integer distinction used by the shared
Python model's protocol parser and the separation of domain errors in Elixir.

1. Numeric parameters must have `type(x) is int`. No bool, float, strings,
   int subclasses or `__index__`/coercion fallback. Wrong types raise `TypeError`.
2. Constructor count must be nonnegative; negative count raises ordinary
   `ValueError` (not `SchedulerError`).
3. Queue-taking operations check the index's type, then its range, before
   inspecting the batch or quantum. Thus invalid index plus zero quantum,
   malformed batch or wrong quantum type reports `invalid_index` first.
4. For enqueue, after valid index, require `type(items)` to be list or tuple;
   other containers/iterables raise `TypeError`. Each element must be an `Item`
   instance. Check elements in order: record type, cost type, then sign/range.
   Wrong element/cost type raises `TypeError`; negative cost raises ordinary
   `ValueError`; zero/oversized nonnegative cost raises its shared error. Stop
   at the first invalid element; never append a prefix.
5. For set-quantum, after valid index, check quantum type then sign/range.
   Negative quantum raises ordinary `ValueError`; zero/oversized nonnegative
   quantum raises its shared error.
6. For take, check n's type, then negative/zero/positive cases.

No item payload validation occurs. There is no batch iteration that executes a
caller generator. Mutation of the input list during a call is unsupported.
All documented validation failures, shared and Python-local, leave all queues,
quanta, credits, cursor and active flag unchanged. No default logging occurs.
Resource exhaustion, cancellation/termination and unsupported caller interference
are not rollback guarantees and must not be relabeled as shared error codes.
No artificial queue/item/take cap is added to the core contract.

## 4. State and exact operations

This is the abstract state, **not** a public representation requirement:
ordered queues `0..N-1`, each FIFO items, quantum and credit; cursor; active flag.
After every supported operation:

- Empty queues have credit 0.
- At N=0, cursor=0; otherwise `0 <= cursor < N`.
- Active implies the cursor queue is nonempty.
- Credit is an exact nonnegative integer at most
  `18_446_744_073_709_551_613` (`2**64 - 3`).

“Advance” means `cursor = (cursor + 1) % N`. “Close visit” means clear active,
then advance. Advance is used only where N>0. Observable behavior is exactly
shared SPEC §5, summarized here with Python signatures and results.

### Constructor: `Scheduler[T](count: int)`

Create count empty queues, quantum 1 and credit 0 each. Set cursor 0, inactive.
Count zero is valid. Constructor returns the scheduler instance.

### `enqueue(queue: int, items: list[Item[T]] | tuple[Item[T], ...]) -> None`

Validate as §3, then append every item FIFO as one batch. An empty batch still
checks the index, then changes nothing. No credit, cursor or active change.
Appending to the active queue joins that visit without another grant.

### `set_quantum(queue: int, quantum: int) -> None`

Validate as §3; replace only the selected quantum. Preserve credit, cursor,
items and active. The new value is used on the next grant, never on resuming a
paused active visit. Setting the same quantum changes nothing.

### `add_queue() -> int`

Append empty queue with quantum 1 and credit 0; return old N. Cursor and active
unchanged. Adding at N=0 leaves cursor 0, inactive. Existing indices do not move.

### `remove_queue() -> None`

At N=0 do nothing. Otherwise let last=N-1:

1. If active and cursor==last, clear active and set cursor=0.
2. Remove that queue and discard its items, quantum and credit; N becomes last.
3. If last==0 set cursor=0; else if cursor>=last set cursor=cursor % last.

Other queues retain their items, credit, quantum and indices. The removed index
may be reused by a later add. Removed items are not returned.

### `remove_head(queue: int) -> Item[T] | None`

Validate index. Empty queue: return None with no state change. Otherwise withdraw
its FIFO head without spending credit. If items remain, preserve credit and any
active visit. If now empty, reset credit to 0 and, only if this was the active
cursor queue, close the visit. Return the withdrawn record.

### `drain_queue(queue: int) -> list[Item[T]]`

Validate index, withdraw all items FIFO (possibly []), and reset its credit to 0.
If active on that queue, close the visit. Otherwise cursor/active stay unchanged.
No scheduling or credit expenditure. Quantum unchanged.

### `take(n: int) -> list[Scheduled[T]]`

Validate n. At zero return [] without changing state. While fewer than n results
and some queue has items:

1. Let q=cursor. If not active: if q is empty, reset its credit to 0, advance and
   continue; otherwise add its quantum to its credit and set active=true.
2. If credit[q] < head.cost, close the visit and continue. Never inspect a later
   item for eligibility while the head blocks.
3. Otherwise debit head.cost, pop head, append
   `Scheduled(q, head.value, head.cost)` to results.
4. If q is now empty, reset credit to 0 and close the visit.

Stop at n or all empty. Reaching n with items left in the active queue preserves
that visit and its remaining credit, even if the next head cannot be afforded.
Resume without granting. Zero queues/already-all-empty return [] without moving
the cursor. All normal results are lists, never None. No output storage is
preallocated solely in proportion to n when fewer items exist.

## 5. Exactness and algorithm freedoms

Python arbitrary-precision integers do not relax the shared cost/quantum limits.
Use exact integer arithmetic, never floating-point division/ceil or rounded
credit. Direct idle-round calculation is required to handle maximum legal cost
with quantum 1 without visiting each numeric round. This is a practicality
requirement, not a benchmark or constant-time claim for every operation.

One valid optimization, informative rather than a fixed internal seam: with no
active visit and all busy heads strictly unaffordable, compute

```text
r = min((head_cost[i] - credit[i] - 1) // quantum[i] for each busy i)
```

Grant r quanta to each busy queue without serving anything, leaving the same
inactive cursor. Each skipped complete cycle still leaves every head blocked;
execute the next cycle normally in cursor order. If any head is affordable,
this skip is not valid. A resumed active visit must never be regranted. The
Elixir design demonstrates establishing unaffordability after a full unproductive
busy cycle; the upstream Python model demonstrates another valid inactive-point
check. Neither strategy is mandated here; outputs and state effects must match.

Representation, private helpers, FIFO storage, busy membership/traversal and
optimization trigger are local implementation freedoms. A deque is a natural
candidate, not an approved public storage contract. Scanning empty queues is
allowed at this stage; no ordered busy-set or bitmap requirement is imported
from siblings. No complexity claim may be added without a reviewed promise and
supporting checks. Retained storage should represent queues/items, not a history
of grants or results; no observable scheduler history is part of the API.

## 6. Dev/test conformance driver

Proposed repository-only entry point, not a published CLI API:
`python3 scripts/conformance_driver.py`, run from this project after authorized
local installation. Driver owns one scheduler and stdin/stdout. It imports and
uses the public Python core; it must not substitute `tools/spec_model.py`, invoke
Go/Elixir, or recognize recorded cases. No files, network or models are used.

The complete pinned PROTOCOL.md applies, including:

- UTF-8 JSON Lines: one request object per line, exactly one response object plus
  newline for each valid request. Flush **each** response before reading another
  request; no banners, import/build output or diagnostics on stdout. EOF exits 0.
- Validate the whole request before invoking any core operation. Malformed JSON,
  blank/whitespace-only lines, nonobjects, unknown/missing op, request before first
  new, missing/wrong required fields or negative count: category diagnostic on
  stderr, exit 2, no response for that line or later lines. Prior responses stand.
  Do not echo payloads or whole requests in driver diagnostics.
- Extra unused fields are ignored. Duplicate object keys are unspecified upstream;
  either handling is permitted, not a compatibility promise. JSON integers must
  be tokens without fraction/exponent, not booleans or strings. Python's permissive
  acceptance of NaN/Infinity must not turn them into valid JSON requests.
- Required integer fields: count, queue, n and every item value; count>=0.
  The corpus uses signed 32-bit integers, but the protocol does not prescribe that
  as a rejection bound. Do not silently add a wire magnitude or line-size cap.
  Interpreter parsing/serialization limits must be addressed before the driver
  kit is finalized; resource exhaustion is not a scheduler error (§9).
- Costs/quanta are canonical decimal **strings**, full grammar `0|[1-9][0-9]*`,
  range 0..18_446_744_073_709_551_615 (`2**64-1`). No signs, spaces, leading zeroes,
  Unicode-digit substitutions or decimal points. In-range zero and values above
  the scheduler MAX reach shared scheduler validation. Out-of-wire-range strings
  are protocol errors, not cost/quantum-too-large responses.
- Protocol-first precedence is distinct from core index-first precedence:
  invalid queue + cost `"01"` exits 2; invalid queue + cost `"0"` reports
  `invalid_index` and continues. All enqueue item shapes/types must be parsed
  before any scheduler check, even if an earlier parsed cost is zero.
- A new request replaces the current scheduler. SchedulerError yields
  `{"error":"<code>"}` and continues with unchanged state.

Successful response mapping (wire values are integers, costs decimal strings):

| Operation | `ok` value |
| --- | --- |
| new, enqueue, set_quantum, remove_queue | null |
| add_queue | New index |
| remove_head | null or `{"value":v,"cost":"c"}` |
| drain_queue | List of `{"value":v,"cost":"c"}` |
| take | List of `{"queue":q,"value":v,"cost":"c"}` |

Empty collection is [], not null. Responses compare as parsed JSON with exact
values; key order/whitespace are irrelevant, number/string distinction is not.
The core never performs JSON conversion; the adapter handles wire shape and codes.

## 7. Promise-to-check mapping (intended, not prepared)

No test below exists or has run in this directory. These are approval-stage
acceptance targets, not a tasks.json, kit manifest, judge expectations or pass
report. Source-named tests should identify the relevant operation and failure.

| README promise / shared source | Intended checks |
| --- | --- |
| API/first example | Execute both README Python histories; derive results from actual calls; verify exact printed output, imports and result shapes |
| Records/ownership/effects | Frozen field assignment; opaque unhashable/mutable/callable/None values preserve identity; independent output lists; no payload equality/hash/call invocation; no runtime I/O/logging/process/config hooks by source review plus focused seam checks |
| Constructor/add/remove / shared §§5.1, 5.4–5.5 | Counts 0/1/many; default quantum; last deletion active/inactive; cursor repair; removal empty; reuse index without stale state |
| Enqueue/errors / shared §§5.2, 6 | Empty batch still checks index; first-invalid order; valid prefix rejected atomically; invalid index beats costs; errors followed by successful operations prove no state mutation |
| Set quantum / shared §5.3 | Preserve credit and active; same-value no-op; affect next grant only; zero/oversized and index-first failures |
| Head/drain / shared §§5.6–5.7 | FIFO withdrawal; None vs Item(None,cost); empty no-op; credit reset and active closure only on emptying the visited queue |
| Take / shared §5.8 | Exact affordability equality; blocked head/no overtaking; retrieval split/resume equivalence; join/reweight during paused visit; zero/negative/all-empty; no allocation proportional merely to huge n |
| Exact limits/idle skip / shared §§2, 8 | 1, 2**53+1, MAX, MAX+1 and large Python ints; reachable peak credit 2**64-3; MAX-cost/quantum-1 bounded-time fixture; cursor order/ties/active resume/withdraw-exposed affordable head |
| Python-domain failures | bool/non-int arguments, negative count/cost/quantum, malformed batch/records, rejected generator without iteration; state remains usable after every validation failure |
| All shared operations | All seven corpus files replayed natively through public methods, asserting nonzero exact case/step counts; no external model invoked in that executor |
| General behavioral confidence | Independent bounded naive step-by-step oracle over small mixed valid/invalid traces; FIFO/conservation/invariants, deterministic replay and split-take equivalence; bounded fixed-quantum continuously-backlogged fairness only |
| Wire contract | Unchanged replay plus check_driver; additional malformed UTF-8, bool/exponent fields, all-item protocol-first validation, wire upper bounds, no-payload diagnostics, fresh new and scheduler-error continuation |
| Useful package | After packaging decisions, install in isolated environment and run public examples without sibling/runtime dependencies; verify selected minimum/current Python runtimes |

The naive oracle must not share production scheduling/skip helpers or import
upstream's optimized model as the implementation. Keep its trace magnitudes and
step count bounded; use analytic/corpus fixtures rather than stepping `2**63`
rounds. No third-party property-testing dependency is proposed. A review of the
skip proof and mutation sensitivity (in a separately authorized disposable copy)
should complement output checks; never mutate siblings or expected corpus data.
Private invariant checks may inspect an agreed test seam when preparing a kit;
that seam must not become a new public API accidentally.

Available upstream corpus, counted from the inspected JSONL files:

| File | Cases | Steps |
| --- | ---: | ---: |
| examples.jsonl | 2 | 15 |
| edge-cases.jsonl | 20 | 225 |
| errors.jsonl | 10 | 70 |
| boundaries.jsonl | 7 | 53 |
| random-small.jsonl | 1,000 | 23,659 |
| random-large.jsonl | 500 | 13,933 |
| random-skip.jsonl | 300 | 6,773 |
| **Total** | **1,839** | **44,728** |

Examples cover shared examples/bytes; edge cases cover mutation and visit rules;
errors cover codes, precedence and atomicity; boundaries cover numeric limits,
peak credit and huge skips; random files cover small domains, near-limit arithmetic
and idle cycles respectively. Upstream records responses from Go v0.10.1 and
cross-checks its executable model; four huge boundary cases omit the infeasible
step-by-step model run. Seeds: 20261112, 20261113, 20261114 respectively for the
three random files. This is corpus provenance, not Python validation.

For a later implemented driver, intended external checks from this root are:

```sh
python3 ../dwrr-spec/tools/replay.py --driver 'python3 scripts/conformance_driver.py'
python3 ../dwrr-spec/tools/check_driver.py --driver 'python3 scripts/conformance_driver.py'
```

The historical upstream tools at the commit below have these summaries:
`PASS: 1839 cases, 44728 steps, 7 files` and
`PASS: 36 of 36 checks passed`. The intentionally corrected working-tree
checker now expects `PASS: 41 of 41 checks passed`; its source hash is recorded
below, separately from that historical commit. All prior checks and corpus bytes
remain. Neither command was run against Python here.
If fixtures are later copied, preserve source bytes, hashes, provenance and MIT
license; copying/preparing them is not authorized by this draft. Upstream's live
generating/fuzzing/shrinking harness is planned, not available evidence.

## 8. Source provenance and ambiguity resolution

Historical inspection commits, with current correction overlays identified below:

| Source | Exact revision / status | Use |
| --- | --- | --- |
| `../dwrr-spec` | `8a0e3cf9ae860ba207213590c00feeb822bdd8f2`; now dirty with intentional consistency corrections | Normative behavior/protocol 0.1.1 draft; corpus and tools |
| `../dwrr` | HEAD `492dc7e3e54f430212f483a728957ff7f151b4a5`; dirty tracked/untracked working tree | Informative APIs, ownership, current unreleased extensions; **not** an immutable source pin for inspected working-tree bytes |
| Go v0.10.1 tag | `7109d4d4da265258f348598a378545656db0c241` | Corpus's recorded reference release, not current Go working tree |
| `../dwrr-elixir` | `07729f3da8149826bc5ab3561ce2ef601dd9bd12`; clean at initial inspection | README, SPEC, docs/SPEC-DRAFT.md, core/data/driver separation and design tradeoffs |

During documentation validation, external activity advanced Elixir HEAD to
`4e170fc9036056e5e296972c785934238a8906a3` (clean). A read-only comparison confirmed
that all six inspected Elixir files listed below were unchanged between those
revisions; the three inspected design-document hashes also match the initial
commit bytes. Provenance above intentionally retains the inspected snapshot,
not a claim that another project's branch is stationary. A runtime-owned `.wtha/`
also appeared here; it was not authored, changed or removed by this task.

Current authoritative SHA-256 of selected inspected files. The shared SPEC and
PROTOCOL and Go README hashes below supersede the initial inspection hashes
because of intentional consistency wording/mapping/qualification corrections.
Shared version remains draft 0.1.1; no corpus/tag identity is changed:

```text
dwrr-spec/SPEC.md
  0096790e040a63f65dcb89f54a8b0d944b309da262caefc76e0217bc415c06cf
dwrr-spec/PROTOCOL.md
  c52a562c46b6d15054b166ada7eaa83e5d3609179c9f8f6415917dbaae40beac
dwrr/dwrr.go
  827c9b158fdc57acf7b9f67350f2cc37ade10dabc6b7edaadde801f2287791cb
dwrr/README.md
  e4cc7864e4485a21f0690c485b0c86daf03abcd6e8afd6618e1dcf5820b6d56a
```

The historical Elixir comparison above predates this correction pass. Elixir
HEAD is still `4e170fc9036056e5e296972c785934238a8906a3`, now with intentional
documentation edits. Its vendored shared documents, corpus and provenance/hash
guards retain the original immutable `8a0e3cf` snapshot; do not relabel them as
these uncommitted shared corrections. No scheduler semantics/corpus changed.
Additional current overlay hashes (not immutable commit pins):

```text
dwrr-spec/tools/check_driver.py
  ccbaa88298d9e3418b50433ae90d435876bc825af799bdc55f9888c92e9f7775
dwrr-spec/drivers/go/main.go
  d8ef31b1885b02be2f39ff87b82543486516b6236a7f862e7e871bfb6c02d5e4
dwrr-spec/drivers/go/README.md
  cfa93b014b3301e9ed7c3ce16c8f6f53cf324154a1125bad407eda29ddb8c7b7
dwrr-elixir/README.md
  736c88c1e1df9151e9becda03bc68b2f0e827b046ce0aa7d633ed3511b462260
dwrr-elixir/SPEC.md
  02900fa1fb24c93020f62189183c38c37c1f4986dbf1d45815c67d701095ab2f
dwrr-elixir/docs/SPEC-DRAFT.md
  9a34704e74664e37f21862fa78013dbeb58e66278e19cb1ecda95d2fa9ec3d57
dwrr-elixir/TESTING.md
  54008bebf0c9a08ce000f0557b341c0402ba8093689749b592b1f168ac3aaede
```

The Go adapter corrections ignore unused recognized malformed fields and preserve
arbitrary-size integer payloads/indexes/take limits; take is reduced only to the
actual backlog, which is behavior-equivalent. Both pinned v0.10.1 and current Go
Take APIs are supported without upgrading the module pin. Native-int constructor
count decoding and a pre-existing 64 MiB line ceiling remain Go adapter restrictions
pending an owner policy decision, not changes to this proposed Python domain.
Current Go's 2^64−1 mutation-generation budget also qualifies its fixed-core
all-sequences conformance; no such lifetime cap is added here or in Elixir.
Fresh sibling conformance results are not Python results or D1–D5 approvals.

Inspected `dwrr-spec`: README, SPEC, PROTOCOL, corpus README/all record counts,
`tools/spec_model.py`, and `tools/check_driver.py`. Inspected Go README and
`dwrr.go` public and scheduling paths. Inspected Elixir README, binding SPEC,
`docs/SPEC-DRAFT.md`, public `lib/dwrr.ex` and `lib/dwrr/core.ex`.

Resolved distinctions:

- Shared SPEC explicitly permits language-idiomatic names/errors and caller
  coordination. Go's mutex and Elixir's immutability are not core conformance
  requirements. Proposed Python mutability/no lock is a design choice, not a
  conclusion that either sibling behaves that way.
- Shared input domain does not assign negative costs/quanta or Python bools a
  shared code. Elixir rejects negatives outside its tagged error domain; Python
  proposes ordinary ValueError/TypeError. No negative is mislabeled zero.
- Protocol 0.1.1 settles blank lines, negative count and whole-request parsing as
  protocol errors before scheduler validation. Go extensions do not change it.
- The inspected Go README explicitly describes unreleased working-tree behavior;
  it does not establish adaptive callbacks as part of shared 0.1.1. Constant-only
  scope needs approval (D1), not a speculative port of those extensions.
- Elixir design records both implemented core contracts and later-stage Server
  decisions; neither their approvals nor their test-pass claims transfer here.

No conflicting shared-core rule remains unresolved after inspection. Material
Python product choices remain proposals D1–D5, especially extension scope and
state/concurrency ownership. The consistency pass changed sibling adapter/docs/tests
under separate authorization, but no Python approval or implementation status.

## 9. Limitations, deferred choices and next gate

**Approved decisions/stage:** none for Python; this directory remains documentation-only.
Cross-language consistency repairs do not approve a Python implementation stage.
No implementation feasibility, runtime minimum,
packaging, conformance pass, race safety, benchmark, hosted CI or real application
use has been demonstrated. Corpus counts/hashes and source inspection are the
only technical evidence supplied now.

**Before affected kit preparation:** obtain actual inline approval of README
D1–D5 and any revisions. If the author instead needs adaptive callbacks or
built-in synchronization, revise both contracts before preparing that work;
no coder may select that scope. Before a driver kit, resolve exact handling of
Python >=3.11 integer-string conversion limits without weakening protocol or
changing application-global interpreter settings. This is an implementation
feasibility question: first use a small authorized local parser/serializer
experiment with long integer tokens; return for a decision if a cap/new promise
is needed. No experiment or scaffolding has been made now.

**Deferred until before packaging kit:** version, owner-controlled distribution/
repository identity, build backend/build dependencies, metadata, selected runtime
CI matrix and release procedure. The local install promise needs those choices
and isolated install evidence; no publishing action is implied. No runtime
dependencies are proposed. Additional dependency installation needs permission.

**Independent future scope:** wrappers, adaptive quantum policy, keyed queues,
performance thresholds and sparse indexing need a new author gate; they are
not hidden tasks in the core stage. Private helpers/data structures/test layout
remain local freedoms within the approved observable contract.

**After approval, not now:** read the skill's kit-format reference, prepare only
an authorized bounded kit with protected contracts/fixtures/checks, verify failing
stubs and passing private reference using the unchanged runner judge and hand
interface examples, then return for review. Protect every approved README and
this subordinate SPEC. Do not fabricate passing evidence or run implementation
models merely because design is approved.

At initial draft review, this directory was not a Git repository. Git initialization,
branch and baseline commits require separate authorization. Launching the unchanged runner additionally
requires both automatic commit and failed-attempt-owned-discard permission,
explicit model/provider access and spending authorization, confirmation of the
exact commands in the README, prerequisite availability, and a reviewed verified
kit. No such permission has been inferred. Stop here for author review.

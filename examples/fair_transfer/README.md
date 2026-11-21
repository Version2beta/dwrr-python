# Fair file-transfer simulator

A standalone Python >=3.11 example using the installed `dwrr` public API and
standard library only. There are no actual transfers: file names and byte sizes
are pretend records in memory. No file contents, networking, sleeps, database,
configuration, or third-party runtime dependencies are involved.

## Run from a local checkout

Use a virtual environment if your Python installation requires one. The library
is not published; install this checkout, not a similarly named public package:

```sh
python -m pip install /absolute/path/to/dwrr-python
cd /tmp
python /absolute/path/to/dwrr-python/examples/fair_transfer/fair_transfer.py
```

Alternatively, from `dwrr-python/examples/fair_transfer`:

```sh
python -m pip install ../..
python fair_transfer.py
python -m unittest discover -s tests -v
```

Use the same environment's Python for installation, execution and tests. The
script works outside the checkout's working directory and does not modify
`sys.path`. It is checkout-only, not an installed CLI or part of the library
wheel/sdist. No flags or input files are required.

## What it demonstrates

Each customer has one FIFO queue, with fixed byte quanta per visit:

| Customer | Quantum |
| --- | ---: |
| Basic | 1024 |
| Team | 2048 |
| Business | 4096 |

`Transfer` is a dataclass payload; each `Item` costs its `size_bytes`. The
scheduler is created once. Repeated `Scheduler.take(1)` calls select one whole
transfer at a time, preserving credit and any active visit between calls. The
printed cumulative byte counters belong to the example, not the scheduler.

Fairness is in **bytes, not jobs**. While all queues remain backlogged with fixed
quanta, byte service follows the quantum proportions (1:2:4) over enough visits,
subject to whole-file granularity. A single selection or short prefix need not
match that ratio. Team's first two 1024-byte files and Business's first three
files (2048, 1024, 1024) consume their initial grants across separate `take(1)`
calls, without a new grant on every call.

Basic's 3072-byte `archive.zip` initially exceeds its 1024-byte quantum. Credit
accumulates over visits until it is affordable. Its cheap 256-byte `note.txt`
stays behind it: FIFO heads can block smaller files, which never overtake them.

The deterministic run starts with Team's `draft.pdf`, then `chart.png`, then
Business's `slides.pdf`, `logo.png`, and `summary.pdf`; only then is Basic's
`archive.zip` selected. Every line names the transfer, its size, and all three
cumulative byte totals. The final selection line is:

```text
12 Basic report.pdf 1024 bytes | cumulative bytes: Basic=5120 Team=6656 Business=12288
```

Those finite totals are exactly the queued demand, **not a promised 1:2:4 final
split**. Once a customer empties, the continuously-backlogged comparison no
longer applies; the remaining queues continue until empty. Tests pin the entire
output/order, FIFO behavior, conservation, single-item retrieval and absence of
transfer I/O effects.

## Not a bandwidth limiter

This selects transfer **order only**. There is no elapsed-time model, bandwidth
throttling, execution, or preemption. A real sender that sends an entire selected
large file before asking again could monopolize the connection during that file.
For finer-grained interleaving, a real sender would enqueue bounded chunks with
byte costs and perform its own I/O, rate limiting, buffering and error handling.

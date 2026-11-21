# Local verification and release handoff

Version `0.1.0` is implemented but not uploaded. Actual implementation source
`b97fc29c0a4776bbb5d41f632aeb37ff1a23986a` passed the frozen T1–T5 checks on
2026-11-19 with CPython 3.15.0 and 3.11.15 on Darwin arm64. See
[KIT-VERIFICATION.md](KIT-VERIFICATION.md) and `verification/execution-final-*.log`.
Independent code acceptance was read-only source review, not an independent test
rerun. Finite checks do not prove all-sequence conformance.

## Setup

Runtime: Python >=3.11, standard library only. Checkout verification additionally
uses Bash, Git, jq and timeout/gtimeout. Pi/provider credentials are needed only
for an authorized model loop, not these checks. Prepare offline build tools once
(network/dependency installation is a separate setup step):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install build 'setuptools>=77' wheel
mkdir -p .loop/build-wheels
.venv/bin/python -m pip download --only-binary=:all: --dest .loop/build-wheels 'setuptools>=77' wheel packaging
```

`package_check.py` builds in temporary directories, installs outside the checkout,
and uses the cached wheels without network access. Its two README histories and
expected output must remain executable.

## Exact checks

Fast integrity/whitespace checks, plus focused package/README verification:

```sh
python3 -B scripts/kit_check.py
git diff --check
python3 -B scripts/package_check.py
```

The actual final implementation was checked with these full-run commands (the
second selects the locally installed minimum interpreter via uv):

```sh
bash scripts/loop.sh --check
PATH="$(dirname "$(uv python find 3.11)"):$PATH" bash scripts/loop.sh --check
```

`--check` invokes no coder, commits or discards. It runs all five tasks, including
all 31 tests, corpus replay, protocol checks, package examples and the fake-coder
runner regression suite. It is not necessary to repeat the expensive runner
regressions solely for documentation edits. For individual components:

```sh
python3 -B scripts/judge.py all
python3 -B vendor/shared/tools/replay.py --driver 'python3 -B scripts/conformance_driver.py'
python3 -B vendor/shared/tools/check_driver.py --driver 'python3 -B scripts/conformance_driver.py'
python3 -B scripts/package_check.py
bash scripts/test_loop.sh
```

The runner regression suite uses fake coders in disposable repos and reports
26 cases passed / 26 regressions caught with no model calls. This is distinct
from the actual implementation loop's authorized model calls. No hosted CI or
other-platform pass is claimed. Protected docs/evidence changes require manifest
hash maintenance by the parent author outside the coder loop; never edit tests or
task expectations to make a documentation refresh pass.

## Fair-transfer example checks

With this checkout installed in the active Python environment, run the separate
standard-library example tests (not part of the frozen 31-test core judge):

```sh
(cd examples/fair_transfer && python -B -m unittest discover -s tests -v)
```

See [the example README](examples/fair_transfer/README.md) for installation and
execution from outside the checkout. Its five tests pin full output, order,
FIFO/conservation, resumed single-item takes, and no transfer I/O or sleeps.
Example source, docs and tests are protected inventory entries; they are excluded
from library archives. No core API or frozen core test expectations changed.

## Remaining release gate

- Obtain complete owner release sign-off; implementation/code acceptance is not
  publication approval. Do not infer approval from sibling projects or this file.
- On an approved release candidate, verify version, metadata, license, archive
  contents, isolated installs/examples and applicable runtime checks; retain the
  exact source revision and artifact evidence. The checked-in version is 0.1.0.
- Hand the reviewed source/artifacts and verification record to the owner or an
  explicitly authorized publisher for the PyPI release. No upload has occurred;
  no credentials or publishing command are recorded here.

This documentation completion authorizes no push, merge, tag or publication.

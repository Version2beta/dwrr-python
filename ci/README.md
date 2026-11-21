# Post-kit CI maintenance

The preparation manifest remains unchanged (SHA-256 `01457bf484eaf186395e20bcf1f21709e94e526923864d2534c90f4bfcda6323`).
`post-kit.json` records only the four explicitly evolved files and three new
CI assets named in `scripts/kit_check.py`. README evolution includes the owner's
pre-existing language crosslinks and the authorized shared-spec explanation. No vendor assets, tests, task expectations or
original provenance records are replaced. All other baseline hashes and the
source effect/syntax checks still apply; unlisted files are rejected. Like the
original inventory, this is a reviewed integrity record, not a signature or a
sandbox. Inventory changes require owner review, not automatic rehashing.

The push/PR workflow uses Python 3.11 (minimum) and 3.14 (stable supported target),
read-only repository permissions and a 15-minute job limit. It runs the 31-test
judge, frozen vendored corpus/protocol tools, five fair-transfer tests and
integrity mutation regressions. It provisions explicitly versioned public build
tools, then runs the same offline archive/install/README checks using
`DWRR_BUILD_PYTHON` and `DWRR_BUILD_WHEELS` rather than hidden local inputs.
The unchanged default paths still support historical local runner use.

The expensive fake-coder loop regression suite is not a push/PR gate: this CI
checks the library, not model orchestration. Shared tools remain frozen at their
vendored provenance; current spec CI is a separate check, not a silent repin.
Workflows are configured locally, not evidence of a hosted pass or publication.

Build version provenance: the existing preparation `.loop/dependencies.log`
records downloads/cache use and successful installation of build 1.6.1,
setuptools 84.2.1, wheel 0.48.0, packaging 26.3 and pyproject_hooks 1.3.3;
`.loop/build-wheels.log` records the three offline build wheels. The retained
KIT-VERIFICATION record also lists the first four versions. No new registry
query was made for CI setup: these records support the declared versions, not
a claim of current public-registry availability or successful hosted provisioning.

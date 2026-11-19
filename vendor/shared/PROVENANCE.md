# Frozen upstream provenance — complete; do not change

Copied byte-for-byte from ../dwrr-spec at committed HEAD
243dd125470365df2c52a6ce72de3ee8ecfce3fe (clean at preparation).
SPEC.md/PROTOCOL.md are draft 0.1.1. tools/replay.py and tools/check_driver.py
are unchanged; the current protocol checker has 41 checks, not the historical 36.
No optimized upstream spec_model.py is copied or used by this kit.

The corpus retains its historical origin: generated 2026-11-12, responses from
Go github.com/version2beta/dwrr v0.10.1 (tag commit
7109d4d4da265258f348598a378545656db0c241), cross-checked by the upstream model.
Historical inspected shared commit: 8a0e3cf9ae860ba207213590c00feeb822bdd8f2.
Seven JSONL files: 1,839 cases / 44,728 steps; original README records file
counts, seeds and the four huge boundary cases not naively stepped. No corpus
bytes or expected responses were generated or edited here. Current shared
protocol corrections are not a change to corpus identity. MIT license retained.

kit-manifest.json records SHA-256 hashes of every copied file as well as protected
kit contracts/tests. Runner files scripts/loop.sh and scripts/test_loop.sh were
copied unchanged from /Users/rob/.pi/agent/skills/spec-loop/scripts at preparation;
those hashes are also in the manifest. The runner's max default is historical;
owner's explicit high STRONGEST_CMD override is in README, not tasks.json.

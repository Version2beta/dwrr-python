#!/usr/bin/env python3
"""Complete; do not change. Explicit standard-library test selection and stdout proof."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
GROUPS = {
    'state': [('tests.test_state', 9)],
    'withdraw': [('tests.test_withdraw', 4)],
    'schedule': [('tests.test_schedule', 9), ('tests.test_concurrency', 4), ('tests.test_corpus', 1)],
    'driver': [('tests.test_driver', 4)],
}


class Result(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        print('PASS ' + test.id(), flush=True)


def main():
    group = sys.argv[1]
    selected = list(GROUPS.values()) if group == 'all' else [GROUPS[group]]
    loader = unittest.TestLoader()
    suites = []
    count = 0
    for modules in selected:
        for module, expected in modules:
            suite = loader.loadTestsFromName(module)
            if suite.countTestCases() != expected:
                raise RuntimeError(f'{module}: expected {expected} tests, got {suite.countTestCases()}')
            suites.append(suite)
            count += expected
    result = unittest.TextTestRunner(stream=sys.stderr, resultclass=Result, verbosity=2).run(unittest.TestSuite(suites))
    if not result.wasSuccessful() or result.skipped or result.testsRun != count:
        return 1
    print(f'PASS group {group}: {count} tests, no skips', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())

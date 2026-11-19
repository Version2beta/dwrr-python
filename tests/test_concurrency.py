"""Complete; do not change. Internal-lock seam and real concurrent public histories."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Barrier
import subprocess
import sys
import unittest
from dwrr import Scheduler, Item


class ConcurrencyTests(unittest.TestCase):
    def test_remove_queue_releases_payload_after_unlock(self):
        code = '''
import weakref
from dwrr import Scheduler, Item
for mode in ('finalizer', 'weakref'):
    s = Scheduler(2)
    observed, errors = [], []
    def reenter():
        try:
            assert len(s._engine.state.queues) == 1
            assert s._engine.state.cursor == 0 and not s._engine.state.active
            assert s.add_queue() == 1
            s.enqueue(1, [Item('new', 1)])
            assert [i.value for i in s.take(10)] == ['new']
            observed.append(mode)
        except BaseException as error:
            errors.append(type(error).__name__)
    class Payload:
        def __del__(self):
            if mode == 'finalizer':
                reenter()
    payload = Payload()
    handle = weakref.ref(payload, lambda _: reenter()) if mode == 'weakref' else None
    s.enqueue(1, [Item('first', 1), Item(payload, 1)])
    del payload
    assert s.take(1)[0].value == 'first'
    assert s.remove_queue() is None
    assert observed == [mode] and not errors, (observed, errors)
    assert len(s._engine.state.queues) == 2
print('PASS removal finalizer and weakref reentry after unlock')
'''
        result = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, 'PASS removal finalizer and weakref reentry after unlock\n')

    def test_every_operation_lock_covers_entire_engine_call(self):
        calls = [('enqueue', (0, [])), ('set_quantum', (0, 1)), ('add_queue', ()),
                 ('remove_queue', ()), ('remove_head', (0,)), ('drain_queue', (0,)), ('take', (1,))]
        for name, args in calls:
            entered, release, second_started, second_entered = Event(), Event(), Event(), Event()
            class Probe:
                def __getattr__(self, method):
                    def invoke(*args):
                        if method == name and not entered.is_set():
                            entered.set()
                            if not release.wait(3):
                                raise AssertionError('probe release timed out')
                        else:
                            second_entered.set()
                    return invoke
            s = Scheduler(1)
            s._engine = Probe()
            def second():
                second_started.set()
                s.take(0)
            with ThreadPoolExecutor(2) as pool:
                first = pool.submit(getattr(s, name), *args)
                try:
                    self.assertTrue(entered.wait(2), name)
                    next_call = pool.submit(second)
                    self.assertTrue(second_started.wait(2))
                    self.assertFalse(second_entered.wait(0.03), 'overlapping engine operations: ' + name)
                finally:
                    release.set()
                first.result(timeout=2)
                next_call.result(timeout=2)
                self.assertTrue(second_entered.is_set())

    def test_concurrent_batches_and_takes_conserve_fifo_without_interleaving(self):
        s = Scheduler(1)
        start = Barrier(5)
        def producer(worker):
            start.wait(timeout=3)
            for batch in range(30):
                s.enqueue(0, [Item((worker, batch, i), 1) for i in range(5)])
        observed = []
        def consumer():
            start.wait(timeout=3)
            for _ in range(200):
                observed.extend(i.value for i in s.take(7))
        with ThreadPoolExecutor(5) as pool:
            futures = [pool.submit(producer, w) for w in range(4)] + [pool.submit(consumer)]
            for future in futures:
                future.result(timeout=10)
        observed.extend(i.value for i in s.take(10**100))
        self.assertEqual(len(observed), 600)
        self.assertEqual(set(observed), {(w, b, i) for w in range(4) for b in range(30) for i in range(5)})
        for offset in range(0, len(observed), 5):
            batch = observed[offset:offset + 5]
            self.assertEqual([v[2] for v in batch], list(range(5)))
            self.assertEqual(len({v[:2] for v in batch}), 1)
        for worker in range(4):
            self.assertEqual([v[1:] for v in observed if v[0] == worker], [(b, i) for b in range(30) for i in range(5)])

    def test_concurrent_take_returns_complete_serial_slices(self):
        s = Scheduler(2)
        expected = Scheduler(2)
        for target in (s, expected):
            for q in range(2):
                target.set_quantum(q, q + 1)
                target.enqueue(q, [Item((q, i), i % 5 + 1) for i in range(200)])
        serial = [[i.value for i in expected.take(100)] for _ in range(2)]
        start = Barrier(2)
        def take():
            start.wait(timeout=3)
            return [i.value for i in s.take(100)]
        with ThreadPoolExecutor(2) as pool:
            futures = [pool.submit(take) for _ in range(2)]
            a, b = [f.result(timeout=5) for f in futures]
        self.assertTrue([a, b] == serial or [b, a] == serial)
        self.assertEqual([i.value for i in s.take(1000)], [i.value for i in expected.take(1000)])

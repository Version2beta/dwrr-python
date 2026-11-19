"""Complete; do not change. Exact order, arithmetic, idle skip, independent oracle."""
import gc
import random
import time
import unittest
import weakref
from dwrr import Scheduler, Item, SchedulerError, MAX_COST
from tests.naive import Naive
from tests.support import snapshot, invariant, Opaque, IntSubclass, Indexable


def triples(items):
    return [(i.queue, i.value, i.cost) for i in items]


class ScheduleTests(unittest.TestCase):
    def test_take_example_exact_order(self):
        s = Scheduler(2)
        s.set_quantum(0, 2)
        s.set_quantum(1, 3)
        s.enqueue(0, [Item('a', 2), Item('b', 2)])
        s.enqueue(1, [Item('x', 4), Item('y', 1)])
        self.assertEqual(triples(s.take(10)), [(0, 'a', 2), (0, 'b', 2), (1, 'x', 4), (1, 'y', 1)])
        invariant(self, s)

    def test_take_resume_join_and_reweight(self):
        s = Scheduler(2)
        s.set_quantum(0, 5)
        s.enqueue(0, [Item(1, 1), Item(2, 4), Item(3, 1)])
        s.enqueue(1, [Item(8, 1)])
        self.assertEqual(triples(s.take(1)), [(0, 1, 1)])
        s.set_quantum(0, 1)
        s.enqueue(0, [Item(4, 1)])
        self.assertEqual(triples(s.take(2)), [(0, 2, 4), (1, 8, 1)])
        self.assertEqual(triples(s.take(10)), [(0, 3, 1), (0, 4, 1)])

    def test_take_head_blocking_zero_huge_request(self):
        s = Scheduler(2)
        s.enqueue(0, [Item('head', 5), Item('cheap', 1)])
        s.enqueue(1, [Item('other', 1)])
        before = snapshot(s)
        self.assertEqual(s.take(0), [])
        self.assertEqual(snapshot(s), before)
        self.assertEqual(triples(s.take(10**100)), [(1, 'other', 1), (0, 'head', 5), (0, 'cheap', 1)])
        before = snapshot(s)
        self.assertEqual(s.take(10**100), [])
        self.assertEqual(snapshot(s), before)
        self.assertEqual(Scheduler(0).take(10**100), [])

    def test_take_validation_atomic(self):
        s = Scheduler(1)
        s.enqueue(0, [Item(None, 1)])
        for n, exception in [(True, TypeError), (1.0, TypeError), ('1', TypeError),
                             (IntSubclass(1), TypeError), (Indexable(), TypeError), (-10**100, SchedulerError)]:
            before = snapshot(s)
            with self.assertRaises(exception) as cm:
                s.take(n)
            if n == -10**100:
                self.assertEqual(cm.exception.code, 'negative_take')
            self.assertEqual(snapshot(s), before)
        self.assertEqual(s.take(1)[0].cost, 1)

    def test_take_peak_credit_and_withdraw_exposed_head(self):
        m = MAX_COST
        s = Scheduler(2)
        s.set_quantum(0, m - 1)
        s.enqueue(0, [Item('withdraw', m), Item('cheap', 1), Item('expensive', m)])
        s.enqueue(1, [Item('pause', 1)])
        self.assertEqual(triples(s.take(1)), [(1, 'pause', 1)])
        self.assertEqual(s._engine.state.queues[0].credit, m - 1)
        s.set_quantum(0, m)
        self.assertEqual(s.remove_head(0).value, 'withdraw')
        self.assertEqual(triples(s.take(1)), [(0, 'cheap', 1)])
        # Before the debit the grant reaches the proven peak 2**64-3.
        self.assertEqual(s._engine.state.queues[0].credit, 2**64 - 4)
        self.assertEqual(triples(s.take(1)), [(0, 'expensive', m)])
        invariant(self, s)

    def test_take_maximum_skip_and_tie_cursor(self):
        s = Scheduler(3)
        s.enqueue(0, [Item(0, MAX_COST)])
        s.enqueue(1, [Item(1, MAX_COST)])
        s.enqueue(2, [Item(2, MAX_COST)])
        s._engine.state.cursor = 1
        start = time.monotonic()
        self.assertEqual(triples(s.take(4)), [(1, 1, MAX_COST), (2, 2, MAX_COST), (0, 0, MAX_COST)])
        self.assertLess(time.monotonic() - start, 5, 'numeric rounds must be skipped, not stepped')

    def test_take_payload_identity_no_effects_and_release(self):
        s = Scheduler(1)
        payload = Opaque()
        ref = weakref.ref(payload)
        s.enqueue(0, [Item(payload, 2**53 + 1)])
        out = s.take(1)
        self.assertIs(out[0].value, payload)
        del payload, out
        gc.collect()
        self.assertIsNone(ref())

    def test_take_independent_bounded_mixed_traces(self):
        rng = random.Random(807241)
        for trace in range(80):
            s, model = Scheduler(3), Naive(3)
            for step in range(160):
                op = rng.choice(['enqueue', 'enqueue', 'take', 'set_quantum', 'remove_head', 'drain_queue', 'add_queue', 'remove_queue'])
                count = len(model.queues)
                q = rng.randrange(-1, count + 2)
                if op == 'enqueue':
                    args = (q, [(trace * 1000 + step * 3 + i, rng.randrange(0, 16)) for i in range(rng.randrange(4))])
                elif op == 'set_quantum':
                    args = (q, rng.randrange(0, 8))
                elif op in ('remove_head', 'drain_queue'):
                    args = (q,)
                elif op == 'take':
                    args = (rng.randrange(-1, 10),)
                else:
                    args = ()
                want = model.run(op, *args)
                try:
                    call_args = (q, [Item(*i) for i in args[1]]) if op == 'enqueue' else args
                    got = getattr(s, op)(*call_args)
                    if op == 'take':
                        got = triples(got)
                    elif op == 'drain_queue':
                        got = [(i.value, i.cost) for i in got]
                    elif op == 'remove_head' and got is not None:
                        got = (got.value, got.cost)
                    actual = ('ok', got)
                except SchedulerError as error:
                    actual = ('error', error.code)
                self.assertEqual(actual, want, (trace, step, op, args))
                st = s._engine.state
                observed = (st.cursor, st.active, tuple((q.quantum, q.credit, tuple((i.value, i.cost) for i in q.items)) for q in st.queues))
                self.assertEqual(observed, model.snapshot(), (trace, step, op))
                invariant(self, s)

    def test_take_split_and_continuously_backlogged_fairness(self):
        def prepared():
            s = Scheduler(3)
            for q, quantum in enumerate((1, 3, 7)):
                s.set_quantum(q, quantum)
                s.enqueue(q, [Item(i, 1) for i in range(1000)])
            return s
        whole, split = prepared(), prepared()
        want = triples(whole.take(550))
        got = []
        for n in (0, 1, 7, 113, 429):
            got += triples(split.take(n))
        self.assertEqual(got, want)
        self.assertEqual([sum(i[0] == q for i in want) for q in range(3)], [50, 150, 350])

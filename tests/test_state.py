"""Complete; do not change. SPEC §§2–4 constructor, enqueue, weights, queue mutation."""
import dataclasses
import gc
import unittest
import weakref
from dwrr import Item, Scheduled, Scheduler, SchedulerError, MAX_COST, MAX_QUANTUM
from tests.support import snapshot, invariant, Opaque, IntSubclass, Indexable


class StateTests(unittest.TestCase):
    def test_constructor_and_queue_defaults(self):
        for count in (0, 1, 4):
            s = Scheduler(count)
            self.assertEqual(snapshot(s), (0, False, tuple((1, 0, ()) for _ in range(count))))
            self.assertEqual(s.add_queue(), count)
            self.assertEqual(len(s._engine.state.queues), count + 1)
            invariant(self, s)
        for value in (True, 1.0, '1', None, IntSubclass(1), Indexable()):
            with self.assertRaises(TypeError):
                Scheduler(value)
        with self.assertRaises(ValueError) as cm:
            Scheduler(-1)
        self.assertNotIsInstance(cm.exception, SchedulerError)

    def test_records_and_payloads(self):
        value = Opaque()
        item = Item(value, 1)
        self.assertTrue(dataclasses.is_dataclass(item))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            item.cost = 2
        with self.assertRaises(dataclasses.FrozenInstanceError):
            Scheduled(0, value, 1).value = None
        self.assertIs(Item(None, 0).value, None)
        s = Scheduler(1)
        values = [value, None, [], lambda: self.fail('executed')]
        self.assertIsNone(s.enqueue(0, tuple(Item(v, 1) for v in values)))
        actual = s._engine.state.queues[0].items
        self.assertEqual([id(i.value) for i in actual], [id(v) for v in values])
        values[2].append(7)
        self.assertEqual(actual[2].value, [7])

    def test_enqueue_atomic_first_invalid(self):
        s = Scheduler(1)
        s.enqueue(0, [Item('kept', 1)])
        for costs, code in [([1, 0, MAX_COST + 1], 'zero_cost'),
                            ([1, MAX_COST + 1, 0], 'cost_too_large')]:
            before = snapshot(s)
            with self.assertRaises(SchedulerError) as cm:
                s.enqueue(0, [Item('reject', c) for c in costs])
            self.assertEqual(cm.exception.code, code)
            self.assertEqual(snapshot(s), before)
        self.assertIsNone(s.enqueue(0, []))
        s.enqueue(0, [Item('max', MAX_COST), Item('exact', 2**53 + 1)])
        self.assertEqual([i.cost for i in s._engine.state.queues[0].items], [1, MAX_COST, 2**53 + 1])

    def test_index_precedence(self):
        s = Scheduler(1)
        for q in (-1, 1, 10**100):
            for method, args in [(s.enqueue, (q, [])), (s.enqueue, (q, object())),
                                 (s.set_quantum, (q, False))]:
                before = snapshot(s)
                with self.assertRaises(SchedulerError) as cm:
                    method(*args)
                self.assertEqual(cm.exception.code, 'invalid_index')
                self.assertEqual(snapshot(s), before)
        for q in (True, 0.0, '0', IntSubclass(0), Indexable()):
            for method, args in [(s.enqueue, (q, [])), (s.set_quantum, (q, 1))]:
                before = snapshot(s)
                with self.assertRaises(TypeError):
                    method(*args)
                self.assertEqual(snapshot(s), before)

    def test_python_batch_domain(self):
        s = Scheduler(1)
        def generator():
            self.fail('generator executed')
            yield Item(0, 1)
        for batch in (generator(), {1}, 'bad', None):
            with self.assertRaises(TypeError):
                s.enqueue(0, batch)
        for bad in (object(), (1, 1), Item(0, True), Item(0, 1.0), Item(0, IntSubclass(1)), Item(0, Indexable())):
            before = snapshot(s)
            with self.assertRaises(TypeError):
                s.enqueue(0, [Item(1, 1), bad])
            self.assertEqual(snapshot(s), before)
        for cost, exception in [(-1, ValueError), (0, SchedulerError), (10**100, SchedulerError)]:
            before = snapshot(s)
            with self.assertRaises(exception) as cm:
                s.enqueue(0, [Item(1, 1), Item(2, cost)])
            if cost < 0:
                self.assertNotIsInstance(cm.exception, SchedulerError)
            self.assertEqual(snapshot(s), before)

    def test_quantum_validation_preserves_visit(self):
        s = Scheduler(1)
        s.enqueue(0, [Item(1, 1)])
        state = s._engine.state
        state.active = True
        state.queues[0].credit = 9
        for q in (1, 2**53 + 1, MAX_QUANTUM):
            before = snapshot(s)
            self.assertIsNone(s.set_quantum(0, q))
            self.assertEqual(snapshot(s)[:2], before[:2])
            self.assertEqual(state.queues[0].credit, 9)
            self.assertEqual(state.queues[0].quantum, q)
        for q, exception, code in [(False, TypeError, None), (1.0, TypeError, None),
                                   (IntSubclass(1), TypeError, None), (Indexable(), TypeError, None), (-1, ValueError, None),
                                   (0, SchedulerError, 'zero_quantum'),
                                   (MAX_QUANTUM + 1, SchedulerError, 'quantum_too_large')]:
            before = snapshot(s)
            with self.assertRaises(exception) as cm:
                s.set_quantum(0, q)
            if code:
                self.assertEqual(cm.exception.code, code)
            else:
                self.assertNotIsInstance(cm.exception, SchedulerError)
            self.assertEqual(snapshot(s), before)

    def test_remove_queue_repairs_cursor_and_reuse(self):
        for active in (False, True):
            s = Scheduler(3)
            s.enqueue(2, [Item(8, 1)])
            s._engine.state.cursor = 2
            s._engine.state.active = active
            self.assertIsNone(s.remove_queue())
            self.assertEqual(snapshot(s)[:2], (0, False))
            self.assertEqual(s.add_queue(), 2)
            self.assertEqual(snapshot(s)[2][-1], (1, 0, ()))
            for _ in range(5):
                s.remove_queue()
                invariant(self, s)
            self.assertEqual(snapshot(s), (0, False, ()))
        s = Scheduler(3)
        s.enqueue(0, [Item(8, 1)])
        s._engine.state.active = True
        s._engine.state.queues[0].credit = 4
        s.remove_queue()
        self.assertEqual(snapshot(s)[:2], (0, True))
        self.assertEqual(s._engine.state.queues[0].credit, 4)

    def test_remove_queue_releases_payload(self):
        s = Scheduler(1)
        payload = Opaque()
        ref = weakref.ref(payload)
        s.enqueue(0, [Item(payload, 1)])
        del payload
        self.assertIsNotNone(ref(), 'enqueue must retain queued payloads')
        s.remove_queue()
        gc.collect()
        self.assertIsNone(ref())

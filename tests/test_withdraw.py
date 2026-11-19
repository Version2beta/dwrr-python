"""Complete; do not change. SPEC §4 withdrawals and paused visits."""
import unittest
from dwrr import Scheduler, Item, SchedulerError
from tests.support import snapshot, invariant, Opaque, IntSubclass, Indexable


class WithdrawTests(unittest.TestCase):
    def prepared(self):
        s = Scheduler(2)
        s.enqueue(0, [Item(None, 5), Item(Opaque(), 1)])
        s.enqueue(1, [Item(7, 1)])
        s._engine.state.active = True
        s._engine.state.queues[0].credit = 4
        return s

    def test_remove_head_preserves_credit_until_empty(self):
        s = self.prepared()
        result = s.remove_head(0)
        self.assertIsInstance(result, Item)
        self.assertIsNone(result.value)
        self.assertEqual(result.cost, 5)
        self.assertEqual(snapshot(s)[:2], (0, True))
        self.assertEqual(s._engine.state.queues[0].credit, 4)
        payload = s._engine.state.queues[0].items[0].value
        self.assertIs(s.remove_head(0).value, payload)
        self.assertEqual(snapshot(s)[:2], (1, False))
        self.assertEqual(s._engine.state.queues[0].credit, 0)
        before = snapshot(s)
        self.assertIsNone(s.remove_head(0))
        self.assertEqual(snapshot(s), before)
        invariant(self, s)

    def test_drain_queue_closes_only_matching_visit(self):
        s = self.prepared()
        self.assertEqual([i.value for i in s.drain_queue(1)], [7])
        self.assertEqual(snapshot(s)[:2], (0, True))
        result = s.drain_queue(0)
        self.assertEqual([i.cost for i in result], [5, 1])
        self.assertIsNone(result[0].value)
        self.assertEqual(snapshot(s)[:2], (1, False))
        result.clear()
        s.enqueue(0, [Item(9, 1)])
        self.assertEqual(len(s._engine.state.queues[0].items), 1)
        invariant(self, s)

    def test_withdraw_validation_atomic(self):
        s = self.prepared()
        for method in (s.remove_head, s.drain_queue):
            for q, error in [(-1, SchedulerError), (2, SchedulerError), (True, TypeError),
                             (IntSubclass(0), TypeError), (Indexable(), TypeError)]:
                before = snapshot(s)
                with self.assertRaises(error) as cm:
                    method(q)
                if isinstance(cm.exception, SchedulerError):
                    self.assertEqual(cm.exception.code, 'invalid_index')
                self.assertEqual(snapshot(s), before)

    def test_empty_drain_is_fresh_noop(self):
        s = Scheduler(2)
        s._engine.state.cursor = 1
        a = s.drain_queue(0)
        b = s.drain_queue(0)
        self.assertEqual(a, [])
        self.assertIsNot(a, b)
        self.assertEqual(snapshot(s)[:2], (1, False))

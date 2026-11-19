"""Complete; do not change. Payload-safe state snapshots and invariants."""
from dwrr import MAX_COST


def snapshot(scheduler):
    state = scheduler._engine.state
    return (state.cursor, state.active, tuple(
        (q.quantum, q.credit, tuple((id(i.value), i.cost) for i in q.items))
        for q in state.queues))


def invariant(test, scheduler):
    state = scheduler._engine.state
    test.assertTrue(0 <= state.cursor < len(state.queues) if state.queues else state.cursor == 0)
    if state.active:
        test.assertTrue(state.queues[state.cursor].items)
    for queue in state.queues:
        test.assertTrue(0 <= queue.credit <= 2 * MAX_COST - 1)
        if not queue.items:
            test.assertEqual(queue.credit, 0)


class IntSubclass(int):
    pass


class Indexable:
    def __index__(self):
        raise AssertionError('numeric coercion')


class Opaque:
    def __eq__(self, other):
        raise AssertionError("payload equality")

    def __hash__(self):
        raise AssertionError("payload hash")

    def __call__(self):
        raise AssertionError("payload execution")

    def __copy__(self):
        raise AssertionError("payload copy")

    def __deepcopy__(self, memo):
        raise AssertionError("payload deepcopy")

    def __str__(self):
        raise AssertionError("payload conversion")

    __repr__ = __str__

"""Implementation tasks T1–T3. Follow SPEC §§3–5; no external effects.

Private Engine is called only while Scheduler holds its internal operation lock.
The State seam is fixed; helpers/algorithms are otherwise implementation choices.
"""
from typing import Generic
from ._contracts import Item, Scheduled, SchedulerError, MAX_COST, MAX_QUANTUM, T
from ._state import State, Queue


def _check_amount(value: int, limit: int, zero_code: str, large_code: str) -> None:
    """Validate a cost or quantum in the order of SPEC §3 (type, sign, zero, range)."""
    if type(value) is not int:
        raise TypeError("amount must be a built-in int")
    if value < 0:
        raise ValueError("amount must be nonnegative")
    if value == 0:
        raise SchedulerError(zero_code)
    if value > limit:
        raise SchedulerError(large_code)


class Engine(Generic[T]):
    def __init__(self, count: int):
        """T1: strict nonnegative count; create count default queues (§4)."""
        if type(count) is not int:
            raise TypeError("count must be a built-in int")
        if count < 0:
            raise ValueError("count must be nonnegative")
        self.state = State[T](queues=[Queue[T]() for _ in range(count)])

    def _queue(self, queue: int) -> Queue[T]:
        """Check index type, then range, before any other argument is inspected."""
        if type(queue) is not int:
            raise TypeError("queue index must be a built-in int")
        if not 0 <= queue < len(self.state.queues):
            raise SchedulerError("invalid_index")
        return self.state.queues[queue]

    def enqueue(self, queue: int, items: list[Item[T]] | tuple[Item[T], ...]) -> None:
        """T1: index first, validate entire batch in order, append atomically (§3)."""
        target = self._queue(queue)
        if type(items) is not list and type(items) is not tuple:
            raise TypeError("batch must be a list or tuple")
        accepted: list[Item[T]] = []
        for item in items:
            if not isinstance(item, Item):
                raise TypeError("batch element must be an Item")
            _check_amount(item.cost, MAX_COST, "zero_cost", "cost_too_large")
            accepted.append(item)
        target.items.extend(accepted)

    def set_quantum(self, queue: int, quantum: int) -> None:
        """T1: index first; change only quantum, preserve visit/credit (§4)."""
        target = self._queue(queue)
        _check_amount(quantum, MAX_QUANTUM, "zero_quantum", "quantum_too_large")
        target.quantum = quantum

    def add_queue(self) -> int:
        """T1: append default queue, return old count, preserve visit/cursor (§4)."""
        index = len(self.state.queues)
        self.state.queues.append(Queue[T]())
        return index

    def remove_queue(self) -> Queue[T] | None:
        """T1: repair state; return retired queue for facade release after unlock."""
        state = self.state
        if not state.queues:
            return None
        last = len(state.queues) - 1
        if state.active and state.cursor == last:
            state.active = False
            state.cursor = 0
        retired = state.queues.pop()
        if last == 0:
            state.cursor = 0
        elif state.cursor >= last:
            state.cursor %= last
        return retired

    def _reset_emptied(self, index: int) -> None:
        """Reset an emptied queue's credit; close its visit only if it is the active cursor queue."""
        state = self.state
        state.queues[index].credit = 0
        if state.active and state.cursor == index:
            state.active = False
            state.cursor = (state.cursor + 1) % len(state.queues)

    def remove_head(self, queue: int) -> Item[T] | None:
        """T2: withdraw FIFO without spending credit; close only if emptied (§4)."""
        target = self._queue(queue)
        if not target.items:
            return None
        head = target.items.popleft()
        if not target.items:
            self._reset_emptied(queue)
        return head

    def drain_queue(self, queue: int) -> list[Item[T]]:
        """T2: withdraw FIFO, reset credit, close active matching visit (§4)."""
        target = self._queue(queue)
        drained = list(target.items)
        target.items.clear()
        self._reset_emptied(queue)
        return drained

    def take(self, n: int) -> list[Scheduled[T]]:
        """T3: exact cyclic scheduling, resume active visit, direct idle skip (§§4–5)."""
        return []

"""Complete; do not change. Public facade with complete-operation locking."""
from threading import Lock
from typing import Generic
from ._contracts import Item, Scheduled, SchedulerError, MAX_COST, MAX_QUANTUM, T
from ._engine import Engine

__all__ = ["Item", "Scheduled", "Scheduler", "SchedulerError", "MAX_COST", "MAX_QUANTUM"]


class Scheduler(Generic[T]):
    """Mutable cost-aware FIFO scheduler. Every operation is internally serialized.

    Locks protect scheduler state, not caller mutations of payloads/input batches.
    Scheduling never executes payloads. No async or blocking-producer API.
    """

    def __init__(self, count: int):
        self._lock = Lock()
        self._engine = Engine[T](count)

    def enqueue(self, queue: int, items: list[Item[T]] | tuple[Item[T], ...]) -> None:
        """Append a validated batch atomically; index validation comes first."""
        with self._lock:
            return self._engine.enqueue(queue, items)

    def set_quantum(self, queue: int, quantum: int) -> None:
        """Set next grant's quantum without changing current visit or credit."""
        with self._lock:
            return self._engine.set_quantum(queue, quantum)

    def add_queue(self) -> int:
        """Append a default empty queue and return its index."""
        with self._lock:
            return self._engine.add_queue()

    def remove_queue(self) -> None:
        """Discard last queue, repairing state before releasing payload references."""
        with self._lock:
            retired = self._engine.remove_queue()
        # Last-reference release can run Python finalizers; state is coherent and
        # the operation lock must already be released before that happens.
        del retired

    def remove_head(self, queue: int) -> Item[T] | None:
        """Withdraw one head without spending credit; None means empty."""
        with self._lock:
            return self._engine.remove_head(queue)

    def drain_queue(self, queue: int) -> list[Item[T]]:
        """Withdraw all queued items FIFO, resetting credit and matching visit."""
        with self._lock:
            return self._engine.drain_queue(queue)

    def take(self, n: int) -> list[Scheduled[T]]:
        """Select at most n items, preserving paused visits and exact credit."""
        with self._lock:
            return self._engine.take(n)

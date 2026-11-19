"""Complete; do not change. Public records and error vocabulary (SPEC §§2–3)."""
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
MAX_COST = MAX_QUANTUM = 2**63 - 1
ERROR_CODES = frozenset({
    "invalid_index", "zero_cost", "cost_too_large", "zero_quantum",
    "quantum_too_large", "negative_take",
})


@dataclass(frozen=True)
class Item(Generic[T]):
    value: T
    cost: int


@dataclass(frozen=True)
class Scheduled(Generic[T]):
    queue: int
    value: T
    cost: int


class SchedulerError(ValueError):
    """Scheduling-domain failure; only code, not message text, is stable."""

    def __init__(self, code: str):
        if code not in ERROR_CODES:
            raise ValueError("unknown scheduler error code")
        self.code = code
        super().__init__(code)

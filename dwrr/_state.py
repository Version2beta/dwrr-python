"""Complete; do not change. Private representation/test seam, not public API.

Engine owns State; facade holds its lock for the entire call, including validation.
Tests may inspect invariants here without inspecting payloads or constraining helpers.
"""
from collections import deque
from dataclasses import dataclass, field
from typing import Generic
from ._contracts import Item, T


@dataclass
class Queue(Generic[T]):
    items: deque[Item[T]] = field(default_factory=deque)
    quantum: int = 1
    credit: int = 0


@dataclass
class State(Generic[T]):
    queues: list[Queue[T]] = field(default_factory=list)
    cursor: int = 0
    active: bool = False

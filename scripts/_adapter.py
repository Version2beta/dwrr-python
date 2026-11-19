"""T4 implementation. Translate parsed requests using public dwrr methods only."""
from dwrr import Scheduler
from scripts.wire import Request, decimal


def _item(item) -> dict:
    return {"value": item.value, "cost": decimal(item.cost)}


def execute(scheduler: Scheduler | None, request: Request) -> tuple[Scheduler, dict]:
    """Return (current scheduler, {'ok': wire result}); new replaces the scheduler.

    All eight operations and result shapes follow SPEC §6. Let SchedulerError
    propagate to the complete driver. Parsing and stream control are not here.
    Never import a model/oracle or recognize fixture names/requests.
    """
    op, args = request.op, request.args
    if op == "new":
        return Scheduler(args[0]), {"ok": None}
    if op == "enqueue":
        scheduler.enqueue(args[0], args[1])
        return scheduler, {"ok": None}
    if op == "set_quantum":
        scheduler.set_quantum(args[0], args[1])
        return scheduler, {"ok": None}
    if op == "add_queue":
        return scheduler, {"ok": scheduler.add_queue()}
    if op == "remove_queue":
        scheduler.remove_queue()
        return scheduler, {"ok": None}
    if op == "remove_head":
        item = scheduler.remove_head(args[0])
        return scheduler, {"ok": None if item is None else _item(item)}
    if op == "drain_queue":
        return scheduler, {"ok": [_item(item) for item in scheduler.drain_queue(args[0])]}
    if op == "take":
        selected = scheduler.take(args[0])
        return scheduler, {"ok": [
            {"queue": s.queue, "value": s.value, "cost": decimal(s.cost)} for s in selected
        ]}
    raise AssertionError("unreachable: wire parser admits only known operations")

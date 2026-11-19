"""T4 implementation. Translate parsed requests using public dwrr methods only."""
from dwrr import Scheduler
from scripts.wire import Request, decimal


def execute(scheduler: Scheduler | None, request: Request) -> tuple[Scheduler, dict]:
    """Return (current scheduler, {'ok': wire result}); new replaces the scheduler.

    All eight operations and result shapes follow SPEC §6. Let SchedulerError
    propagate to the complete driver. Parsing and stream control are not here.
    Never import a model/oracle or recognize fixture names/requests.
    """
    return scheduler, {"ok": None}

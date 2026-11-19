#!/usr/bin/env python3
"""Complete; do not change. Repository-only stdio seam; not a shipped CLI."""
import sys
from pathlib import Path

# Dev/test checkout entry point, never a fallback or reference import.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dwrr import SchedulerError
from scripts.wire import ProtocolError, parse, encode
from scripts._adapter import execute


def main():
    scheduler = None
    try:
        for line in sys.stdin.buffer:
            request = parse(line)
            if scheduler is None and request.op != "new":
                raise ProtocolError("request before new")
            try:
                scheduler, response = execute(scheduler, request)
            except SchedulerError as error:
                response = {"error": error.code}
            print(encode(response), flush=True)
    except ProtocolError as error:
        print("protocol error: " + str(error), file=sys.stderr)
        return 2
    except (MemoryError, OverflowError):
        print("resource exhaustion", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

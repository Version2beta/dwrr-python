"""Complete; do not change. PROTOCOL 0.1.1 parser and exact JSON integer codec.

500-digit chunks avoid CPython's application-global decimal-conversion limit.
There is no protocol magnitude cap on integer fields. Resource failures remain
resource failures. Costs/quanta have the protocol's separate uint64 string bound.
"""
import json
import re
from dataclasses import dataclass
from dwrr import Item


class ProtocolError(Exception):
    pass


def parse_integer(token: str) -> int:
    negative = token.startswith("-")
    digits = token[1:] if negative else token
    value = 0
    for start in range(0, len(digits), 500):
        part = digits[start:start + 500]
        value = value * 10**len(part) + int(part)
    return -value if negative else value


def decimal(value: int) -> str:
    if value < 0:
        return "-" + decimal(-value)
    chunks = []
    while value >= 10**500:
        value, remainder = divmod(value, 10**500)
        chunks.append(str(remainder).zfill(500))
    return str(value) + "".join(reversed(chunks))


def encode(value) -> str:
    """Only driver-owned response shapes; never serialize core opaque payloads."""
    if value is None:
        return "null"
    if type(value) is int:
        return decimal(value)
    if type(value) is str:
        return json.dumps(value)
    if type(value) is list:
        return "[" + ",".join(encode(v) for v in value) + "]"
    if type(value) is dict:
        return "{" + ",".join(json.dumps(k) + ":" + encode(v) for k, v in value.items()) + "}"
    raise TypeError("unexpected response shape")


@dataclass(frozen=True)
class Request:
    op: str
    args: tuple


def _invalid_constant(_):
    raise ProtocolError("JSON constant")


def parse(line: bytes) -> Request:
    try:
        obj = json.loads(line.decode("utf-8"), parse_int=parse_integer,
                         parse_float=lambda _: object(), parse_constant=_invalid_constant)
    except (UnicodeError, json.JSONDecodeError):
        raise ProtocolError("JSON syntax") from None
    if type(obj) is not dict or type(obj.get("op")) is not str:
        raise ProtocolError("request object/op")
    op = obj["op"]

    def integer(source, field):
        value = source.get(field)
        if type(value) is not int:
            raise ProtocolError("integer field")
        return value

    def cost(source, field):
        value = source.get(field)
        if (type(value) is not str or not re.fullmatch(r"0|[1-9][0-9]*", value)
                or len(value) > 20 or (len(value) == 20 and value > "18446744073709551615")):
            raise ProtocolError("cost/quantum string")
        return int(value)

    if op == "new":
        count = integer(obj, "count")
        if count < 0:
            raise ProtocolError("negative count")
        args = (count,)
    elif op == "enqueue":
        queue = integer(obj, "queue")
        items = obj.get("items")
        if type(items) is not list or any(type(i) is not dict for i in items):
            raise ProtocolError("items shape")
        args = (queue, [Item(integer(i, "value"), cost(i, "cost")) for i in items])
    elif op == "set_quantum":
        args = (integer(obj, "queue"), cost(obj, "quantum"))
    elif op in ("remove_head", "drain_queue"):
        args = (integer(obj, "queue"),)
    elif op == "take":
        args = (integer(obj, "n"),)
    elif op in ("add_queue", "remove_queue"):
        args = ()
    else:
        raise ProtocolError("unknown op")
    return Request(op, args)

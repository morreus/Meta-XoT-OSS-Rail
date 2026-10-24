import json

import events as E
import ticket as T
import vocabulary as V

REQUIRED = ("ticket", "status", "flag")
COUNTS = ("h", "m", "l")
KNOWN = REQUIRED + COUNTS

ROLLBACK_NEEDS = ("h", "m")


class BadLine(ValueError):
    pass


def _object_and_note(text):
    if not isinstance(text, str):
        raise BadLine("a process-log line is text, not %r" % (type(text).__name__,))
    start = text.find("{")
    end = text.find("}")
    if start == -1 or end == -1 or end < start:
        raise BadLine("this line carries no JSON object, so it records nothing a gate can read: "
                      "%r" % (text[:60],))
    if text[:start].strip():
        raise BadLine("this line begins with %r before its object — the line is an object "
                      "FOLLOWED BY the note, and prose in front of it is dropped in silence "
                      "unless it is refused here" % (text[:start].strip()[:40],))
    return text[start:end + 1], text[end + 1:].strip()


def parse_line(text):
    raw, note = _object_and_note(text)
    try:
        fields = json.loads(raw)
    except ValueError as exc:
        raise BadLine("the object on this line is not readable JSON (%s): %r" % (exc, raw[:60]))

    for name in (E.AT,) + E.OTHER_CLOCKS:
        if name in fields:
            raise BadLine("this line carries a clock (%r), and the event's stamp is the only time "
                          "in the system — a record may carry only one" % (name,))

    unknown = sorted(set(fields) - set(KNOWN))
    if unknown:
        raise BadLine("this line carries %s, which the shape does not know — the expected shape "
                      "is known before the read" % ", ".join(repr(u) for u in unknown))
    missing = [name for name in REQUIRED if name not in fields]
    if missing:
        raise BadLine("this line is missing %s — a record that does not parse names the field "
                      "that is wrong" % ", ".join(repr(m) for m in missing))

    if T.parse_ticket(fields["ticket"]) is None:
        raise BadLine("%r is not a readable ticket, and the line is joined to its close by it"
                      % (fields["ticket"],))

    counts = dict((name, fields.get(name)) for name in COUNTS)
    try:
        V.check_line(fields["status"], flag=fields["flag"], **counts)
    except V.BadValue as exc:
        raise BadLine("this line does not hold together: %s" % exc)

    _rollback_needs_a_finding(fields["status"], fields["flag"], counts)

    record = dict((name, fields.get(name)) for name in KNOWN)
    record["note"] = note
    return record


def _rollback_needs_a_finding(status, flag, counts):
    if V.rollback_step(flag) is None:
        return
    if not any(counts.get(name) for name in ROLLBACK_NEEDS):
        raise BadLine("this %r line orders %r beside %s — ordering a rollback is finding "
                      "something, and h and m are the fields that say one was found"
                      % (status, flag, ", ".join("%s=%r" % (n, counts.get(n))
                                                 for n in ROLLBACK_NEEDS)))


def last_line(text):
    if not isinstance(text, str):
        raise BadLine("the process log is text, not %r" % (type(text).__name__,))
    for candidate in reversed(text.splitlines()):
        if candidate.strip():
            return parse_line(candidate)
    raise BadLine("the process log holds no line to read — a close needs one, and an empty file "
                  "is a refusal rather than a silence")


def line_for(text, open_ticket):
    if T.parse_ticket(open_ticket) is None:
        raise BadLine("%r is not a readable ticket, so no line can be matched to it"
                      % (open_ticket,))
    record = last_line(text)
    if record["ticket"] != open_ticket:
        raise BadLine("the last line is for %r and the open ticket is %r — write the line again "
                      "for the ticket that is open" % (record["ticket"], open_ticket))
    return record


def agrees(record, status, h=None, m=None, l=None, flag=None):
    if not isinstance(record, dict) or not set(KNOWN) | {"note"} <= set(record):
        raise BadLine("the first side of this comparison is a line as `parse_line` returns it, "
                      "carrying %s — not %r"
                      % (", ".join(sorted(set(KNOWN) | {"note"})), record))
    if record["status"] != status:
        raise BadLine("the line closes %r and the command says %r — the two records disagree "
                      "about what happened" % (record["status"], status))
    given = {"h": h, "m": m, "l": l}
    for name in COUNTS:
        if record[name] != given[name]:
            raise BadLine("the line says %s=%r and the command says %s=%r — a transposition does "
                          "not announce itself, so the two records are compared field by field"
                          % (name, record[name], name, given[name]))
    return True

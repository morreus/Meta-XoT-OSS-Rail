import hashlib
import json

PREV = "prev"

FIRST = "genesis"


def link(prev, row):
    return hashlib.sha256(
        (prev + json.dumps(row, sort_keys=True, default=str)).encode()).hexdigest()


def verify(rows):
    prev = FIRST
    for index, row in enumerate(rows):
        if PREV not in row:
            return ("row %d carries no %r, so nothing says what it follows — every row the books "
                    "write carries one, and a row without it was not written by them"
                    % (index, PREV))
        if row[PREV] != prev:
            return ("row %d says it follows %s, but what precedes it is %s — a row has been "
                    "removed, inserted, or re-pointed at this position"
                    % (index, row[PREV], prev))
        prev = link(prev, row)
    return None


def head(rows):
    prev = FIRST
    for row in rows:
        prev = link(prev, row)
    return prev


def against_anchor(rows, anchored):
    if anchored is None:
        return None
    found = head(rows)
    if found == anchored:
        return None
    return ("the log ends at %s and the anchor outside the project records %s — the records were "
            "rebuilt after the anchor was written, or the anchor belongs to another run"
            % (found, anchored))

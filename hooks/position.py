import ast
import os

import events as E
import ticket as T
import vocabulary as V

OPERATOR = V.check_by("OPERATOR")
PIPELINE = V.check_by("pipeline")
WRITER_INDEPENDENT = V.check_writer("INDEPENDENT")

NOBODY = "nobody governed"
ORCH = "orchestrator"
INDEPENDENT = "independent"
REFUSE = "refuse"
ANSWERS = (NOBODY, ORCH, INDEPENDENT, REFUSE)

TWO_OPEN = "two open tickets"
DUPLICATE = "a duplicate ticket string"
CLOSE_BEFORE_OPEN = "a close before its open"
SECOND_CLOSE = "a second close of one ticket"
CLOSE_BY_ANOTHER = "a close by anyone but the ticket's writer"
UNREADABLE = "an unreadable ticket"
SHAPES = (TWO_OPEN, DUPLICATE, CLOSE_BEFORE_OPEN, SECOND_CLOSE, CLOSE_BY_ANOTHER, UNREADABLE)

DISAGREEMENT = "the issues file disagrees with the line"

FROM_A_CUT = (CLOSE_BEFORE_OPEN, TWO_OPEN)

SEVERITIES = ("HIGH", "MEDIUM", "LOW")
LOW = "LOW"

BLOCKING = tuple(s for s in SEVERITIES if s != LOW)


class BadPosition(ValueError):
    pass


def _flag(truncated):
    if not isinstance(truncated, bool):
        raise BadPosition("the truncation flag is required and must be True or False, not %r — "
                          "without it a truncated log is returned as if complete" % (truncated,))
    return truncated


def _permission_functions():
    tree = ast.parse(open(os.path.abspath(__file__)).read())
    good, bad = [], []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
            continue
        args = [a.arg for a in node.args.args]
        if "events" not in args:
            continue
        (good if "truncated" in args else bad).append(node.name)
    return sorted(good), sorted(bad)


def flagged():
    return _permission_functions()[0]


def unflagged():
    return _permission_functions()[1]


def _cannot_decide(events):
    reasons = sorted({f["shape"] for f in broken_books(events, False)})
    if reasons:
        return reasons
    holder = open_ticket(events, False)
    if holder is not None and holder.get("writer") not in V.WRITERS:
        return ["the open ticket's writer is %r, which is not one of %s"
                % (holder.get("writer"), ", ".join(V.WRITERS))]
    return []


def who_may_write(events, truncated):
    if _flag(truncated):
        return REFUSE
    if _cannot_decide(events):
        return REFUSE
    holder = open_ticket(events, False)
    if holder is None:
        return NOBODY
    return INDEPENDENT if holder["writer"] == WRITER_INDEPENDENT else ORCH


def open_ticket(events, truncated):
    if _flag(truncated):
        raise BadPosition("a truncated log has no readable open ticket; ask who_may_write, which "
                          "answers %r" % (REFUSE,))
    damage = broken_books(events, False)
    if damage:
        tickets = sorted({str(f["ticket"]) for f in damage if f.get("ticket") is not None})
        raise BadPosition(
            "the books are broken — %s — so which ticket governs is undecidable%s"
            % ("; ".join(sorted({f["shape"] for f in damage})),
               (": %s" % ", ".join(tickets)) if tickets else ""))
    live = {}
    for event in events:
        if event.get("kind") == "open":
            live[event.get("ticket")] = event
        elif event.get("kind") == "close":
            live.pop(event.get("ticket"), None)
    if not live:
        return None
    return list(live.values())[0]


def explain_open_failure(events, truncated):
    _flag(truncated)
    try:
        open_ticket(events, truncated)
    except BadPosition as exc:
        return str(exc)
    return ""


def broken_books(events, truncated):
    cut = _flag(truncated)
    found = []
    seen_open, closed_once, live = set(), set(), {}

    for event in events:
        kind, tk = event.get("kind"), event.get("ticket")
        why = None
        if tk is None:
            if "ticket" in E.REQUIRED.get(kind, ()):
                why = ("a %r event carries a ticket and this one has none — the ticket is required, "
                       "and it is missing" % (kind,))
        elif T.parse_ticket(tk) is None:
            why = "%r is not a readable ticket, and credit is keyed on it" % (tk,)
        if why is not None:
            note = {"shape": UNREADABLE, "ticket": tk, "why": why}
            if cut and event is events[-1]:
                note["maybe_from_the_cut"] = True
                note["why"] += "; it is the last event of a truncated log, so it is the half-line"
            found.append(note)
            continue
        if kind == "open":
            if tk in seen_open:
                found.append({"shape": DUPLICATE, "ticket": tk,
                              "why": "opened twice, so one identifier covers two pieces of work"})
            seen_open.add(tk)
            live[tk] = event
        elif kind == "close":
            if tk not in live and tk not in closed_once:
                found.append({"shape": CLOSE_BEFORE_OPEN, "ticket": tk,
                              "why": "closed with no open ahead of it"})
            elif tk in closed_once:
                found.append({"shape": SECOND_CLOSE, "ticket": tk,
                              "why": "closed twice; one close discharges one round"})
            opened_by = live.pop(tk, None)
            closed_once.add(tk)
            if opened_by is not None and not _close_is_allowed(opened_by, event):
                found.append({"shape": CLOSE_BY_ANOTHER, "ticket": tk,
                              "why": "opened for %r and closed by %r"
                                     % (opened_by.get("writer"), event.get("by"))})

    if len(live) > 1:
        for tk in sorted(live):
            found.append({"shape": TWO_OPEN, "ticket": tk,
                          "why": "%d tickets are open at once; one run holds one" % len(live)})

    if cut:
        for finding in found:
            if finding["shape"] in FROM_A_CUT:
                finding["maybe_from_the_cut"] = True
                finding["why"] += ("; the log was truncated, so the event that would explain this "
                                   "may simply not have landed")
    return found


def _close_is_allowed(opened_event, close_event):
    by, writer = close_event.get("by"), opened_event.get("writer")
    if by == writer:
        return True
    if by == OPERATOR:
        return True
    return by == PIPELINE and close_event.get("status") == "passed"


def disagreements(events, issues, truncated):
    cut = _flag(truncated)
    for entry in issues:
        if not isinstance(entry, dict) or not entry.get("ticket"):
            raise BadPosition("every issues entry carries its ticket; %r does not"
                              % (entry,))
        if T.parse_ticket(entry["ticket"]) is None:
            raise BadPosition("the issues entry carries %r, which is not a readable ticket — the "
                              "join is on the ticket, so an entry nobody can join is a finding "
                              "dropped in silence" % (entry["ticket"],))
        if entry.get("severity") not in SEVERITIES:
            raise BadPosition("the issues entry for %s carries severity %r; every "
                              "entry carries one of %s, and a finding nobody classified read as "
                              "harmless is the reading that empties this check"
                              % (entry["ticket"], entry.get("severity"), ", ".join(SEVERITIES)))
    blocking = {e["ticket"] for e in issues if e["severity"] in BLOCKING}
    found = []
    for event in events:
        if event.get("kind") != "close" or event.get("ticket") not in blocking:
            continue
        if event.get("status") not in V.STATUSES:
            raise BadPosition("the close of %s carries status %r, which is not one of the close "
                              "statuses %s — an unreadable status is not a close that records no counts"
                              % (event["ticket"], event.get("status"), ", ".join(V.STATUSES)))
        if event.get("status") not in V.CARRIES_COUNTS:
            continue
        h, m = event.get("h"), event.get("m")
        if any(isinstance(c, bool) or not isinstance(c, int) for c in (h, m)):
            raise BadPosition("the %r close of %s carries counts %r and %r, which are not whole "
                              "numbers — a count that cannot be read is not a count of zero, and "
                              "reading it as 'not 0H 0M' drops the finding in silence"
                              % (event.get("status"), event["ticket"], h, m))
        if h == 0 and m == 0:
            note = {"shape": DISAGREEMENT, "ticket": event["ticket"],
                    "why": "the line closes 0H 0M while the issues file carries findings "
                           "for this ticket"}
            if cut:
                note["maybe_from_the_cut"] = True
                note["why"] += "; the log was truncated, so a later close may be missing"
            found.append(note)
    return found


def explain(answer, events, truncated):
    cut = _flag(truncated)
    if answer not in ANSWERS:
        raise BadPosition("%r is not one of the four answers %s" % (answer, ", ".join(ANSWERS)))
    actual = who_may_write(events, cut)
    if answer != actual:
        raise BadPosition("this log answers %r, not %r — a sentence about an answer the log does "
                          "not give is a false report of the run" % (actual, answer))
    if answer == REFUSE and cut:
        return ("the log was truncated, so who holds the ticket cannot be known — a half-written "
                "last line can hide a live independent lock and let a second writer in")
    if answer == REFUSE:
        return "the books cannot say who holds the ticket: %s" % "; ".join(_cannot_decide(events))
    if answer == NOBODY:
        return "no ticket is open, so no rule governs a write"
    return "the open ticket was written by %s" % (
        "an independent reviewer" if answer == INDEPENDENT else "the orchestrator")

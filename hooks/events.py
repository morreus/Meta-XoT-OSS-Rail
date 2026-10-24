import re

import ticket as T
import vocabulary as V

TYPES = ("open", "close", "attempt", "question", "override", "claim")

REQUIRED = {
    "open": ("ticket", "step", "writer"),
    "close": ("ticket", "step", "writer", "by", "status"),
    "attempt": ("ticket", "outcome", "raw"),
    "question": ("qid", "ticket", "asks", "text", "legal", "step"),
    "override": ("text", "question", "ticket"),
    "claim": ("project", "run_hash", "chain", "base_commit"),
}

ONLY_ON = {
    "chain": ("claim", "one run has one chain, and a second is a second answer to what the "
                       "target is"),
    "ms_hash": ("close", "the hash pins the plan section a milestone earned credit for, and a "
                         "digest on a record nobody compares it from is a fact written where "
                         "nothing checks it"),
    "base_commit": ("claim", "the starting commit is one of the run's four facts and belongs "
                             "with the other three; a second one is a second answer to what "
                             "milestone 1 is measured against"),
    "commit": ("close", "the sha records what a milestone was fixed at when it earned credit, "
                        "and one carried anywhere else is a commit nobody credits"),
    "score": ("close", "the score moves when something CLOSES, so a vector on any other record "
                       "is a figure nothing produced"),
    "options": ("question", "options are the choices a question put to the operator, and on any other "
                            "record they are choices nobody was asked"),
}

LAST_MILESTONED = {"lite": "31-review-impl", "full": "51-review-tests"}

LENGTHS = {"lite": 6, "full": 10}

OUTCOMES = ("succeeded", "refused")

AT = "at"
OTHER_CLOCKS = ("timestamp", "time", "ts", "when", "date", "datetime", "created", "recorded")

MS_ID_RE = re.compile(r"\AM(?P<n>0|[1-9][0-9]*)\Z")

PLAN_REVIEW_STEP = "21-review-plan"

MILESTONE_PAIRS = {"30-implement-plan": "31-review-impl",
                   "40-test-plan": "41-review-test-plan",
                   "50-test-impl": "51-review-tests"}

MILESTONE_STEPS = frozenset(MILESTONE_PAIRS) | frozenset(MILESTONE_PAIRS.values())

MS_HASH = "ms_hash"
COMMIT = "commit"
SCORE = "score"
CODE_DIGEST = "code_digest"
OPTIONS = "options"
MAX_PARTS, MIN_CHOICES, MAX_CHOICES = 4, 2, 4

COMPLETING = ("done", "attested", "passed")

CLEAN_WRITER = "INDEPENDENT"


def completes(event):
    if event.get("kind") != "close":
        return False
    status = event.get("status")
    if status in COMPLETING:
        return True
    if status != "reviewed":
        return False
    return (event.get("writer") == CLEAN_WRITER
            and event.get("h") == 0 and event.get("m") == 0)


DENOMINATOR_SETTERS = ("a clean INDEPENDENT close of the plan's review",
                       "an attested close of the plan's review")


class BadEvent(ValueError):
    pass


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _milestone_ids(value):
    if not isinstance(value, (list, tuple)):
        raise BadEvent("the milestone ids must be an ordered list, not %r" % (value,))
    ids = list(value)
    for one in ids:
        if not isinstance(one, str) or not MS_ID_RE.match(one):
            raise BadEvent("%r is not a milestone id" % (one,))
    if len(set(ids)) != len(ids):
        raise BadEvent("a milestone id appears twice in %r; numbers are never reused" % (ids,))
    return ids


def last_milestone(ids):
    ids = _milestone_ids(ids)
    if not ids:
        raise BadEvent("there is no last milestone of an empty list")
    return max(ids, key=lambda one: int(MS_ID_RE.match(one).group("n")))


def sets_denominator(event):
    if event.get("kind") != "close" or event.get("step") != PLAN_REVIEW_STEP:
        return False
    try:
        V.check_status(event.get("status"))
    except V.BadValue as exc:
        raise BadEvent("this close cannot be read as setting the denominator or not: %s" % exc)
    if event.get("status") == "attested":
        return True
    if event.get("status") != "reviewed":
        return False
    if event.get("writer") != "INDEPENDENT":
        return False
    return event.get("h") == 0 and event.get("m") == 0


def make_event(kind, clock, /, **fields):
    if not callable(clock):
        raise BadEvent("the clock must be callable and is called here; %r is a value, and a value "
                       "passed in is a second clock" % (clock,))

    for name in (AT,) + OTHER_CLOCKS:
        if name in fields:
            raise BadEvent(
                "%r is written by the machine and may not be supplied — two clocks in one "
                "record can make a review look older than the work it reviewed" % (name,))

    if "kind" in fields:
        raise BadEvent("%r is the EVENT's own type and no field may overwrite it; a record whose "
                       "type has been replaced by a field's value is an event of no type at all"
                       % ("kind",))

    event = {"kind": kind, AT: clock()}
    event.update(fields)
    return check_event(event)


def check_event(event):
    kind = event.get("kind")
    if kind not in TYPES:
        raise BadEvent("%r is not one of the six event types: %s" % (kind, ", ".join(TYPES)))
    for name in OTHER_CLOCKS:
        if name in event:
            raise BadEvent("%r is a second clock in one record beside the %r the pipeline "
                           "wrote" % (name, AT))
    if not isinstance(event.get(AT), str) or not event[AT].strip():
        raise BadEvent("every event carries the %r the pipeline wrote; %r is not one"
                       % (AT, event.get(AT)))

    for name in REQUIRED[kind]:
        value = event.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise BadEvent("a %r event carries %s; %r is missing"
                           % (kind, ", ".join(REQUIRED[kind]), name))

    if "ticket" in event and event["ticket"] is not None:
        if T.parse_ticket(event["ticket"]) is None:
            raise BadEvent(
                "%r is not a readable ticket, and the event log is where credit is stored — "
                "an unreadable ticket is refused there, so this record may not carry it"
                % (event["ticket"],))

    for field, (owner, why) in ONLY_ON.items():
        if kind != owner and event.get(field) is not None:
            raise BadEvent("only a %r carries %r, and this %r event carries one — %s"
                           % (owner, field, kind, why))

    if event.get("ms") is not None and not MS_ID_RE.match(str(event.get("ms"))):
        raise BadEvent("%r is not a milestone id — credit is keyed on it, so a number no reader "
                       "can parse is credit no reader can place" % (event.get("ms"),))

    if (kind == "close" and event.get("step") in MILESTONE_STEPS
            and event.get("ms") is not None and completes(event)):
        value = event.get(MS_HASH)
        if not _text(value):
            raise BadEvent(
                "a close of %r earns milestone credit, so it carries %r — %r is not a hash, and a "
                "milestone credited against nothing leaves the re-plan's refusal with nothing to "
                "compare against" % (event.get("step"), MS_HASH, value))

    if SCORE in event:
        vector = event.get(SCORE)
        if (not isinstance(vector, (list, tuple)) or not vector
                or any(isinstance(n, bool) or not isinstance(n, (int, float))
                       for n in vector)):
            raise BadEvent(
                "%r is not a score — the field carries one number per step of the chain, and a "
                "close recording something else says nothing about where the run stood"
                % (vector,))

    for field in ("base_commit", COMMIT):
        if field in event and not _text(event.get(field)):
            raise BadEvent(
                "%r is not a commit, and %r carries one that says nothing — a run measured "
                "against a blank baseline, or a milestone recorded as fixed in git at no "
                "sha, is a record no later reader can use" % (event.get(field), field))
    if OPTIONS in event and event.get(OPTIONS) is not None:
        parts = event[OPTIONS]
        if (not isinstance(parts, (list, tuple)) or not 1 <= len(parts) <= MAX_PARTS
                or any(not isinstance(part, (list, tuple))
                       or not MIN_CHOICES <= len(part) <= MAX_CHOICES
                       or not all(_text(label) and label.splitlines() == [label] for label in part)
                       or len(set(part)) != len(part) for part in parts)):
            raise BadEvent(
                "%r are not a question's options — they are 1 to %d parts of %d to %d labels, each saying "
                "something on one line and none twice in a part, as the sheet shows them; the operator would "
                "be asked to choose from nothing, or from keys they cannot tell apart"
                % (parts, MAX_PARTS, MIN_CHOICES, MAX_CHOICES))
    if CODE_DIGEST in event and not _text(event.get(CODE_DIGEST)):
        raise BadEvent(
            "%r is not a digest, and %r carries one that says nothing — the code's later closes "
            "would compare against a blank" % (event.get(CODE_DIGEST), CODE_DIGEST))

    for field, checker in (("writer", V.check_writer), ("by", V.check_by),
                           ("status", V.check_status), ("flag", V.check_flag),
                           ("chain", V.check_chain)):
        if field in event and event[field] is not None:
            try:
                checker(event[field])
            except V.BadValue as exc:
                raise BadEvent("on the %r of this %r event: %s" % (field, kind, exc))

    if kind != "close" and (event.get("ms_n") is not None or event.get("ms_ids") is not None):
        raise BadEvent("only a close may carry the denominator, and a %r event carries %s — "
                       "anywhere else it is the same fact written where nothing checks it"
                       % (kind, "ms_n" if event.get("ms_n") is not None else "ms_ids"))

    if kind == "attempt" and event["outcome"] not in OUTCOMES:
        raise BadEvent("an attempt's outcome is one of %s, not %r"
                       % (", ".join(OUTCOMES), event["outcome"]))

    if kind == "close":
        _check_close(event)
    return event


def _check_close(event):
    try:
        V.check_close(event["status"], event["by"])
    except V.BadValue as exc:
        raise BadEvent("this close does not belong to the party writing it: %s" % exc)

    counts = {n: event.get(n) for n in ("h", "m", "l")}
    if V.writes_entry(event["status"]):
        try:
            V.check_line(event["status"], h=counts["h"], m=counts["m"], l=counts["l"],
                         flag=event.get("flag") or "", by=event.get("by"))
        except V.BadValue as exc:
            raise BadEvent("this close would not be a legal line: %s" % exc)
    else:
        present = sorted(n for n, v in counts.items() if v is not None)
        if event.get("flag"):
            present.append("a flag")
        if present:
            raise BadEvent("a %r close carries no counts — no agent worked the step — and this one "
                           "carries %s" % (event["status"], ", ".join(present)))

    has_n = event.get("ms_n") is not None
    has_ids = event.get("ms_ids") is not None

    if (has_n or has_ids) and not sets_denominator(event):
        raise BadEvent(
            "only a close that SETS the denominator may carry it, and this one does not: the two "
            "setters are %s" % "; ".join(DENOMINATOR_SETTERS))

    if has_n != has_ids:
        raise BadEvent("the denominator and its ordered milestone ids travel together or not at "
                       "all; this close carries %s alone"
                       % ("the count" if has_n else "the ids"))
    if has_n:
        ids = _milestone_ids(event["ms_ids"])
        if not isinstance(event["ms_n"], int) or isinstance(event["ms_n"], bool):
            raise BadEvent("the denominator is a whole number, not %r" % (event["ms_n"],))
        if event["ms_n"] != len(ids):
            raise BadEvent("the denominator says %r and its own list holds %d; one fact, one place"
                           % (event["ms_n"], len(ids)))
        event["ms_ids"] = ids


def append(log, event):
    if (event.get("kind") == "close" and event.get("step") in MILESTONE_STEPS
            and event.get("ms") is not None and completes(event)):
        chain = next((older.get("chain") for older in log
                      if older.get("kind") == "claim"), None)
        if chain not in LAST_MILESTONED:
            raise BadEvent(
                "this close of %r would credit a milestone, and the log carries no claim naming "
                "the chain — which step COMPLETES a milestone is %r on lite and %r on full, so "
                "without it the question has no answer and a default is wrong either way"
                % (event.get("step"), LAST_MILESTONED["lite"], LAST_MILESTONED["full"]))
        if event.get("step") == LAST_MILESTONED[chain] and not _text(event.get(COMMIT)):
            raise BadEvent(
                "a close of %r finishes milestone %r on the %s chain, so the pipeline has just "
                "committed and the sha rides here — %r is not a commit, and a milestone recorded "
                "as fixed in git at no sha is the false record the rule exists to stop"
                % (event.get("step"), event.get("ms"), chain, event.get(COMMIT)))

    if event.get("kind") == "close" and SCORE in event:
        chain = next((older.get("chain") for older in log
                      if older.get("kind") == "claim"), None)
        if chain is not None:
            wanted = LENGTHS[chain]
            got = len(event.get(SCORE) or ())
            if got != wanted:
                raise BadEvent(
                    "this close carries %d numbers and the %s chain has %d steps — a score "
                    "measured against the wrong chain is a figure about a run that is not this "
                    "one" % (got, chain, wanted))

    if event.get("kind") == "claim":
        for older in log:
            if older.get("kind") == "claim":
                raise BadEvent("this log already opens with a claim, and a second one is a second "
                               "answer about whose books these are")
    if event.get("kind") in ("open", "close"):
        for older in log:
            if older.get("kind") == event["kind"] and older.get("ticket") == event.get("ticket"):
                raise BadEvent(
                    "the log already holds a %r for %r. Silent precedence is forbidden "
                    "outright on the event log: a second answer is not written over the first, "
                    "here or anywhere; only the process log lets its last line win, in its own "
                    "record" % (event["kind"], event.get("ticket")))
    return list(log) + [event]


def opens(log):
    return [e for e in log if e.get("kind") == "open"]


def next_version(log, step_num):
    return T.next_version([e["ticket"] for e in opens(log)], step_num)

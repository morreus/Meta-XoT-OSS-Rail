import re

import chain as C
import events as E
import line as L
import open_close as O
import ticket as T
import vocabulary as V


class BadFloor(ValueError):
    pass


CLEAR = "clear"
TOLD = "told blocking"
UNKNOWN = "unknown"

_RANK = (CLEAR, UNKNOWN, TOLD)

_COUNT_IN_TEXT = re.compile(r"[\"']?(?P<name>[hm])[\"']?\s*:\s*(?P<value>-?[0-9]+)")


def told_by(raw, events):
    try:
        record = L.parse_line(raw)
    except L.BadLine:
        for found in _COUNT_IN_TEXT.finditer(raw if isinstance(raw, str) else ""):
            if int(found.group("value")) != 0:
                return TOLD
        return UNKNOWN
    if record["ticket"] in _closed(events):
        return None
    return TOLD if (record.get("h") or record.get("m")) else CLEAR


def _closed(events):
    return set(event.get("ticket") for event in events if event.get("kind") == "close")


def is_review(ticket):
    step = _step_of(ticket)
    return step is not None and C.kind_of(step) == O.REVIEW


def _step_of(ticket):
    fields = T.parse_ticket(ticket) if isinstance(ticket, str) else None
    if fields is None:
        return None
    for step, _kind in C.STEPS:
        if int(step.split("-")[0]) == fields["step"]:
            return step
    return None


def floor(ticket, events, raw=None):
    if not is_review(ticket):
        return CLEAR
    standing = CLEAR
    said = [told_by(event["raw"], events) for event in events
            if event.get("kind") == "attempt" and event.get("ticket") == ticket]
    if raw is not None:
        said.append(told_by(raw, events))
    for answer in said:
        if answer is not None and _RANK.index(answer) > _RANK.index(standing):
            standing = answer
    return standing


def reach(step):
    kind = None
    try:
        kind = C.kind_of(step)
    except C.BadChain:
        return ()
    number = int(step.split("-")[0])
    behind = number - 1 if kind == O.REVIEW else number
    return tuple(sorted((t for t in C.TARGETS if t < behind), reverse=True))


_CODE = int(O.IMPLEMENT.split("-")[0])


def _reach_now(step, ticket, events):
    fields = T.parse_ticket(ticket) if isinstance(ticket, str) else None
    done = fields is not None and fields["milestone"] in C.delivered(events)
    return tuple(t for t in reach(step) if not (done and t == _CODE))


UNREACHABLE = "unreachable"
WRONG_INPUT = "input"
MISOPENED = "misopened"
ASK = "ask"
ANSWER_FORM = "ANSWER <your answer>"
END = "end"
END_FORM = "OVERRIDE END"
OBSERVE = "observe"
KINDS = (UNREACHABLE, WRONG_INPUT, UNKNOWN, MISOPENED, ASK, END, OBSERVE)
OTHER = "OTHER"


def is_content(question):
    asks = question.get("asks") if isinstance(question, dict) else question
    return asks in (ASK, OBSERVE)


def is_other(said):
    return bool(said) and str(said.get("text", "")).startswith(OTHER + " ")

_ROLLBACK = "OVERRIDE ROLLBACK %d"
_CLOSE = "OVERRIDE CLOSE %s"
_OPEN = "OVERRIDE OPEN %s"

OPERATOR = V.check_by("OPERATOR")


def legal(events, asks, ticket, step):
    if asks == MISOPENED:
        raise BadFloor(
            "the amendment's set — `OVERRIDE OPEN <ticket>` for every ticket the chain could "
            "legally have cut — is LISTED BY THE PIPELINE from the chain, not computed "
            "here. "
            "Answering nothing here would be indistinguishable from a state that does not hold, "
            "which would silently take away the operator's way out")
    if asks == UNKNOWN:
        return (_CLOSE % ticket,) if floor(ticket, events) == UNKNOWN else ()
    if asks == UNREACHABLE:
        return _targets(step, ticket, events) if _ordered_out_of_reach(ticket, events, step) else ()
    if asks == WRONG_INPUT:
        return () if is_review(ticket) else _targets(step, ticket, events)
    if is_content(asks):
        return () if is_review(ticket) else (ANSWER_FORM,)
    if asks == END:
        return () if short_of_target(events) is None else (END_FORM, _OPEN % ticket)
    return ()


def short_of_target(events):
    chain = C.chain_of(events)
    reached, target = tuple(C.score(events)), tuple(C.target(chain))
    return None if reached == target else (reached, chain, target)


def _targets(step, ticket, events):
    return tuple(_ROLLBACK % target for target in _reach_now(step, ticket, events))


def _ordered_out_of_reach(ticket, events, step):
    target = _ordered(ticket, events)
    return target is not None and target not in _reach_now(step, ticket, events)


def _ordered(ticket, events):
    for event in reversed(events):
        if event.get("kind") != "attempt" or event.get("ticket") != ticket:
            continue
        try:
            record = L.parse_line(event["raw"])
        except L.BadLine:
            return None
        return V.rollback_step(record["flag"])
    return None


def why_held(events, state, ticket, step):
    if state != UNREACHABLE:
        return None
    target = _ordered(ticket, events)
    reachable = _reach_now(step, ticket, events)
    if target not in C.TARGETS:
        why = "%s is not a step a rollback can go back to — the targets are %s" % (target, joined(C.TARGETS))
    elif target in reach(step):
        why = ("%s's code was delivered and committed, so its code step is no longer a target; "
               "undoing delivered code is a new milestone" % T.parse_ticket(ticket)["milestone"])
    else:
        why = "%s reaches only %s" % (step, joined(reachable))
    return "%s ordered ROLLBACK %s, which it cannot reach: %s" % (ticket, target, why)


def repeats(events, move, ticket, step, asks=None):
    target = V.override_rollback_step(move)
    if target is not None:
        return _rollback_costs(events, target, ticket)
    if move == END_FORM:
        short = short_of_target(events)
        return ("ends the run where it stands, %s, short of the %s chain's target %s" % short
                if short else "")
    if move.startswith(_CLOSE % ""):
        return "closes %s on your word; nothing repeats" % move.split()[-1]
    if move.startswith("OVERRIDE OPEN "):
        wanted = move.split()[-1]
        if asks == END:
            return "keeps the run going: %s stays open and nothing ends" % ticket
        return ("declines the amendment: %s stays open and nothing changes" % ticket if wanted == ticket
                else "voids %s and opens %s in its place; nothing repeats" % (ticket, wanted))
    return ""


def _rollback_costs(events, target, ticket):
    order = C.steps(C.chain_of(events))
    after = [int(sid.split("-")[0]) for sid in order if int(sid.split("-")[0]) > target]
    reworked = [sid for sid in order if int(sid.split("-")[0]) == target]
    named = reworked[0] if reworked else str(target)
    ids = C.denominator(events)[1] or ()
    fields = T.parse_ticket(ticket) if isinstance(ticket, str) else None
    milestone = fields["milestone"] if fields and fields["milestone"] in ids else None
    if not ids or (target >= _CODE and milestone is None):
        return "reworks %s; %s %s" % (named, joined(after), _repeat(after))
    if target >= _CODE:
        return "reworks %s for %s; %s's %s %s" % (named, milestone, milestone, joined(after), _repeat(after))
    done = C.delivered(events)
    stage = [n for n in after if n < _CODE]
    again = [ms for ms in ids if ms not in done]
    return "reworks %s; %s %s, then %s again from %d%s" % (
        named, joined(stage), _repeat(stage), joined(again) or "no milestone", _CODE,
        "; %s %s" % (joined(done), "keep their credit" if len(done) > 1 else "keeps its credit")
        if done else "")


def _repeat(items):
    return "repeats" if len(items) == 1 else "repeat"


def joined(items):
    words = [str(item) for item in items]
    return ", ".join(words[:-1]) + " and " + words[-1] if len(words) > 1 else "".join(words)


def asked(events):
    for event in reversed(events):
        if event.get("kind") == "question":
            return event
    return None


def waiting(events):
    question = asked(events)
    if question is None:
        return None
    said = authority(events)
    if said is not None and not (is_other(said) and is_content(question)):
        return None
    if question.get("asks") == OBSERVE:
        after = events[max(i for i, event in enumerate(events) if event is question) + 1:]
        if any(event.get("kind") == "close" for event in after):
            return None
    return question


def holds(events, question):
    if question is None or question.get("asks") == OBSERVE:
        return False
    if question.get("asks") == MISOPENED:
        return True
    return bool(legal(events, question.get("asks"), question.get("ticket"), question.get("step")))


def asking(events):
    question = waiting(events)
    if question is None or not holds(events, question) or authority(events) is not None:
        return None
    return question


def authority(events):
    question = asked(events)
    if question is None:
        return None
    for event in reversed(events):
        if event.get("kind") == "override" and event.get("question") == question["qid"]:
            return event
    return None


_LETTERS = "abcdefghijklmnopqrstuvwxyz"


def keys(question):
    if question.get("asks") == OBSERVE:
        return []
    if not is_content(question):
        return [(_LETTERS[n], move) for n, move in enumerate(question.get("legal") or [])]
    parts = question.get(E.OPTIONS) or []
    return [((str(p + 1) if len(parts) > 1 else "") + _LETTERS[n], label)
            for p, part in enumerate(parts) for n, label in enumerate(part)]


def chosen(question, text):
    words = (text or "").replace(",", " ").lower().split()
    table = dict(keys(question))
    if not words or any(word not in table for word in words):
        return None
    parts = question.get(E.OPTIONS) or []
    if not is_content(question) or len(parts) <= 1:
        return (table[words[0]] if not is_content(question) else words[0]) if len(words) == 1 else None
    if sorted(word[:-1] for word in words) != [str(p + 1) for p in range(len(parts))]:
        return None
    return " ".join(sorted(words))


_STEP_WORDS = {10: "map step", 11: "map review", 20: "plan step", 21: "plan review", 30: "code step",
               31: "code review", 40: "test plan step", 41: "test plan review", 50: "test step", 51: "test review",
               92: "fix step", 93: "repair step"}


def _named(number, milestone):
    words = _STEP_WORDS.get(number, "step %d" % number)
    return ("%s's %s" % (milestone, words) if milestone and milestone != T.NO_MILESTONE and number >= 30
            else "the %s" % words)


def label(move, ticket):
    asked = T.parse_ticket(ticket) or {}
    if move == END_FORM:
        return "End the run here"
    words = move.split()
    if len(words) != 3 or words[0] != "OVERRIDE":
        return move
    if words[1] == "ROLLBACK" and words[2].isdigit():
        return "Go back to %s" % _named(int(words[2]), asked.get("milestone"))
    named = T.parse_ticket(words[2])
    if named is None:
        return move
    step = _named(named["step"], named["milestone"])
    if words[1] == "CLOSE":
        return "Accept %s as it stands" % step
    if words[1] == "OPEN":
        return ("Keep going with %s" % step) if words[2] == ticket else ("Open %s instead" % step)
    return move


def labels(question):
    if is_content(question):
        return {}
    out = {}
    for move in question.get("legal") or []:
        plain = label(move, question.get("ticket"))
        out[move] = plain if plain not in out.values() else "%s (%s)" % (plain, move)
    return out


def check_override(events):
    question = asked(events)
    if question is None:
        raise BadFloor("no question is open, and an override answers a posed question — the "
                       "word, one of the instructions, and a question already open are "
                       "the three conditions, all read off the books")
    override = authority(events)
    if override is None:
        raise BadFloor("no override answers %r, the question this run is waiting on. An override "
                       "is read once, against the question it answers — one written for an "
                       "earlier question was spent there, by the act it named or by its refusal"
                       % (question["qid"],))
    allowed = legal(events, question.get("asks"), question.get("ticket"), question.get("step"))
    if override["text"] not in allowed:
        raise BadFloor(
            "%r is not legal here. What is legal is %s — computed from the run's state and never "
            "from the question, because a menu the asking agent authored is a menu an attacker "
            "wrote. This record is spent by the refusal"
            % (override["text"], ", ".join(repr(a) for a in allowed) if allowed
               else "nothing: the state this question names does not hold"))
    return override["text"]


def _cleared_by(events, ticket):
    try:
        return check_override(events) == _CLOSE % ticket
    except BadFloor:
        return False


def attempt(events, close, raw, clock, refused=None):
    ticket = close["ticket"]
    step = close["step"]
    refusal = refused
    state = None
    standing = floor(ticket, events, raw)
    clean = not (close.get("h") or close.get("m"))

    if standing == UNKNOWN and clean and not _cleared_by(events, ticket):
        refusal = refusal or (
            "the line recorded for %s could not be read, so what it said is UNKNOWN — a clean "
            "close is refused against it, and this one is cleared by the operator alone" % ticket)
        state = UNKNOWN
    elif standing == UNKNOWN and clean and close.get("by") != OPERATOR:
        refusal = refusal or (
            "%s closes on the operator's authority, so its `by` is %r and not %r — the "
            "authorisation and the act it authorised are two records, and an act written as the "
            "reviewer's says the reviewer closed a ticket the reviewer could not close"
            % (ticket, OPERATOR, close.get("by")))
    elif standing == TOLD and clean:
        refusal = refusal or (
            "%s was already told something blocking, and a ticket cannot close with fewer "
            "findings than it was already told. The comparison is yes/no on blocking and never "
            "HIGH versus MEDIUM: nothing may branch on that difference" % ticket)
    else:
        target = V.rollback_step(close.get("flag") or "")
        if target is not None and target not in _reach_now(step, ticket, events):
            if not reach(step):
                refusal = refusal or (
                    "%s orders a rollback and this step reaches no target at all — the thing "
                    "this review is reading is the first document, with nothing behind it. "
                    "*The thing I am reviewing is wrong* is a fix, not a rollback"
                    % (step,))
                state = _still_held(events, ticket)
            else:
                state = UNREACHABLE
        else:
            state = _still_held(events, ticket)

    return (E.make_event("attempt", clock, ticket=ticket, raw=raw,
                         outcome="refused" if (refusal or state) else "succeeded"),
            refusal, state)


def _still_held(events, ticket):
    question = waiting(events)
    if question is None or question.get("ticket") != ticket or not holds(events, question):
        return None
    return question["asks"]

import os
import shlex
import uuid

import books as K
import chain as C
import events as E
import floor as F
import line as L
import open_close as O
import position as P
import replan as R
import ticket as T
import vocabulary as V


class BadCommand(ValueError):
    pass


COMMANDS = ("init", "close", "status", "report", "question", "archive", "bind")

INTERNAL = ("gate", "statedir", "reset")

REMOVED = {
    "begin": "not a command — the pipeline opens each ticket itself and no agent does, "
             "so permission belongs to the TICKET rather than to an agent's identity",
    "issues": "not a command — the pipeline records EVERY close attempt automatically, "
              "with the raw process-log line; findings go to `.metaxotrail/issues.jsonl`",
    "merge": "`status` shows what to do next",
    "release": "`status` shows what to do next",
    "retract": "`status` shows what to do next",
    "claim": "not a command — `init` records the project, the "
             "run hash, the chain and the starting commit when it makes the books",
    "clean": "not a command — a step is closed with `close`",
    "override": "not a command at all — it is the record the write hook writes when the operator "
                "answers a question, and the pipeline READS it. An `override` subcommand is the "
                "pipeline taking an agent's word that a human approved",
    "adopt": "not a command — adoption is an ARGUMENT to `init`",
}

OPERATOR = V.check_by("OPERATOR")


def _log(project):
    try:
        return K.read_log(project)
    except K.BadBooks as exc:
        raise _unreadable(project, exc)


def _unreadable(project, exc):
    import gate as _S8
    try:
        here = K.running(project)
    except K.BadBooks:
        here = True
    above = None if here else _S8.live_run_above(project)
    if above is not None:
        return BadCommand("the shell stands in %s, below the live run at %s, and there are no books "
                          "here. Run `cd %s` on its own, then repeat this command. If the shell does "
                          "not stay at %s, this session was started below it, and Claude Code returns "
                          "the shell to the folder it started in: restart the session at %s. Nothing "
                          "here is read as that run's books."
                          % (project, above, shlex.quote(above), above, above))
    return BadCommand("these books cannot be read: %s" % exc)


def _undamaged(project):
    try:
        found = K.damage(project)
    except K.BadBooks as exc:
        raise BadCommand("these books cannot be read: %s" % exc)
    if found is None:
        return None
    raise BadCommand("the records have been altered and this close would credit work on them: "
                     "%s.\nNothing here can repair that — `status` and `report` still read, so "
                     "look first, and `question end`, then `archive --abandon` on the operator's `OVERRIDE END`, "
                     "ends the run and says so on the record"
                     % found)


def _open(project, events):
    event = P.open_ticket(events, False)
    if event is None:
        raise BadCommand("nothing is open in this run, so there is nothing to close: %s"
                         % P.explain_open_failure(events, False))
    return event["ticket"]


def _step_of(events, ticket):
    for event in events:
        if event.get("kind") == "open" and event.get("ticket") == ticket:
            return event.get("step"), event.get("ms")
    raise BadCommand("%r was never opened in this run" % (ticket,))


def _raw_line(project):
    body = K.read_process_log(project)
    lines = [line for line in body.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def artifact_for(project, step):
    if step in ("10-context-map", "20-plan-impl", "40-test-plan"):
        return os.path.join(project, K.WORKING_DOCUMENT)
    if step == "50-test-impl":
        return os.path.join(project, K.RESULTS)
    return None


def baseline_for(events):
    for event in reversed(events):
        if event.get("kind") == "close" and event.get(E.COMMIT):
            return event[E.COMMIT]
    return events[0]["base_commit"]


def _evidence(project, events, step, record, ms=None):
    counts = () if record is None else tuple(record.get(name) for name in ("h", "m", "l"))
    return {
        "artifact": artifact_for(project, step),
        "run_hash": events[0]["run_hash"],
        "row": record is not None,
        "count": record is not None and all(value is not None for value in counts),
        "discharged": any(counts),
        "tick": record is not None and record.get("flag") == V.QA,
        "changed": (O.changed_since(project, baseline_for(events))
                    if step == O.IMPLEMENT else None),
        "secrets": O.secret_like(project) if step in O.SECRET_STEPS else None,
        "code": (O.code_digest(project) if "frozen code" in O.close_conditions(step, ms, events)
                 else None),
        "document": artifact_for(project, O.worked_on(step)),
    }


def apply_answer(project, clock):
    events = _log(project)
    question = F.asked(events)
    override = F.authority(events)
    if question is None or override is None:
        return None
    if F.is_content(question):
        return None
    if question.get("asks") == F.END:
        try:
            _honoured(events, question)
        except BadCommand as exc:
            if override["text"] != F.END_FORM and F.short_of_target(events) is None:
                return None
            return _spend_by_refusing(project, clock, events, question, exc)
        return None
    if not _unread(events, question):
        return None
    try:
        text = _honoured(events, question)
    except BadCommand as exc:
        return _spend_by_refusing(project, clock, events, question, exc)
    try:
        if text.startswith("OVERRIDE OPEN "):
            return _amend(project, clock, events, text.split()[-1])
        if text.startswith("OVERRIDE ROLLBACK "):
            return _repair(project, clock, events, V.override_rollback_step(text), question)
        return _close_on_his_word(project, clock, events, text.split()[-1], question)
    except BadCommand as exc:
        return _spend_by_refusing(project, clock, events, question, exc)


def _unread(events, question):
    after = events[events.index(question) + 1:]
    return not [event for event in after
                if event.get("kind") == "close" and event.get("ticket") == question["ticket"]]


def _spend_by_refusing(project, clock, events, question, refusal):
    said = F.authority(events)
    reply = said["text"] if said else ""
    offered = question.get("legal") or []
    why = ("it is not one of the replies offered. What is legal is %s"
           % ", ".join(repr(move) for move in offered) if reply not in offered else str(refusal))
    text = "%s — your reply %r was not accepted: %s" % (
        str(question.get("text")).split(" — your reply ")[0],
        reply[len(F.OTHER) + 1:] if F.is_other(said) else reply, why)
    try:
        note = _ask(project, clock, question["asks"], question["ticket"], question["step"], text)
    except BadCommand:
        return ("%s\nThe run is no longer in the state that instruction answered, so nothing is "
                "asked again and nothing is held — carry on from where the run stands" % refusal)
    raise BadCommand("%s\n%s" % (refusal, note))


def _honoured(events, question):
    override = F.authority(events)
    if question.get("asks") == F.MISOPENED:
        legal = amendment_set(events)
        if override["text"] not in legal:
            raise BadCommand("%r is not legal here. What is legal is %s — and this record is "
                             "spent by the refusal"
                             % (override["text"], ", ".join(repr(one) for one in legal)))
        return override["text"]
    try:
        return F.check_override(events)
    except F.BadFloor as exc:
        raise BadCommand(str(exc))


def _amend(project, clock, events, wanted):
    open_now = _open(project, events)
    if wanted == open_now:
        return ("%r is the ticket already open — you are saying the pipeline was right. Nothing "
                "is opened and nothing is voided, and the run continues on it" % (wanted,))
    step, ms = _step_of(events, open_now)
    record_close(project, clock, events, ticket=open_now, step=step, ms=ms,
           writer=O.writer_of(open_now, events), by=OPERATOR, status="void")
    wanted_step = _named_step(events, wanted)
    named = T.parse_ticket(wanted)["milestone"]
    _open_ticket(project, clock, wanted, wanted_step,
                 None if named == T.NO_MILESTONE else named)
    return "applied %r: %s closed `void`, %s opened" % ("OVERRIDE OPEN " + wanted, open_now,
                                                        wanted)


def _named_step(events, wanted):
    for step, ticket in _with_the_open_one(events, _could_have_been_cut(events)):
        if ticket == wanted:
            return step
    raise BadCommand("%r is not a ticket the chain could have cut here" % (wanted,))


def _repair(project, clock, events, target, question):
    ticket = question["ticket"]
    step, ms = _step_of(events, ticket)
    record = _last_attempt(events, ticket)
    writer = O.writer_of(ticket, events)
    if C.kind_of(step) == O.REVIEW:
        record_close(project, clock, events, ticket=ticket, step=step, ms=ms, writer=writer,
               by=O.by_for("reviewed", writer), status="reviewed",
               h=record["h"], m=record["m"], l=record["l"], flag="ROLLBACK %d" % target)
    else:
        record_close(project, clock, events, ticket=ticket, step=step, ms=ms, writer=writer,
               by=OPERATOR, status="void")
    _cut(project, clock, "93-rollback:%d" % target, ms)
    return "applied %r: %s closed, `93-rollback:%d` opened" % (
        "OVERRIDE ROLLBACK %d" % target, ticket, target)


def _close_on_his_word(project, clock, events, ticket, question):
    step, ms = _step_of(events, ticket)
    record = _last_attempt(events, ticket)
    writer = O.writer_of(ticket, events)
    record_close(project, clock, events, ticket=ticket, step=step, ms=ms, writer=writer,
           by=OPERATOR, status="reviewed", h=record["h"], m=record["m"], l=record["l"],
           flag=record["flag"])
    _after(project, clock, ticket)
    return "applied %r: %s closed on your authority" % ("OVERRIDE CLOSE " + ticket, ticket)


def _last_attempt(events, ticket):
    for event in reversed(events):
        if event.get("kind") == "attempt" and event.get("ticket") == ticket:
            try:
                return L.parse_line(event["raw"])
            except L.BadLine:
                continue
    return {"h": 0, "m": 0, "l": 0, "flag": ""}


def init(project, clock, chain, start_step=0, milestones_done=None, session=None):
    if chain not in V.CHAINS:
        raise BadCommand("`init` takes the chain the operator picked — %s — and has no default: "
                         "a lite run measured against ten steps never finishes"
                         % " or ".join(V.CHAINS))
    try:
        base = O.head_of(project)
    except O.BadClose as exc:
        raise BadCommand("no repository, no baseline: %s" % exc)
    names = K.set_aside_in_root(project)
    try:
        keep = O.tracked(project, names) if names else ()
    except O.BadClose as exc:
        raise BadCommand("git could not say which set-aside files it tracks: %s" % exc)
    _checked_adoption(project, chain, int(start_step or 0),
                      None if milestones_done is None else list(milestones_done))
    if milestones_done:
        try:
            held = O.secrets_held(project, "init")
        except O.BadClose as exc:
            raise BadCommand("git could not say which new files look like secrets: %s" % exc)
        if held:
            raise BadCommand("this adoption delivers %s, and its commit would be held: %s"
                             % (", ".join(milestones_done), held))
    run_hash = uuid.uuid4().hex[:8]
    try:
        K.init(project, run_hash, clock, chain, base, adopted=bool(start_step),
               start_step=int(start_step), keep=keep)
    except K.BadBooks as exc:
        raise BadCommand("the books were not made: %s" % exc)
    keep_copies(project)
    import undo_block as U
    U.install(project)
    import gate as S8
    S8.attach(project, clock, session=session)
    if start_step:
        try:
            _attest(project, clock, chain, int(start_step), list(milestones_done or ()))
        except BadCommand as exc:
            raise BadCommand("%s\nThe books were made before this could be known, so the run is "
                             "live and unattested: `question end`, then `archive --abandon` on the "
                             "operator's `OVERRIDE END`, ends it and says so, and "
                             "`init` refuses a live log" % exc)
    _open_next(project, clock, _first_step(chain, int(start_step)), None)
    return "run %s initialised on the %s chain" % (run_hash, chain)


NONE_DONE = "none"


def _checked_adoption(project, chain, start_step, milestones_done):
    if not start_step:
        return
    first = _first_step(chain, start_step)
    inside = first in C.milestoned(chain)
    if inside and milestones_done is None:
        raise BadCommand("a run adopted inside the milestone branch must say WHICH milestones "
                         "are done — the start step %s begins at %r, and steps 30 through 51 run "
                         "once per milestone, so that names as many different places as the "
                         "plan has milestones. Say which, or say %r"
                         % (start_step, first, NONE_DONE))
    if not inside and milestones_done:
        raise BadCommand("the milestones named after the start step say which passes through the "
                         "milestone branch are finished, and the start step %s begins at %r, before the "
                         "branch — there is no pass to have finished. Drop it, or start inside the branch"
                         % (start_step, first))
    ids = _plan_ids(project)
    if not milestones_done:
        return
    unknown = [ms for ms in milestones_done if ms not in ids]
    if unknown:
        raise BadCommand("the plan does not contain %s — the operator's word may attest work "
                         "the plan can name, and numbers are never reused"
                         % ", ".join(repr(one) for one in unknown))
    if not [ms for ms in ids if ms not in milestones_done]:
        raise BadCommand("every milestone in the plan is named as done, so no pass is in force "
                         "and the step you are starting at belongs to none of them — a "
                         "milestoned ticket cut without a milestone earns nothing at any step. "
                         "A run with nothing left to do is finished, not adopted")


def _first_step(chain, start_step):
    for step in C.steps(chain):
        if int(step.split("-")[0]) >= (start_step or 0):
            return step
    raise BadCommand("step %s is past the end of the %s chain" % (start_step, chain))


def _attest(project, clock, chain, start_step, milestones_done):
    ids = _plan_ids(project)
    for step in C.steps(chain):
        if int(step.split("-")[0]) >= start_step:
            break
        if step in C.milestoned(chain):
            continue
        extra = {}
        if step == E.PLAN_REVIEW_STEP:
            extra = {"ms_n": len(ids), "ms_ids": list(ids)}
        _attested(project, clock, step, None, extra)
    for milestone in milestones_done:
        for step in C.milestoned(chain):
            _attested(project, clock, step, milestone, {})
    for step in C.milestoned(chain):
        if int(step.split("-")[0]) < start_step:
            _attested(project, clock, step, _in_force(_log(project)), {})


def _attested(project, clock, step, milestone, extra):
    events = _log(project)
    ticket = _cut(project, clock, step, milestone)
    record_close(project, clock, _log(project), ticket=ticket, step=step, ms=milestone,
           writer=O.writer_at_open(step, milestone, events), by=OPERATOR, status="attested",
           **extra)


def _plan_ids(project):
    try:
        return R.milestones(_plan_text(project))
    except R.BadReplan as exc:
        raise BadCommand("the plan's milestones cannot be read: %s" % exc)


def _plan_text(project):
    path = os.path.join(project, K.WORKING_DOCUMENT)
    try:
        with open(path) as handle:
            return handle.read()
    except OSError as exc:
        raise BadCommand("the plan cannot be read at %s: %s" % (path, exc))


def close(project, clock, status, h=None, m=None, l=None, flag="", from_fork=False):
    note = apply_answer(project, clock)
    _undamaged(project)
    events = _log(project)
    ticket = _open(project, events)
    step, ms = _step_of(events, ticket)
    writer = O.writer_of(ticket, events)
    if writer == E.CLEAN_WRITER and not from_fork:
        _record_attempt(project, ticket, _raw_line(project), clock)
        raise BadCommand("%s%r was cut to %r and this command did not come from inside the "
                         "reviewer — run the review, do not retry the close"
                         % (note + "\n" if note else "", ticket, writer))

    raw = _raw_line(project)
    if not raw.strip():
        raise BadCommand("the process log holds no line for %r — a close needs one, and an "
                         "empty file is a refusal rather than a silence" % (ticket,))
    record, refusal = _read_line(raw, ticket)
    try:
        event = close_event(project, clock, ticket=ticket, step=step, ms=ms, writer=writer,
                            by=O.by_for(status, writer), status=status, h=h, m=m, l=l,
                            flag=flag)
    except (E.BadEvent, V.BadValue, O.BadClose) as exc:
        _record_attempt(project, ticket, raw, clock)
        raise BadCommand("%sthis close is not a record the books may hold: %s"
                         % (note + "\n" if note else "", exc))
    if refusal is None:
        refusal = _judged(project, events, step, ms, record, event)
    attempt, refusal, state = F.attempt(events, event, raw, clock, refused=refusal)
    try:
        K.append_event(project, attempt)
    except K.BadBooks as exc:
        raise BadCommand("the books would not hold this attempt: %s" % exc)
    if state is not None:
        return "\n".join(filter(None, [note,
                                       _hold(project, clock, ticket, step, state, refusal)]))
    if refusal is not None:
        raise BadCommand("%s%s" % (note + "\n" if note else "", refusal))
    write_close(project, clock, events, event)
    return "\n".join(filter(None, [note, _after(project, clock, ticket)]))


def _hashed(project, fields):
    stamped = O.stamp_plan_hash(os.path.join(project, K.WORKING_DOCUMENT),
                                dict(fields, kind="close"))
    return {name: value for name, value in stamped.items() if name != "kind"}


def close_event(project, clock, **fields):
    fields = dict(fields, **_denominator_if_set(project, fields.get("step"),
                                                fields.get("status"), fields.get("writer"),
                                                fields.get("h"), fields.get("m")))
    return E.make_event("close", clock, **_hashed(project, fields))


def write_close(project, clock, events, event):
    taken = _taken(project, event)
    if taken is not None:
        event = dict(event, **{K.FINGERPRINT: K.fingerprint(taken[1])})
    try:
        K.append_event(project, _stamped(project, clock, events, event))
    except K.BadBooks as exc:
        raise BadCommand("the books would not hold this close: %s" % exc)
    keep_copies(project, taken)
    return event


def document_reviewed(project, step):
    produced = {_review_of(int(name.split("-")[0])): name
                for name, kind in C.STEPS if kind != O.REVIEW}
    if step not in produced:
        return None
    return artifact_for(project, produced[step])


def _taken(project, event):
    if event.get("status") != "reviewed":
        return None
    document = document_reviewed(project, event.get("step"))
    if document is None:
        return None
    try:
        with open(document, "rb") as handle:
            data = handle.read()
        return K.copy_name(document, event["ticket"]), data
    except (OSError, K.BadBooks):
        return None


def _loop_copies(events, step, ms):
    rounds = [event for event in O.loop_of(step, ms, events) if event.get("status") == "reviewed"]
    if not rounds:
        return None, None
    fresh = next((event for event in reversed(rounds)
                  if event.get("writer") == E.CLEAN_WRITER), None)
    return fresh, rounds[-1]


def _copy_of(project, close):
    if close is None:
        return None
    document = document_reviewed(project, close.get("step"))
    return None if document is None else K.copy_name(document, close["ticket"])


def keep_copies(project, taken=None, ending=False):
    try:
        wanted = set()
        if not ending:
            events = K.read_log(project)
            last = next((event for event in reversed(events)
                         if event.get("kind") == "close" and event.get("status") == "reviewed"),
                        None)
            if last is not None:
                wanted = {name for name in (_copy_of(project, close) for close in
                                            _loop_copies(events, last["step"], last.get("ms")))
                          if name}
        for name in K.copies(project):
            if name not in wanted:
                K.remove_copy(project, name)
        if taken is not None and taken[0] in wanted and taken[0] not in K.copies(project):
            K.write_copy(project, taken[0], taken[1])
    except (OSError, K.BadBooks):
        pass
    return None


def _copy_line(project, events, standing):
    step = standing["step"]
    document = document_reviewed(project, step)
    if document is None:
        return None
    fresh, latest = _loop_copies(events, step, standing.get("ms"))
    if fresh is None and latest is None:
        return ("the document's copy: no copy — the first review of this loop reads the whole "
                "document")
    fresh_round = standing.get("writer") == E.CLEAN_WRITER
    compare = fresh if fresh_round else latest
    try:
        name = _copy_of(project, compare)
        if name is None or not K.matching_copy(project, name, compare.get(K.FINGERPRINT)):
            return ("the document's copy: no copy — it is missing or altered; read the whole "
                    "document")
        kept = os.path.join(K.FLOW, name)
        line = ("the document's copy: %s, as the %s saw it — review what changed since: "
                "`git diff --no-index --word-diff %s %s`"
                % (kept, "last fresh review" if fresh_round else "last review",
                                     kept, os.path.basename(document)))
        newer = _copy_of(project, latest) if fresh_round and latest is not compare else None
        if newer is not None and K.matching_copy(project, newer, latest.get(K.FINGERPRINT)):
            line += "; the latest review's copy is %s" % os.path.join(K.FLOW, newer)
        return line
    except K.BadBooks:
        return None


def record_close(project, clock, events, **fields):
    return write_close(project, clock, events, close_event(project, clock, **fields))


def _record_attempt(project, ticket, raw, clock):
    try:
        K.append_event(project, E.make_event("attempt", clock, ticket=ticket,
                                             outcome="refused", raw=raw))
    except (K.BadBooks, E.BadEvent, V.BadValue):
        pass


def _denominator_if_set(project, step, status, writer, h, m):
    if step != E.PLAN_REVIEW_STEP or status != "reviewed":
        return {}
    if writer != E.CLEAN_WRITER or (h or m):
        return {}
    ids = _plan_ids(project)
    return {"ms_n": len(ids), "ms_ids": list(ids)}


def _read_line(raw, ticket):
    try:
        return L.parse_line(raw) if raw.strip() else None, None
    except L.BadLine as exc:
        return None, str(exc)


def _judged(project, events, step, ms, record, event):
    if record["ticket"] != event["ticket"]:
        return ("the last line is for %r and the open ticket is %r — write the line again for "
                "the ticket that is open" % (record["ticket"], event["ticket"]))
    try:
        L.agrees(record, event["status"], h=event.get("h"), m=event.get("m"), l=event.get("l"))
    except L.BadLine as exc:
        return str(exc)
    try:
        O.check_close(events, event, **_evidence(project, events, step, record, ms))
    except O.BadClose as exc:
        return str(exc)
    return None


def _stamped(project, clock, events, event):
    stamped = O.stamp_score(events, event)
    try:
        return O.stamp_milestone(project, os.path.join(project, K.WORKING_DOCUMENT), events,
                                 stamped)
    except O.BadClose as exc:
        raise BadCommand(str(exc))


def _hold(project, clock, ticket, step, state, refusal):
    events = _log(project)
    waiting = F.waiting(events)
    text = (F.why_held(events, state, ticket, step) or refusal
            or (waiting.get("text") if waiting and waiting.get("ticket") == ticket else None))
    last = F.asked(events)
    if (last is not None and last is waiting and F.holds(events, last) and last.get("ticket") == ticket
            and last.get("asks") == state and last.get("text") == (text or _NO_TEXT)):
        note = _shown(events, last)
    else:
        note = _ask(project, clock, state, ticket, step, text)
    if refusal is not None:
        raise BadCommand("%s\n%s" % (refusal, note))
    return note


def question(project, clock, kind, text, *choices):
    options = _options(kind, choices)
    note = apply_answer(project, clock)
    events = _log(project)
    standing = F.asking(events)
    if standing is not None and (kind != F.END or standing.get("asks") == F.END):
        if kind == F.END:
            return "\n".join(filter(None, [note, _shown(events, standing)]))
        raise BadCommand("%s is still waiting on the operator — %s. One question at a time: wait for their answer "
                         "and end the turn; nothing new is asked meanwhile but `question end`.\n%s"
                         % (standing["qid"], standing.get("text"), _shown(events, standing)))
    held = F.waiting(events)
    if kind == F.OBSERVE and held is not None and F.holds(events, held) and F.is_other(F.authority(events)):
        raise BadCommand("%s is a decision the operator answered in their own words, and it still holds the ticket — "
                         "bring their words back on a new `question ask` box, not an observation, which would lift "
                         "the hold" % held["qid"])
    lapsed = ("%s, the observation, is no longer waiting — say so in the chat before the new box" % held["qid"]
              if held is not None and held.get("asks") == F.OBSERVE else None)
    note = "\n".join(filter(None, [note, lapsed]))
    if kind == F.END:
        ticket, step = _last_opened(events)
        return "\n".join(filter(None, [note, _ask(project, clock, kind, ticket, step, text)]))
    ticket = _open(project, events)
    step, _ms = _step_of(events, ticket)
    if kind not in F.KINDS:
        raise BadCommand("%r is not a kind of question this system has — they are %s, and the "
                         "kind is an argument rather than a reading of the text"
                         % (kind, ", ".join(F.KINDS)))
    return "\n".join(filter(None, [note, _ask(project, clock, kind, ticket, step, text, options)]))


def _options(kind, choices):
    if not choices:
        return None
    if not F.is_content(kind):
        raise BadCommand("a %r question takes no options — its replies are the moves the run's state "
                         "computes, never a menu the asking agent wrote; only `question ask` and `question "
                         "observe` take `--option`" % (kind,))
    if kind == F.OBSERVE and "--part" in choices:
        raise BadCommand("an observation takes one part — `--option \"<label>\"` for each choice, and no `--part`")
    parts, words = [], list(choices)
    while words:
        word = words.pop(0)
        if word == "--part":
            parts.append([])
        elif word == "--option" and words and words[0].strip() and not words[0].startswith("--"):
            (parts[-1] if parts else parts.append([]) or parts[-1]).append(words.pop(0).strip())
        else:
            raise BadCommand("%r is not part of a question's options — they are `--option \"<label>\"` for "
                             "each, and `--part` before each part's options" % (word,))
    if (not 1 <= len(parts) <= E.MAX_PARTS
            or any(not E.MIN_CHOICES <= len(part) <= E.MAX_CHOICES for part in parts)
            or any(label.splitlines() != [label] or part.count(label) > 1 for part in parts for label in part)):
        raise BadCommand("a question has %d to %d options in each part, each on one line and none twice, and at "
                         "most %d parts, as the sheet shows them; these are %r"
                         % (E.MIN_CHOICES, E.MAX_CHOICES, E.MAX_PARTS, parts))
    return parts


def _ask(project, clock, kind, ticket, step, text=None, options=None):
    events = _log(project)
    legal = (amendment_set(events) if kind == F.MISOPENED
             else F.legal(events, kind, ticket, step))
    if not legal:
        raise BadCommand("a %r question offers nothing in this state, and a question nobody can "
                         "answer holds the run on a door with no exit" % (kind,))
    if F.is_content(kind) and not (text or "").strip():
        raise BadCommand("a content question needs its text — `question ask \"<what you need to "
                         "know>\"` — a blank holds the run with nothing to answer")
    qid = "q%d" % (1 + len([e for e in events if e.get("kind") == "question"]))
    try:
        K.append_event(project, E.make_event(
            "question", clock, qid=qid, ticket=ticket, asks=kind,
            text=text or _NO_TEXT, legal=list(legal), step=step,
            **({E.OPTIONS: options} if options else {})))
    except K.BadBooks as exc:
        raise BadCommand("the books would not hold this question: %s" % exc)
    asked = {"asks": kind, "legal": list(legal), E.OPTIONS: options}
    return "\n".join(["%s — reply with%s" % (qid, _replies(asked))] + _costs(events, asked, ticket, step)
                     + [_BRIEF_FIRST])


_NO_TEXT = "the run is waiting on you"

_BRIEF_FIRST = ("Before the operator answers this, on a sheet or by typing, brief them in the chat, in this message: "
                "what they need to decide or do — each option's pros, cons and cost, or the steps and how to check "
                "them — and your recommendation (MetaXoTRail's rule \"Brief before you ask\").")


def _shown(events, question):
    return "\n".join(["%s — %s — reply with%s" % (question["qid"], question.get("text"), _replies(question))]
                     + _costs(events, question, question.get("ticket"), question.get("step")))


def _replies(question):
    if question.get("asks") == F.OBSERVE:
        return ": a click on one of its options, or %s — it has no keys" % F.ANSWER_FORM
    if not F.is_content(question):
        return " one of: %s" % ", ".join(question["legal"])
    keyed = [key for key, _label in F.keys(question)]
    if not keyed:
        return ": %s" % ", ".join(question["legal"])
    if len(question[E.OPTIONS]) > 1:
        return " one key for each part, as %s — or %s" % (" ".join(key for key in keyed if key.endswith("a")),
                                                           F.ANSWER_FORM)
    return " one of: %s — or %s" % (", ".join(keyed), F.ANSWER_FORM)


def _costs(events, question, ticket, step):
    if question.get("asks") == F.OBSERVE:
        return ["  - %s" % label for part in question.get(E.OPTIONS) or [] for label in part]
    if F.is_content(question):
        return ["  %s) %s" % (key, label) for key, label in F.keys(question)]
    named = F.labels(dict(question, ticket=question.get("ticket", ticket)))
    return ["  %s) %s%s — on the sheet: \"%s\"" % (key, move, " — %s" % cost if cost else "", named[move])
            for key, move in F.keys(question)
            for cost in [F.repeats(events, move, ticket, step, question.get("asks"))]]


def _last_opened(events):
    for event in reversed(events):
        if event.get("kind") == "open":
            return event.get("ticket"), event.get("step")
    return None, None


def _with_the_open_one(events, out):
    standing = P.open_ticket(events, False)
    if standing is None or standing["ticket"] in [ticket for _step, ticket in out]:
        return out
    return [(standing["step"], standing["ticket"])] + out


def amendment_set(events):
    return ["OVERRIDE OPEN %s" % ticket
            for _step, ticket in _with_the_open_one(events, _could_have_been_cut(events))]


def _could_have_been_cut(events):
    last = next((e for e in reversed(events)
                 if e.get("kind") == "close" and e.get("status") != "void"), None)
    if last is None:
        raise BadCommand("nothing has closed in this run, so no ticket followed anything and "
                         "there is no amendment to make")
    step = last["step"]
    steps = C.steps(C.chain_of(events))
    number = int(step.split("-")[0])
    if step not in steps:
        return [(_review_of(V.repair_target(step) or _fixed_step(step)),
                 _would_be(events, _review_of(V.repair_target(step) or _fixed_step(step)),
                           last.get("ms")))]
    out = []
    if C.kind_of(step) == O.REVIEW:
        out.append((step, _would_be(events, step, last.get("ms"))))
    else:
        out.append((steps[steps.index(step) + 1], _would_be(events, steps[steps.index(step) + 1],
                                                            last.get("ms"))))
    out.append(("92-fix:%d" % (number - 1 if C.kind_of(step) == O.REVIEW else number),
                _would_be(events, "92-fix", last.get("ms"))))
    ordered = V.rollback_step(last.get("flag") or "")
    if ordered is not None:
        out.append(("93-rollback:%d" % ordered,
                    _would_be(events, "93-rollback", last.get("ms"))))
    if E.completes(last) and steps.index(step) + 1 < len(steps):
        following = steps[steps.index(step) + 1]
        pair = (following, _would_be(events, following, last.get("ms")))
        if pair not in out:
            out.append(pair)
    return out


def _would_be(events, step, ms):
    number = int(step.split("-")[0].split(":")[0])
    standing = P.open_ticket(events, False)
    if standing is not None and int(standing["ticket"][:2]) == number:
        return standing["ticket"]
    opened = [e["ticket"] for e in events if e.get("kind") == "open"]
    return T.make_ticket(number, ms, T.next_version(opened, number))


def _after(project, clock, closed_ticket):
    events = _log(project)
    close_event = next(e for e in reversed(events)
                       if e.get("kind") == "close" and e.get("ticket") == closed_ticket)
    step = close_event["step"]
    ms = close_event.get("ms")
    status = close_event["status"]
    number = int(step.split("-")[0])

    if status == "fixed":
        target = V.repair_target(step)
        nxt = _review_of(target) if target is not None else _review_of(_fixed_step(step))
        return _open_next(project, clock, nxt, ms)
    if C.kind_of(step) == O.REVIEW:
        if close_event.get("h") or close_event.get("m"):
            rollback = V.rollback_step(close_event.get("flag") or "")
            if rollback is not None:
                return _open_next(project, clock, "93-rollback:%d" % rollback, ms)
            return _open_next(project, clock, "92-fix:%d" % (number - 1), ms)
        if close_event["writer"] != E.CLEAN_WRITER:
            return _open_next(project, clock, step, ms)
        return _open_following(project, clock, step, ms)
    return _open_next(project, clock, _review_of(number), ms)


def _review_of(number):
    for step, kind in C.STEPS:
        if kind == O.REVIEW and int(step.split("-")[0]) == int(number) + 1:
            return step
    raise BadCommand("step %s has no review in the chain" % (number,))


def _fixed_step(step):
    return int(step.split(":")[-1])


def _open_following(project, clock, step, ms):
    events = _log(project)
    chain = C.chain_of(events)
    steps = C.steps(chain)
    position = steps.index(step)
    if step == E.LAST_MILESTONED.get(chain):
        pending = _in_force(events)
        if pending is not None:
            return _open_next(project, clock, _branch_opens_at(steps), pending)
    if position + 1 >= len(steps):
        return "the chain is complete — nothing opens, and `archive` ends the run"
    return _open_next(project, clock, steps[position + 1], ms)


def _branch_opens_at(steps):
    return next(step for step in steps if step in E.MILESTONE_PAIRS)


def _in_force(events):
    return C.in_force(events)


def milestone_for(events, step, ms):
    if step in E.MILESTONE_PAIRS or step in E.MILESTONE_PAIRS.values():
        return _in_force(events)
    if step in C.steps(C.chain_of(events)):
        return None
    return ms


def _open_next(project, clock, step, ms):
    ticket = _cut(project, clock, step, milestone_for(_log(project), step, ms))
    ms = T.parse_ticket(ticket)["milestone"]
    ms = None if ms == "MX" else ms
    if not O.needs_a_line(step, ms, _log(project)):
        return _closes_itself(project, clock, ticket, step, ms)
    return "%s opened as %s" % (step, ticket)


def _closes_itself(project, clock, ticket, step, ms):
    record_close(project, clock, _log(project), ticket=ticket, step=step, ms=ms,
           writer=O.writer_of(ticket, _log(project)), by=O.by_for("passed", "orch"),
           status="passed")
    return "%s opened as %s and closed itself `passed` — %s\n%s" % (
        step, ticket, "the integration milestone builds nothing, so the close fires at the open",
        _after(project, clock, ticket))


def _open_ticket(project, clock, ticket, step, ms):
    try:
        K.append_event(project, E.make_event("open", clock, ticket=ticket, step=step, ms=ms,
                                             writer=O.writer_at_open(step, ms, _log(project))))
    except K.BadBooks as exc:
        raise BadCommand("the books would not hold this open: %s" % exc)
    return ticket


def _cut(project, clock, step, ms):
    events = _log(project)
    milestone = ms
    number = int(step.split("-")[0])
    try:
        ticket = K.cut_ticket(project, number, milestone)
    except (K.BadBooks, T.BadTicket) as exc:
        raise BadCommand("the ticket could not be cut: %s" % exc)
    return _open_ticket(project, clock, ticket, step, milestone)


def status(project, clock):
    note = apply_answer(project, clock)
    import undo_block as U
    U.install(project)
    return "\n".join(filter(None, [note, describe(project, _log(project))]))


def describe(project, events):
    note = None
    standing = _positioned(events)
    if standing is _BROKEN:
        return "\n".join(filter(None, [note, _damage_note(project),
                                       "the books cannot be positioned: %s"
                                       % _why_not(events),
                                       "`report` still lists what closed, and `question "
                                       "end`, then `archive --abandon` on the operator's "
                                       "`OVERRIDE END`, ends the run and says so on the record"]))
    if standing is None:
        return "\n".join(filter(None, [note, _damage_note(project),
                                       "nothing is open: %s"
                                       % P.explain_open_failure(events, False)]))
    ticket = standing["ticket"]
    step = standing["step"]
    held = F.waiting(events)
    observed = held if held is not None and held.get("asks") == F.OBSERVE else None
    other = F.authority(events) if held is not None and F.is_other(F.authority(events)) else None
    held = held if F.holds(events, held) else None
    answer = _content_answer(events)
    return "\n".join(filter(None, [
        note,
        _damage_note(project),
        "open: %s at %s" % (ticket, step),
        ("\n".join(["WAITING ON THE OPERATOR — %s: %s. Reply with%s"
                    % (held["qid"], held["text"], _replies(held))]
                   + _costs(events, held, held.get("ticket"), held.get("step"))))
        if held else None,
        ("their reply to %s (not an answer): %s" % (held["qid"], other["text"][len(F.OTHER) + 1:]))
        if held and other else None,
        ("\n".join(["asked %s (an observation, holds nothing): %s" % (observed["qid"], observed.get("text"))]
                   + _costs(events, observed, observed.get("ticket"), observed.get("step"))))
        if observed else None,
        ("answered %s: %s" % answer) if answer else None,
        ("answered %s: %s — `archive --abandon` ends the run" % (F.asked(events)["qid"], F.END_FORM))
        if _end_authorised(events) else None,
        ("answered %s: %s — the run goes on" % (F.asked(events)["qid"], _kept_going(events)))
        if _kept_going(events) else None,
        "who may write: %s" % P.who_may_write(events, False),
        _frozen_line(events),
        None if held else "the line to append: %s" % O.line_at_open(ticket, step),
        _copy_line(project, events, standing),
        "score: %s" % (C.score(events),)]))


def _frozen_line(events):
    ms = C.frozen(events)
    if ms is None:
        return None
    again = [sid.split("-")[0] for sid in C.milestoned_in_force(events) if sid != O.IMPLEMENT]
    return ("the project's production code is locked until %s is delivered; a production change "
            "sends %s back to its code step: %s repeat"
            % (ms, ms, F.joined(again)))


def _content_answer(events):
    question = F.asked(events)
    if question is None or not F.is_content(question):
        return None
    override = F.authority(events)
    if override is None or F.is_other(override):
        return None
    standing = P.open_ticket(events, False)
    if standing is None or standing["ticket"] != question.get("ticket"):
        return None
    return (question["qid"], _reading(question, override["text"]))


def _reading(question, text):
    labels = dict(F.keys(question))
    chose = text.split() if F.chosen(question, text) == text else []
    return "; ".join("%s — %s" % (key, labels[key]) for key in chose) or text


def report(project, clock):
    note = apply_answer(project, clock)
    events = _log(project)
    rows = [note] if note else []
    asked = {e.get("qid"): e for e in events if e.get("kind") == "question" and F.is_content(e)}
    for event in events:
        if event.get("kind") == "question" and F.is_content(event):
            rows.append("%-20s asked     %s  %s" % (event.get("step"), event.get("qid"), event.get("text")))
            continue
        if event.get("kind") == "override" and event.get("question") in asked and F.is_other(event):
            rows.append("%-20s replied   %s  %s" % ("", event.get("question"), event["text"][len(F.OTHER) + 1:]))
            continue
        if event.get("kind") == "override" and event.get("question") in asked:
            rows.append("%-20s answered  %s  %s" % ("", event.get("question"),
                                                     _reading(asked[event.get("question")], event.get("text"))))
            continue
        if event.get("kind") != "close":
            continue
        rows.append("%-20s %-9s %-8s %s" % (event.get("step"), event.get("status"),
                                            event.get("ms") or "", _on_trust(event)))
    return "\n".join(filter(None, [_damage_note(project),
                                   "run %s on the %s chain" % (events[0]["run_hash"],
                                                               events[0]["chain"])]
                                  + rows + ["score: %s" % (C.score(events),)]))


_BROKEN = object()


def _positioned(events):
    try:
        return P.open_ticket(events, False)
    except P.BadPosition:
        return _BROKEN


def _why_not(events):
    try:
        P.open_ticket(events, False)
    except P.BadPosition as exc:
        return str(exc)
    return ""


def _damage_note(project):
    try:
        found = K.damage(project)
    except K.BadBooks:
        return None
    return None if found is None else "THE RECORDS HAVE BEEN ALTERED — %s" % found


def _on_trust(event):
    if event.get("status") == "attested":
        return "ATTESTED BY THE OPERATOR, not checked"
    if event.get("by") == OPERATOR:
        return "CLOSED ON THE OPERATOR'S AUTHORITY, not on a reviewer's verdict"
    if event.get("status") == "passed":
        return "CLOSED BY THE PIPELINE at its open — the integration pass builds nothing"
    return ""


def _kept_going(events):
    try:
        said = F.check_override(events)
    except F.BadFloor:
        return None
    question = F.asked(events)
    if question.get("asks") != F.END or said == F.END_FORM:
        return None
    after = events[events.index(question) + 1:]
    return None if [event for event in after if event.get("kind") == "close"] else said


def _end_authorised(events):
    try:
        said = F.check_override(events)
    except F.BadFloor:
        return False
    after = events[events.index(F.asked(events)) + 1:]
    return said == F.END_FORM and not [event for event in after if event.get("kind") == "close"]


def archive(project, clock, abandon=False, from_fork=False):
    if from_fork:
        raise BadCommand("`archive` is refused from a subagent — a delegated reviewer must not "
                         "be able to switch the gate off. Run it from the main thread")
    note = apply_answer(project, clock)
    events = _log(project)
    chain = C.chain_of(events)
    reached, target = C.score(events), C.target(chain)
    if tuple(reached) != tuple(target) and not abandon:
        raise BadCommand("this run stands at %s and the %s chain's target is %s — `archive "
                         "--abandon` ends it anyway and says so on the record, on the operator's "
                         "`OVERRIDE END` to `question end`"
                         % (tuple(reached), chain, tuple(target)))
    if tuple(reached) != tuple(target) and not _end_authorised(events):
        raise BadCommand((note + "\n" if note else "") +
                         "this run stands at %s, short of the %s chain's target %s, and ending it "
                         "there is the operator's decision: ask `question end \"<what is being "
                         "dropped, and why>\"`, show them the question, and run `archive --abandon` "
                         "again once they have answered `OVERRIDE END`"
                         % (tuple(reached), chain, tuple(target)))
    keep_copies(project, ending=True)
    try:
        K.end_run(project)
    except K.BadBooks as exc:
        raise BadCommand("the run was not ended: %s" % exc)
    return "\n".join(filter(None, [
        note,
        ("run ABANDONED at %s, short of the %s chain's target %s"
         % (tuple(reached), chain, tuple(target))) if abandon else "run archived at target"]))


def run(name, args, clock, project=None, from_fork=False):
    project = project or os.getcwd()
    import write_block as W
    from_fork = from_fork or W.from_fork(project, clock)
    import gate as _S8
    bound_to = _S8.session_at_the_door(project, clock)
    W.spend_marker(project)
    if name in REMOVED:
        raise BadCommand("`%s` is not a command: %s" % (name, REMOVED[name]))
    if name in INTERNAL:
        raise BadCommand("`%s` is not a command anyone types" % (name,))
    if name == "bind":
        import gate as S8
        try:
            return "run bound to session %s" % S8.bind(project, clock, session=bound_to)
        except S8.BadBind as exc:
            raise BadCommand(str(exc))
    if name not in COMMANDS:
        raise BadCommand("`%s` is not a command. They are: %s" % (name, ", ".join(COMMANDS)))
    try:
        return {"init": lambda: init(project, clock, *_init_args(args), session=bound_to),
                "close": lambda: close(project, clock, *_close_args(args),
                                       from_fork=from_fork),
                "status": lambda: status(project, clock),
                "report": lambda: report(project, clock),
                "question": lambda: question(project, clock, *args),
                "archive": lambda: archive(project, clock, abandon="--abandon" in args,
                                           from_fork=from_fork)}[name]()
    except TypeError as exc:
        raise BadCommand("`%s` was given arguments it cannot take: %s" % (name, exc))


def _whole(text, what):
    if text in (None, ""):
        return None
    try:
        return int(text)
    except (TypeError, ValueError):
        raise BadCommand("`%s` takes a whole number and was given %r" % (what, text))


def _init_args(args):
    chain = args[0] if args else None
    start = _whole(args[1], "start step") if len(args) > 1 else 0
    rest = list(args[2:])
    if not rest:
        return (chain, start or 0, None)
    return (chain, start or 0, [] if rest == [NONE_DONE] else rest)


def _close_args(args):
    status_word = args[0] if args else None
    counts = [_whole(args[i], name) if len(args) > i else None
              for i, name in ((1, "h"), (2, "m"), (3, "l"))]
    return tuple([status_word] + counts + [args[4] if len(args) > 4 else ""])


def main(argv):
    import datetime
    if not argv:
        print("usage: pipeline.py {%s}" % ",".join(COMMANDS))
        return 2
    try:
        print(run(argv[0], argv[1:],
                  lambda: datetime.datetime.now(datetime.timezone.utc)
                  .strftime("%Y-%m-%dT%H:%M:%SZ")))
    except BadCommand as exc:
        print("REFUSED: %s" % exc)
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))

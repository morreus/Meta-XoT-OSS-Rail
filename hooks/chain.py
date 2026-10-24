import events as E
import ticket as T
import vocabulary as V

STEPS = (
    ("10-context-map", "produce"),
    ("11-review-map", "review"),
    ("20-plan-impl", "produce"),
    ("21-review-plan", "review"),
    ("30-implement-plan", "produce"),
    ("31-review-impl", "review"),
    ("40-test-plan", "produce"),
    ("41-review-test-plan", "review"),
    ("50-test-impl", "produce"),
    ("51-review-tests", "review"),
)

LENGTHS = {"lite": 6, "full": 10}

MILESTONE_PAIRS = E.MILESTONE_PAIRS

TARGETS = (10, 20, 30, 40)

OPERATOR = V.check_by("OPERATOR")


class BadChain(ValueError):
    pass


def steps(chain):
    try:
        V.check_chain(chain)
    except V.BadValue as exc:
        raise BadChain("there is no step list for that chain: %s" % exc)
    return tuple(sid for sid, _kind in STEPS[:LENGTHS[chain]])


def kind_of(step):
    for sid, kind in STEPS:
        if sid == step:
            return kind
    raise BadChain("%r is not a step of any chain in this system" % (step,))


def chain_of(events):
    for event in events:
        if event.get("kind") == "claim":
            return event["chain"]
    raise BadChain("this log has no claim, so there is no chain in force and no target to reach. "
                   "The claim is written by `init` and is the first event of every run")


def target(chain):
    total = len(steps(chain))
    return tuple(total - i for i in range(total))


def milestoned(chain):
    inside = steps(chain)
    pairs = set(MILESTONE_PAIRS) | set(MILESTONE_PAIRS.values())
    return tuple(sid for sid in inside if sid in pairs)


completes = E.completes
COMPLETING = E.COMPLETING
CLEAN_WRITER = E.CLEAN_WRITER


def denominator(events):
    found = (None, None)
    for event in events:
        if E.sets_denominator(event) and event.get("ms_n") is not None:
            found = (event["ms_n"], tuple(event["ms_ids"]))
    return found


def last_milestone(events):
    _count, ids = denominator(events)
    if not ids:
        return None
    return E.last_milestone(list(ids))


def milestoned_in_force(events):
    count, _ids = denominator(events)
    if not count:
        return ()
    return milestoned(chain_of(events))


def share(count):
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise BadChain("a share is one milestone's part of %r milestones, which is not a number "
                       "this divides by. A plan declaring none has no milestoned steps at all"
                       % (count,))
    return round(1.0 / count, 4)


def summed(credited, count):
    if not count:
        return 0.0
    total = round(share(count) * credited, 2)
    if credited < count and total >= 1.00:
        return 0.99
    return total


def milestone_complete(credited, count):
    if not count:
        return True
    return credited == count and round(share(count) * credited, 2) == 1.00


def _ordered_rollback(event):
    kind = event.get("kind")
    if kind == "close":
        step = V.rollback_step(event.get("flag") or "")
        return (step, event.get("by")) if step is not None else None
    if kind == "override":
        step = V.override_rollback_step(event.get("text"))
        return (step, OPERATOR) if step is not None else None
    return None


def _performed_rollback(event):
    if event.get("kind") != "open":
        return None
    step = V.repair_target(event.get("step"))
    if step is None:
        return None
    fields = T.parse_ticket(event.get("ticket") or "")
    return step, (fields["milestone"] if fields else None)


def rollbacks(events):
    out = []
    for event in events:
        found = _ordered_rollback(event)
        if found is None:
            continue
        step, by = found
        out.append({"step": step, "at": event[E.AT], "by": by,
                    "ticket": event.get("ticket")})
    return out


def unreachable(step):
    return step not in TARGETS


def _completed_steps(events, order, milestones=()):
    position = {sid: i for i, sid in enumerate(order)}
    milestoned_here = set(milestones)
    per_step = {sid: [] for sid in milestoned_here}
    done = []
    breaches = []
    cleared = {sid: None for sid in order}
    count, ids = 0, ()
    reached_back = False
    set_pending = False
    for event in events:
        if event.get("kind") not in ("close", "open"):
            continue
        step = event.get("step")
        if E.sets_denominator(event) and event.get("ms_n") is not None:
            was_ids = ids
            count, ids = event["ms_n"], tuple(event["ms_ids"])
            if reached_back:
                seen = dict.fromkeys(m for sid in milestoned_here for m in per_step[sid])
                delivered = [ms for ms in seen
                             if all(ms in per_step[sid] for sid in milestoned_here)]
                for sid in milestoned_here:
                    per_step[sid] = [ms for ms in delivered if ms in ids]
                reached_back = False
                set_pending = True
            elif was_ids and ids != was_ids:
                for sid in milestoned_here:
                    per_step[sid] = [ms for ms in per_step[sid] if ms in ids]
        if completes(event) and step in position:
            i = position[step]
            if step in milestoned_here:
                if (event.get("ms") and event["ms"] not in per_step[step]
                        and (not ids or event["ms"] in ids)):
                    per_step[step].append(event["ms"])
                if not milestone_complete(len(per_step[step]), count):
                    continue
            earlier = [sid for sid in order[:i] if sid not in done]
            if earlier:
                breaches.append("%s completed while %s was still at zero"
                                % (step, ", ".join(earlier)))
            else:
                done.append(step)
        if set_pending:
            for sid in order:
                if (sid in milestoned_here and sid not in done
                        and milestone_complete(len(per_step[sid]), count)
                        and not [e for e in order[:position[sid]] if e not in done]):
                    done.append(sid)
            set_pending = False

        performed = _performed_rollback(event)
        if performed is not None:
            number, of_milestone = performed
            after = [sid for sid in order if int(sid.split("-")[0]) > number]
            done = [sid for sid in done if sid not in after]
            if number < min(int(sid.split("-")[0]) for sid in MILESTONE_PAIRS):
                reached_back = True
            else:
                for sid in after:
                    if sid in per_step and of_milestone in per_step[sid]:
                        per_step[sid].remove(of_milestone)
            for sid in after:
                cleared[sid] = event[E.AT]
    return done, breaches, cleared, per_step


def score(events):
    order = steps(chain_of(events))
    every = milestoned_in_force(events)
    done, _breaches, _cleared, per_step = _completed_steps(events, order, every)
    finished = set(done)
    cells = [sum(1 for sid in order[i:] if sid in finished) for i in range(len(order))]
    count, _ids = denominator(events)
    for i, sid in enumerate(order):
        if cells[i] == 0 and sid in every:
            cells[i] = _share_of(per_step, sid, count)
    return tuple(cells)


def score_disagreements(events):
    found = []
    sofar = []
    for event in events:
        sofar.append(event)
        if event.get("kind") != "close" or E.SCORE not in event:
            continue
        stored = tuple(event.get(E.SCORE) or ())
        recomputed = score(sofar)
        if stored != tuple(recomputed):
            found.append("%s: stored %s, recomputed %s"
                         % (event.get("ticket"), list(stored), list(recomputed)))
    return found


def breaches(events):
    order = steps(chain_of(events))
    _done, found, _cleared, _per = _completed_steps(
        events, order, milestoned_in_force(events))
    return found


def cleared_at(events):
    order = steps(chain_of(events))
    _done, _found, cleared, _per = _completed_steps(
        events, order, milestoned_in_force(events))
    return cleared


def _credited_milestones(events, step):
    out = []
    for event in events:
        if (event.get("kind") == "close" and event.get("step") == step
                and event.get("ms") and completes(event) and event["ms"] not in out):
            out.append(event["ms"])
    return out


def delivered(events):
    every = milestoned_in_force(events)
    per_step = {sid: _credited_milestones(events, sid) for sid in every}
    seen = dict.fromkeys(ms for sid in every for ms in per_step[sid])
    return [ms for ms in seen if all(ms in per_step[sid] for sid in every)]


def in_force(events):
    _count, ids = denominator(events)
    if not ids:
        return None
    done = delivered(events)
    return next((ms for ms in ids if ms not in done), None)


def frozen(events):
    ms = in_force(events)
    if ms is None:
        return None
    _done, _found, _cleared, per_step = _completed_steps(
        events, steps(chain_of(events)), milestoned_in_force(events))
    if ms not in per_step.get("31-review-impl", ()):
        return None
    return None if _code_loop_reopened(events, ms) else ms


_CODE_LOOP = ("31-review-impl", "92-fix:30")


def _code_loop_reopened(events, ms):
    clean = [i for i, event in enumerate(events) if event.get("kind") == "close"
             and event.get("step") == "31-review-impl" and event.get("ms") == ms and E.completes(event)]
    opens = [i for i, event in enumerate(events) if event.get("kind") == "open"]
    if not clean or not opens or opens[-1] < clean[-1]:
        return False
    last = events[opens[-1]]
    closed = any(event.get("kind") == "close" and event.get("ticket") == last.get("ticket")
                 for event in events[opens[-1] + 1:])
    return not closed and last.get("ms") == ms and last.get("step") in _CODE_LOOP


def milestone_sum(events, step):
    if step not in milestoned(chain_of(events)):
        raise BadChain("%r is not a milestoned step, so it has no per-milestone share. The "
                       "milestoned steps are the pairs intersected with the chain in force: %s"
                       % (step, ", ".join(milestoned(chain_of(events)))))
    count, _ids = denominator(events)
    _done, _found, _cleared, per_step = _completed_steps(
        events, steps(chain_of(events)), milestoned_in_force(events))
    return _share_of(per_step, step, count)


def _share_of(per_step, step, count):
    return summed(len(per_step.get(step, [])), count)


def milestone_share(events, step):
    if step not in milestoned(chain_of(events)):
        raise BadChain("%r is not a milestoned step, so it has no per-milestone share" % (step,))
    count, _ids = denominator(events)
    if not count:
        return 0.0
    return share(count)


def out_of_order(events):
    _count, ids = denominator(events)
    every = milestoned(chain_of(events))
    found = []
    for at, event in enumerate(events):
        if event.get("kind") != "open" or event.get("step") not in every:
            continue
        ms = event.get("ms")
        if ms not in ids or ids.index(ms) == 0:
            continue
        previous = ids[ids.index(ms) - 1]
        head = events[:at]
        if not all(previous in _credited_milestones(head, sid) for sid in every):
            found.append("%s started while %s had not closed" % (ms, previous))
    return found

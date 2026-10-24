import hashlib
import re

import chain as C
import events as E

HEADING_RE = re.compile(r"\A(?P<hashes>#+)[ \t]+(?P<id>\S+)")


class BadReplan(ValueError):
    pass


def _lines_with_offsets(text):
    if not isinstance(text, str):
        raise BadReplan("a plan is text, not %r"
                        % (type(text).__name__,))
    out, at = [], 0
    for line in text.splitlines(True):
        out.append((at, line))
        at += len(line)
    return out


FENCE_RE = re.compile(r"\A[ \t]*(?P<fence>```+|~~~+)")


def _headings(text):
    found, fence = [], None
    for at, line in _lines_with_offsets(text):
        opening = FENCE_RE.match(line)
        if fence is not None:
            if opening is not None and opening.group("fence")[0] == fence[0] \
                    and len(opening.group("fence")) >= len(fence):
                fence = None
            continue
        if opening is not None:
            fence = opening.group("fence")
            continue
        match = HEADING_RE.match(line)
        if match is not None:
            word = match.group("id").rstrip(":")
            if E.MS_ID_RE.match(word):
                found.append((word, at))
    return found


def _number(ms_id):
    return int(E.MS_ID_RE.match(ms_id).group("n"))


def milestones(text):
    found = [one for one, _at in _headings(text)]
    twice = sorted({one for one in found if found.count(one) > 1}, key=_number)
    if twice:
        raise BadReplan("the plan names %s more than once, so how many milestones it names cannot "
                        "be answered — one milestone, one heading, and a list with a "
                        "number in it twice is refused" % (", ".join(twice),))
    return found


def denominator(text):
    return len(milestones(text))


def section(text, ms_id):
    if not isinstance(ms_id, str) or not E.MS_ID_RE.match(ms_id):
        raise BadReplan("%r is not a milestone id" % (ms_id,))
    found = _headings(text)
    hits = [i for i, (one, _at) in enumerate(found) if one == ms_id]
    if not hits:
        raise BadReplan("the plan names no milestone %r, and an absent section is not an empty "
                        "one — an empty section hashes to a real digest and two absent milestones "
                        "would then agree with each other" % (ms_id,))
    if len(hits) > 1:
        raise BadReplan("the plan carries %d headings for %s, so which section its hash covers is "
                        "undecidable; one milestone, one heading" % (len(hits), ms_id))
    start = found[hits[0]][1]
    after = [at for _one, at in found if at > start]
    end = after[0] if after else len(text)
    return text[start:end]


def hash_bytes(text):
    if not isinstance(text, str):
        raise BadReplan("a section is text, not %r" % (type(text).__name__,))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_section(text, ms_id):
    return hash_bytes(section(text, ms_id))


def _issued(events):
    seen = set()
    for event in events:
        ids = event.get("ms_ids")
        if not isinstance(ids, (list, tuple)):
            continue
        for one in ids:
            if not isinstance(one, str) or not E.MS_ID_RE.match(one):
                raise BadReplan("this log records %r as an issued milestone number and it cannot "
                                "be read — a number that cannot be read is a number that could be "
                                "issued twice" % (one,))
            seen.add(one)
    return seen


def next_number(events):
    issued = _issued(events)
    if not issued:
        raise BadReplan("this log has issued no milestone numbers, so there is no next one — the "
                        "next number is one past the highest ever issued, and a re-plan follows a "
                        "plan whose review recorded its ids")
    return "M%d" % (max(_number(one) for one in issued) + 1)


def delivered(events):
    return C.delivered(events)


def _recorded_hashes(events):
    out = {}
    for event in events:
        if (event.get("kind") != "close" or event.get("step") not in E.MILESTONE_STEPS
                or not C.completes(event)):
            continue
        one = event.get("ms")
        if not isinstance(one, str) or not E.MS_ID_RE.match(one):
            raise BadReplan("a close of %r credits milestone %r, which cannot be read as a "
                            "milestone id — credit is stored against the number, so a number "
                            "nobody can read is credit nobody can place"
                            % (event.get("step"), one))
        out.setdefault(one, []).append(event.get("ms_hash"))
    return out


def moved(text, events, _why=None):
    recorded = _recorded_hashes(events)
    out, why = [], {} if _why is None else _why
    for one in delivered(events):
        seen = recorded.get(one) or [None]
        want = seen[0]
        if any(not isinstance(value, str) or not value.strip() for value in seen):
            raise BadReplan("the close that credited %s carries no plan-section hash, so whether "
                            "its section has moved cannot be answered — such a close is never "
                            "written, so this log has been edited" % (one,))
        if len(set(seen)) > 1:
            raise BadReplan("the closes that credited %s carry %d different plan-section hashes, "
                            "so which text it was credited for is undecidable — the section "
                            "changed between two closes that both credited it"
                            % (one, len(set(seen))))
        try:
            here = hash_section(text, one)
        except BadReplan as exc:
            why[one] = str(exc)
            out.append(one)
            continue
        if here != want:
            why[one] = ("its section is not the bytes it was credited for — a delivered milestone "
                        "comes out of a rework byte for byte as it went in")
            out.append(one)
    return out


def _recorded_order(events):
    order = []
    for event in events:
        ids = event.get("ms_ids")
        if isinstance(ids, (list, tuple)) and ids:
            order = [one for one in ids if isinstance(one, str) and E.MS_ID_RE.match(one)]
    return order


def reordered(text, events):
    was = _recorded_order(events)
    shipped = set(delivered(events))
    before = [one for one in was if one in shipped]
    now = [one for one in milestones(text) if one in shipped]
    if before == now:
        return []
    return sorted({one for i, one in enumerate(before)
                   if i >= len(now) or now[i] != one} | {one for i, one in enumerate(now)
                                                         if i >= len(before) or before[i] != one},
                  key=_number)


def check_replan(text, events):
    why = {}
    changed = moved(text, events, why)
    if changed:
        raise BadReplan("this re-plan changes delivered milestone(s) %s, and a delivered milestone "
                        "is immutable — if delivered work must change, that is a NEW milestone. %s"
                        % (", ".join(changed),
                           "; ".join("%s: %s" % (one, why[one]) for one in changed)))
    issued = _issued(events)
    if issued:
        here = set(milestones(text))
        recycled = sorted(here & issued - set(_recorded_order(events)), key=_number)
        if recycled:
            raise BadReplan(
                "this re-plan names %s, and %s already issued and dropped by an earlier plan — a "
                "number is issued once and never reused, because credit is stored against it and "
                "a recycled number attaches credit to work that never earned it"
                % (", ".join(recycled), "that number was" if len(recycled) == 1 else
                   "those numbers were"))
    out_of_place = reordered(text, events)
    if out_of_place:
        raise BadReplan("this re-plan moves delivered milestone(s) %s out of their recorded order, "
                        "and position is immutable with the text — the content, the numbering "
                        "and the order of a delivered milestone are fixed together"
                        % (", ".join(out_of_place),))
    return True


def credit(shipped, total):
    if not isinstance(shipped, int) or not isinstance(total, int) \
            or isinstance(shipped, bool) or isinstance(total, bool):
        raise BadReplan("a count of milestones is a whole number, not %r and %r"
                        % (shipped, total))
    if shipped < 0 or total < 0:
        raise BadReplan("a count of milestones is not negative: %d of %d" % (shipped, total))
    if total == 0:
        return 0
    if shipped > total:
        raise BadReplan("%d milestones are delivered and the plan declares %d — a delivered "
                        "milestone has gone missing from the plan, and %d/%d is not a share of "
                        "anything" % (shipped, total, shipped, total))
    return shipped / total

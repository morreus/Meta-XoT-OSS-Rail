import re

WRITERS = ("orch", "INDEPENDENT")
BY = ("orch", "INDEPENDENT", "OPERATOR", "pipeline")

STATUSES = ("done", "reviewed", "fixed", "void", "attested", "passed")

ENTRY_LESS = ("void", "attested", "passed")

CLOSE_BY = {"void": "OPERATOR", "attested": "OPERATOR", "passed": "pipeline"}

VOID_PRODUCERS = ("OVERRIDE OPEN", "OVERRIDE ROLLBACK")

CARRIES_COUNTS = ("reviewed", "fixed")

CHAINS = ("lite", "full")

QA = "QA"

ROLLBACK_RE = re.compile(r"\AROLLBACK (?P<step>0|[1-9][0-9]?)\Z")

OVERRIDE_ROLLBACK_RE = re.compile(r"\AOVERRIDE ROLLBACK (?P<step>0|[1-9][0-9]?)\Z")


REPAIR_STEP_RE = re.compile(r"\A93-rollback:(?P<step>0|[1-9][0-9]?)\Z")


class BadValue(ValueError):
    pass


def _one_of(kind, value, allowed):
    if not isinstance(value, str):
        raise BadValue("%s must be one of %s, not %r — refused, not coerced"
                       % (kind, ", ".join(allowed), value))
    if value not in allowed:
        raise BadValue("%s must be exactly one of %s; %r is not one of them. A near miss — "
                       "the constant's NAME, a different case, or a stray space — is a "
                       "different value and every reader compares it unequal"
                       % (kind, ", ".join(allowed), value))
    return value


def check_writer(value):
    return _one_of("writer", value, WRITERS)


def check_by(value):
    return _one_of("by", value, BY)


def check_status(value):
    return _one_of("status", value, STATUSES)


def check_chain(value):
    return _one_of("chain", value, CHAINS)


def writes_entry(status):
    return check_status(status) not in ENTRY_LESS


def check_flag(value):
    if not isinstance(value, str):
        raise BadValue("flag must be text, not %r" % (value,))
    if value in ("", QA):
        return value
    if ROLLBACK_RE.match(value):
        return value
    if value == "—":
        raise BadValue(
            "`—` is how the EVENT LOG renders an empty cell; in the process log an absent flag is "
            "the empty string, never a dash — one meaning, one spelling")
    raise BadValue(
        "flag must be empty, %r, or %r with the BARE step number — %r is not. One repair may not "
        "have two ticket strings (`93-rollback:20` and `93-rollback:20-plan-impl`)"
        % (QA, "ROLLBACK <step>", value))


def rollback_step(flag):
    check_flag(flag)
    match = ROLLBACK_RE.match(flag)
    return int(match.group("step")) if match else None


def override_rollback_step(text):
    if not isinstance(text, str):
        return None
    found = OVERRIDE_ROLLBACK_RE.match(text)
    return int(found.group("step")) if found else None

def repair_target(step):
    if not isinstance(step, str):
        return None
    found = REPAIR_STEP_RE.match(step)
    return int(found.group("step")) if found else None


def check_close(status, by, produced_by=None):
    check_status(status)
    check_by(by)
    expected = CLOSE_BY.get(status)
    if expected is not None and by != expected:
        raise BadValue("a %r close carries by %r, not %r — %s"
                       % (status, expected, by,
                          "`passed` is nobody's close" if status == "passed"
                          else "this is the operator's own close and carries their name"))
    if status == "void":
        if produced_by is not None and produced_by not in VOID_PRODUCERS:
            raise BadValue("a void close comes from %s — %r is neither"
                           % (" or ".join(VOID_PRODUCERS), produced_by))
    elif produced_by is not None:
        raise BadValue("`produced_by` narrows only a void close; a %r close does not have one, and "
                       "accepting it here would answer a question that was never asked" % (status,))
    return True


def _count(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise BadValue("%s must be a whole number, not %r — refused, not coerced"
                       % (name, value))
    if value < 0:
        raise BadValue("%s cannot be negative, got %r" % (name, value))
    return value


def check_line(status, h=None, m=None, l=None, flag="", by=None):
    check_status(status)
    if not writes_entry(status):
        raise BadValue(
            "a %r close writes NO process-log entry, so there is no line to check — demanding or "
            "accepting one would mean the pipeline writing on behalf of the party it is correcting"
            % (status,))
    if by is not None:
        check_by(by)
    check_flag(flag)

    given = {"h": h, "m": m, "l": l}
    if status in CARRIES_COUNTS:
        for name, value in given.items():
            if value is None:
                raise BadValue("a %r line carries all three counts; %s is missing" % (status, name))
            _count(name, value)
    else:
        present = sorted(n for n, v in given.items() if v is not None)
        if present:
            raise BadValue(
                "a %r line omits the counts ENTIRELY — not a dash, not zeroes — and this one "
                "carries %s. A zero and a dash both read as a verdict of nothing found, and this "
                "step never had a verdict" % (status, ", ".join(present)))

    if status == "fixed" and flag != QA:
        raise BadValue(
            "a fix closes only with the %r tick, and THERE IS NO WAIVER — the rule is 'No tick, "
            "no close', without exception, and no state offers an instruction that would waive "
            "one, not even the operator's" % QA)
    if flag == QA and status != "fixed":
        raise BadValue("the %r tick belongs to a fix; a %r line may not carry it" % (QA, status))

    if rollback_step(flag) is not None and status != "reviewed":
        raise BadValue(
            "only a review may order a rollback; a %r line carrying %r would be a produce or "
            "repair step ordering rework, and the operator's override is the only other way"
            % (status, flag))
    return True

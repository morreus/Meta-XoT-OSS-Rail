import re

NO_MILESTONE = "MX"

TICKET_RE = re.compile(
    r"\A(?P<step>[0-9]{2})(?P<ms>MX|M[0-9]+)V(?P<v>[1-9][0-9]*)\Z")


class BadTicket(ValueError):
    pass


def make_ticket(step_num, milestone, version):
    for name, value in (("step", step_num), ("version", version)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise BadTicket("%s must be a whole number, not %r" % (name, value))

    text = "%02d%sV%d" % (step_num, str(milestone or NO_MILESTONE).upper(), version)

    if not TICKET_RE.match(text):
        raise BadTicket(
            "would have cut an unreadable ticket %r — step must be 0..99, milestone must be MX "
            "or M<digits>, and version must be 1 or more" % (text,))
    return text


def parse_ticket(text):
    match = TICKET_RE.match(text) if isinstance(text, str) else None
    if not match:
        return None
    return {"step": int(match.group("step")), "milestone": match.group("ms"),
            "version": int(match.group("v"))}


def next_version(opened_tickets, step_num):
    if isinstance(step_num, bool) or not isinstance(step_num, int):
        raise BadTicket("step must be a whole number, not %r — a step that does not compare "
                        "equal silently counts nothing and hands out a live version"
                        % (step_num,))
    try:
        opened_tickets = list(opened_tickets)
    except TypeError:
        raise BadTicket("expected a list of opened tickets, not %r" % (opened_tickets,))

    highest = 0
    for text in opened_tickets:
        fields = parse_ticket(text)
        if fields is None:
            raise BadTicket(
                "the books hold an unreadable ticket %r; they must be repaired before another "
                "can be cut" % (text,))
        if fields["step"] == step_num and fields["version"] > highest:
            highest = fields["version"]
    return highest + 1

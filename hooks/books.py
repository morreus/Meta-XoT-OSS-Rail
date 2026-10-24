import errno
import hashlib
import json
import os
import re

import events as E
import ledger as D
import line as L
import ticket as T
import vocabulary as V

FLOW = ".metaxotrail"
GITIGNORE = ".gitignore"
GITIGNORE_TEXT = "*\n"

LOG = "events.jsonl"
PROCESS_LOG = "process.log"
ISSUES = "issues.jsonl"
FILES = (LOG, PROCESS_LOG, ISSUES)

WORKING_DOCUMENT = "WORKING.md"
RESULTS = "TEST_RESULTS.md"

HEADER_PREFIX = "<!-- metaxotrail-run: "
HEADER_SUFFIX = " -->"

RESULTS_STEP = 50

INIT_CASES = (
    "fresh run, no document — created, empty but for the header",
    "adopted run, document with no run header — stamped into it, nothing else touched",
    "adopted run, document with a previous run's header — the header REPLACED, not appended",
    "adopted run, document missing — refused",
    "fresh run, a results file exists — renamed aside",
    "adopted run at or past step 50, results file exists — kept, its header stamped or replaced",
    "adopted run at or past step 50, results file missing — refused",
    "adopted run before step 50, results file exists — renamed aside, as on a fresh run",
    "fresh run, document exists — renamed aside, then created as in case 1",
)


class BadBooks(ValueError):
    pass


def address(project_path):
    if not isinstance(project_path, str) or not project_path.strip():
        raise BadBooks("the project path must be a path, not %r" % (project_path,))
    return os.path.join(_spelled(project_path), FLOW)


def _spelled(project_path):
    return os.path.realpath(project_path)


def header(run_hash):
    if not isinstance(run_hash, str) or not run_hash.strip():
        raise BadBooks("a run hash is text, not %r" % (run_hash,))
    if len(run_hash.splitlines()) != 1 or HEADER_SUFFIX.strip() in run_hash:
        raise BadBooks("a run hash is one line and does not carry the header's own delimiters; "
                       "%r would write two headers into one document" % (run_hash,))
    return HEADER_PREFIX + run_hash + HEADER_SUFFIX


def _read_text(path, what):
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except IsADirectoryError:
        raise BadBooks("%s is a DIRECTORY at %s, and the books cannot read it" % (what, path))
    except OSError as exc:
        if exc.errno == errno.EISDIR:
            raise BadBooks("%s is a DIRECTORY at %s, and the books cannot read it" % (what, path))
        if exc.errno == errno.ENOENT:
            raise BadBooks("%s is not there — no file at %s. The books are made by `init`, and an "
                           "absent one is never an empty run" % (what, path))
        raise BadBooks("%s at %s could not be read: %s" % (what, path, exc))
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BadBooks("%s at %s is not UTF-8 (%s) — a record nobody can read is not a record of "
                       "nothing" % (what, path, exc))


def read_log(project_path):
    return _not_yours(project_path)


def _not_yours(project_path):
    events = _read_events(project_path)
    if _whose(events, project_path) == COLLISION:
        raise BadBooks("these books were claimed by %r, which still exists — two checkouts "
                       "pointing at one set of books share a run, count each other's tickets and "
                       "wedge each other. Ownership is declared, and this is not yours"
                       % events[0]["project"])
    return events


def _read_events(project_path):
    path = os.path.join(address(project_path), LOG)
    text = _read_text(path, "the event log")
    events = []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        events.append(_read_event(raw, number, path))
    if not events:
        raise BadBooks("the event log at %s holds no events. A run's log always opens with its "
                       "claim, so an empty one has been truncated — and an emptied log read as a "
                       "brand-new project would lift every lock the run holds" % path)
    return events


def _read_event(raw, number, path):
    try:
        record = json.loads(raw)
    except ValueError as exc:
        raise BadBooks("line %d of the event log is not readable JSON (%s): %r"
                       % (number, exc, raw[:60]))
    if not isinstance(record, dict):
        raise BadBooks("line %d of the event log is not an event object: %r" % (number, raw[:60]))
    try:
        E.check_event(record)
    except E.BadEvent as exc:
        raise BadBooks("line %d of the event log does not hold together: %s" % (number, exc))
    return record


def append_event(project_path, event):
    events = read_log(project_path)
    try:
        E.append(events, event)
    except E.BadEvent as exc:
        raise BadBooks("that event may not be appended: %s" % exc)
    path = os.path.join(address(project_path), LOG)
    event = dict(event, **{D.PREV: D.head(events)})
    line = json.dumps(event, sort_keys=True)
    _read_event(line, len(events) + 1, path)
    with open(path, "a") as handle:
        handle.write(line + "\n")
    _anchor(events[0]["run_hash"], D.link(D.head(events), event))
    return event


ANCHORS = os.path.join(os.path.expanduser("~"), ".claude", "metaxotrail-anchor")


def anchor_path(run_hash):
    return os.path.join(ANCHORS, D.link(D.FIRST, {"run": run_hash})[:16] + ".head")


def _anchor(run_hash, value):
    try:
        os.makedirs(ANCHORS, exist_ok=True)
        with open(anchor_path(run_hash), "w") as handle:
            handle.write(value)
    except OSError:
        return None
    return value


def anchored(run_hash):
    try:
        with open(anchor_path(run_hash)) as handle:
            return handle.read().strip() or None
    except OSError:
        return None


def damage(project_path):
    events = read_log(project_path)
    return D.verify(events) or D.against_anchor(events, anchored(events[0]["run_hash"]))


def cut_ticket(project_path, step_num, milestone):
    with _locked(project_path):
        events = read_log(project_path)
        version = E.next_version(events, step_num)
        return T.make_ticket(step_num, milestone, version)


class _locked(object):

    def __init__(self, project_path):
        self.path = os.path.join(address(project_path), ".lock")

    def __enter__(self):
        try:
            self.handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileNotFoundError:
            raise BadBooks("there are no books at %s to lock. They are made by `init`, and an "
                           "absent one is never an empty run" % os.path.dirname(self.path))
        except FileExistsError:
            raise BadBooks("the books at %s are locked by another pipeline command still running. "
                           "A lock left behind by a killed process (`.lock` in that folder) is removed by "
                           "the operator, by hand, deliberately: "
                           "the alternative is a "
                           "timeout that guesses" % os.path.dirname(self.path))
        return self

    def __exit__(self, *exc):
        os.close(self.handle)
        os.remove(self.path)
        return False


SAME, MOVED, COLLISION = "same", "moved", "collision"


def _whose(events, project_path):
    claim = events[0]
    if claim.get("kind") != "claim":
        raise BadBooks("these books do not open with a claim, so they say nothing about whose "
                       "they are — ownership is declared, never inferred")
    recorded = claim["project"]
    if recorded == _spelled(project_path):
        return SAME
    return COLLISION if _holds_this_run(recorded, claim.get("run_hash")) else MOVED


def _holds_this_run(path, run_hash):
    head = os.path.join(path, FLOW, LOG)
    try:
        with open(head, "rb") as handle:
            for raw in handle:
                line = raw.decode("utf-8")
                if not line.strip():
                    continue
                return json.loads(line).get("run_hash") == run_hash
        return False
    except (OSError, ValueError, AttributeError):
        return False


def ownership(project_path):
    return _whose(_read_events(project_path), project_path)


def read_process_log(project_path):
    _not_yours(project_path)
    return _read_text(os.path.join(address(project_path), PROCESS_LOG),
                      "the process log")


def append_line(project_path, text):
    _not_yours(project_path)
    if not isinstance(text, str) or len(text.splitlines()) != 1:
        raise BadBooks("a process-log line is one line of text as the READER counts lines, and %r "
                       "is %d" % (text, len(text.splitlines()) if isinstance(text, str) else -1))
    try:
        L.parse_line(text)
    except L.BadLine as exc:
        raise BadBooks("that is not a process-log line, so the books will not write it: %s" % exc)
    with open(os.path.join(address(project_path), PROCESS_LOG), "a") as handle:
        handle.write(text.rstrip("\n") + "\n")
    return text


def read_issues(project_path):
    _not_yours(project_path)
    path = os.path.join(address(project_path), ISSUES)
    text = _read_text(path, "the issues file")
    entries = []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except ValueError as exc:
            raise BadBooks("line %d of the issues file is not readable JSON (%s)" % (number, exc))
        _check_issue(entry, "line %d of the issues file" % number)
        entries.append(entry)
    return entries


def _check_issue(entry, where):
    if not isinstance(entry, dict):
        raise BadBooks("%s is not an entry object" % where)
    if T.parse_ticket(entry.get("ticket")) is None:
        raise BadBooks("%s carries %r, which is not a readable ticket — the ticket is what lets "
                       "the detector join the finding to the line"
                       % (where, entry.get("ticket")))
    if entry.get("severity") not in SEVERITIES:
        raise BadBooks("%s carries severity %r; an entry carries one of %s, and a finding nobody "
                       "classified reads as not blocking"
                       % (where, entry.get("severity"), ", ".join(SEVERITIES)))
    for name in ("finding", "fix"):
        value = entry.get(name)
        if not isinstance(value, str) or not value.strip():
            raise BadBooks("%s carries its %s as %r; an entry carries it in words"
                           % (where, name, value))
    return True


def append_issue(project_path, ticket, severity, finding, fix):
    _not_yours(project_path)
    entry = {"ticket": ticket, "severity": severity, "finding": finding, "fix": fix}
    _check_issue(entry, "an issues entry")
    with open(os.path.join(address(project_path), ISSUES), "a") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


SEVERITIES = ("HIGH", "MEDIUM", "LOW")


def running(project_path):
    path = os.path.join(address(project_path), LOG)
    if os.path.exists(path) and not os.path.isfile(path):
        raise BadBooks("the event log at %s is not a file, so whether a run is live cannot be "
                       "answered — and `no run here` is not `the books are broken`" % path)
    return os.path.isfile(path)


def rotated(project_path):
    books = address(project_path)
    if not os.path.isdir(books):
        return []
    names = [name for name in os.listdir(books)
             if name.startswith(LOG + ".") and name[len(LOG) + 1:].isdigit()]
    return sorted(names, key=lambda name: int(name[len(LOG) + 1:]))


def end_run(project_path):
    books = address(project_path)
    path = os.path.join(books, LOG)
    if not os.path.isfile(path):
        raise BadBooks("there is no live run to end at %s — its log is already rotated aside, and "
                       "ending twice would rotate an absent file into a second name" % books)
    _not_yours(project_path)
    os.rename(path, _free(path, "%s.%d"))
    return True


FINGERPRINT = "copy"
COPY_SUFFIX = ".md"
_COPY_STEMS = tuple(os.path.splitext(name)[0] for name in (WORKING_DOCUMENT, RESULTS))


def copy_name(document, ticket):
    stem = os.path.splitext(os.path.basename(document))[0]
    if stem not in _COPY_STEMS or T.parse_ticket(ticket) is None:
        raise BadBooks("a copy is of the working document or the results file, named by a ticket; "
                       "%r at %r is neither" % (document, ticket))
    return "%s.%s%s" % (stem, ticket, COPY_SUFFIX)


def _is_copy(name):
    for stem in _COPY_STEMS:
        prefix = stem + "."
        if name.startswith(prefix) and name.endswith(COPY_SUFFIX):
            if T.parse_ticket(name[len(prefix):-len(COPY_SUFFIX)]) is not None:
                return True
    return False


def _a_copy(name):
    if not _is_copy(name):
        raise BadBooks("%r is not a copy's name, and the copies' door touches nothing else in "
                       "the books" % (name,))
    return name


def copy_path(project_path, name):
    return os.path.join(address(project_path), _a_copy(name))


def copies(project_path):
    books = address(project_path)
    names = os.listdir(books) if os.path.isdir(books) else []
    return sorted(name for name in names if _is_copy(name))


def fingerprint(data):
    return hashlib.sha256(data).hexdigest()


def write_copy(project_path, name, data):
    path = copy_path(project_path, name)
    _not_yours(project_path)
    if os.path.lexists(path):
        raise BadBooks("a copy is written once and never modified, and %s is already there" % path)
    try:
        with open(path, "xb") as handle:
            handle.write(data)
    except BaseException:
        if os.path.isfile(path):
            os.remove(path)
        raise
    return True


def remove_copy(project_path, name):
    path = copy_path(project_path, name)
    _not_yours(project_path)
    try:
        os.remove(path)
    except FileNotFoundError:
        return False
    return True


def matching_copy(project_path, name, expected):
    path = copy_path(project_path, name)
    _not_yours(project_path)
    try:
        with open(path, "rb") as handle:
            return fingerprint(handle.read()) == expected
    except OSError:
        return False


def _free(path, shape):
    index = 1
    while os.path.exists(shape % (path, index)):
        index += 1
    return shape % (path, index)


def _aside(path, into=None, name=None):
    target = os.path.join(into, name or os.path.basename(path)) if into else path
    os.rename(path, _free(target, "%s.aside-%d"))
    return True


_SET_ASIDE = re.compile(r"\A(%s|%s)\.aside-(\d+)\Z" % (re.escape(WORKING_DOCUMENT), re.escape(RESULTS)))


def set_aside_in_root(project_path):
    found = [(match.group(1), int(match.group(2)), name)
             for name in os.listdir(project_path)
             if os.path.isfile(os.path.join(project_path, name))
             for match in [_SET_ASIDE.match(name)] if match]
    return [name for _base, _number, name in sorted(found)]


def _is_header(line):
    return line.startswith(HEADER_PREFIX) and line.rstrip("\r").endswith(HEADER_SUFFIX)


def _stamp(path, run_hash, what):
    text = _read_text(path, what)
    lines = text.split("\n")
    while lines and _is_header(lines[0]):
        lines.pop(0)
    kept = lines
    beside = path + ".stamping"
    try:
        with open(beside, "w", newline="") as handle:
            handle.write(header(run_hash) + "\n" + "\n".join(kept))
        os.replace(beside, path)
    except BaseException:
        if os.path.exists(beside):
            os.remove(beside)
        raise
    return True


def init(project_path, run_hash, clock, chain, base_commit, adopted=False, start_step=0, keep=()):
    if not isinstance(adopted, bool):
        raise BadBooks("`adopted` says whether this run takes over work already done, and it is "
                       "true or false; %r is neither" % (adopted,))
    if not isinstance(start_step, int) or isinstance(start_step, bool):
        raise BadBooks("`start_step` is the step number this run begins at; %r is not one"
                       % (start_step,))

    books = address(project_path)
    if os.path.isfile(os.path.join(books, LOG)):
        raise BadBooks("a run is already live at %s. Starting a second over it would let the new "
                       "run inherit the old one's log, which is what ending a run exists to "
                       "prevent" % books)
    document = os.path.join(project_path, WORKING_DOCUMENT)
    results = os.path.join(project_path, RESULTS)

    if not os.path.isdir(project_path):
        raise BadBooks("there is no project at %s to start a run in. The books live INSIDE the "
                       "project, at `.metaxotrail`, so there is nowhere to make them" 
                       % _spelled(project_path))
    if os.path.exists(books) and not os.path.isdir(books):
        raise BadBooks("%s is not a directory, so the books cannot be made in it" % books)
    for path, what in ((document, "the working document"), (results, "the test-results file"),
                       (os.path.join(books, LOG), "the event log"),
                       (os.path.join(books, PROCESS_LOG), "the process log"),
                       (os.path.join(books, ISSUES), "the issues file")):
        if os.path.exists(path) and not os.path.isfile(path):
            raise BadBooks("%s at %s is not a file — the books cannot read it or write it, and "
                           "`there is no %s` would be false" % (what, path, what))
    if adopted and not os.path.isfile(document):
        raise BadBooks("this run adopts work, and there is no working document at %s. Adoption "
                       "stands on artifacts that are there" % document)
    if adopted and start_step >= RESULTS_STEP and not os.path.isfile(results):
        raise BadBooks("this run adopts work at or past step %d, and there is no test-results "
                       "file at %s — it is the artifact step 51 reviews"
                       % (RESULTS_STEP, results))

    if adopted:
        _read_text(document, "the working document")
        if start_step >= RESULTS_STEP and os.path.isfile(results):
            _read_text(results, "the test-results file")

    run_header = header(run_hash)
    try:
        claim = E.make_event("claim", clock, project=_spelled(project_path),
                             run_hash=run_hash, chain=chain, base_commit=base_commit)
    except E.BadEvent as exc:
        raise BadBooks("the run's claim cannot be built, so there is nothing to open the books "
                       "with: %s" % exc)

    os.makedirs(books, exist_ok=True)
    with open(os.path.join(books, GITIGNORE), "w") as handle:
        handle.write(GITIGNORE_TEXT)
    for name in FILES:
        existing = os.path.join(books, name)
        if os.path.isfile(existing) and os.path.getsize(existing):
            _aside(existing)
        open(existing, "a").close()
    for name in set_aside_in_root(project_path):
        if name not in frozenset(keep):
            _aside(os.path.join(project_path, name), books, _SET_ASIDE.match(name).group(1))

    claim = dict(claim, **{D.PREV: D.FIRST})
    with open(os.path.join(books, LOG), "w") as handle:
        handle.write(json.dumps(claim, sort_keys=True) + "\n")
    _anchor(run_hash, D.head([claim]))

    if adopted:
        _stamp(document, run_hash, "the working document")
        if os.path.isfile(results):
            if start_step >= RESULTS_STEP:
                _stamp(results, run_hash, "the test-results file")
            else:
                _aside(results, books)
    else:
        if os.path.isfile(document):
            _aside(document, books)
        with open(document, "w") as handle:
            handle.write(run_header + "\n")
        if os.path.isfile(results):
            _aside(results, books)
    return True

import sys

import events as E
import vocabulary as V


class BadClose(ValueError):
    pass


CLOSE_BY = V.CLOSE_BY

REVIEW = "review"


def _is_review(step):
    import chain as C
    try:
        return C.kind_of(step) == REVIEW
    except C.BadChain:
        return False


def writer_at_open(step, ms, events):
    if not _is_review(step):
        return "orch"

    rounds = loop_of(step, ms, events)
    if not rounds:
        return "INDEPENDENT"

    last = rounds[-1]
    if last.get("writer") == "orch" and last.get("h") == 0 and last.get("m") == 0:
        return "INDEPENDENT"
    return "orch"


def _loop_start(events):
    start = -1
    for index, event in enumerate(events):
        if event.get("kind") == "close" and str(event.get("flag") or "").startswith("ROLLBACK"):
            start = index
    return start


def loop_of(step, ms, events):
    closes = [event for event in events[_loop_start(events) + 1:]
              if event.get("kind") == "close" and event.get("step") == step
              and event.get("ms") == ms and event.get("status") != "void"]
    ended = [index for index, event in enumerate(closes) if E.completes(event)]
    return closes[ended[-1] + 1:] if ended else closes


def writer_of(ticket, events):
    for event in events:
        if event.get("kind") == "open" and event.get("ticket") == ticket:
            return event.get("writer")
    raise BadClose("no open for %r is in this log, so the ticket has no writer — and a writer "
                   "guessed at is a write block guarding nothing" % (ticket,))


SECTIONS = {
    "10-context-map": ("What this is", "How it works today", "What is unclear"),
    "20-plan-impl": ("Milestones", "Acceptance rules", "What could go wrong"),
    "40-test-plan": ("What is tested", "What is not tested", "How to run it"),
    "50-test-impl": ("Results", "What failed", "What was not run"),
}


def missing_sections(step, path):
    wanted = SECTIONS.get(step, ())
    if not wanted:
        return []
    headings = set()
    for raw in _text_of(path).splitlines():
        line = raw.strip()
        if line.startswith("#"):
            headings.add(line.lstrip("#").strip())
    return [head for head in wanted if head not in headings]


def run_hash_ok(run_hash, path):
    import books as K
    return K.header(run_hash) in _text_of(path)


def _text_of(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise BadClose("this step's artifact cannot be read at %s (%s), and a close judged on "
                       "an artifact nobody can open is a close judged on nothing"
                       % (path, exc.strerror or exc))
    except UnicodeDecodeError:
        raise BadClose("this step's artifact at %s is not text this system can read" % (path,))


def plan_hash(path, ms):
    import replan as R
    try:
        return R.hash_section(_text_of(path), ms)
    except R.BadReplan as exc:
        raise BadClose("this close earns milestone credit and the plan cannot be hashed for "
                       "%r: %s" % (ms, exc))


def score_at_close(events, close):
    import chain as C
    return C.score(list(events) + [close])


def stamp_score(events, close):
    return dict(close, **{E.SCORE: list(score_at_close(events, close))})


def reads_stored_score():
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(sys.modules[__name__]))
    return [node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and getattr(node.func, "attr", None) == "get"
            and node.args and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "score"]


def artifact_is_fresh(path, step, events):
    import chain as C
    when = C.cleared_at(events).get(step)
    if when is None:
        return True
    return _mtime_of(path) > _moment(when)


def _mtime_of(path):
    import os as _os
    try:
        return _os.path.getmtime(path)
    except OSError as exc:
        raise BadClose("this step's artifact cannot be dated at %s (%s)" % (path, exc))


def _moment(stamp):
    import datetime
    return datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc).timestamp()


def _not_code():
    import books as K
    return (K.WORKING_DOCUMENT, K.RESULTS)


NOT_CODE = _not_code()


def _git(root, *args):
    import subprocess
    try:
        done = subprocess.run(("git", "-C", root) + args,
                              capture_output=True, text=True, errors="replace", timeout=120)
    except OSError as exc:
        raise BadClose("git could not be run (%s), so this milestone cannot be fixed in the "
                       "repository — and crediting it as committed would be a false record"
                       % (exc,))
    if done.returncode != 0:
        raise BadClose("`git %s` failed in %s: %s"
                       % (" ".join(args), root, (done.stderr or "").strip()[:200]))
    return done.stdout.strip()


def head_of(root):
    return _git(root, "rev-parse", "HEAD")


def commit_milestone(root, ms):
    held = secrets_held(root, "delivery")
    if held:
        raise BadClose("the delivery commit of %s is held: %s" % (ms, held))
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=metaxotrail@localhost", "-c", "user.name=metaxotrail",
         "commit", "-q", "--allow-empty", "-m", "%s delivered" % ms)
    return head_of(root)


def changed_since(root, base):
    names = _git(root, "status", "--porcelain", "--untracked-files=all")
    changed = {line[3:].strip().strip('"') for line in names.splitlines() if line.strip()}
    committed = _git(root, "diff", "--name-only", base, "HEAD")
    changed |= {line.strip() for line in committed.splitlines() if line.strip()}
    return sorted(name for name in changed if name not in NOT_CODE) != []


def tracked(root, names):
    return tuple(line for line in _git(root, "ls-files", "--", *names).splitlines() if line)


SECRET_NAMES = (".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.p8", "*.jks",
                "*.keystore", "key.properties", "id_rsa*", "id_ed25519*", "credentials*.json",
                "*service-account*.json")
NOT_SECRET = (".env.example", ".env.sample")
SECRET_STEPS = tuple(E.MILESTONE_PAIRS)


def secret_like(root):
    import os
    listed = _git(root, "ls-files", "-z", "--others", "--exclude-standard", "--full-name",
                  "--", ":/").split("\0")
    return sorted(path for path in listed if path and _looks_secret(os.path.basename(path)))


_HOW = {
    "produce": "Ask the operator with `question ask`: they add {0} to `.gitignore`, or commit {0} themselves",
    "delivery": "The operator adds {0} to `.gitignore`, or commits {0} themselves, and the close is made "
                "again — a review cannot ask a question, so a reviewer reports this in its reply",
    "init": "The operator adds {0} to `.gitignore`, or commits {0} themselves; then `init` is run again",
}


def _secrets_said(names, door="produce"):
    one = len(names or ()) == 1
    pronoun = "it" if one else "them"
    said = ("%s %s, and git neither tracks nor ignores %s (%s from the repository's top). %s"
            % (", ".join(names or ()), "looks like a secret" if one else "look like secrets",
               pronoun, "the path is" if one else "the paths are", _HOW[door].format(pronoun)))
    return said if names else "git was not asked which new files look like secrets"


def secrets_held(root, door):
    found = secret_like(root)
    return _secrets_said(found, door) if found else None


TEST_FOLDERS = ("test", "tests", "__tests__", "integration_test", "Tests", "spec")
TEST_NAMES = ("test_*", "*_test.*", "*.test.*", "*.spec.*", "*Test.cs", "*Tests.cs",
              "conftest.py", "pytest.ini", "jest.config.*", "vitest.config.*", "karma.conf.*")
WRITABLE_SUFFIXES = (".md", ".markdown", ".log")
WRITABLE_FOLDERS = (".metaxotrail", ".claude", ".vscode", "docs", "Docs", ".evidence", "evidence")
TEST_DATA = ("fixture", "fixtures", "mock", "mocks", "testdata")
FROZEN_STEPS = ("40-test-plan", "50-test-impl")
CODE_REVIEW = "31-review-impl"


def _looks_secret(name):
    import fnmatch
    low = name.lower()
    return low not in NOT_SECRET and any(fnmatch.fnmatchcase(low, shape) for shape in SECRET_NAMES)


def is_production(rel):
    import fnmatch
    parts = [p for p in rel.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts:
        return False
    name = parts[-1]
    if (name in NOT_CODE or name == ".gitignore" or name.lower().endswith(WRITABLE_SUFFIXES)
            or _looks_secret(name) or any(fnmatch.fnmatchcase(name, shape) for shape in TEST_NAMES)):
        return False
    return not any(f in TEST_FOLDERS or f in WRITABLE_FOLDERS
                   or any(f == w or f.endswith("_" + w) or f.endswith("-" + w) for w in TEST_DATA)
                   for f in parts)


def code_digest(root):
    import hashlib
    import os
    listed = _git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
    whole = hashlib.sha256()
    for rel in sorted(set(path for path in listed if path and is_production(path))):
        path = os.path.join(root, rel)
        whole.update(rel.encode("utf-8", "replace") + b"\0")
        if os.path.islink(path):
            whole.update(b"link " + os.readlink(path).encode("utf-8", "replace"))
        else:
            one = hashlib.sha256()
            try:
                with open(path, "rb") as handle:
                    for chunk in iter(lambda: handle.read(1 << 20), b""):
                        one.update(chunk)
                whole.update(one.hexdigest().encode())
            except OSError:
                whole.update(b"unreadable")
        whole.update(b"\n")
    return whole.hexdigest()


def _stamped_digest(events, ms):
    found = None
    for event in events:
        if (event.get("kind") == "close" and event.get("step") == CODE_REVIEW
                and event.get("ms") == ms and E.completes(event)):
            found = event.get(E.CODE_DIGEST)
    return found


def _frozen_said(ms):
    return ("the project's production code changed after %s's code review closed clean. If that is a "
            "new file a program wrote — a cache, a build output — ask the operator whether to add it "
            "to `.gitignore`, then close again; "
            "if it is the code, ask the operator with `question input`: their `OVERRIDE ROLLBACK 30` sends %s "
            "back to its code step" % (ms, ms))


def pushes():
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(_git))
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and node.value == "push"]


IMPLEMENT = "30-implement-plan"


def pattern_of(step, ms, events):
    if _auto_closes(step, ms, events):
        return "D"
    if _is_review(step):
        return "B"
    if not _in_chain(step):
        return "C"
    return "A"


def _in_chain(step):
    import chain as C
    try:
        C.kind_of(step)
    except C.BadChain:
        return False
    return True


def _auto_closes(step, ms, events):
    if step != IMPLEMENT or ms is None:
        return False
    import chain as C
    _count, ids = C.denominator(events)
    if len([one for one in ids or () if _number(one) != 0]) < 2:
        return False
    return _number(ms) == max(_number(i) for i in ids)


TICK = V.QA

NEW_FACTS = "New facts (%s):"
OPEN_QUESTIONS = "Open questions (%s): none"
CONDITION_WORDS = {"fingerprint": "the working tree changed since the last milestone's commit",
                   "row": "a readable process-log line", "count": "the h/m/l counts on that line"}
LINES = {"new facts": NEW_FACTS, "open questions": OPEN_QUESTIONS}
HOW = {"new facts": "on a line of its own, the table below it or `none` after it",
       "open questions": "on a line of its own, nothing after `none`"}
ASKS_BEFORE_CLOSING = ("10-context-map", "20-plan-impl")


def worked_on(step):
    import chain as C
    number = step.split(":", 1)[1] if isinstance(step, str) and ":" in step else None
    for name, _kind in C.STEPS:
        if name == step or name.split("-")[0] == number:
            return name
    return None


def _lines_owed(step):
    target = worked_on(step)
    if V.repair_target(step) is not None or step in ASKS_BEFORE_CLOSING:
        return ("open questions",) if target in ASKS_BEFORE_CLOSING else ()
    if target != step and target in SECTIONS:
        return ("new facts",)
    return ()


def holds_line(path, *forms):
    if not _exists(path):
        return False
    lines = [raw.strip() for raw in _text_of(path).splitlines()]
    return any(form in lines for form in forms)


def close_conditions(step, ms, events):
    pattern = pattern_of(step, ms, events)
    if pattern == "D":
        return ()
    if pattern == "B":
        return ("count",)
    if pattern == "C":
        return ("row", "discharged", "tick") + _lines_owed(step)
    if step == IMPLEMENT:
        return ("fingerprint", "row") + _secrets_owed(step, events)
    return (("artifact", "sections", "run hash", "row") + _lines_owed(step) + _secrets_owed(step, events)
            + _code_owed(step, ms, events))


def _secrets_owed(step, events):
    import chain as C
    return ("secrets",) if step in SECRET_STEPS and step in C.milestoned_in_force(events) else ()


def _code_owed(step, ms, events):
    return ("frozen code",) if step in FROZEN_STEPS and _stamped_digest(events, ms) is not None else ()


def needs_a_line(step, ms, events):
    return pattern_of(step, ms, events) != "D"


def _number(ms_id):
    got = E.MS_ID_RE.match(str(ms_id))
    if got is None:
        raise BadClose("%r is not a milestone id, so it has no number to compare" % (ms_id,))
    return int(got.group("n"))


def unmet(step, ms, events, artifact=None, run_hash=None, row=None, count=None,
          changed=None, discharged=None, tick=None, document=None, ticket=None, secrets=None,
          code=None):
    met = ANSWERS(step, ms, events, artifact, run_hash, row, count, changed, discharged, tick,
                  document, ticket, secrets, code)
    wanted = close_conditions(step, ms, events)
    if "artifact" in wanted and not _exists(artifact):
        return ["artifact"]
    return [c for c in wanted if c != "artifact" and not met[c]()]


def ANSWERS(step, ms, events, artifact, run_hash, row, count, changed, discharged, tick,
            document=None, ticket=None, secrets=None, code=None):
    return {
        "sections": lambda: not missing_sections(step, artifact),
        "run hash": lambda: (run_hash_ok(run_hash, artifact)
                             and artifact_is_fresh(artifact, step, events)),
        "fingerprint": lambda: bool(changed),
        "count": lambda: bool(count),
        "row": lambda: bool(row),
        "discharged": lambda: bool(discharged),
        "tick": lambda: bool(tick),
        "new facts": lambda: holds_line(document, NEW_FACTS % ticket, NEW_FACTS % ticket + " none"),
        "open questions": lambda: holds_line(document, OPEN_QUESTIONS % ticket),
        "secrets": lambda: secrets is not None and not secrets,
        "frozen code": lambda: code is not None and code == _stamped_digest(events, ms),
    }


def _exists(path):
    import os
    return isinstance(path, str) and os.path.isfile(path)


def check_close(events, close, **conditions):
    writer = writer_of(close.get("ticket"), events)
    exempt = close.get("by") in (CLOSE_BY.get("void"), CLOSE_BY.get("passed"))
    if close.get("writer") != writer and not exempt:
        raise BadClose(
            "%r was opened to %r and this close names %r — a close belongs to the ticket's "
            "writer, and the two exemptions are the operator's override and the pipeline's own "
            "`passed`" % (close.get("ticket"), writer, close.get("writer")))

    if not V.writes_entry(close.get("status")):
        return close

    conditions = dict(conditions, ticket=close.get("ticket"))
    short = unmet(close.get("step"), close.get("ms"), events, **conditions)
    if short:
        import os
        raise BadClose(
            "this close of %r is judged by %s, and %s %s not met%s"
            % (close.get("step"),
               ", ".join(CONDITION_WORDS.get(c, c)
                         for c in close_conditions(close.get("step"), close.get("ms"), events)),
               ", ".join(CONDITION_WORDS.get(c, c) for c in short), "is" if len(short) == 1 else "are",
               "".join(" — write the line `%s` in %s, %s"
                       % (LINES[c] % close.get("ticket"),
                          os.path.basename(str(conditions.get("document"))), HOW[c])
                       for c in short if c in LINES)
               + (" — " + _secrets_said(conditions.get("secrets")) if "secrets" in short else "")
               + (" — " + _frozen_said(close.get("ms")) if "frozen code" in short else "")))
    return close


def earns_milestone_credit(events, close):
    import chain as C
    return [ms for ms in C.delivered(list(events) + [close]) if ms not in C.delivered(events)]


def stamp_plan_hash(plan, close):
    ms = close.get("ms")
    if not (close.get("step") in E.MILESTONE_STEPS and ms is not None and E.completes(close)):
        return close
    return dict(close, **{E.MS_HASH: plan_hash(plan, ms)})


def stamp_milestone(root, plan, events, close):
    stamped = stamp_plan_hash(plan, close)
    ms = close.get("ms")
    delivers = earns_milestone_credit(events, close)
    if close.get("step") == CODE_REVIEW and ms is not None and E.completes(close) and not delivers:
        stamped = dict(stamped, **{E.CODE_DIGEST: code_digest(root)})
    if not delivers:
        return stamped
    reviewed = _stamped_digest(events, ms)
    if reviewed is not None and code_digest(root) != reviewed:
        raise BadClose("the delivery of %s is held: the project's production code changed after its "
                       "code review closed clean. If that is a new file a program wrote — a cache, a "
                       "build output — the operator adds it to `.gitignore` and the close is made "
                       "again; a review cannot ask a question, so a reviewer reports this in its "
                       "reply. If it is the code, the reviewer closes with a finding and `ROLLBACK "
                       "30`, which sends %s back to its code step" % (ms, ms))
    return dict(stamped, **{E.COMMIT: commit_milestone(root, ms)})


def by_for(status, writer):
    return CLOSE_BY.get(status, writer)


def writes_supplied_by():
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(by_for))
    return [node.arg for node in ast.walk(tree)
            if isinstance(node, ast.arg) and node.arg == "by"]


def line_at_open(ticket, step):
    import json
    return json.dumps({"ticket": ticket, "status": _status_at_open(step), "flag": ""},
                      sort_keys=True)


def _status_at_open(step):
    if not _in_chain(step):
        return "fixed"
    return "reviewed" if _is_review(step) else "done"

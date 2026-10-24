import datetime
import json
import os
import re
import shlex
import sys

import books as K
import scope as S
import chain as C
import events as E
import floor as F
import open_close as O
import pipeline as G
import position as P

ALLOW, DENY = "allow", "deny"


SUB, MAIN = "sub", "main"
MARKER = "caller.json"

CALLER_MAX_AGE = 120

WRITE_TOOLS = ("Write", "Edit", "NotebookEdit")

PATH_FIELDS = ("file_path", "notebook_path")

INSTRUCTIONS = ("OVERRIDE CLOSE", "OVERRIDE OPEN", "OVERRIDE ROLLBACK",
                "OVERRIDE END",
                "ANSWER")

BARE = ("OVERRIDE END",)
KEYED = re.compile(r"\s*(?:[a-z]|[1-4][a-z](?:[\s,]+[1-4][a-z])*)\s*", re.IGNORECASE)
MEASURED_MODES = ("auto", "default", "acceptEdits")
SHEET_HEADER = re.compile(r"(q\d+)(?:·([1-4]))?")
RECOMMENDED = " (Recommended)"

LEGIT = G.COMMANDS

CARVED_OUT = (K.ISSUES, K.PROCESS_LOG)

WRITE_VERBS = ("cp", "mv", "rm", "tee", "dd", "truncate", "ln", "install",
               "chmod", "chown", "chgrp", "chflags")
IN_PLACE_VERBS = ("sed", "perl")
_PREFIX_WORDS = ("sudo", "command", "builtin", "exec", "nohup", "env", "time")

_PUNCTUATION = "();<>|&`"
_SEPARATORS = (";", ";;", "&", "&&", "|", "||", "|&", "(", ")", "`")


class Unreadable(ValueError):
    pass


def _events(project):
    if not K.running(project):
        return []
    return K.read_log(project)


def open_review(events):
    standing = P.open_ticket(events, False)
    if standing is None:
        return None
    steps = C.steps(C.chain_of(events))
    step = standing.get("step")
    if step not in steps or C.kind_of(step) != O.REVIEW:
        return None
    return standing


def under_review(events):
    review = open_review(events)
    if review is None or review.get("writer") != E.CLEAN_WRITER:
        return None
    steps = C.steps(C.chain_of(events))
    position = steps.index(review["step"])
    return steps[position - 1] if position else None


def artifact_of(step, project):
    if step not in O.SECTIONS:
        return None
    document = K.RESULTS if step == "50-test-impl" else K.WORKING_DOCUMENT
    return os.path.join(K.address(project), os.pardir, document)


def _same(one, two):
    return os.path.realpath(one) == os.path.realpath(two)


def _inside(path, folder):
    here = os.path.realpath(path)
    root = os.path.realpath(folder)
    return here == root or here.startswith(root + os.sep)


def _located(path, here):
    expanded = os.path.expanduser(path)
    return expanded if os.path.isabs(expanded) else os.path.join(here, expanded)


def _reviewer_at_the_door(payload):
    return bool(payload.get("agent_id"))


def _way_back(events, review, held):
    if review is not None:
        return "this review's reviewer closes it with a finding and `ROLLBACK 30`"
    standing = P.open_ticket(events, False) or {}
    if O.worked_on(standing.get("step")) in ("10-context-map", "20-plan-impl"):
        return ("this repair reworks the map or the plan, not the code — finish it; once the plan's "
                "review closes clean, the code step opens again and the code is changed there")
    if str(standing.get("step")).startswith(("92-fix", "93-rollback")):
        return ("this repair cannot change code — do not close it; ask `question misopened`: the "
                "operator's `OVERRIDE OPEN` of the review's next round voids this ticket, and that "
                "round orders `ROLLBACK 30`")
    return ("ask the operator with `question input`: their `OVERRIDE ROLLBACK 30` sends %s back to its "
            "code step" % held)


def _judge_path(path, project, payload, here=None):
    path = _located(path, here or project)
    governing = S.above(project)
    if governing is not None and S.under(path, governing):
        return (DENY, "the shell stands in %s, below the live run at %s, and there are no books "
                      "here: this guard cannot judge that run's rules from here — it would read an "
                      "empty log and allow what the root refuses. Run `cd %s` on its own, then "
                      "repeat. If the shell does not stay at %s, this session was started below "
                      "it, and Claude Code returns the shell to the folder it started in: restart "
                      "the session at %s. Nothing here has been judged against that run."
                % (project, governing, shlex.quote(governing), governing, governing))
    if _inside(path, os.path.dirname(os.path.abspath(K.__file__))):
        return (DENY, "this file is a hook: a block the party it judges can edit is a block that "
                      "party has already removed. Nothing here is written by an agent")
    if _inside(path, K.ANCHORS):
        return (DENY, "that is the head anchored outside the project: the one record that "
                      "disagrees when the log is rebuilt. A party that could write it could "
                      "truncate the books, re-chain what was left and move the anchor to match, "
                      "and nothing would say so. Only the pipeline writes it, when it appends "
                      "to the log")
    if _inside(path, os.path.join(project, ".git")):
        return (DENY, "that is inside `.git`, which is git's own state: `config` decides what a "
                      "later git command does, and `hooks/` is code that runs on the next commit. "
                      "Nothing in there is written by an agent — git writes it itself when you "
                      "run ordinary commands")
    books = K.address(project)
    name = os.path.basename(path)
    carved = any(_same(path, os.path.join(books, out)) for out in CARVED_OUT)
    if _inside(path, books) and not carved:
        return (DENY, "`%s` is the run's records folder or a file in it: what a refused attempt left, "
                      "the counts the score is computed from, the marker that says which session is "
                      "running, and the logs of the runs before this one all live in that folder, "
                      "and nothing in it is written by an agent but the two files agents append to, "
                      "`process.log` and `issues.jsonl` — every other write goes through `pipeline.py`, "
                      "which validates it" % name)
    reviewer = _reviewer_at_the_door(payload)
    try:
        events = _events(project)
        review = open_review(events)
    except (K.BadBooks, P.BadPosition, C.BadChain) as exc:
        return (DENY, "who may write cannot be answered, because the books cannot be read: %s. "
                      "The books refuse a log like this, and so does this guard — the "
                      "run cannot go on. Show the operator this: if the log can be read, `question "
                      "end`, then `archive --abandon` on their `OVERRIDE END`, ends it; if it cannot, "
                      "the operator repairs the log or moves it aside by hand" % exc)
    step = under_review(events)

    if K.running(project) and not S.ours(project, payload) and any(_same(path, paper)
                                                                   for paper in S.papers(project)):
        return (DENY, "%s is this run's, and this window is not the run's — the run belongs to "
                      "another conversation, and its working files are closed to every window but that "
                      "one while it is live. Only the operator can move the run here: ask them before "
                      "running `pipeline.py bind`; `pipeline.py status` says where it stands" % name)

    if not S.ours(project, payload):
        return (ALLOW, "")

    held = C.frozen(events)
    rel = os.path.relpath(os.path.realpath(path), os.path.realpath(project))
    if held is not None and _inside(path, project) and O.is_production(rel):
        return (DENY, "%s is production code, and the project's production code is frozen until %s "
                      "is delivered: its code review closed clean, and until then no party writes a "
                      "production file — tests, Markdown, logs, settings, test data and documents "
                      "stay writable, and "
                      "output that is not code goes to a `.log` file, outside the project or under a "
                      "test folder. The way back to the code is `ROLLBACK 30`: %s"
                % (rel, held, _way_back(events, review, held)))

    if carved:
        if name == K.ISSUES:
            if review is None:
                return (DENY, "findings are raised only while a REVIEW ticket is open, and none "
                              "is. A repair discharges findings and records that on its own line")
            if review.get("writer") == E.CLEAN_WRITER and not reviewer:
                return (DENY, "the review of %s is open and INDEPENDENT: its findings are the "
                              "reviewer's to write, not the orchestrator's" % step)
            if review.get("writer") != E.CLEAN_WRITER and reviewer:
                return (DENY, "%s is the orchestrator's own round: its writer is the orchestrator, "
                              "which is the reviewer this time, and a subagent at the door is not it"
                        % review.get("ticket"))
            return (ALLOW, "")
        if step is not None and not reviewer:
            return (DENY, "the review of %s is open and INDEPENDENT: the verdict line is the "
                          "reviewer's. Wait for it; on findings the pipeline "
                          "opens `92-fix` for you" % step)
        return (ALLOW, "")

    if step is None:
        return (ALLOW, "")
    document = artifact_of(step, project)
    if document is not None:
        if _same(path, document):
            return (DENY, "the review of %s is open and INDEPENDENT, and this is that step's "
                          "artifact. Wait for the review; on findings the pipeline opens `92-fix` for you"
                    % step)
        return (ALLOW, "")
    if not _inside(path, project):
        return (ALLOW, "")
    if any(_same(path, os.path.join(project, name)) for name in O.NOT_CODE):
        return (ALLOW, "")
    return (DENY, "the review of %s is open and INDEPENDENT, and that step's artifact is the code. "
                  "Wait for the review; on findings the pipeline opens `92-fix` for you" % step)


def _uncommented(text):
    out, quote, prev, i = [], None, None, 0
    while i < len(text):
        char = text[i]
        if quote is None and char == "\\":
            out.append(text[i:i + 2])
            prev, i = "\\", i + 2
            continue
        if quote is None and char in "'\"":
            quote = char
        elif quote == char:
            quote = None
        elif quote == '"' and char == "\\":
            out.append(text[i:i + 2])
            prev, i = "\\", i + 2
            continue
        elif quote is None and char == "#" and (prev is None or prev.isspace()
                                                or prev in _PUNCTUATION):
            newline = text.find("\n", i)
            i = len(text) if newline < 0 else newline
            continue
        elif quote is None and char == "\n":
            out.append(" ; ")
            prev, i = ";", i + 1
            continue
        out.append(char)
        prev, i = char, i + 1
    return "".join(out)


def _shlexed(text):
    lexer = shlex.shlex(text, posix=True, punctuation_chars=_PUNCTUATION)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError as exc:
        raise Unreadable("this command cannot be read as shell (%s), so nothing in it can be "
                         "judged — and bash would not run it as it stands either" % exc)


def _heredoc_terminator(line):
    try:
        tokens = _shlexed(_uncommented(line))
    except Unreadable:
        return None
    for position, token in enumerate(tokens[:-1]):
        if token in ("<<", "<<-"):
            return tokens[position + 1]
    return None


def _strip_heredocs(command):
    kept, terminator = [], None
    for raw in command.split("\n"):
        if terminator is not None:
            if raw.strip() == terminator:
                terminator = None
            continue
        kept.append(raw)
        terminator = _heredoc_terminator(raw)
    return "\n".join(kept)


def _segments(command):
    tokens = _shlexed(_uncommented(_strip_heredocs(_arithmetic_masked(command))))
    out, current = [], []
    for token in tokens:
        if token in _SEPARATORS:
            out.append(current)
            current = []
        else:
            current.append(token)
    out.append(current)
    return [segment for segment in out if segment]


_ARITHMETIC_BODY = re.compile(r"\A(?:[A-Za-z0-9_ \t+\-*/%<>=!?:(),~^]"
                              r"|\$[A-Za-z_][A-Za-z0-9_]*|\$\{[A-Za-z_][A-Za-z0-9_]*\})*\Z")


def _arithmetic_masked(command):
    out, i = [], 0
    while True:
        start = command.find("$((", i)
        if start < 0:
            out.append(command[i:])
            return "".join(out)
        end = _arithmetic_end(command, start + 3)
        body = command[start + 3:end] if end is not None else None
        if (body is None or (start and command[start - 1] in "\\$")
                or not _ARITHMETIC_BODY.match(body)):
            out.append(command[i:start + 3])
            i = start + 3
            continue
        out.append(command[i:start + 3] + body.replace(">", "_").replace("<", "_") + "))")
        i = end + 2


def _arithmetic_end(text, position):
    depth = 2
    while position < len(text):
        char = text[position]
        if char == "(":
            depth += 1
        elif char == ")":
            if depth == 2:
                return position if text[position + 1:position + 2] == ")" else None
            depth -= 1
        position += 1
    return None


def _command_words(segment):
    words = list(segment)
    while words and (re.match(r"^\w+=", words[0]) or words[0] in _PREFIX_WORDS):
        words.pop(0)
    return words


def _pipeline_argv(segment):
    words = _command_words(segment)
    if not words:
        return None
    if _is_pipeline(words[0]):
        return words[1:]
    if re.match(r"^python[0-9.]*$", os.path.basename(words[0])):
        rest = words[1:]
        while rest and rest[0].startswith("-"):
            rest.pop(0)
        if rest and _is_pipeline(rest[0]):
            return rest[1:]
    return None


def _is_pipeline(word):
    return os.path.basename(word) == "pipeline.py"


def _runs_pipeline(segment):
    return _pipeline_argv(segment) is not None


def _legal_pipeline_call(segment):
    argv = _pipeline_argv(segment)
    if argv is None:
        return False
    return bool(argv) and argv[0] in LEGIT


def _redirect_targets(segment):
    return [segment[position + 1] for position, token in enumerate(segment[:-1])
            if _is_redirect(token) and not _is_redirect(segment[position + 1])
            and segment[position + 1] not in _SEPARATORS
            and not (token.endswith("&") and _DESCRIPTOR.match(segment[position + 1]))]


_DESCRIPTOR = re.compile(r"\A(?:[0-9]+|-)\Z")


def _is_redirect(token):
    return bool(token) and set(token) <= set(_PUNCTUATION) and ">" in token


def _arguments(words):
    out, skip = [], False
    for position, word in enumerate(words):
        if skip:
            skip = False
            continue
        if word and set(word) <= set(_PUNCTUATION) and ("<" in word or ">" in word):
            skip = True
            if out and out[-1].isdigit():
                out.pop()
            continue
        out.append(word)
    return out


def _verb_targets(segment):
    words = _command_words(segment)
    if not words:
        return []
    verb = os.path.basename(words[0])
    if verb in IN_PLACE_VERBS and not any(w.startswith("-i") for w in words[1:]):
        return []
    if verb not in WRITE_VERBS + IN_PLACE_VERBS:
        return []
    return [w.split("=", 1)[1] if verb == "dd" and "=" in w else w
            for w in words[1:] if not w.startswith("-")]


def _judge_command(command, project, payload):
    try:
        segments = _segments(command)
    except Unreadable as exc:
        return (DENY, str(exc))
    here, pushed = project, []
    for segment in segments:
        moved = _destination(segment, here, pushed)
        if moved is not _NOT_A_MOVE:
            here, pushed = moved
            continue
        if _runs_pipeline(segment) and not _legal_pipeline_call(segment):
            return (DENY, "`pipeline.py` is exempt for its own subcommands — %s — and this names "
                          "none of them" % ", ".join(LEGIT))
        for target in _redirect_targets(segment) + _verb_targets(segment):
            if here is None and not os.path.isabs(os.path.expanduser(target)):
                return (DENY, "this command moves the shell somewhere this hook cannot work out — "
                              "`cd -`, a variable, or a bare `pushd` — so a relative path after it "
                              "names a file nobody can identify, and a write that cannot be "
                              "judged is not allowed. Use an absolute path, or change directory "
                              "to one written out in full")
            answer = _judge_path(target, project, payload, here)
            if answer[0] == DENY:
                if "$" in target:
                    return (DENY, "%s. `%s` holds a variable, and this hook does not read "
                                  "variables: it judged that path as written. If you meant another "
                                  "path, write it in full" % (answer[1].rstrip("."), target))
                return answer
    return (ALLOW, "")


_NOT_A_MOVE = object()

_MOVERS = ("cd", "pushd", "popd")

_EXPANDS = ("$", "*", "?", "[", "`")

_CD_FLAGS = ("-P", "-L", "-e", "-@")


def _destination(segment, here, pushed):
    words = _command_words(segment)
    if not words or os.path.basename(words[0]) not in _MOVERS:
        return _NOT_A_MOVE
    verb, args = os.path.basename(words[0]), words[1:]
    flags = [word for word in args if word.startswith(("-", "+"))]
    named = [word for word in args if word not in flags]
    if verb == "cd":
        if [flag for flag in flags if flag not in _CD_FLAGS] or len(named) > 1:
            return (None, pushed)
        if not named:
            return (os.path.expanduser("~"), pushed)
        return ((None, pushed) if _expanded(named[0])
                else (_joined(here, named[0]), pushed))
    if verb == "pushd":
        if flags or len(named) != 1 or _expanded(named[0]):
            return (None, pushed)
        return (_joined(here, named[0]), pushed + [here])
    if flags or named or not pushed:
        return (None, [])
    return (pushed[-1], pushed[:-1])


def _expanded(word):
    return any(mark in word for mark in _EXPANDS)


def _joined(here, target):
    if here is None:
        return None
    return os.path.realpath(os.path.join(here, os.path.expanduser(target)))


def decide(payload, project):
    tool = payload.get("tool_name")
    if tool == "Bash":
        command = payload.get("tool_input", {}).get("command", "")
        import undo_block as U
        answer = _judge_command(command, project, payload)
        if answer[0] == DENY:
            return (DENY, answer[1] + U.overruled(command, project))
        return U.judge(command, project, payload)
    if tool in WRITE_TOOLS:
        given = payload.get("tool_input", {})
        path = next((given[field] for field in PATH_FIELDS if given.get(field)), "")
        if not path:
            return (ALLOW, "")
        return _judge_path(path, project, payload)
    return (ALLOW, "")


def _names_pipeline(command):
    try:
        return any(_runs_pipeline(segment) for segment in _segments(command))
    except Unreadable:
        return False


def marker_path(project):
    return os.path.join(K.address(project), MARKER)


def write_marker(project, payload, clock):
    if payload.get("tool_name") != "Bash" or not _names_pipeline(
            payload.get("tool_input", {}).get("command", "")):
        return None
    caller = SUB if _reviewer_at_the_door(payload) else MAIN
    try:
        os.makedirs(K.address(project), exist_ok=True)
        with open(marker_path(project), "w") as handle:
            json.dump({"caller": caller, "at": clock(),
                       "session": payload.get("session_id") or None}, handle, sort_keys=True)
    except OSError:
        return None
    return caller


def _age(one, two):
    stamp = "%Y-%m-%dT%H:%M:%SZ"
    return (datetime.datetime.strptime(two, stamp)
            - datetime.datetime.strptime(one, stamp)).total_seconds()


def read_marker_record(project, clock):
    try:
        with open(marker_path(project)) as handle:
            record = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict):
        return None
    try:
        if _age(record.get("at", ""), clock()) > CALLER_MAX_AGE:
            return None
    except (TypeError, ValueError):
        return None
    return record


def read_marker(project, clock):
    record = read_marker_record(project, clock)
    return None if record is None else record.get("caller")


def from_fork(project, clock):
    return read_marker(project, clock) == SUB


def spend_marker(project):
    try:
        os.remove(marker_path(project))
    except OSError:
        return False
    return True


def _instruction(text):
    stripped = text.strip()
    for name in INSTRUCTIONS:
        if name in BARE and stripped == name:
            return (name, "")
        if stripped.startswith(name + " ") and stripped[len(name):].strip():
            return (name, stripped[len(name):].strip())
    return None


_BROWSER_BLOCK = re.compile(r"\A\s*<browser_instruction>.*?</browser_instruction>\s*", re.DOTALL)
_PASTED = re.compile(r"\A\s*<pasted_content\b[^>\n]*>[ \t]*\n?([^\n]*)\n?[ \t]*</pasted_content\b[^>\n]*>\s*\Z")


def _unwrapped(prompt):
    text = _BROWSER_BLOCK.sub("", prompt, count=1)
    whole = _PASTED.match(text)
    return whole.group(1) if whole else text


def _open_question(events):
    return F.waiting(events)


def override(payload, project, clock):
    prompt = _unwrapped(payload.get("prompt", "") or "")
    parsed = _instruction(prompt)
    if parsed is None and not KEYED.fullmatch(prompt):
        return None
    if parsed is None and not S.ours(project, payload):
        return None
    try:
        events = _events(project)
        question = _open_question(events)
    except (K.BadBooks, P.BadPosition, C.BadChain, F.BadFloor):
        return None
    if question is None:
        return None
    text = prompt.strip() if parsed is not None else F.chosen(question, prompt)
    if text is None:
        return None
    try:
        return K.append_event(project, E.make_event(
            "override", clock, text=text,
            question=question.get("qid"), ticket=question.get("ticket")))
    except (K.BadBooks, E.BadEvent):
        return None


def clicked(payload, project, clock):
    if payload.get("tool_name") != "AskUserQuestion" or payload.get("permission_mode") not in MEASURED_MODES:
        return None
    if not S.ours(project=project, payload=payload):
        return None
    response = payload.get("tool_response")
    answers = response.get("answers") if isinstance(response, dict) else None
    if not isinstance(answers, dict):
        return None
    try:
        question = _open_question(_events(project))
    except (K.BadBooks, P.BadPosition, C.BadChain, F.BadFloor):
        return None
    if question is None:
        return None
    replies = _replies_clicked(question, (payload.get("tool_input") or {}).get("questions") or [], answers)
    if replies is None:
        return None
    if question.get("asks") == F.OBSERVE:
        text = "ANSWER %s" % replies[0][1]
    elif all(key for _part, _label, key in replies):
        text = F.chosen(question, " ".join(key for _part, _label, key in replies))
    else:
        text = "%s %s" % (F.OTHER, replies[0][1] if len(replies) == 1 else
                          "; ".join("part %s: %s" % (part, label) for part, label, _key in replies))
    try:
        return K.append_event(project, E.make_event(
            "override", clock, text=text,
            question=question.get("qid"), ticket=question.get("ticket")))
    except (K.BadBooks, E.BadEvent):
        return None


def _replies_clicked(question, asked, answers):
    keyed = F.keys(question)
    named = F.labels(question)
    parts = question.get(E.OPTIONS) or []
    many = F.is_content(question) and len(parts) > 1
    texts = [one.get("question") for one in asked]
    if len(set(texts)) != len(texts):
        return None
    got = {}
    for one in asked:
        header = SHEET_HEADER.fullmatch(str(one.get("header", "")))
        if header is None or header.group(1) != question.get("qid") or one.get("multiSelect"):
            return None
        part = header.group(2) or ""
        label = answers.get(one.get("question"))
        if part in got or not isinstance(label, str) or not label.strip():
            return None
        offered = ([(key, meaning) for key, meaning in keyed if key[:-1] == part]
                   if question.get("asks") != F.OBSERVE else [(None, option) for option in (parts or [[]])[0]])
        match = [(key, meaning) for key, meaning in offered if label in (meaning, named.get(meaning))]
        if not match and label.endswith(RECOMMENDED):
            match = [(key, meaning) for key, meaning in offered
                     if label[:-len(RECOMMENDED)] in (meaning, named.get(meaning))]
        got[part] = (match[0][1], match[0][0]) if match else (label.strip(), None)
    wanted = [str(p + 1) for p in range(len(parts))] if many else [""]
    if sorted(got) != wanted:
        return None
    return [(part, got[part][0], got[part][1]) for part in wanted]


def source_of(name):
    import inspect
    return inspect.getsource(globals()[name])


def main(argv, stdin, stdout):
    try:
        payload = json.load(stdin)
    except ValueError:
        return 0
    project = payload.get("cwd") or os.getcwd()
    if payload.get("hook_event_name") == "UserPromptSubmit":
        override(payload, project, _now)
        import undo_block as U
        U.authorise(payload, project, _now)
        return 0
    if payload.get("hook_event_name") == "PostToolUse":
        clicked(payload, project, _now)
        return 0
    write_marker(project, payload, _now)
    permission, reason = decide(payload, project)
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                      "permissionDecision": permission,
                                      "permissionDecisionReason": reason}}, stdout)
    return 0


def _now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin, sys.stdout))
